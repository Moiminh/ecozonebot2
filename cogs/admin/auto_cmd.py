# bot/cogs/admin/auto_cmd.py
import nextcord
from nextcord.ext import commands
import logging # <<< THÊM IMPORT NÀY

from core.database import get_guild_config, save_guild_config
from core.utils import try_send
# from core.config import COMMAND_PREFIX # Không cần thiết trực tiếp trong file này
from core.icons import ICON_SUCCESS, ICON_ERROR, ICON_INFO # Đảm bảo các icon này có trong core/icons.py

logger = logging.getLogger(__name__) # <<< LẤY LOGGER CHO MODULE NÀY

class AutoCommandCog(commands.Cog, name="Auto Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"AutoCommandCog initialized.")

    @commands.command(name="auto")
    @commands.has_guild_permissions(administrator=True) 
    async def auto_toggle_bare_commands(self, ctx: commands.Context):
        """(Admin) Bật/Tắt nhận diện lệnh không cần prefix cho kênh này."""
        logger.debug(f"Lệnh 'auto' được gọi bởi {ctx.author.name} (ID: {ctx.author.id}) tại guild {ctx.guild.id}, kênh {ctx.channel.id}.")
        
        if not ctx.guild: 
            logger.warning(f"Lệnh 'auto' được gọi ngoài guild bởi {ctx.author.id}.")
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server.")
            return
            
        current_guild_config = get_guild_config(ctx.guild.id)
        active_channels = current_guild_config.get("bare_command_active_channels", [])
        channel_id = ctx.channel.id
        
        action_taken = "" # Để ghi log
        msg_content = ""
        if channel_id in active_channels:
            active_channels.remove(channel_id)
            action_taken = "TẮT"
            msg_content = f"{ICON_ERROR} Đã **TẮT** tính năng lệnh tắt (không cần prefix) cho kênh {ctx.channel.mention} này."
        else:
            active_channels.append(channel_id)
            action_taken = "BẬT"
            msg_content = f"{ICON_SUCCESS} Đã **BẬT** tính năng lệnh tắt (không cần prefix) cho kênh {ctx.channel.mention} này."
            
        current_guild_config["bare_command_active_channels"] = active_channels
        save_guild_config(ctx.guild.id, current_guild_config)

        # Ghi log hành động admin
        logger.info(f"ADMIN ACTION: {ctx.author.display_name} ({ctx.author.id}) đã {action_taken} chế độ 'auto' cho kênh {ctx.channel.name} (ID: {channel_id}) trong guild {ctx.guild.id}.")
        
        await try_send(ctx, content=msg_content)
        logger.debug(f"Lệnh 'auto' cho kênh {channel_id} bởi {ctx.author.name} đã xử lý xong. Trạng thái mới: {action_taken}.")

    @auto_toggle_bare_commands.error 
    async def auto_toggle_bare_commands_error(self, ctx: commands.Context, error):
        command_name_for_log = ctx.command.name if ctx.command else "auto"
        if isinstance(error, commands.MissingPermissions):
            logger.warning(f"MissingPermissions cho lệnh '{command_name_for_log}' bởi user {ctx.author.id}: {error}")
            await try_send(ctx, content=f"{ICON_ERROR} Bạn cần quyền `Administrator` để sử dụng lệnh này.")
        else:
            logger.error(f"Lỗi không xác định trong lệnh '{command_name_for_log}' bởi user {ctx.author.id}: {error}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Có lỗi xảy ra với lệnh `auto`.")

def setup(bot: commands.Bot):
    bot.add_cog(AutoCommandCog(bot))
