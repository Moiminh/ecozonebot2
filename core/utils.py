# bot/core/utils.py
import nextcord
from nextcord.ext import commands
from datetime import datetime, timedelta
import logging 
from .database import get_guild_config 

utils_logger = logging.getLogger(__name__)

# --- Helper function for Guild Owner Check (Giữ nguyên) ---
def is_guild_owner_check(interaction_or_ctx):
    # ... (code giữ nguyên) ...
    user = interaction_or_ctx.user if isinstance(interaction_or_ctx, nextcord.Interaction) else interaction_or_ctx.author
    guild = interaction_or_ctx.guild
    if guild is None: return False
    return user.id == guild.owner_id

# --- get_time_left_str (Giữ nguyên) ---
def get_time_left_str(last_timestamp, cooldown_seconds):
    # ... (code giữ nguyên) ...
    if not last_timestamp: return None
    now = datetime.now().timestamp()
    time_passed = now - last_timestamp
    if time_passed >= cooldown_seconds: return None
    time_left_seconds = cooldown_seconds - time_passed
    return str(timedelta(seconds=int(time_left_seconds))).split('.')[0]


# --- Safe Message Sending (KHÔI PHỤC MUTE CHECK + GIỮ DEBUG LOG) ---
async def try_send(target, content=None, embed=None, ephemeral=False):
    utils_logger.critical(f"TRY_SEND_DEBUG: === Được gọi với target type {type(target)}, ephemeral={ephemeral}, content='{str(content)[:70]}...' ===")

    channel = None
    guild = None
    is_interaction = isinstance(target, nextcord.Interaction)
    is_context = isinstance(target, commands.Context)

    if is_interaction:
        channel = target.channel
        guild = target.guild
        # Check for ephemeral for interactions early
        if ephemeral: # If ephemeral, bypass mute check for public messages
            utils_logger.critical(f"TRY_SEND_DEBUG: Interaction is ephemeral, bypassing public mute check.")
        elif guild and channel: # Non-ephemeral interaction in a guild
            guild_config_data = get_guild_config(guild.id)
            if channel.id in guild_config_data.get("muted_channels", []):
                utils_logger.critical(f"TRY_SEND_DEBUG: Kênh {channel.id} (Interaction) bị mute, tin nhắn công khai (non-ephemeral) bị chặn.")
                if hasattr(target.user, 'guild_permissions') and target.user.guild_permissions.administrator:
                    try:
                        if not target.response.is_done(): # Check if initial response is already sent
                           await target.response.send_message("Bot đang bị tắt tiếng công khai trong kênh này. (Admin thấy)", ephemeral=True, delete_after=10)
                        else: # If already responded (e.g. deferred), use followup
                           await target.followup.send("Bot đang bị tắt tiếng công khai trong kênh này. (Admin thấy)", ephemeral=True, delete_after=10)
                    except Exception as admin_warn_exc:
                        utils_logger.error(f"TRY_SEND_DEBUG: Lỗi gửi cảnh báo mute cho admin (Interaction): {admin_warn_exc}")
                return None
    elif is_context: # Prefix command context
        channel = target.channel
        guild = target.guild
        # For context (prefix commands), ephemeral is not a direct send option.
        # Mute check applies to all messages sent via ctx.send() if channel is muted.
        if guild and channel:
            guild_config_data = get_guild_config(guild.id)
            if channel.id in guild_config_data.get("muted_channels", []):
                utils_logger.critical(f"TRY_SEND_DEBUG: Kênh {channel.id} (Context) bị mute, tin nhắn bị chặn.")
                # For prefix commands, we can't easily send an ephemeral warning to just the admin author.
                # The command will execute, but the reply via try_send will be suppressed.
                return None
    
    sent_message = None
    try:
        if is_context:
            utils_logger.critical(f"TRY_SEND_DEBUG: Chuẩn bị gọi target.send() cho Context.")
            sent_message = await target.send(content=content, embed=embed)
            utils_logger.critical(f"TRY_SEND_DEBUG: ĐÃ GỌI XONG target.send() cho Context. Message ID: {sent_message.id if sent_message else 'None'}")
            
        elif is_interaction:
            utils_logger.critical(f"TRY_SEND_DEBUG: Xử lý Interaction. Response is_done: {target.response.is_done()}")
            if target.response.is_done(): # Deferred or already responded
                sent_message = await target.followup.send(content=content, embed=embed, ephemeral=ephemeral)
                utils_logger.critical(f"TRY_SEND_DEBUG: ĐÃ GỌI XONG target.followup.send(). Message ID: {sent_message.id if sent_message else 'None'}")
            else: # Initial response for interaction
                await target.response.send_message(content=content, embed=embed, ephemeral=ephemeral)
                utils_logger.critical(f"TRY_SEND_DEBUG: ĐÃ GỌI XONG target.response.send_message().")
                # sent_message = await interaction.original_response() # If needed
        
        return sent_message

    except nextcord.errors.HTTPException as e:
        utils_logger.error(f"TRY_SEND_DEBUG: HTTPException khi gửi tin nhắn: {e} (Kênh: {channel.id if channel else 'N/A'})", exc_info=True)
    except Exception as e:
        utils_logger.error(f"TRY_SEND_DEBUG: Lỗi không xác định khi gửi tin nhắn: {e} (Kênh: {channel.id if channel else 'N/A'})", exc_info=True)
    
    utils_logger.critical(f"TRY_SEND_DEBUG: === Kết thúc hàm try_send (có thể đã lỗi hoặc không gửi được) ===")
    return None
