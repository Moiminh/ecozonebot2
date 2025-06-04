# bot/cogs/admin/mutebot_cmd.py
import nextcord
from nextcord.ext import commands
import logging # <<< THÊM IMPORT NÀY

from core.database import get_guild_config, save_guild_config
from core.utils import try_send
from core.icons import ICON_ERROR, ICON_INFO, ICON_MUTE # Giả sử bạn có ICON_MUTE = "🔇" hoặc tương tự trong icons.py

logger = logging.getLogger(__name__) # <<< LẤY LOGGER CHO MODULE NÀY

class MuteBotCommandCog(commands.Cog, name="MuteBot Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"MuteBotCommandCog initialized.")

    @commands.command(name="mutebot")
    @commands.has_guild_permissions(administrator=True)
    async def mute_bot_channel(self, ctx: commands.Context, channel: nextcord.TextChannel = None):
        target_channel = channel or ctx.channel
        logger.debug(f"Lệnh 'mutebot' được gọi bởi {ctx.author.name} (ID: {ctx.author.id}) cho kênh {target_channel.name} (ID: {target_channel.id}) tại guild {ctx.guild.id}.")
        
        if not ctx.guild:
            logger.warning(f"Lệnh 'mutebot' được gọi ngoài guild bởi {ctx.author.id}.")
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server.")
            return
            
        current_guild_config = get_guild_config(ctx.guild.id)
        muted_channels_list = current_guild_config.get("muted_channels", [])
        
        action_taken_log = "" # Để ghi log
        msg_content = ""

        if target_channel.id in muted_channels_list:
            action_taken_log = "không thay đổi (kênh đã được mute từ trước)"
            msg_content = f"{ICON_INFO} Bot đã bị tắt tiếng (công khai) trong kênh {target_channel.mention} rồi."
        else:
            muted_channels_list.append(target_channel.id)
            current_guild_config["muted_channels"] = muted_channels_list
            save_guild_config(ctx.guild.id, current_guild_config)
            action_taken_log = f"MUTE kênh {target_channel.name} (ID: {target_channel.id})"
            # Sử dụng ICON_MUTE nếu có, hoặc giữ emoji gốc
            msg_content = f"{ICON_MUTE if 'ICON_MUTE' in globals() else '🔇'} Bot đã bị **TẮT TIẾNG** (công khai) trong kênh {target_channel.mention}. Các tin nhắn ephemeral (nếu có) vẫn hoạt động."
        
        # Ghi log hành động admin
        logger.info(f"ADMIN ACTION: {ctx.author.display_name} ({ctx.author.id}) thực hiện 'mutebot'. Kết quả: {action_taken_log} trong guild {ctx.guild.id}.")
        
        await try_send(ctx, content=msg_content)
        logger.debug(f"Lệnh 'mutebot' cho kênh {target_channel.id} bởi {ctx.author.name} đã xử lý xong. Trạng thái: {action_taken_log}.")

    @mute_bot_channel.error
    async def mute_bot_channel_error(self, ctx: commands.Context, error):
        command_name_for_log = ctx.command.name if ctx.command else "mutebot"
        if isinstance(error, commands.MissingPermissions):
            logger.warning(f"MissingPermissions cho lệnh '{command_name_for_log}' bởi user {ctx.author.id}: {error}")
            await try_send(ctx, content=f"{ICON_ERROR} Bạn cần quyền `Administrator` để dùng lệnh này.")
        elif isinstance(error, commands.BadArgument):
            logger.warning(f"BadArgument cho lệnh '{command_name_for_log}' bởi user {ctx.author.id}: {error}")
            await try_send(ctx, content=f"{ICON_ERROR} Không tìm thấy kênh được chỉ định hoặc bạn nhập sai.")
        else:
            logger.error(f"Lỗi không xác định trong lệnh '{command_name_for_log}' bởi user {ctx.author.id}: {error}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Có lỗi xảy ra khi thực hiện lệnh tắt tiếng bot.")

def setup(bot: commands.Bot):
    bot.add_cog(MuteBotCommandCog(bot))
