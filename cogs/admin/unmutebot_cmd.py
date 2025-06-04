# bot/cogs/admin/unmutebot_cmd.py
import nextcord
from nextcord.ext import commands

from core.database import get_guild_config, save_guild_config # Chỉ cần 2 hàm này
from core.utils import try_send
# from core.config import COMMAND_PREFIX # Không cần thiết cho file này
from core.icons import ICON_ERROR, ICON_INFO, ICON_SUCCESS # Đảm bảo các icon này có trong core/icons.py

class UnmuteBotCommandCog(commands.Cog, name="UnmuteBot Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="unmutebot") # Tên lệnh mà người dùng sẽ gõ
    @commands.has_guild_permissions(administrator=True)
    async def unmute_bot_channel(self, ctx: commands.Context, channel: nextcord.TextChannel = None): # Tên hàm có thể giữ nguyên hoặc đổi
        """(Admin) Bật lại tiếng bot (cho phép gửi tin nhắn công khai) trong kênh này hoặc kênh được chỉ định."""
        target_channel = channel or ctx.channel
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server.")
            return
            
        current_guild_config = get_guild_config(ctx.guild.id)
        # Lấy list hiện tại, hoặc list rỗng nếu chưa có key
        muted_channels_list = current_guild_config.get("muted_channels", [])
        
        if target_channel.id not in muted_channels_list:
            await try_send(ctx, content=f"{ICON_INFO} Bot không bị tắt tiếng (công khai) trong kênh {target_channel.mention}.")
        else:
            muted_channels_list.remove(target_channel.id)
            current_guild_config["muted_channels"] = muted_channels_list # Cập nhật list
            save_guild_config(ctx.guild.id, current_guild_config) # Lưu lại toàn bộ object config của guild
            # Bạn có thể dùng ICON_SUCCESS hoặc giữ lại emoji gốc 🔊 tùy thích
            await try_send(ctx, content=f"🔊 Bot đã được **BẬT TIẾNG** (công khai) trở lại trong kênh {target_channel.mention}.")

    @unmute_bot_channel.error # Tên hàm xử lý lỗi phải khớp với tên hàm lệnh
    async def unmute_bot_channel_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await try_send(ctx, content=f"{ICON_ERROR} Bạn cần quyền `Administrator` để dùng lệnh này.")
        elif isinstance(error, commands.BadArgument):
            await try_send(ctx, content=f"{ICON_ERROR} Không tìm thấy kênh được chỉ định hoặc bạn nhập sai.")
        else:
            command_name_for_log = ctx.command.name if ctx.command else "unmutebot"
            print(f"Lỗi không xác định trong lệnh {command_name_for_log}: {error}")
            await try_send(ctx, content=f"{ICON_ERROR} Có lỗi xảy ra khi thực hiện lệnh bật tiếng bot.")

def setup(bot: commands.Bot):
    bot.add_cog(UnmuteBotCommandCog(bot))
