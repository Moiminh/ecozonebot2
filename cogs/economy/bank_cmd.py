# bot/cogs/economy/bank_cmd.py
import nextcord
from nextcord.ext import commands
import logging # <<< THÊM IMPORT NÀY

# Import các thành phần cần thiết từ package 'core'
from core.database import get_user_data
from core.utils import try_send
from core.config import CURRENCY_SYMBOL
from core.icons import ICON_BANK, ICON_ERROR, ICON_INFO # Giả sử ICON_INFO đã được import

logger = logging.getLogger(__name__) # <<< LẤY LOGGER CHO MODULE NÀY

class BankCommandCog(commands.Cog, name="Bank Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"BankCommandCog initialized.") # DEBUG, chỉ vào general log

    @commands.command(name='bank')
    async def bank(self, ctx: commands.Context, user: nextcord.Member = None):
        """Hiển thị số dư tiền trong ngân hàng của bạn hoặc của người dùng được chỉ định."""
        target_user = user or ctx.author
        logger.debug(f"Lệnh 'bank' được gọi bởi {ctx.author.name} cho target {target_user.name} (ID: {target_user.id}) tại guild {ctx.guild.id}.")

        guild_id_str = str(ctx.guild.id)
        user_id_str = str(target_user.id)

        full_data = get_user_data(ctx.guild.id, target_user.id)
        user_specific_data = full_data.get(guild_id_str, {}).get(user_id_str, {})

        if user_id_str == "config" or not isinstance(user_specific_data, dict):
            logger.warning(f"Dữ liệu ngân hàng không hợp lệ cho user {user_id_str} guild {guild_id_str} khi gọi lệnh 'bank'. Data: {user_specific_data}")
            await try_send(ctx, content=f"{ICON_ERROR} Lỗi: Không tìm thấy dữ liệu ngân hàng cho {target_user.mention}.")
            return
        
        bank_bal = user_specific_data.get("bank_balance", 0)
        await try_send(ctx, content=f"{ICON_BANK} Ngân hàng của {target_user.mention}: **{bank_bal:,}** {CURRENCY_SYMBOL}.")
        logger.debug(f"Hiển thị bank balance thành công cho {target_user.name}: {bank_bal} {CURRENCY_SYMBOL}.")

def setup(bot: commands.Bot):
    bot.add_cog(BankCommandCog(bot))
