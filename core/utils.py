import nextcord
from nextcord.ext import commands
from datetime import datetime, timedelta
import logging 

from .config import MODERATOR_USER_IDS
from .database import load_economy_data, get_or_create_guild_config, load_moderator_ids
from .icons import ICON_ERROR

utils_logger = logging.getLogger(__name__)

def is_guild_owner_check(interaction_or_ctx):
    user = interaction_or_ctx.user if isinstance(interaction_or_ctx, nextcord.Interaction) else interaction_or_ctx.author
    guild = interaction_or_ctx.guild
    if guild is None: return False
    return user.id == guild.owner_id

def get_time_left_str(last_timestamp, cooldown_seconds):
    if not last_timestamp: return None
    now = datetime.now().timestamp()
    time_passed = now - last_timestamp
    if time_passed >= cooldown_seconds: return None
    time_left_seconds = cooldown_seconds - time_passed
    return str(timedelta(seconds=int(time_left_seconds))).split('.')[0]

async def try_send(target, content=None, embed=None, ephemeral=False):
    utils_logger.debug(f"TRY_SEND_DEBUG: Called for target type {type(target)}, ephemeral={ephemeral}, content='{str(content)[:70]}...'")
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

    if guild and channel:
        try:
            economy_data = load_economy_data()
            guild_config_data = get_or_create_guild_config(economy_data, guild.id)
            if channel.id in guild_config_data.get("muted_channels", []) and not ephemeral:
                utils_logger.warning(f"TRY_SEND_DEBUG: Kênh {channel.id} bị mute, tin nhắn công khai bị chặn.")
                if is_interaction and hasattr(target.user, 'guild_permissions') and target.user.guild_permissions.administrator:
                    try:
                        if not target.response.is_done(): await target.response.send_message(f"{ICON_ERROR} Bot đang bị tắt tiếng công khai trong kênh này.", ephemeral=True, delete_after=10)
                        else: await target.followup.send(f"{ICON_ERROR} Bot đang bị tắt tiếng công khai trong kênh này.", ephemeral=True, delete_after=10)
                    except Exception as admin_warn_exc: utils_logger.error(f"TRY_SEND_DEBUG: Lỗi gửi cảnh báo mute cho admin: {admin_warn_exc}")
                return None
        except Exception as e_get_config:
            utils_logger.error(f"TRY_SEND_DEBUG: Lỗi khi get_guild_config cho mute check: {e_get_config}", exc_info=True)
    
    sent_message = None
    try:
        if is_context:
            sent_message = await target.send(content=content, embed=embed)
        elif is_interaction:
            if target.response.is_done(): 
                sent_message = await target.followup.send(content=content, embed=embed, ephemeral=ephemeral)
            else: 
                await target.response.send_message(content=content, embed=embed, ephemeral=ephemeral)
        return sent_message
    except Exception as e: 
        utils_logger.error(f"TRY_SEND_DEBUG: Lỗi không xác định khi gửi tin nhắn: {e}", exc_info=True)
    return None

async def is_bot_moderator(ctx: commands.Context) -> bool:
    try:
        if await ctx.bot.is_owner(ctx.author):
            return True
    except Exception as e_owner_check:
        utils_logger.error(f"Lỗi khi kiểm tra is_owner: {e_owner_check}", exc_info=True)
    try:
        moderator_ids = load_moderator_ids()
        if ctx.author.id in moderator_ids:
            return True
    except Exception as e_load_mods:
        utils_logger.error(f"Lỗi khi tải danh sách moderator: {e_load_mods}", exc_info=True)
    return False

async def check_is_bot_moderator_interaction(interaction: nextcord.Interaction) -> bool:
    if await interaction.client.is_owner(interaction.user):
        utils_logger.debug(f"Interaction Check: User {interaction.user.id} là owner.")
        return True
    try:
        moderator_ids = load_moderator_ids() 
        if interaction.user.id in moderator_ids:
            utils_logger.debug(f"Interaction Check: User {interaction.user.id} là moderator.")
            return True
    except Exception as e:
        utils_logger.error(f"Lỗi khi tải danh sách moderator trong check_is_bot_moderator_interaction: {e}", exc_info=True)
        return False
    
    utils_logger.warning(f"Interaction Check: User {interaction.user.id} không có quyền moderator cho lệnh slash /{interaction.application_command.name}.")
    try:
        if not interaction.response.is_done():
             await interaction.response.send_message(f"{ICON_ERROR} Bạn không có đủ quyền (Moderator/Owner) để sử dụng lệnh này.", ephemeral=True)
    except Exception as e:
        utils_logger.error(f"Lỗi gửi tin nhắn từ chối quyền trong check_is_bot_moderator_interaction: {e}")
        
    return False
