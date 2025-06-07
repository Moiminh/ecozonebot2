# bot/cogs/moderation/mod_tools_slash.py
import nextcord
from nextcord.ext import commands, application_checks
import logging

from core.utils import check_is_bot_moderator_interaction
from core.icons import ICON_ADMIN_PANEL, ICON_SUCCESS, ICON_ERROR

logger = logging.getLogger(__name__)

class ModToolsSlashCog(commands.Cog, name="Moderator Slash Tools"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("ModToolsSlashCog (v2) initialized.")

    # --- Lệnh cha /mod ---
    @nextcord.slash_command(
        name="mod", 
        description="Các công cụ dành cho Moderator của Bot"
    )
    async def mod(self, interaction: nextcord.Interaction):
        """
        Lệnh cha cho các công cụ của moderator. Lệnh này sẽ không bao giờ được thực thi trực tiếp.
        """
        pass

    # --- Lệnh con /mod ping ---
    @mod.subcommand(name="ping", description="Kiểm tra xem bạn có quyền Moderator của bot không.")
    @application_checks.check(check_is_bot_moderator_interaction)
    async def mod_ping(self, interaction: nextcord.Interaction):
        """
        Một lệnh ping đơn giản để xác nhận quyền hạn moderator.
        """
        logger.info(f"MODERATOR ACTION: {interaction.user.id} đã sử dụng '/mod ping' thành công.")
        
        await interaction.response.send_message(
            f"{ICON_SUCCESS} {interaction.user.mention}, bạn có quyền Moderator/Owner! Các lệnh `/mod` đã sẵn sàng!",
            ephemeral=True # Tin nhắn chỉ hiển thị cho người dùng lệnh
        )
    
    @mod_ping.error
    async def mod_ping_error(self, interaction: nextcord.Interaction, error: Exception):
        """
        Xử lý lỗi cho lệnh /mod ping, chủ yếu là lỗi không có quyền.
        """
        # Hàm check_is_bot_moderator_interaction đã tự gửi tin nhắn lỗi,
        # nên chúng ta chỉ cần log lại ở đây nếu cần.
        if isinstance(error, application_checks.ApplicationCheckFailure):
            logger.warning(f"User không có quyền {interaction.user.id} đã cố gắng dùng /mod ping.")
        else:
            logger.error(f"Lỗi không xác định với /mod ping: {error}", exc_info=True)
            # Gửi một tin nhắn lỗi chung nếu có lỗi khác xảy ra
            if not interaction.response.is_done():
                await interaction.response.send_message(f"{ICON_ERROR} Đã có lỗi xảy ra với lệnh này.", ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(ModToolsSlashCog(bot))
