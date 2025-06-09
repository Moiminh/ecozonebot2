# bot/cogs/misc/richest_cmd.py
import nextcord
from nextcord.ext import commands
import logging
from core.utils import try_send, format_large_number
from core.icons import ICON_CROWN, ICON_INFO, ICON_ERROR, ICON_MONEY_BAG

logger = logging.getLogger(__name__)

class RichestCommandCog(commands.Cog, name="Richest Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug("RichestCommandCog (SQLite Ready) initialized.")

    @commands.command(name='richest')
    @commands.guild_only()
    async def richest(self, ctx: commands.Context):
        logger.debug(f"Lệnh 'richest' được gọi bởi {ctx.author.name} tại guild '{ctx.guild.name}'.")
        await ctx.message.add_reaction("⏳")
        
        try:
            richest_user_data = self.bot.db.get_richest_user_in_guild(ctx.guild.id)
            await ctx.message.remove_reaction("⏳", self.bot.user)

            if not richest_user_data:
                await try_send(ctx, content=f"{ICON_INFO} Không tìm thấy người giàu nhất trong server này.")
                return
                
            try:
                user_obj = await self.bot.fetch_user(richest_user_data['user_id'])
                max_local_wealth = richest_user_data['total_local_wealth']
                await try_send(ctx, content=f"{ICON_CROWN} Người giàu nhất server **{ctx.guild.name}** là **{user_obj.name}** với tổng tài sản local là **{format_large_number(max_local_wealth)}** {ICON_MONEY_BAG}!")
            except Exception:
                logger.error(f"Lỗi khi fetch user ID {richest_user_data['user_id']} cho lệnh 'richest'.")
                await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi tìm người giàu nhất.")

        except Exception as e:
            logger.error(f"Lỗi không mong muốn trong lệnh 'richest': {e}", exc_info=True)
            if ctx.guild:
                try: await ctx.message.remove_reaction("⏳", self.bot.user)
                except: pass
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra, vui lòng thử lại sau.")

def setup(bot: commands.Bot):
    bot.add_cog(RichestCommandCog(bot))
