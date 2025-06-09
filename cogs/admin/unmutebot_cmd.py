# bot/cogs/admin/unmutebot_cmd.py
import nextcord
from nextcord.ext import commands
import logging
import json
from core.utils import try_send
from core.icons import ICON_ERROR, ICON_INFO, ICON_UNMUTE

logger = logging.getLogger(__name__)

class UnmuteBotCommandCog(commands.Cog, name="UnmuteBot Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug("UnmuteBotCommandCog (SQLite Ready) initialized.")

    @commands.command(name="unmutebot")
    @commands.has_guild_permissions(administrator=True)
    @commands.guild_only()
    async def unmute_bot_channel(self, ctx: commands.Context, channel: nextcord.TextChannel = None):
        """(Admin) Bật lại tiếng cho bot trong một kênh đã bị tắt tiếng."""
        target_channel = channel or ctx.channel
        
        guild_config = self.bot.db.get_or_create_guild_config(ctx.guild.id)
        muted_channels = json.loads(guild_config['muted_channels'])
        
        if target_channel.id not in muted_channels:
            await try_send(ctx, content=f"{ICON_INFO} Bot không bị tắt tiếng trong kênh {target_channel.mention}.")
        else:
            muted_channels.remove(target_channel.id)
            self.bot.db.update_guild_config_list(ctx.guild.id, 'muted_channels', muted_channels)
            
            logger.info(f"ADMIN ACTION: {ctx.author.display_name} đã UNMUTE bot trong kênh {target_channel.name}.")
            await try_send(ctx, content=f"{ICON_UNMUTE} Bot đã được **BẬT TIẾNG** (công khai) trở lại trong kênh {target_channel.mention}.")

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
