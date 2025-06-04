# bot/cogs/economy/bank_cmd.py
import nextcord
from nextcord.ext import commands

# Import các thành phần cần thiết từ package 'core'
from core.database import get_user_data
from core.utils import try_send
from core.config import CURRENCY_SYMBOL
from core.icons import ICON_BANK, ICON_ERROR # Đảm bảo các icon này có trong core/icons.py

class BankCommandCog(commands.Cog, name="Bank Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='bank')
    async def bank(self, ctx: commands.Context, user: nextcord.Member = None):
        """Hiển thị số dư tiền trong ngân hàng của bạn hoặc của người dùng được chỉ định."""
        target_user = user or ctx.author
        guild_id_str = str(ctx.guild.id)
        user_id_str = str(target_user.id)

        full_data = get_user_data(ctx.guild.id, target_user.id)
        # Truy cập dữ liệu người dùng cụ thể từ full_data
        user_specific_data = full_data.get(guild_id_str, {}).get(user_id_str, {})

        if user_id_str == "config" or not isinstance(user_specific_data, dict):
            await try_send(ctx, content=f"{ICON_ERROR} Lỗi: Không tìm thấy dữ liệu ngân hàng cho {target_user.mention}.")
            return
        
        bank_bal = user_specific_data.get("bank_balance", 0)
        await try_send(ctx, content=f"{ICON_BANK} Ngân hàng của {target_user.mention}: **{bank_bal:,}** {CURRENCY_SYMBOL}.")

def setup(bot: commands.Bot):
    bot.add_cog(BankCommandCog(bot))
