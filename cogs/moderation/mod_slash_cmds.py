# bot/cogs/moderation/mod_slash_cmds.py
import nextcord
from nextcord.ext import commands, application_checks
import logging

# Import hàm check mới và các icon
from core.utils import check_is_bot_moderator_interaction
from core.icons import ICON_ADMIN_PANEL, ICON_SUCCESS, ICON_INFO

logger = logging.getLogger(__name__)

class ModSlashCommandsCog(commands.Cog, name="Moderator Slash Commands"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info(f"{ICON_INFO} ModSlashCommandsCog initialized.")


    mod = nextcord.SlashCommandGroup(
        "mod", 
        "Các công cụ dành cho Moderator của Ecoworld",
        default_member_permissions=nextcord.Permissions(manage_guild=True)
    )

    # --- LỆNH CON ĐẦU TIÊN: /mod ping ---
    @mod.subcommand(name="ping", description="Kiểm tra xem bạn có quyền Moderator không.")
    @application_checks.check(check_is_bot_moderator_interaction) # Áp dụng hàm check
    async def mod_ping(self, interaction: nextcord.Interaction):
        """(Moderator/Owner Only) Lệnh ping đơn giản để kiểm tra quyền moderator."""
        
        logger.info(f"MODERATOR SLASH ACTION: {interaction.user.display_name} ({interaction.user.id}) đã sử dụng '/mod ping' thành công.")
        
        # Không cần defer ở đây vì phản hồi rất nhanh
        await interaction.response.send_message(
            f"{ICON_SUCCESS} {interaction.user.mention}, bạn có quyền Moderator/Owner! Lệnh slash `/mod` hoạt động!",
            ephemeral=True # Chỉ người gọi lệnh thấy
        )
    

def setup(bot: commands.Bot):
    bot.add_cog(ModSlashCommandsCog(bot))
