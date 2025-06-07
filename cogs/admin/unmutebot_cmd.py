import nextcord
from nextcord.ext import commands
import logging

from core.database import load_economy_data, get_or_create_guild_config, save_economy_data
from core.utils import try_send
from core.icons import ICON_ERROR, ICON_INFO, ICON_UNMUTE

logger = logging.getLogger(__name__)

class UnmuteBotCommandCog(commands.Cog, name="UnmuteBot Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"UnmuteBotCommandCog initialized.")

    @commands.command(name="unmutebot")
    @commands.has_guild_permissions(administrator=True)
    async def unmute_bot_channel(self, ctx: commands.Context, channel: nextcord.TextChannel = None):
        target_channel = channel or ctx.channel
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server.")
            return
            
        economy_data = load_economy_data()
        guild_config = get_or_create_guild_config(economy_data, ctx.guild.id)
        
        muted_channels_list = guild_config.get("muted_channels", [])
        
        if target_channel.id not in muted_channels_list:
            await try_send(ctx, content=f"{ICON_INFO} Bot không bị tắt tiếng (công khai) trong kênh {target_channel.mention}.")
        else:
            muted_channels_list.remove(target_channel.id)
            guild_config["muted_channels"] = muted_channels_list
            save_economy_data(economy_data)
            
            logger.info(f"ADMIN ACTION: {ctx.author.display_name} ({ctx.author.id}) tại guild '{ctx.guild.name}' ({ctx.guild.id}) đã UNMUTE bot trong kênh {target_channel.name} ({target_channel.id}).")
            
            msg_content = f"{ICON_UNMUTE if 'ICON_UNMUTE' in globals() or 'ICON_UNMUTE' in locals() else '🔊'} Bot đã được **BẬT TIẾNG** (công khai) trở lại trong kênh {target_channel.mention}."
            await try_send(ctx, content=msg_content)

    @unmute_bot_channel.error
    async def unmute_bot_channel_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await try_send(ctx, content=f"{ICON_ERROR} Bạn cần quyền `Administrator` để dùng lệnh này.")
        elif isinstance(error, commands.BadArgument):
            await try_send(ctx, content=f"{ICON_ERROR} Không tìm thấy kênh được chỉ định hoặc bạn nhập sai.")
        else:
            logger.error(f"Lỗi trong lệnh 'unmutebot' bởi {ctx.author.name}:", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Có lỗi xảy ra khi thực hiện lệnh bật tiếng bot.")

def setup(bot: commands.Bot):
    bot.add_cog(UnmuteBotCommandCog(bot))
