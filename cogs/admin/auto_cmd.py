# bot/cogs/admin/auto_cmd.py
import nextcord
from nextcord.ext import commands

from core.database import get_guild_config, save_guild_config # Chỉ cần 2 hàm này
from core.utils import try_send
# from core.config import COMMAND_PREFIX # Không cần COMMAND_PREFIX trong file này
from core.icons import ICON_SUCCESS, ICON_ERROR # Đảm bảo các icon này có trong core/icons.py

class AutoCommandCog(commands.Cog, name="Auto Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="auto") # Tên lệnh mà người dùng sẽ gõ
    @commands.has_guild_permissions(administrator=True) 
    async def auto_toggle_bare_commands(self, ctx: commands.Context): # Tên hàm có thể giữ nguyên hoặc đổi
        """(Admin) Bật/Tắt nhận diện lệnh không cần prefix cho kênh này."""
        if not ctx.guild: 
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server.")
            return
            
        current_guild_config = get_guild_config(ctx.guild.id)
        # Lấy list hiện tại, hoặc list rỗng nếu chưa có key
        active_channels = current_guild_config.get("bare_command_active_channels", [])
        channel_id = ctx.channel.id
        
        msg_content = ""
        if channel_id in active_channels:
            active_channels.remove(channel_id)
            msg_content = f"{ICON_ERROR} Đã **TẮT** tính năng lệnh tắt (không cần prefix) cho kênh {ctx.channel.mention} này."
        else:
            active_channels.append(channel_id)
            msg_content = f"{ICON_SUCCESS} Đã **BẬT** tính năng lệnh tắt (không cần prefix) cho kênh {ctx.channel.mention} này."
            
        current_guild_config["bare_command_active_channels"] = active_channels
        save_guild_config(ctx.guild.id, current_guild_config) # Lưu lại toàn bộ object config của guild
        await try_send(ctx, content=msg_content)

    @auto_toggle_bare_commands.error # Tên hàm xử lý lỗi phải khớp với tên hàm lệnh
    async def auto_toggle_bare_commands_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await try_send(ctx, content=f"{ICON_ERROR} Bạn cần quyền `Administrator` để sử dụng lệnh này.")
        else:
            command_name_for_log = ctx.command.name if ctx.command else "auto"
            print(f"Lỗi không xác định trong lệnh {command_name_for_log}: {error}")
            await try_send(ctx, content=f"{ICON_ERROR} Có lỗi xảy ra với lệnh `auto`.")

def setup(bot: commands.Bot):
    bot.add_cog(AutoCommandCog(bot))
