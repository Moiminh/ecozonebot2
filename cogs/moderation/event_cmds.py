# bot/cogs/moderation/event_cmds.py
import nextcord
from nextcord.ext import commands
from datetime import datetime, timedelta, timezone # Cần cho việc tính toán thời gian sự kiện
import logging

# Import các thành phần cần thiết từ 'core'
from core.database import get_guild_config, save_guild_config
from core.utils import is_bot_moderator, try_send # is_bot_moderator để check quyền, try_send để gửi tin nhắn
from core.config import COMMAND_PREFIX # Có thể cần để hiển thị ví dụ lệnh
from core.icons import ICON_SUCCESS, ICON_ERROR, ICON_INFO, ICON_ADMIN_PANEL # Hoặc các icon bạn muốn dùng

logger = logging.getLogger(__name__)

# Danh sách các loại sự kiện được hỗ trợ (có thể mở rộng sau)
# Key là tên người dùng nhập vào, value là key sẽ lưu trong active_events (thường là giống nhau)
SUPPORTED_EVENT_TYPES = {
    "work": "work",
    "fish": "fish",
    "daily": "daily"
    # Thêm các loại sự kiện khác ở đây nếu cần, ví dụ: "crime", "slots"
    # Event type có thể là tên lệnh gốc mà sự kiện sẽ ảnh hưởng
}

class EventManagementCog(commands.Cog, name="Event Management"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info(f"{ICON_INFO} EventManagementCog initialized.")

    # --- Các lệnh quản lý sự kiện sẽ được thêm vào đây ---
    # Ví dụ: @commands.command(name="mod_startevent")
    #         @commands.check(is_bot_moderator)
    #         async def mod_start_event(self, ctx, ...):
    #             pass

    # Có thể thêm các lệnh khác như mod_stopevent, mod_listevents sau

def setup(bot: commands.Bot):
    bot.add_cog(EventManagementCog(bot))
    logger.info(f"EventManagementCog has been loaded.") # Thêm log khi cog được load
