# bot/cogs/economy/balance_cmd.py
import nextcord
from nextcord.ext import commands
import logging # <<< THÊM IMPORT NÀY

# Import các thành phần cần thiết từ package 'core'
from core.database import get_user_data
from core.utils import try_send
from core.config import CURRENCY_SYMBOL
from core.icons import ICON_MONEY_BAG, ICON_ERROR, ICON_INFO # Giả sử ICON_INFO đã được import

logger = logging.getLogger(__name__) # <<< LẤY LOGGER CHO MODULE NÀY

class BalanceCommandCog(commands.Cog, name="Balance Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"BalanceCommandCog initialized.") # DEBUG, chỉ vào general log

    @commands.command(name='balance', aliases=['bal', 'cash', 'money', '$'])
    async def balance(self, ctx: commands.Context, user: nextcord.Member = None):
        """Hiển thị số dư tiền trong ví của bạn hoặc của một người dùng khác."""
        target_user = user or ctx.author
        logger.debug(f"Lệnh 'balance' được gọi bởi {ctx.author.name} cho target {target_user.name} (ID: {target_user.id}) tại guild {ctx.guild.id}.")

        guild_id_str = str(ctx.guild.id)
        user_id_str = str(target_user.id)
        
        try:
            full_data = get_user_data(ctx.guild.id, target_user.id)
            user_account_data = full_data.get(guild_id_str, {}).get(user_id_str)

            if user_id_str == "config" or not isinstance(user_account_data, dict):
                logger.warning(f"Dữ liệu tài khoản không hợp lệ cho user {user_id_str} guild {guild_id_str} khi gọi lệnh 'balance'. Data: {user_account_data}")
                await try_send(ctx, content=f"{ICON_ERROR} Lỗi: Dữ liệu tài khoản của {target_user.mention} không đúng định dạng hoặc không tìm thấy.")
                return
            
            bal = user_account_data.get("balance", 0)
            await try_send(ctx, content=f"{ICON_MONEY_BAG} Ví của {target_user.mention}: **{bal:,}** {CURRENCY_SYMBOL}.")
            logger.debug(f"Hiển thị balance thành công cho {target_user.name}: {bal} {CURRENCY_SYMBOL}.")

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'balance' cho user {target_user.name}: {e}", exc_info=True) # Ghi cả traceback
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi không xác định khi xem số dư của {target_user.mention}.")

def setup(bot: commands.Bot):
    bot.add_cog(BalanceCommandCog(bot))
