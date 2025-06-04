# bot/cogs/test_slash_cog.py
import nextcord
from nextcord.ext import commands
import traceback
from core.icons import ICON_INFO, ICON_ERROR # Giả sử bạn có các icon này

class TestSlashCog(commands.Cog, name="Test Slash Cog"):
    def __init__(self, bot):
        self.bot = bot
        print(f"{ICON_INFO} [TEST COG] TestSlashCog initialized.")

    @nextcord.slash_command(name="pingtest", description="Lệnh test slash đơn giản.")
    async def pingtest(self, interaction: nextcord.Interaction):
        print(f"{ICON_INFO} [TEST COG] /pingtest invoked by {interaction.user.name}")
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
            print(f"{ICON_INFO} [TEST COG] /pingtest deferred.")
            await interaction.followup.send("Pong! Lệnh test slash hoạt động!", ephemeral=True)
            print(f"{ICON_INFO} [TEST COG] /pingtest followup sent.")
        except Exception as e:
            print(f"{ICON_ERROR} [TEST COG] Error in /pingtest: {e}")
            traceback.print_exc()

def setup(bot):
    bot.add_cog(TestSlashCog(bot))
