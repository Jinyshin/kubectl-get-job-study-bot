import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import config
import database

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="통계", description="개인 주간 통계를 조회합니다.")
    async def stats(self, interaction: discord.Interaction, 멤버: discord.Member = None):

        if interaction.channel_id != config.CH_STATS:
            await interaction.response.send_message(
                f"<#{config.CH_STATS}> 채널에서만 사용 가능합니다.", ephemeral=True)
            return

        target = 멤버 or interaction.user
        now = datetime.now(config.KST)
        today = now.date()
        week_start = today - timedelta(days=today.weekday())

        with database.get_conn() as conn:
            c = conn.cursor()

            # 기상 챌린지 참여 여부
            c.execute("SELECT COUNT(*) FROM weekly_participants WHERE discord_id = ? AND week_start = ?",
                      (str(target.id), week_start))
            is_participant = c.fetchone()[0] > 0

            # 이번 주 기상 인증 횟수
            c.execute("""
                SELECT COUNT(*) FROM wake_logs
                WHERE discord_id = ? AND DATE(certified_at) >= ?
            """, (str(target.id), week_start))
            wake_count = c.fetchone()[0]

            # 이번 주 코테 인증 횟수
            c.execute("""
                SELECT COUNT(*) FROM ct_logs
                WHERE discord_id = ? AND DATE(certified_at) >= ?
            """, (str(target.id), week_start))
            ct_count = c.fetchone()[0]

            # 데일리 인증 전체 누적
            c.execute("SELECT COUNT(*) FROM daily_logs WHERE discord_id = ?",
                      (str(target.id),))
            daily_total = c.fetchone()[0]

            # 이번 주 데일리 인증 횟수
            c.execute("""
                SELECT COUNT(*) FROM daily_logs
                WHERE discord_id = ? AND DATE(certified_at) >= ?
            """, (str(target.id), week_start))
            daily_week = c.fetchone()[0]

        # 기상 달성률
        weekday = today.weekday()  # 0=월 ~ 4=금
        total_days = min(weekday + 1, 5)  # 오늘까지 평일 수
        wake_pct = int(wake_count / total_days * 100) if is_participant and total_days > 0 else 0

        embed = discord.Embed(
            title=f"📊 {target.display_name}님의 이번 주 통계",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="☀️ 기상 챌린지",
            value=f"{'참여중' if is_participant else '미참여'} | {wake_count}/{total_days} ({wake_pct}%)" if is_participant else "이번 주 미참여",
            inline=False
        )
        embed.add_field(
            name="💻 코테 인증",
            value=f"이번 주 {ct_count}회",
            inline=False
        )
        embed.add_field(
            name="📝 데일리 인증",
            value=f"이번 주 {daily_week}회 | 누적 {daily_total}회",
            inline=False
        )

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Stats(bot))