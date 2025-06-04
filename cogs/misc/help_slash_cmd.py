# bot/cogs/misc/help_slash_cmd.py
import nextcord
from nextcord.ext import commands
import traceback 

from core.icons import ICON_INFO, ICON_ERROR 

class HelpSlashCommandCog(commands.Cog, name="Help Slash Command SUPER DEBUG"): # Đổi tên Cog
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"{ICON_INFO} [SUPER DEBUG] HelpSlashCommandCog (SUPER DEBUG version) initialized.")

    @nextcord.slash_command(name="help", description=f"{ICON_INFO} Test help command.") # Bỏ SlashOption
    async def help_slash_command(self, interaction: nextcord.Interaction):
        print(f"{ICON_INFO} [SUPER DEBUG] /help SUPER DEBUG invoked by {interaction.user.name}.")
        try:
            print(f"{ICON_INFO} [SUPER DEBUG] Attempting to defer (SUPER DEBUG)...")
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
            print(f"{ICON_INFO} [SUPER DEBUG] Interaction deferred (SUPER DEBUG).")
            
            await interaction.followup.send(content=f"{ICON_INFO} SUPER DEBUG /help response!", ephemeral=True)
            print(f"{ICON_INFO} [SUPER DEBUG] Followup sent for SUPER DEBUG /help.")

        except Exception as e:
            print(f"{ICON_ERROR} [SUPER DEBUG] Error in /help SUPER DEBUG command:")
            traceback.print_exc()
            try:
                if interaction.response.is_done() and not interaction.is_expired():
                    await interaction.followup.send(content=f"{ICON_ERROR} Lỗi trong /help SUPER DEBUG.", ephemeral=True)
            except Exception as followup_e:
                print(f"{ICON_ERROR} [SUPER DEBUG] Failed to send error followup for /help SUPER DEBUG: {followup_e}")

def setup(bot: commands.Bot):
    bot.add_cog(HelpSlashCommandCog(bot))
