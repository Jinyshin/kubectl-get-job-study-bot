import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import config
import database

class DailyModal(discord.ui.Modal, title="데일리 인증"):
    content = discord.ui.TextInput(
        label="오늘 한 것",
        style=discord.TextStyle.long,
        placeholder="예) CJ 자소서 초안 작성 완료",
        required=True,
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):
        now = datetime.now(config.KST)

        with database.get_conn() as conn:
            c = conn.cursor()

            # 전체 누적 횟수 조회
            c.execute("SELECT COUNT(*) FROM daily_logs WHERE discord_id = ?",
                      (str(interaction.user.id),))
            total = c.fetchone()[0]

            # DB 저장
            c.execute("INSERT INTO daily_logs (discord_id, content, certified_at) VALUES (?, ?, ?)",
                      (str(interaction.user.id), self.content.value, now))
            conn.commit()

        # 날짜 포맷
        today = now.strftime("%y.%m.%d")

        # 내용 줄별로 파싱 (이미 -로 시작하면 그대로, 아니면 - 붙임)
        lines = [line.strip() for line in self.content.value.strip().splitlines() if line.strip()]
        content_str = "\n".join([line if line.startswith("-") else f"- {line}" for line in lines])

        await interaction.response.send_message(
            f"**{today} | {interaction.user.mention} {total + 1}번째 데일리 인증**\n{content_str}"
        )

class Daily(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="데일리인증", description="오늘 한 것을 기록합니다.")
    async def daily_cert(self, interaction: discord.Interaction):
        if interaction.channel_id != config.CH_DAILY:
            await interaction.response.send_message(
                f"<#{config.CH_DAILY}> 채널에서만 사용 가능합니다.", ephemeral=True)
            return
        await interaction.response.send_modal(DailyModal())

async def setup(bot):
    await bot.add_cog(Daily(bot))