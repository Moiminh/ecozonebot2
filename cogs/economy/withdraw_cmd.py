# bot/cogs/economy/withdraw_cmd.py
import nextcord
from nextcord.ext import commands

# Import các thành phần cần thiết từ package 'core'
from core.database import get_user_data, save_data # Cần save_data
from core.utils import try_send
from core.config import CURRENCY_SYMBOL
from core.icons import ICON_BANK, ICON_MONEY_BAG, ICON_SUCCESS, ICON_ERROR, ICON_WARNING # Đảm bảo các icon này có trong core/icons.py

class WithdrawCommandCog(commands.Cog, name="Withdraw Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='withdraw', aliases=['wd'])
    async def withdraw(self, ctx: commands.Context, amount_str: str):
        """Rút tiền từ tài khoản ngân hàng về ví của bạn."""
        data = get_user_data(ctx.guild.id, ctx.author.id)
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]
        
        try:
            if amount_str.lower() == 'all':
                amount = user_data.get("bank_balance", 0)
            else:
                amount = int(amount_str)
        except ValueError:
            await try_send(ctx, content=f"{ICON_WARNING} Vui lòng nhập một số tiền hợp lệ hoặc 'all'.")
            return
            
        if amount <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Số tiền rút phải lớn hơn 0.")
            return
        if user_data.get("bank_balance", 0) < amount:
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ tiền trong ngân hàng. {ICON_BANK} Ngân hàng của bạn: {user_data.get('bank_balance',0):,} {CURRENCY_SYMBOL}")
            return

        user_data["balance"] = user_data.get("balance", 0) + amount
        user_data["bank_balance"] -= amount
        save_data(data)
        await try_send(ctx, content=f"{ICON_SUCCESS} Bạn đã rút **{amount:,}** {CURRENCY_SYMBOL} từ ngân hàng.\n{ICON_MONEY_BAG} Ví: **{user_data['balance']:,}** | {ICON_BANK} Ngân hàng: **{user_data['bank_balance']:,}**")

def setup(bot: commands.Bot):
    bot.add_cog(WithdrawCommandCog(bot))
