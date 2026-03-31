"""기상 챌린지 모집 메시지를 수동으로 한 번 전송하는 스크립트"""
import asyncio
import discord
import config
import database
from datetime import datetime, timedelta

async def main():
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        channel = client.get_channel(config.CH_WAKE)
        if not channel:
            print(f"CH_WAKE 채널을 찾을 수 없습니다: {config.CH_WAKE}")
            await client.close()
            return

        msg = await channel.send(
            "🌅 **이번 주 기상 챌린지 참여자 모집!**\n"
            "이 메시지에 아무 리액션이나 달면 참가자로 등록됩니다."
        )
        await msg.add_reaction("✅")

        now = datetime.now(config.KST)
        week_start = (now - timedelta(days=now.weekday())).date()

        database.init_db()
        with database.get_conn() as conn:
            c = conn.cursor()
            c.execute("INSERT INTO wake_recruit_messages (message_id, week_start) VALUES (?, ?)",
                      (str(msg.id), week_start))
            conn.commit()

        print(f"모집 메시지 전송 완료 (message_id={msg.id}, week_start={week_start})")
        await client.close()

    await client.start(config.TOKEN)

asyncio.run(main())
