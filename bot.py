import discord
from discord.ext import commands
import config
import database
from scheduler import setup_scheduler

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
_synced = False

@bot.event
async def on_ready():
    global _synced
    print(f"봇 시작됨: {bot.user}")

    if not _synced:
        try:
            guild = discord.Object(id=config.GUILD_ID) if config.GUILD_ID else None
            if guild:
                bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            _synced = True
            print(f"슬래시 커맨드 동기화 완료: {len(synced)}개 커맨드")
        except Exception as e:
            print(f"슬래시 커맨드 동기화 실패: {e}")

@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    # 봇 자신의 리액션은 무시
    if payload.user_id == bot.user.id:
        return
    # 기상 채널 리액션만 처리
    if payload.channel_id != config.CH_WAKE:
        return

    with database.get_conn() as conn:
        c = conn.cursor()
        # 모집 메시지인지 확인
        c.execute("SELECT week_start FROM wake_recruit_messages WHERE message_id = ?",
                  (str(payload.message_id),))
        row = c.fetchone()
        if not row:
            return

        # weekly_participants에 등록 (중복 시 무시)
        c.execute("INSERT OR IGNORE INTO weekly_participants (discord_id, week_start) VALUES (?, ?)",
                  (str(payload.user_id), row[0]))
        conn.commit()

@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    if payload.user_id == bot.user.id:
        return
    if payload.channel_id != config.CH_WAKE:
        return

    with database.get_conn() as conn:
        c = conn.cursor()
        # 모집 메시지인지 확인
        c.execute("SELECT week_start FROM wake_recruit_messages WHERE message_id = ?",
                  (str(payload.message_id),))
        row = c.fetchone()
        if not row:
            return

        # 참여 취소
        c.execute("DELETE FROM weekly_participants WHERE discord_id = ? AND week_start = ?",
                  (str(payload.user_id), row[0]))
        conn.commit()

async def main():
    async with bot:
        database.init_db()
        setup_scheduler(bot)

        # cog 로드
        await bot.load_extension("cogs.wake")
        await bot.load_extension("cogs.coding")
        await bot.load_extension("cogs.daily")
        await bot.load_extension("cogs.stats")

        await bot.start(config.TOKEN)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())