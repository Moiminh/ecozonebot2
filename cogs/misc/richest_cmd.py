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
        logger.debug("RichestCommandCog (Refactored) initialized.")

    @commands.command(name='richest')
    @commands.guild_only()
    async def richest(self, ctx: commands.Context):
        """Hiển thị người giàu nhất (dựa trên Ví Local) trong server hiện tại."""
        logger.debug(f"Lệnh 'richest' được gọi bởi {ctx.author.name} tại guild '{ctx.guild.name}'.")
        
        await ctx.message.add_reaction("⏳")
        
        try:
            # [TỐI ƯU] Lấy danh sách thành viên trong server trước để giảm số lần lặp
            guild_member_ids = {str(member.id) for member in ctx.guild.members if not member.bot}
            
            all_users_data = self.bot.economy_data.get("users", {})

            richest_user_id = None
            max_local_wealth = -1

            # Lặp qua danh sách thành viên của server (nhỏ hơn) thay vì toàn bộ user của bot
            for user_id in guild_member_ids:
                user_profile = all_users_data.get(user_id)

                if not user_profile or not isinstance(user_profile, dict):
                    continue

                server_data = user_profile.get("server_data", {}).get(str(ctx.guild.id))
                if not server_data:
                    continue

                local_balance_dict = server_data.get("local_balance", {})
                total_local_wealth = local_balance_dict.get("earned", 0) + local_balance_dict.get("adadd", 0)
                
                if total_local_wealth > max_local_wealth:
                    max_local_wealth = total_local_wealth
                    richest_user_id = user_id
            
            await ctx.message.remove_reaction("⏳", self.bot.user)

            if richest_user_id is None:
                await try_send(ctx, content=f"{ICON_INFO} Không tìm thấy người giàu nhất trong server này.")
                return
                
            try:
                user_obj = await self.bot.fetch_user(int(richest_user_id))
                await try_send(ctx, content=f"{ICON_CROWN} Người giàu nhất server **{ctx.guild.name}** là **{user_obj.name}** với tổng tài sản local là **{format_large_number(max_local_wealth)}** {ICON_MONEY_BAG}!")
            except Exception as e:
                logger.error(f"Lỗi khi fetch user ID {richest_user_id} cho lệnh 'richest':", exc_info=True)
                await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi tìm người giàu nhất.")

        except Exception as e:
            logger.error(f"Lỗi không mong muốn trong lệnh 'richest': {e}", exc_info=True)
            if ctx.guild:
                await ctx.message.remove_reaction("⏳", self.bot.user)
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra, vui lòng thử lại sau.")

def setup(bot: commands.Bot):
    bot.add_cog(RichestCommandCog(bot))
