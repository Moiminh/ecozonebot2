# bot/cogs/misc/richest_cmd.py
import nextcord
from nextcord.ext import commands

from core.database import load_data
from core.utils import try_send
from core.config import CURRENCY_SYMBOL
from core.icons import ICON_CROWN, ICON_INFO # Đảm bảo các icon này có trong core/icons.py

class RichestCommandCog(commands.Cog, name="Richest Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='richest')
    async def richest(self, ctx: commands.Context):
        """Hiển thị người giàu nhất trên server."""
        data = load_data()
        guild_id = str(ctx.guild.id)

        if guild_id not in data or not data[guild_id] or all(key == "config" for key in data[guild_id]):
            await try_send(ctx, content=f"{ICON_INFO} Chưa có ai để xếp hạng trên server này!")
            return
        
        guild_user_data = {
            uid: udata for uid, udata in data[guild_id].items()
            if uid != "config" and isinstance(udata, dict) and ("balance" in udata or "bank_balance" in udata)
        }
        if not guild_user_data:
            await try_send(ctx, content=f"{ICON_INFO} Chưa có ai để xếp hạng trên server này!")
            return
            
        sorted_users = sorted(
            guild_user_data.items(),
            key=lambda item: item[1].get('balance', 0) + item[1].get('bank_balance', 0),
            reverse=True
        )

        if not sorted_users: 
            await try_send(ctx, content=f"{ICON_INFO} Chưa có ai để xếp hạng trên server này!")
            return

        top_user_id, top_user_data_dict = sorted_users[0] 
        try:
            user_obj = await self.bot.fetch_user(int(top_user_id))
            total_wealth = top_user_data_dict.get('balance', 0) + top_user_data_dict.get('bank_balance', 0)
            await try_send(ctx, content=f"{ICON_CROWN} Người giàu nhất server là **{user_obj.name}** với tổng tài sản **{total_wealth:,}** {CURRENCY_SYMBOL}!")
        except (nextcord.NotFound, ValueError, KeyError) as e:
            print(f"Richest: Không thể fetch/xử lý user ID {top_user_id}. Lỗi: {e}")
            await try_send(ctx, content=f"{ICON_INFO} Không thể tìm thấy thông tin người giàu nhất (có thể do lỗi fetch user).")

def setup(bot: commands.Bot):
    bot.add_cog(RichestCommandCog(bot))
