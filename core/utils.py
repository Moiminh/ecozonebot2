# bot/core/utils.py
import nextcord
from nextcord.ext import commands
from datetime import datetime, timedelta
import logging
from functools import wraps

from .database import get_or_create_global_user_profile
from .travel_manager import handle_travel_event
from .config import MODERATOR_USER_IDS, WANTED_LEVEL_CRIMINAL_THRESHOLD, CITIZEN_TITLES, CRIMINAL_TITLES
from .icons import ICON_ERROR
from .database import load_moderator_ids

utils_logger = logging.getLogger(__name__)

def require_travel_check(func):
    @wraps(func)
    async def wrapper(cog_instance, ctx, *args, **kwargs):
        if not ctx.guild:
            return await func(cog_instance, ctx, *args, **kwargs)

        author_id = ctx.author.id
        guild_id = ctx.guild.id
        
        economy_data = getattr(cog_instance.bot, 'economy_data')
        global_profile = get_or_create_global_user_profile(economy_data, author_id)

        last_active_guild_id = global_profile.get("last_active_guild_id")
        
        if last_active_guild_id != guild_id:
            if last_active_guild_id is not None:
                 utils_logger.info(f"TRAVEL_CHECK: User {author_id} is traveling to new guild {guild_id}. Triggering event.")
                 await handle_travel_event(ctx, cog_instance.bot)
            
            # Cập nhật guild hoạt động cuối cùng dù là lần đầu hay du lịch
            global_profile["last_active_guild_id"] = guild_id
            # Không dừng lệnh ở đây nữa để lệnh đầu tiên ở server mới vẫn chạy được.
        
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

async def try_send(target, **kwargs):
    try:
        return await target.send(**kwargs)
    except (nextcord.Forbidden, nextcord.HTTPException) as e:
        utils_logger.warning(f"Không thể gửi tin nhắn tới target '{getattr(target, 'name', 'N/A')}': {e}")
        return None

def get_time_left_str(last_timestamp: float, cooldown_seconds: int) -> str:
    if not last_timestamp:
        return ""
    
    now = datetime.now().timestamp()
    time_since = now - last_timestamp
    
    if time_since < cooldown_seconds:
        time_left = cooldown_seconds - time_since
        return str(timedelta(seconds=int(time_left)))
    return ""

def is_guild_owner_check(ctx: commands.Context) -> bool:
    return ctx.author.id == ctx.guild.owner_id

def is_bot_moderator(ctx: commands.Context) -> bool:
    moderator_ids = load_moderator_ids()
    return ctx.author.id in moderator_ids or ctx.author.id in MODERATOR_USER_IDS

async def check_is_bot_moderator_interaction(interaction: nextcord.Interaction) -> bool:
    # Đây là hàm check cho application_command, trả về True/False
    # Việc gửi tin nhắn lỗi nên được xử lý trong `on_application_command_error`
    # Hoặc trực tiếp trong lệnh nếu check thất bại.
    # Tuy nhiên, giữ logic hiện tại để không phá vỡ các lệnh slash đang có.
    user_is_mod = interaction.user.id in load_moderator_ids()
    user_is_owner = await interaction.client.is_owner(interaction.user)
    
    is_authorized = user_is_mod or user_is_owner
    
    if not is_authorized:
        try:
            await interaction.response.send_message(
                f"{ICON_ERROR} Bạn không có đủ quyền (Moderator/Owner) để sử dụng lệnh này.", 
                ephemeral=True
            )
        except Exception as e:
            utils_logger.error(f"Lỗi gửi tin nhắn từ chối quyền trong check: {e}")
            
    return is_authorized

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
