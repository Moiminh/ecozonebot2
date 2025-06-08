import nextcord
from nextcord.ext import commands
from datetime import datetime, timedelta
import logging 

from .config import MODERATOR_USER_IDS
from .database import load_economy_data, get_or_create_guild_config, load_moderator_ids
from .icons import ICON_ERROR
from .config import WANTED_LEVEL_CRIMINAL_THRESHOLD, CITIZEN_TITLES, CRIMINAL_TITLES
utils_logger = logging.getLogger(__name__)
def get_player_title(level: int, wanted_level: float) -> str:
    
    title_map = CRIMINAL_TITLES if wanted_level >= WANTED_LEVEL_CRIMINAL_THRESHOLD else CITIZEN_TITLES
    
    current_title = ""
    for level_threshold, title in sorted(title_map.items(), reverse=True):
        if level >= level_threshold:
            current_title = title
            break
            
import nextcord
from nextcord.ext import commands
from datetime import datetime, timedelta
import logging 
from functools import wraps

# [CẢI TIẾN] Import các hàm cần thiết cho decorator
from .database import load_economy_data, get_or_create_global_user_profile
from .travel_manager import handle_travel_event
from .config import MODERATOR_USER_IDS, WANTED_LEVEL_CRIMINAL_THRESHOLD, CITIZEN_TITLES, CRIMINAL_TITLES
from .icons import ICON_ERROR

utils_logger = logging.getLogger(__name__)

# [CẢI TIẾN] Decorator để tự động kiểm tra sự kiện "du lịch"
def require_travel_check(func):
    @wraps(func)
    async def wrapper(cog_instance, ctx, *args, **kwargs):
        if not ctx.guild:
            # Bỏ qua check nếu lệnh được dùng trong DM hoặc không có guild context
            return await func(cog_instance, ctx, *args, **kwargs)

        author_id = ctx.author.id
        guild_id = ctx.guild.id
        
        # Sử dụng economy_data từ bot cache nếu có, nếu không thì load
        economy_data = getattr(cog_instance.bot, 'economy_data', load_economy_data())
        global_profile = get_or_create_global_user_profile(economy_data, author_id)

        if global_profile.get("last_active_guild_id") != guild_id:
            utils_logger.info(f"TRAVEL_CHECK: User {author_id} is traveling to new guild {guild_id}. Triggering event.")
            await handle_travel_event(ctx, cog_instance.bot)
            # Dừng lệnh gốc lại sau khi xử lý du lịch.
            # Người dùng cần chạy lại lệnh để tương tác với server mới.
            # Điều này ngăn chặn race condition.
            return
        
        # Nếu không có du lịch, chạy lệnh gốc
        return await func(cog_instance, ctx, *args, **kwargs)
    return wrapper


def get_player_title(level: int, wanted_level: float) -> str:
    
    title_map = CRIMINAL_TITLES if wanted_level >= WANTED_LEVEL_CRIMINAL_THRESHOLD else CITIZEN_TITLES
    
    current_title = ""
    for level_threshold, title in sorted(title_map.items(), reverse=True):
        if level >= level_threshold:
            current_title = title
            break
            
    return f"{current_title} (Level {level})"
# bot/cogs/actions/use_cmd.py
import nextcord
from nextcord.ext import commands
import logging

from core.database import get_or_create_global_user_profile, get_or_create_user_local_data
from core.utils import try_send
from core.icons import ICON_SUCCESS, ICON_ERROR, ICON_INFO, ICON_SURVIVAL

logger = logging.getLogger(__name__)

class UseCommandCog(commands.Cog, name="Use Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("UseCommandCog (v2 - Refactored) initialized.")

    @commands.command(name='use')
    async def use(self, ctx: commands.Context, item_id: str):
        """Sử dụng một vật phẩm tiêu thụ từ túi đồ của bạn."""
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server.")
            return
            
        author_id = ctx.author.id
        guild_id = ctx.guild.id
        item_id_to_use = item_id.lower().strip()

        try:
            economy_data = self.bot.economy_data
            global_profile = get_or_create_global_user_profile(economy_data, author_id)
            local_data = get_or_create_user_local_data(global_profile, guild_id)

            # Tìm vật phẩm trong cả hai túi đồ
            inventory_local = local_data.get("inventory_local", [])
            inventory_global = global_profile.get("inventory_global", [])
            
            item_to_remove = None
            source_inventory = None

            # Ưu tiên tìm trong túi local trước
            for item in inventory_local:
                if isinstance(item, dict) and item.get("item_id") == item_id_to_use:
                    item_to_remove = item
                    source_inventory = inventory_local
                    break
            
            if not item_to_remove:
                for item in inventory_global:
                    if isinstance(item, dict) and item.get("item_id") == item_id_to_use:
                        item_to_remove = item
                        source_inventory = inventory_global
                        break
            
            if not item_to_remove:
                await try_send(ctx, content=f"{ICON_ERROR} Bạn không có vật phẩm `{item_id_to_use}` trong túi đồ.")
                return

            # Kiểm tra xem vật phẩm có thể sử dụng được không
            item_details = self.bot.item_definitions.get(item_id_to_use, {})
            if not item_details or "effect" not in item_details:
                await try_send(ctx, content=f"{ICON_ERROR} Bạn không thể 'dùng' vật phẩm này.")
                return
            
            # Áp dụng hiệu ứng
            effect = item_details["effect"]
            stat_to_change = effect["stat"]
            value_to_add = effect["value"]
            
            stats = local_data.get("survival_stats")
            original_value = stats[stat_to_change]
            stats[stat_to_change] = min(100, original_value + value_to_add) # Không cho vượt quá 100

            # Xóa vật phẩm đã dùng
            source_inventory.remove(item_to_remove)
            
            stat_name_vn = {"health": "Máu", "hunger": "Độ no", "energy": "Năng lượng"}
            stat_name = stat_name_vn.get(stat_to_change, stat_to_change)
            
            await try_send(ctx, content=f"{ICON_SUCCESS} Bạn đã dùng **{item_details['description']}** và hồi phục **{value_to_add} {stat_name}** {ICON_SURVIVAL}.")
            logger.info(f"User {author_id} đã dùng {item_id_to_use}, hồi {value_to_add} {stat_to_change}.")

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'use' cho user {author_id}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi khi bạn sử dụng vật phẩm.")


def setup(bot: commands.Bot):
    bot.add_cog(UseCommandCog(bot))
n.response.send_message(f"{ICON_ERROR} Bạn không có đủ quyền (Moderator/Owner) để sử dụng lệnh này.", ephemeral=True)
    except Exception as e:
        utils_logger.error(f"Lỗi gửi tin nhắn từ chối quyền trong check_is_bot_moderator_interaction: {e}")
        
    return False

def format_large_number(num):
    if abs(num) < 1000:
        return str(num)
    if abs(num) < 1_000_000:
        return f"{num / 1000:.1f}k".replace(".0", "")
    if abs(num) < 1_000_000_000:
        return f"{num / 1_000_000:.2f}M".replace(".00", "")
    if abs(num) < 1_000_000_000_000:
        return f"{num / 1_000_000_000:.2f}B".replace(".00", "")
    return f"{num / 1_000_000_000_000:.2f}T".replace(".00", "")
".replace(".00", "")
