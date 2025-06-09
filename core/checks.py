# bot/core/checks.py
import nextcord
from nextcord.ext import commands

from .database import load_moderator_ids
from .config import MODERATOR_USER_IDS
from .icons import ICON_ERROR

async def check_is_bot_moderator_interaction(interaction: nextcord.Interaction) -> bool:
    """Kiểm tra quyền Moderator/Owner cho lệnh slash."""
    user_is_mod = interaction.user.id in load_moderator_ids()
    user_is_owner = await interaction.client.is_owner(interaction.user)

    is_authorized = user_is_mod or user_is_owner

    if not is_authorized:
        try:
            await interaction.response.send_message(
                f"{ICON_ERROR} Bạn không có đủ quyền (Moderator/Owner) để sử dụng lệnh này.", 
                ephemeral=True
            )
        except Exception:
            pass # Bỏ qua nếu không thể gửi tin nhắn

    return is_authorized

def is_bot_moderator(ctx: commands.Context) -> bool:
    """Kiểm tra quyền Moderator/Owner cho lệnh prefix."""
    moderator_ids = load_moderator_ids()
    return ctx.author.id in moderator_ids or ctx.author.id in MODERATOR_USER_IDS

def is_guild_owner_check(ctx: commands.Context) -> bool:
    """Kiểm tra người dùng có phải là chủ server không."""
    if not ctx.guild:
        return False
    return ctx.author.id == ctx.guild.owner_id
