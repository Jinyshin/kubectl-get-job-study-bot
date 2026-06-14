"""주간 통계 + 청문회 소환을 수동으로 한 번 실행하는 스크립트

사용:
  python run_once_weekly_stats.py            # 실제 발송 (디스코드에 통계 + 소환장)
  python run_once_weekly_stats.py --dry-run  # 콘솔 출력만 (발송 안 함, 소환 대상 미리보기)
"""
import asyncio
import sys
import discord
import config
import database
from scheduler import run_weekly_stats

async def main():
    dry_run = "--dry-run" in sys.argv

    intents = discord.Intents.default()
    intents.members = True  # 소환 모집단(guild.members) 조회용

    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        database.init_db()
        # 방금 로그인한 직후라 멤버 캐시가 비어 있을 수 있어 강제 로드
        guild = client.get_guild(config.GUILD_ID)
        if guild:
            await guild.chunk()
        await run_weekly_stats(client, dry_run=dry_run)
        await client.close()

    await client.start(config.TOKEN)

asyncio.run(main())
