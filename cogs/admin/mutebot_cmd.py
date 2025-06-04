# bot/cogs/admin/mutebot_cmd.py
import nextcord
from nextcord.ext import commands

from core.database import get_guild_config, save_guild_config # Chỉ cần 2 hàm này
from core.utils import try_send
# from core.config import COMMAND_PREFIX # Không cần thiết cho file này
from core.icons import ICON_ERROR, ICON_INFO # Đảm bảo các icon này có trong core/icons.py

class MuteBotCommandCog(commands.Cog, name="MuteBot Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="mutebot") # Tên lệnh mà người dùng sẽ gõ
    @commands.has_guild_permissions(administrator=True)
    async def mute_bot_channel(self, ctx: commands.Context, channel: nextcord.TextChannel = None): # Tên hàm có thể giữ nguyên hoặc đổi
        """(Admin) Tắt tiếng bot (không gửi tin nhắn công khai) trong kênh này hoặc kênh được chỉ định."""
        target_channel = channel or ctx.channel 
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server.")
            return
            
        current_guild_config = get_guild_config(ctx.guild.id)
        # Lấy list hiện tại, hoặc list rỗng nếu chưa có key
        muted_channels_list = current_guild_config.get("muted_channels", [])
        
        if target_channel.id in muted_channels_list:
            await try_send(ctx, content=f"{ICON_INFO} Bot đã bị tắt tiếng (công khai) trong kênh {target_channel.mention} rồi.")
        else:
            muted_channels_list.append(target_channel.id)
            current_guild_config["muted_channels"] = muted_channels_list # Cập nhật list trong bản config đã lấy
            save_guild_config(ctx.guild.id, current_guild_config) # Lưu lại toàn bộ object config của guild
            # Bạn có thể dùng ICON_SUCCESS hoặc giữ lại emoji gốc 🔇 tùy thích
            await try_send(ctx, content=f"🔇 Bot đã bị **TẮT TIẾNG** (công khai) trong kênh {target_channel.mention}. Các tin nhắn ephemeral (nếu có) vẫn hoạt động.")

    @mute_bot_channel.error # Tên hàm xử lý lỗi phải khớp với tên hàm lệnh
    async def mute_bot_channel_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await try_send(ctx, content=f"{ICON_ERROR} Bạn cần quyền `Administrator` để dùng lệnh này.")
        elif isinstance(error, commands.BadArgument): 
            await try_send(ctx, content=f"{ICON_ERROR} Không tìm thấy kênh được chỉ định hoặc bạn nhập sai.")
        else:
            command_name_for_log = ctx.command.name if ctx.command else "mutebot"
            print(f"Lỗi không xác định trong lệnh {command_name_for_log}: {error}")
            await try_send(ctx, content=f"{ICON_ERROR} Có lỗi xảy ra khi thực hiện lệnh tắt tiếng bot.")

def setup(bot: commands.Bot):
    bot.add_cog(MuteBotCommandCog(bot))
