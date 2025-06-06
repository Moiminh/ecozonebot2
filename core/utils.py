# bot/core/utils.py
import nextcord
from nextcord.ext import commands
from datetime import datetime, timedelta
import logging 

# Import các thành phần cần thiết từ các file khác trong 'core'
# Đảm bảo các import này đúng và đầy đủ
from .config import MODERATOR_USER_IDS # Cần cho is_bot_moderator
from .database import get_guild_config, load_moderator_ids # Cần load_moderator_ids cho is_bot_moderator
from .icons import ICON_ERROR # Ví dụ, nếu try_send có dùng (phiên bản hiện tại có)

utils_logger = logging.getLogger(__name__) # Logger cho module utils.py

# --- Helper function for Guild Owner Check (Giữ nguyên) ---
def is_guild_owner_check(interaction_or_ctx):
    """
    Kiểm tra xem người dùng có phải là chủ sở hữu của server (guild) hay không.
    Áp dụng cho cả Context (lệnh prefix) và Interaction (lệnh slash).
    """
    user = interaction_or_ctx.user if isinstance(interaction_or_ctx, nextcord.Interaction) else interaction_or_ctx.author
    guild = interaction_or_ctx.guild
    if guild is None: 
        return False
    return user.id == guild.owner_id

# --- get_time_left_str (Giữ nguyên) ---
def get_time_left_str(last_timestamp, cooldown_seconds):
    """
    Tính toán và trả về chuỗi thời gian còn lại cho một cooldown.
    """
    if not last_timestamp: 
        return None
    now = datetime.now().timestamp() 
    time_passed = now - last_timestamp 
    if time_passed >= cooldown_seconds: 
        return None 
    time_left_seconds = cooldown_seconds - time_passed 
    delta = timedelta(seconds=int(time_left_seconds))
    return str(delta).split('.')[0]


# --- Safe Message Sending (try_send - Đã đổi logger.critical thành logger.debug) ---
async def try_send(target, content=None, embed=None, ephemeral=False):
    """
    Hàm gửi tin nhắn an toàn, xử lý Context/Interaction và kênh bị mute.
    """
    utils_logger.debug(f"TRY_SEND_DEBUG: === Được gọi với target type {type(target)}, ephemeral={ephemeral}, content='{str(content)[:70]}...' ===")

    channel = None
    guild = None
    is_interaction = isinstance(target, nextcord.Interaction)
    is_context = isinstance(target, commands.Context)

    if is_interaction:
        channel = target.channel
        guild = target.guild
        if ephemeral: 
            utils_logger.debug(f"TRY_SEND_DEBUG: Interaction is ephemeral, bypassing public mute check.")
        elif guild and channel: 
            try:
                guild_config_data = get_guild_config(guild.id) 
                if channel.id in guild_config_data.get("muted_channels", []):
                    utils_logger.warning(f"TRY_SEND_DEBUG: Kênh {channel.id} (Interaction) bị mute, tin nhắn công khai (non-ephemeral) bị chặn.")
                    if hasattr(target.user, 'guild_permissions') and target.user.guild_permissions.administrator:
                        try:
                            if not target.response.is_done(): 
                               await target.response.send_message(f"{ICON_ERROR} Bot đang bị tắt tiếng công khai trong kênh này. (Admin thấy)", ephemeral=True, delete_after=10)
                            else: 
                               await target.followup.send(f"{ICON_ERROR} Bot đang bị tắt tiếng công khai trong kênh này. (Admin thấy)", ephemeral=True, delete_after=10)
                        except Exception as admin_warn_exc: 
                            utils_logger.error(f"TRY_SEND_DEBUG: Lỗi gửi cảnh báo mute cho admin (Interaction): {admin_warn_exc}", exc_info=True)
                    return None
            except Exception as e_get_config:
                 utils_logger.error(f"TRY_SEND_DEBUG: Lỗi khi get_guild_config cho mute check (Interaction): {e_get_config}", exc_info=True)

    elif is_context: 
        channel = target.channel
        guild = target.guild
        if guild and channel:
            try:
                guild_config_data = get_guild_config(guild.id) 
                if channel.id in guild_config_data.get("muted_channels", []):
                    utils_logger.warning(f"TRY_SEND_DEBUG: Kênh {channel.id} (Context) bị mute, tin nhắn bị chặn.")
                    return None
            except Exception as e_get_config:
                utils_logger.error(f"TRY_SEND_DEBUG: Lỗi khi get_guild_config cho mute check (Context): {e_get_config}", exc_info=True)
    
    sent_message = None
    try:
        if is_context:
            utils_logger.debug(f"TRY_SEND_DEBUG: Chuẩn bị gọi target.send() cho Context. Content: '{str(content)[:30]}...'")
            sent_message = await target.send(content=content, embed=embed)
            utils_logger.debug(f"TRY_SEND_DEBUG: ĐÃ GỌI XONG target.send() cho Context. Message ID: {sent_message.id if sent_message else 'None'}")
            
        elif is_interaction:
            utils_logger.debug(f"TRY_SEND_DEBUG: Xử lý Interaction. Response is_done: {target.response.is_done()}")
            if target.response.is_done(): 
                sent_message = await target.followup.send(content=content, embed=embed, ephemeral=ephemeral)
                utils_logger.debug(f"TRY_SEND_DEBUG: ĐÃ GỌI XONG target.followup.send(). Message ID: {sent_message.id if sent_message else 'None'}")
            else: 
                await target.response.send_message(content=content, embed=embed, ephemeral=ephemeral)
                utils_logger.debug(f"TRY_SEND_DEBUG: ĐÃ GỌI XONG target.response.send_message().")
                # Nếu cần message object: sent_message = await interaction.original_response()
        
        return sent_message

    except nextcord.errors.HTTPException as e: 
        utils_logger.error(f"TRY_SEND_DEBUG: HTTPException khi gửi tin nhắn: {e} (Kênh: {channel.id if channel else 'N/A'})", exc_info=True)
    except Exception as e: 
        utils_logger.error(f"TRY_SEND_DEBUG: Lỗi không xác định khi gửi tin nhắn: {e} (Kênh: {channel.id if channel else 'N/A'})", exc_info=True)
    
    utils_logger.debug(f"TRY_SEND_DEBUG: === Kết thúc hàm try_send (có thể đã lỗi hoặc không gửi được) ===")
    return None


