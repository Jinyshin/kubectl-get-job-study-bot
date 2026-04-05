import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta
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

        if target.bot:
            await interaction.response.send_message(
                "봇의 통계는 조회할 수 없습니다.", ephemeral=True)
            return
        now = config.now_kst()
        today = now.date()
        week_start = today - timedelta(days=today.weekday())
        uid = str(target.id)

        with database.get_conn() as conn:
            c = conn.cursor()

            # 기상 챌린지 참여 여부
            c.execute("SELECT COUNT(*) FROM weekly_participants WHERE discord_id = ? AND week_start = ?",
                      (uid, week_start))
            is_participant = c.fetchone()[0] > 0

            # 이번 주 기상
            c.execute("SELECT COUNT(*) FROM wake_logs WHERE discord_id = ? AND DATE(certified_at) >= ?",
                      (uid, week_start))
            wake_week = c.fetchone()[0]

            # 누적 기상
            c.execute("SELECT COUNT(*) FROM wake_logs WHERE discord_id = ?", (uid,))
            wake_total = c.fetchone()[0]

            # 이번 주 코테
            c.execute("SELECT COUNT(*) FROM ct_logs WHERE discord_id = ? AND DATE(certified_at) >= ?",
                      (uid, week_start))
            ct_week = c.fetchone()[0]

            # 누적 코테
            c.execute("SELECT COUNT(*) FROM ct_logs WHERE discord_id = ?", (uid,))
            ct_total = c.fetchone()[0]

            # 이번 주 데일리
            c.execute("SELECT COUNT(*) FROM daily_logs WHERE discord_id = ? AND DATE(certified_at) >= ?",
                      (uid, week_start))
            daily_week = c.fetchone()[0]

            # 누적 데일리
            c.execute("SELECT COUNT(*) FROM daily_logs WHERE discord_id = ?", (uid,))
            daily_total = c.fetchone()[0]

        embed = discord.Embed(
            title=f"📊 {target.display_name}님의 통계",
            color=discord.Color.blue()
        )

        if is_participant:
            embed.add_field(name="☀️ 기상 챌린지", value=f"이번 주 참여중 {wake_week}회 | 누적 {wake_total}회", inline=False)
        else:
            embed.add_field(name="☀️ 기상 챌린지", value=f"이번 주 미참여 | 누적 {wake_total}회", inline=False)

        embed.add_field(name="💻 코테 인증", value=f"이번 주 {ct_week}회 | 누적 {ct_total}회", inline=False)
        embed.add_field(name="📝 데일리 인증", value=f"이번 주 {daily_week}회 | 누적 {daily_total}회", inline=False)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Stats(bot))