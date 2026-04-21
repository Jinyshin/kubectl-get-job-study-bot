import discord
from discord.ext import commands
import random
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
            # 길드 커맨드 정리 (이전 길드 sync로 등록된 중복 제거)
            if config.GUILD_ID:
                guild = discord.Object(id=config.GUILD_ID)
                bot.tree.clear_commands(guild=guild)
                await bot.tree.sync(guild=guild)
            synced = await bot.tree.sync()
            _synced = True
            print(f"슬래시 커맨드 동기화 완료: {len(synced)}개 커맨드")
        except Exception as e:
            print(f"슬래시 커맨드 동기화 실패: {e}")

_WELCOME_MESSAGES = [
    "{mention}님 어서오세요! 먼저 [서버 활용법]({url})을 확인해주세요",
    "{mention}님 반가워요! [서버 활용법]({url}) 한번 읽어봐주세요",
    "{mention}님 환영해요! [서버 활용법]({url})부터 확인해주세요",
    "{mention}님이 나타났다! [서버 활용법]({url}) 먼저 확인 부탁드려요",
    "{mention}님 입장! [서버 활용법]({url})을 먼저 확인해주세요",
    "{mention}님 오셨군요! [서버 활용법]({url}) 확인부터 해주세요",
    "어서와요 {mention}님! [서버 활용법]({url})을 먼저 읽어봐주세요",
    "새로운 동료 {mention}님! [서버 활용법]({url}) 먼저 확인해주세요",
    "반가워요 {mention}님! [서버 활용법]({url})부터 확인해주세요",
]
_WELCOME_EMOJIS = ["\U0001f44b", "\U0001f389", "\u2728", "\U0001f64c", "\U0001f4aa", "\U0001f917", "\U0001fae1", "\U0001f60a"]

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: Exception):
    print(f"슬래시 커맨드 에러 [{interaction.command.name}]: {error}")

@bot.event
async def on_member_join(member: discord.Member):
    channel = bot.get_channel(config.CH_WELCOME)
    if not channel:
        return
    msg = random.choice(_WELCOME_MESSAGES).format(mention=member.mention, url=config.WELCOME_GUIDE_URL)
    emoji = random.choice(_WELCOME_EMOJIS)
    await channel.send(f"{msg} {emoji}")

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

        # 메시지에 남은 리액션 확인
        channel = bot.get_channel(payload.channel_id)
        if not channel:
            return
        message = await channel.fetch_message(payload.message_id)
        for reaction in message.reactions:
            users = [user async for user in reaction.users()]
            if any(user.id == payload.user_id for user in users):
                return  # 아직 다른 리액션이 남아있으면 취소 안 함

        # 모든 리액션을 뺐을 때만 참여 취소
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