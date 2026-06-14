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
        print(f"[run_once] on_ready 진입: {client.user}", flush=True)
        database.init_db()
        # discord.py가 시작 시 멤버를 자동 청크(chunk_guilds_at_startup 기본 True)하므로
        # on_ready 시점엔 guild.members가 이미 채워져 있다. 수동 chunk는 불필요.
        guild = client.get_guild(config.GUILD_ID)
        members = len(guild.members) if guild else 0
        print(f"[run_once] guild={guild}, 캐시된 멤버 수={members}", flush=True)
        print(f"[run_once] run_weekly_stats 실행 (dry_run={dry_run})", flush=True)
        await run_weekly_stats(client, dry_run=dry_run)
        print("[run_once] 완료, 종료합니다.", flush=True)
        await client.close()

    print("[run_once] 디스코드 연결 시도 중...", flush=True)
    await client.start(config.TOKEN)

asyncio.run(main())
