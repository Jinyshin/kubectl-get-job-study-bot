import discord
from discord.ext import commands
from discord import app_commands
import config
import database

class Wake(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="기상인증", description="현재 시간이 보이는 사진을 첨부해주세요.")
    async def wake_cert(self, interaction: discord.Interaction, 인증사진: discord.Attachment):

        if not (hasattr(interaction.channel, 'parent_id') and interaction.channel.parent_id == config.CH_WAKE):
            await interaction.response.send_message(
                f"<#{config.CH_WAKE}> 채널의 스레드에서만 사용 가능합니다.", ephemeral=True)
            return

        # 이미지 파일인지 확인
        if not 인증사진.content_type or not 인증사진.content_type.startswith("image/"):
            await interaction.response.send_message("이미지 파일만 첨부 가능합니다.", ephemeral=True)
            return

        now = config.now_kst()
        today = now.date()

        with database.get_conn() as conn:
            c = conn.cursor()

            # 오늘 이미 인증했는지 확인
            c.execute("SELECT id FROM wake_logs WHERE discord_id = ? AND DATE(certified_at) = ?",
                      (str(interaction.user.id), today))
            already_certified = c.fetchone() is not None

            if not already_certified:
                c.execute("INSERT INTO wake_logs (discord_id, certified_at) VALUES (?, ?)",
                          (str(interaction.user.id), now))
                conn.commit()

        if already_certified:
            await interaction.response.send_message("오늘 이미 기상 인증을 완료했습니다 ✅", ephemeral=True)
            return

        await interaction.response.send_message(
            f"☀️ {interaction.user.mention} 기상 인증 완료!",
            files=[await 인증사진.to_file()]
        )

async def setup(bot):
    await bot.add_cog(Wake(bot))