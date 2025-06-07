import nextcord
from nextcord.ext import commands
import logging

from core.database import load_economy_data
from core.utils import try_send
from core.config import CURRENCY_SYMBOL
from core.icons import ICON_CROWN, ICON_INFO, ICON_ERROR

logger = logging.getLogger(__name__)

class RichestCommandCog(commands.Cog, name="Richest Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug("RichestCommandCog initialized for Ecoworld Economy.")

    @commands.command(name='richest')
    async def richest(self, ctx: commands.Context):
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server.")
            return

        logger.debug(f"Lệnh 'richest' được gọi bởi {ctx.author.name} tại guild '{ctx.guild.name}'.")
        
        economy_data = load_economy_data()
        all_users_in_guild = {str(member.id): economy_data.get("users", {}).get(str(member.id)) for member in ctx.guild.members if str(member.id) in economy_data.get("users", {})}
        
        if not all_users_in_guild:
            await try_send(ctx, content=f"{ICON_INFO} Chưa có ai trong server này có dữ liệu để xếp hạng.")
            return

        richest_user_id = None
        max_local_wealth = -1

        for user_id, user_profile in all_users_in_guild.items():
            if not isinstance(user_profile, dict): continue

            server_data = user_profile.get("server_data", {}).get(str(ctx.guild.id), {})
            if not server_data: continue

            local_balance_dict = server_data.get("local_balance", {})
            total_local_wealth = local_balance_dict.get("earned", 0) + local_balance_dict.get("admin_added", 0)
            
            if total_local_wealth > max_local_wealth:
                max_local_wealth = total_local_wealth
                richest_user_id = user_id
        
        if richest_user_id is None:
            await try_send(ctx, content=f"{ICON_INFO} Không tìm thấy người giàu nhất trong server này.")
            return
            
        try:
            user_obj = await self.bot.fetch_user(int(richest_user_id))
            logger.info(f"Richest user in guild '{ctx.guild.name}' is {user_obj.name} ({richest_user_id}) with {max_local_wealth:,} local currency.")
            await try_send(ctx, content=f"{ICON_CROWN} Người giàu nhất server **{ctx.guild.name}** là **{user_obj.name}** với tổng tài sản local là **{max_local_wealth:,}** {CURRENCY_SYMBOL}!")
        except Exception as e:
            logger.error(f"Lỗi khi fetch user ID {richest_user_id} cho lệnh 'richest':", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi tìm người giàu nhất.")

def setup(bot: commands.Bot):
    bot.add_cog(RichestCommandCog(bot))
