import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import config
import database

class Coding(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="코테인증", description="코테 풀이 인증 사진을 첨부해주세요.")
    async def coding_cert(self, interaction: discord.Interaction, 인증사진: discord.Attachment):

        if not (hasattr(interaction.channel, 'parent_id') and interaction.channel.parent_id == config.CH_CODING):
            await interaction.response.send_message(
                f"<#{config.CH_CODING}> 채널의 스레드에서만 사용 가능합니다.", ephemeral=True)
            return

        # 이미지 파일인지 확인
        if not 인증사진.content_type or not 인증사진.content_type.startswith("image/"):
            await interaction.response.send_message("이미지 파일만 첨부 가능합니다.", ephemeral=True)
            return

        with database.get_conn() as conn:
            c = conn.cursor()
            now = datetime.now(config.KST)
            today = now.date()
            week_start = today - timedelta(days=today.weekday())

            # 이번 주 인증 횟수 조회
            c.execute("""
                SELECT COUNT(*) FROM ct_logs
                WHERE discord_id = ? AND DATE(certified_at) >= ?
            """, (str(interaction.user.id), week_start))
            week_count = c.fetchone()[0]

            # DB 저장
            c.execute("INSERT INTO ct_logs (discord_id, certified_at) VALUES (?, ?)",
                      (str(interaction.user.id), now))
            conn.commit()

        await interaction.response.send_message(
            f"💻 {interaction.user.mention} 코테 인증 완료! (이번 주 {week_count + 1}회째)",
            files=[await 인증사진.to_file()]
        )

async def setup(bot):
    await bot.add_cog(Coding(bot))