# bot/cogs/admin/auto_cmd.py
import nextcord
from nextcord.ext import commands
import logging

from core.database import get_or_create_guild_config
from core.utils import try_send
from core.icons import ICON_SUCCESS, ICON_ERROR

logger = logging.getLogger(__name__)

class AutoCommandCog(commands.Cog, name="Auto Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("AutoCommandCog (v2 - Refactored) initialized.")

    @commands.command(name="auto")
    @commands.has_guild_permissions(administrator=True)
    @commands.guild_only()
    async def auto_toggle_bare_commands(self, ctx: commands.Context):
        """Bật/tắt chế độ lệnh không cần prefix trong kênh hiện tại."""
        logger.debug(f"Lệnh 'auto' được gọi bởi {ctx.author.name} tại guild '{ctx.guild.name}' ({ctx.guild.id}).")
        
        # [SỬA] Sử dụng cache của bot
        economy_data = self.bot.economy_data
        guild_config = get_or_create_guild_config(economy_data, ctx.guild.id)
        
        active_channels = guild_config.setdefault("bare_command_active_channels", [])
        channel_id = ctx.channel.id
        
        msg_content = ""
        action_taken = ""
        
        if channel_id in active_channels:
            active_channels.remove(channel_id)
            action_taken = "TẮT"
            msg_content = f"{ICON_ERROR} Đã **TẮT** tính năng lệnh tắt (không cần prefix) cho kênh {ctx.channel.mention} này."
        else:
            active_channels.append(channel_id)
            action_taken = "BẬT"
            msg_content = f"{ICON_SUCCESS} Đã **BẬT** tính năng lệnh tắt (không cần prefix) cho kênh {ctx.channel.mention} này."
            
        # [SỬA] Không cần lưu thủ công
        # guild_config["bare_command_active_channels"] = active_channels
        # save_economy_data(economy_data)

        logger.info(f"ADMIN ACTION: {ctx.author.display_name} ({ctx.author.id}) đã {action_taken} chế độ 'auto' cho kênh {ctx.channel.name} (ID: {channel_id}) trong guild {ctx.guild.id}.")
        
        await try_send(ctx, content=msg_content)

    @auto_toggle_bare_commands.error
    async def auto_toggle_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await try_send(ctx, content=f"{ICON_ERROR} Bạn cần quyền `Administrator` để sử dụng lệnh này.")
        else:
            logger.error(f"Lỗi trong lệnh 'auto' bởi {ctx.author.name}:", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Có lỗi xảy ra với lệnh `auto`.")

def setup(bot: commands.Bot):
    bot.add_cog(AutoCommandCog(bot))
