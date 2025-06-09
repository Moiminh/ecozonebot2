# bot/cogs/misc/richest_cmd.py
import nextcord
from nextcord.ext import commands
import logging

# [SỬA] Import các hàm và hằng số cần thiết từ core
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
        logger.debug(f"Lệnh 'richest' được gọi bởi {ctx.author.name} tại guild '{ctx.guild.name}'.")
        
        # [SỬA] Sử dụng cache của bot
        economy_data = self.bot.economy_data
        
        # Lấy ID của tất cả member trong server hiện tại
        guild_member_ids = {str(member.id) for member in ctx.guild.members}
        all_users_data = economy_data.get("users", {})

        richest_user_id = None
        max_local_wealth = -1

        for user_id, user_profile in all_users_data.items():
            # Chỉ xét những user có trong server này
            if user_id not in guild_member_ids:
                continue

            if isinstance(user_profile, dict):
                server_data = user_profile.get("server_data", {}).get(str(ctx.guild.id), {})
                if not server_data:
                    continue

                local_balance_dict = server_data.get("local_balance", {})
                total_local_wealth = local_balance_dict.get("earned", 0) + local_balance_dict.get("adadd", 0)
                
                if total_local_wealth > max_local_wealth:
                    max_local_wealth = total_local_wealth
                    richest_user_id = user_id
        
        if richest_user_id is None:
            await try_send(ctx, content=f"{ICON_INFO} Không tìm thấy người giàu nhất trong server này.")
            return
            
        try:
            user_obj = await self.bot.fetch_user(int(richest_user_id))
            await try_send(ctx, content=f"{ICON_CROWN} Người giàu nhất server **{ctx.guild.name}** là **{user_obj.name}** với tổng tài sản local là **{format_large_number(max_local_wealth)}** {ICON_MONEY_BAG}!")
        except Exception as e:
            logger.error(f"Lỗi khi fetch user ID {richest_user_id} cho lệnh 'richest':", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi tìm người giàu nhất.")

def setup(bot: commands.Bot):
    bot.add_cog(RichestCommandCog(bot))
