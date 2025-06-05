# bot/core/utils.py
import nextcord
from nextcord.ext import commands
from datetime import datetime, timedelta
import logging # Thêm logging
from .database import get_guild_config 

# Lấy logger cho module utils.py
utils_logger = logging.getLogger(__name__) # Đổi tên logger để tránh trùng với logger ở các file khác nếu copy cả dòng

# --- Helper function for Guild Owner Check (Giữ nguyên) ---
def is_guild_owner_check(interaction_or_ctx):
    user = interaction_or_ctx.user if isinstance(interaction_or_ctx, nextcord.Interaction) else interaction_or_ctx.author
    guild = interaction_or_ctx.guild
    if guild is None: return False
    return user.id == guild.owner_id

# --- get_time_left_str (Giữ nguyên) ---
def get_time_left_str(last_timestamp, cooldown_seconds):
    if not last_timestamp: return None
    now = datetime.now().timestamp()
    time_passed = now - last_timestamp
    if time_passed >= cooldown_seconds: return None
    time_left_seconds = cooldown_seconds - time_passed
    return str(timedelta(seconds=int(time_left_seconds))).split('.')[0]

# --- Safe Message Sending (PHIÊN BẢN DEBUG CHO LỖI GỬI 2 LẦN) ---
async def try_send(target, content=None, embed=None, ephemeral=False):
    # Sử dụng logger.critical để chắc chắn thấy trên console khi debug lỗi này
    utils_logger.critical(f"TRY_SEND_DEBUG: === Được gọi với target type {type(target)}, ephemeral={ephemeral}, content='{str(content)[:70]}...' ===")

    channel = None
    guild = None
    is_interaction = isinstance(target, nextcord.Interaction)
    is_context = isinstance(target, commands.Context)

    if is_interaction:
        channel = target.channel
        guild = target.guild
    elif is_context:
        channel = target.channel
        guild = target.guild
    
    # --- TẠM THỜI BỎ QUA KIỂM TRA MUTE KÊNH ĐỂ DEBUG LỖI GỬI 2 LẦN ---
    # if guild and channel:
    #     guild_config_data = get_guild_config(guild.id)
    #     if channel.id in guild_config_data.get("muted_channels", []) and not ephemeral:
    #         utils_logger.warning(f"TRY_SEND_DEBUG: Kênh {channel.id} bị mute, tin nhắn công khai bị chặn.")
    #         # ... (logic cảnh báo admin nếu cần) ...
    #         return None 
    # --------------------------------------------------------------------

    sent_message = None # Để lưu lại message đã gửi (nếu có)
    try:
        if is_context:
            utils_logger.critical(f"TRY_SEND_DEBUG: Chuẩn bị gọi target.send() cho Context.")
            sent_message = await target.send(content=content, embed=embed)
            utils_logger.critical(f"TRY_SEND_DEBUG: ĐÃ GỌI XONG target.send() cho Context. Message ID: {sent_message.id if sent_message else 'None'}")
            
        elif is_interaction:
            utils_logger.critical(f"TRY_SEND_DEBUG: Xử lý Interaction. Response is_done: {target.response.is_done()}")
            if target.response.is_done():
                sent_message = await target.followup.send(content=content, embed=embed, ephemeral=ephemeral)
                utils_logger.critical(f"TRY_SEND_DEBUG: ĐÃ GỌI XONG target.followup.send(). Message ID: {sent_message.id if sent_message else 'None'}")
            else:
                # Đối với send_message ban đầu của interaction, nó không trả về message object
                await target.response.send_message(content=content, embed=embed, ephemeral=ephemeral)
                utils_logger.critical(f"TRY_SEND_DEBUG: ĐÃ GỌI XONG target.response.send_message().")
                # Nếu muốn lấy message object, cần: sent_message = await interaction.original_response()
                # Nhưng để đơn giản, tạm thời không lấy ở đây.
        
        return sent_message # Trả về message đã gửi nếu là Context hoặc followup

    except nextcord.errors.HTTPException as e:
        utils_logger.error(f"TRY_SEND_DEBUG: HTTPException khi gửi tin nhắn: {e} (Kênh: {channel.id if channel else 'N/A'})", exc_info=True)
    except Exception as e:
        utils_logger.error(f"TRY_SEND_DEBUG: Lỗi không xác định khi gửi tin nhắn: {e} (Kênh: {channel.id if channel else 'N/A'})", exc_info=True)
    
    utils_logger.critical(f"TRY_SEND_DEBUG: === Kết thúc hàm try_send ===")
    return None # Trả về None nếu có lỗi hoặc không phải trường hợp trả về message
