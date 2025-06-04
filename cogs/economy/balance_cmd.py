# bot/cogs/economy/balance_cmd.py
import nextcord
from nextcord.ext import commands

# Import các thành phần cần thiết từ package 'core'
from core.database import get_user_data
from core.utils import try_send
from core.config import CURRENCY_SYMBOL
from core.icons import ICON_MONEY_BAG, ICON_ERROR # Đảm bảo các icon này có trong core/icons.py

class BalanceCommandCog(commands.Cog, name="Balance Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='balance', aliases=['bal', 'cash', 'money', '$'])
    async def balance(self, ctx: commands.Context, user: nextcord.Member = None):
        """Hiển thị số dư tiền trong ví của bạn hoặc của một người dùng khác."""
        target_user = user or ctx.author
        guild_id_str = str(ctx.guild.id)
        user_id_str = str(target_user.id)
        
        try:
            full_data = get_user_data(ctx.guild.id, target_user.id)
            # Truy cập dữ liệu người dùng cụ thể từ full_data
            user_account_data = full_data.get(guild_id_str, {}).get(user_id_str)

            if user_id_str == "config" or not isinstance(user_account_data, dict):
                await try_send(ctx, content=f"{ICON_ERROR} Lỗi: Dữ liệu tài khoản của {target_user.mention} không đúng định dạng hoặc không tìm thấy.")
                return
            
            bal = user_account_data.get("balance", 0)
            await try_send(ctx, content=f"{ICON_MONEY_BAG} Ví của {target_user.mention}: **{bal:,}** {CURRENCY_SYMBOL}.")

        except Exception as e:
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi không xác định khi xem số dư của {target_user.mention}.")
            print(f"ERROR in balance command (cog): {type(e).__name__} - {e}")

def setup(bot: commands.Bot):
    bot.add_cog(BalanceCommandCog(bot))
