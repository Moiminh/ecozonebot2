# bot/cogs/admin/mutebot_cmd.py
import nextcord
from nextcord.ext import commands
import logging

# [SỬA] Import hàm get_or_create_guild_config
from core.database import get_or_create_guild_config
from core.utils import try_send
from core.icons import ICON_ERROR, ICON_INFO, ICON_MUTE

logger = logging.getLogger(__name__)

class MuteBotCommandCog(commands.Cog, name="MuteBot Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"MuteBotCommandCog initialized.")

    @commands.command(name="mutebot")
    @commands.has_guild_permissions(administrator=True)
    @commands.guild_only()
    async def mute_bot_channel(self, ctx: commands.Context, channel: nextcord.TextChannel = None):
        target_channel = channel or ctx.channel
        
        # [SỬA] Sử dụng cache của bot
        economy_data = self.bot.economy_data
        guild_config = get_or_create_guild_config(economy_data, ctx.guild.id)
        
        muted_channels_list = guild_config.setdefault("muted_channels", [])
        
        if target_channel.id in muted_channels_list:
            await try_send(ctx, content=f"{ICON_INFO} Bot đã bị tắt tiếng trong kênh {target_channel.mention} rồi.")
        else:
            muted_channels_list.append(target_channel.id)
            # [XÓA] Không cần save thủ công
            # guild_config["muted_channels"] = muted_channels_list
            # save_economy_data(economy_data)
            
            logger.info(f"ADMIN ACTION: {ctx.author.display_name} ({ctx.author.id}) tại guild '{ctx.guild.name}' ({ctx.guild.id}) đã MUTE bot trong kênh {target_channel.name} ({target_channel.id}).")
            
            await try_send(ctx, content=f"{ICON_MUTE} Bot đã bị **TẮT TIẾNG** (công khai) trong kênh {target_channel.mention}.")

    @mute_bot_channel.error
    async def mute_bot_channel_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await try_send(ctx, content=f"{ICON_ERROR} Bạn cần quyền `Administrator` để dùng lệnh này.")
        elif isinstance(error, commands.BadArgument):
            await try_send(ctx, content=f"{ICON_ERROR} Không tìm thấy kênh được chỉ định hoặc bạn nhập sai.")
        else:
            logger.error(f"Lỗi trong lệnh 'mutebot' bởi {ctx.author.name}:", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Có lỗi xảy ra khi thực hiện lệnh tắt tiếng bot.")

def setup(bot: commands.Bot):
    bot.add_cog(MuteBotCommandCog(bot))
