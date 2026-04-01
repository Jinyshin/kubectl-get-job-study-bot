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
        await channel.send("🏃 @everyone 고생하셨슴다~ 저녁 먹기 전에 잠깐 운동하고 오시죠 ㅎㅎ")

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
            await channel_daily.send("🌙 @everyone 오늘이 가기 전에 `/데일리인증` 해주세요!")

    # 일요일 09:00 — 주간 통계 발행
    @scheduler.scheduled_job('cron', day_of_week="sun", hour=9, minute=0)
    async def weekly_stats():
        channel = bot.get_channel(config.CH_STATS)
        if not channel:
            return
        now = config.now_kst()
        week_start = (now - timedelta(days=now.weekday())).date()
        week_end_fri = week_start + timedelta(days=4)   # 기상: 월~금
        week_end_sun = week_start + timedelta(days=6)   # 코테: 월~일

        with get_conn() as conn:
            c = conn.cursor()

            # 기상 달성률 (월~금)
            c.execute("SELECT discord_id FROM weekly_participants WHERE week_start = ?", (week_start,))
            participants = [row[0] for row in c.fetchall()]

            wake_stats = []
            for uid in participants:
                c.execute("""
                    SELECT COUNT(*) FROM wake_logs
                    WHERE discord_id = ? AND DATE(certified_at) BETWEEN ? AND ?
                """, (uid, week_start, week_end_fri))
                count = c.fetchone()[0]
                wake_stats.append((uid, count))

            wake_stats.sort(key=lambda x: x[1], reverse=True)

            # 코테 횟수 (월~일)
            c.execute("""
                SELECT discord_id, COUNT(*) as cnt FROM ct_logs
                WHERE DATE(certified_at) BETWEEN ? AND ?
                GROUP BY discord_id
                ORDER BY cnt DESC
            """, (week_start, week_end_sun))
            ct_stats = c.fetchall()

        if not wake_stats and not ct_stats:
            await channel.send("📊 이번 주는 인증 기록이 없습니다.")
            return

        # 메시지 생성
        lines = [f"📊 **이번 주 스터디 현황** ({week_start} ~ {week_end_sun}, 일요일 오전 기준)\n"]

        lines.append("**기상 챌린지 달성률**")
        if wake_stats:
            for i, (uid, count) in enumerate(wake_stats):
                bar = "█" * (count * 2) + "░" * ((5 - count) * 2)
                pct = int(count / 5 * 100)
                lines.append(f"{i+1}등 <@{uid}>  {bar} {count}/5 ({pct}%)")
        else:
            lines.append("이번 주 참여자가 없습니다.")

        lines.append("\n**코테 인증 횟수**")
        if ct_stats:
            for i, (uid, count) in enumerate(ct_stats):
                lines.append(f"{i+1}등 <@{uid}>  {count}회")
        else:
            lines.append("이번 주 인증자가 없습니다.")

        await channel.send("\n".join(lines))

    def _job_error_listener(event):
        if event.exception:
            logger.error("스케줄러 job [%s] 실행 중 에러 발생", event.job_id, exc_info=event.exception)

    scheduler.add_listener(_job_error_listener, EVENT_JOB_ERROR)
    scheduler.start()
