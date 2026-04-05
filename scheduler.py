from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.events import EVENT_JOB_ERROR
import config
from database import get_conn
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="Asia/Seoul")

def setup_scheduler(bot):

    # 토요일 09:00 — 기상 챌린지 참여자 모집
    @scheduler.scheduled_job('cron', day_of_week="sat", hour=9, minute=0)
    async def wake_recruit():
        channel = bot.get_channel(config.CH_WAKE)
        if not channel:
            logger.warning("CH_WAKE 채널을 찾을 수 없습니다: %s", config.CH_WAKE)
            return
        msg = await channel.send(
            "🌅 **다음 주 기상 챌린지 참여자 모집!**\n"
            "이 메시지에 아무 리액션이나 달면 참가자로 등록됩니다.\n"
            "마감: 일요일 오후 9시"
        )
        await msg.add_reaction("✅")

        # 다음 주 월요일을 week_start로 저장
        now = config.now_kst()
        next_monday = (now + timedelta(days=(7 - now.weekday()))).date()
        with get_conn() as conn:
            c = conn.cursor()
            c.execute("INSERT INTO wake_recruit_messages (message_id, week_start) VALUES (?, ?)",
                      (str(msg.id), next_monday))
            conn.commit()

    # 월~금 06:00 — 기상 인증 스레드 생성
    @scheduler.scheduled_job('cron', day_of_week="mon-fri", hour=6, minute=0)
    async def wake_thread():
        channel = bot.get_channel(config.CH_WAKE)
        if not channel:
            return
        today = config.format_date(config.now_kst())
        msg = await channel.send(f"☀️ {today} 기상 인증 스레드")
        await msg.create_thread(name=f"{today} 기상 인증")

    # 월~금 09:00 — 기상 미인증자 멘션
    @scheduler.scheduled_job('cron', day_of_week="mon-fri", hour=9, minute=0)
    async def wake_remind():
        channel = bot.get_channel(config.CH_WAKE)
        if not channel:
            return

        # 이번 주 참여자 + 오늘 인증한 사람 조회
        now = config.now_kst()
        week_start = (now - timedelta(days=now.weekday())).date()
        today = now.date()
        with get_conn() as conn:
            c = conn.cursor()
            c.execute("SELECT discord_id FROM weekly_participants WHERE week_start = ?", (week_start,))
            participants = [row[0] for row in c.fetchall()]
            c.execute("SELECT discord_id FROM wake_logs WHERE DATE(certified_at) = ?", (today,))
            certified = [row[0] for row in c.fetchall()]

        # 미인증자 멘션
        not_certified = [p for p in participants if p not in certified]
        if not_certified:
            mentions = " ".join([f"<@{uid}>" for uid in not_certified])
            await channel.send(f"{mentions}\n일어나세요!!!! 아침이 밝았습니다")

    # 매일 06:00 — 코테 인증 스레드 생성 + 전날 인증자 멘션
    @scheduler.scheduled_job('cron', hour=6, minute=0)
    async def coding_thread():
        channel = bot.get_channel(config.CH_CODING)
        if not channel:
            return
        now = config.now_kst()
        today = config.format_date(now)
        yesterday = (now - timedelta(days=1)).date()

        # 전날 인증자 조회
        with get_conn() as conn:
            c = conn.cursor()
            c.execute("SELECT discord_id FROM ct_logs WHERE DATE(certified_at) = ?", (yesterday,))
            certified = [row[0] for row in c.fetchall()]

        if certified:
            mentions = " ".join([f"<@{uid}>" for uid in certified])
            msg = await channel.send(
                f"💻 **{today} 코테 인증 스레드**\n"
                f"어제 푸느라 고생했어요 👍👍👍 {mentions} 오늘도 풀자~!!!"
            )
        else:
            msg = await channel.send(f"💻 **{today} 코테 인증 스레드**\n오늘도 코테 풀자~!")

        thread = await msg.create_thread(name=f"{today} 코테 인증")
        with get_conn() as conn:
            c = conn.cursor()
            c.execute("INSERT INTO ct_threads (date, thread_id) VALUES (?, ?)",
                      (now.date(), str(thread.id)))
            conn.commit()

    # 매일 18:00 — 운동 알림
    @scheduler.scheduled_job('cron', hour=18, minute=0)
    async def exercise_remind():
        channel = bot.get_channel(config.CH_FREE)
        if not channel:
            return
        await channel.send("🏃 고생하셨슴다~ 저녁 먹기 전에 잠깐 운동하고 오시죠 ㅎㅎ")

    # 매일 23:00 — 코테 + 데일리 인증 마감 알림
    @scheduler.scheduled_job('cron', hour=23, minute=0)
    async def night_remind():
        # 오늘자 코테 스레드에 알림
        now = config.now_kst()
        with get_conn() as conn:
            c = conn.cursor()
            c.execute("SELECT thread_id FROM ct_threads WHERE date = ?", (now.date(),))
            row = c.fetchone()
        if row:
            thread = bot.get_channel(int(row[0]))
            if thread:
                await thread.send("아직 안풀었나여? 한 시간 남았는데 빨리 푸시죠")

        # 데일리 마감 알림
        channel_daily = bot.get_channel(config.CH_DAILY)
        if channel_daily:
            await channel_daily.send("🌙 오늘이 가기 전에 `/데일리인증` 해주세요!")

    # 일요일 09:00 — 주간 통계 발행
    @scheduler.scheduled_job('cron', day_of_week="sun", hour=9, minute=0)
    async def weekly_stats():
        channel = bot.get_channel(config.CH_STATS)
        if not channel:
            return
        now = config.now_kst()
        week_start = (now - timedelta(days=now.weekday())).date()
        week_end_fri = week_start + timedelta(days=4)
        week_end_sun = week_start + timedelta(days=6)

        with get_conn() as conn:
            c = conn.cursor()

            # 기상 (월~금)
            c.execute("""
                SELECT discord_id, COUNT(*) FROM wake_logs
                WHERE DATE(certified_at) BETWEEN ? AND ?
                GROUP BY discord_id
            """, (week_start, week_end_fri))
            wake_map = dict(c.fetchall())

            # 코테 (월~일)
            c.execute("""
                SELECT discord_id, COUNT(*) FROM ct_logs
                WHERE DATE(certified_at) BETWEEN ? AND ?
                GROUP BY discord_id
            """, (week_start, week_end_sun))
            ct_map = dict(c.fetchall())

            # 데일리 (월~일)
            c.execute("""
                SELECT discord_id, COUNT(*) FROM daily_logs
                WHERE DATE(certified_at) BETWEEN ? AND ?
                GROUP BY discord_id
            """, (week_start, week_end_sun))
            daily_map = dict(c.fetchall())

        # 인증 기록이 있는 모든 사람
        all_uids = set(wake_map) | set(ct_map) | set(daily_map)
        if not all_uids:
            await channel.send("📊 이번 주는 인증 기록이 없습니다.")
            return

        # 총합 높은 순 정렬
        stats = []
        for uid in all_uids:
            w = wake_map.get(uid, 0)
            ct = ct_map.get(uid, 0)
            d = daily_map.get(uid, 0)
            stats.append((uid, w, ct, d, w + ct + d))
        stats.sort(key=lambda x: x[4], reverse=True)

        week_start_fmt = config.format_date(datetime.combine(week_start, datetime.min.time()))
        week_end_fmt = config.format_date(datetime.combine(week_end_sun, datetime.min.time()))
        lines = [f"📊 **이번 주 스터디 현황** ({week_start_fmt} ~ {week_end_fmt})\n"]

        for uid, w, ct, d, _ in stats:
            parts = []
            if w: parts.append(f"기상 {w}회")
            if ct: parts.append(f"코테 {ct}회")
            if d: parts.append(f"데일리 {d}회")
            lines.append(f"<@{uid}> — {' | '.join(parts)}")

        await channel.send("\n".join(lines))

    def _job_error_listener(event):
        if event.exception:
            logger.error("스케줄러 job [%s] 실행 중 에러 발생", event.job_id, exc_info=event.exception)

    scheduler.add_listener(_job_error_listener, EVENT_JOB_ERROR)
    scheduler.start()