# ========== HÀM CHECK QUYỀN MODERATOR HOẶC OWNER ==========
async def is_bot_moderator(ctx: commands.Context) -> bool:
    """
    Hàm check tùy chỉnh để kiểm tra xem người dùng có phải là chủ sở hữu bot
    HOẶC có User ID nằm trong danh sách moderator (từ file moderators.json) hay không.
    """ 
    if await interaction.client.is_owner(interaction.user):
        utils_logger.debug(f"Interaction Check: User {interaction.user.id} ({interaction.user.name}) là owner.")
        return True
    
    # 2. Kiểm tra xem có trong danh sách moderator đã tải không
    try:
        moderator_ids = load_moderator_ids() # Hàm này từ core.database
        if interaction.user.id in moderator_ids:
            utils_logger.debug(f"Interaction Check: User {interaction.user.id} ({interaction.user.name}) được tìm thấy trong danh sách moderator_ids.")
            return True
    except Exception as e:
        utils_logger.error(f"Lỗi khi tải danh sách moderator trong check_is_bot_moderator_interaction: {e}", exc_info=True)
        # Nếu có lỗi đọc file mod, không cấp quyền cho an toàn
        return False
    
    # 3. Nếu không có quyền, gửi tin nhắn lỗi và trả về False
    utils_logger.warning(f"Interaction Check: User {interaction.user.id} ({interaction.user.name}) không có quyền moderator cho lệnh slash /{interaction.application_command.name}.")
    try:
        # Chỉ gửi nếu interaction chưa được phản hồi
        if not interaction.response.is_done():
             await interaction.response.send_message(f"{ICON_ERROR} Bạn không có đủ quyền (Moderator/Owner) để sử dụng lệnh này.", ephemeral=True)
    except Exception as e:
        # Nếu gửi tin nhắn lỗi cũng bị lỗi (ví dụ interaction đã hết hạn), chỉ log lại
        utils_logger.error(f"Lỗi gửi tin nhắn từ chối quyền trong check_is_bot_moderator_interaction: {e}")
        
    return False

    try:
        if await ctx.bot.is_owner(ctx.author):
            utils_logger.debug(f"is_bot_moderator check: User {ctx.author.id} ({ctx.author.name}) là owner.")
            return True
    except Exception as e_owner_check: # Bắt lỗi nếu is_owner có vấn đề
        utils_logger.error(f"Lỗi khi kiểm tra ctx.bot.is_owner: {e_owner_check}", exc_info=True)

    # 2. Kiểm tra xem có trong danh sách moderator đã tải không
    try:
        moderator_ids = load_moderator_ids() # Hàm này từ core.database (đã được import ở trên)
        if ctx.author.id in moderator_ids:
            utils_logger.debug(f"is_bot_moderator check: User {ctx.author.id} ({ctx.author.name}) được tìm thấy trong danh sách moderator_ids.")
            return True
    except Exception as e_load_mods: # Bắt lỗi nếu load_moderator_ids có vấn đề
        utils_logger.error(f"Lỗi khi tải danh sách moderator trong is_bot_moderator: {e_load_mods}", exc_info=True)
    
    utils_logger.debug(f"is_bot_moderator check: User {ctx.author.id} ({ctx.author.name}) không phải owner và không có trong moderator_ids.")
    return False
   
def format_large_number(num):
    if num < 1000:
        return str(num)
    if num < 1_000_000:
        return f"{num / 1000:.1f}k".replace(".0", "")
    if num < 1_000_000_000:
        return f"{num / 1_000_000:.2f}M".replace(".00", "")
    if num < 1_000_000_000_000:
        return f"{num / 1_000_000_000:.2f}B".replace(".00", "")
    return f"{num / 1_000_000_000_000:.2f}T".replace(".00", "")
# =====================================================
