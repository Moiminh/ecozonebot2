# bot/cogs/economy/deposit_cmd.py
import nextcord
from nextcord.ext import commands
import logging # <<< THÊM IMPORT NÀY

# Import các thành phần cần thiết từ package 'core'
from core.database import get_user_data, save_data 
from core.utils import try_send
from core.config import CURRENCY_SYMBOL
from core.icons import ICON_BANK, ICON_MONEY_BAG, ICON_SUCCESS, ICON_ERROR, ICON_WARNING, ICON_INFO # Đảm bảo có ICON_INFO

logger = logging.getLogger(__name__) # <<< LẤY LOGGER CHO MODULE NÀY

class DepositCommandCog(commands.Cog, name="Deposit Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"DepositCommandCog initialized.")

    @commands.command(name='deposit', aliases=['dep'])
    async def deposit(self, ctx: commands.Context, amount_str: str):
        """Gửi tiền từ ví vào tài khoản ngân hàng của bạn."""
        logger.debug(f"Lệnh 'deposit' được gọi bởi {ctx.author.name} (ID: {ctx.author.id}) với amount_str='{amount_str}' tại guild {ctx.guild.id}.")
        
        data = get_user_data(ctx.guild.id, ctx.author.id)
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]
        
        original_balance = user_data.get("balance", 0)
        original_bank_balance = user_data.get("bank_balance", 0)
        amount = 0 # Khởi tạo amount

        try:
            if amount_str.lower() == 'all':
                amount = original_balance
                logger.debug(f"User {ctx.author.id} chọn deposit 'all', số tiền: {amount}")
            else:
                amount = int(amount_str)
                logger.debug(f"User {ctx.author.id} chọn deposit số tiền: {amount}")

        except ValueError:
            logger.warning(f"Lỗi ValueError khi user {ctx.author.id} nhập amount_str='{amount_str}' cho lệnh 'deposit'.")
            await try_send(ctx, content=f"{ICON_WARNING} Vui lòng nhập một số tiền hợp lệ hoặc 'all'.")
            return
            
        if amount <= 0:
            logger.warning(f"User {ctx.author.id} nhập số tiền deposit không hợp lệ (<=0): {amount}")
            await try_send(ctx, content=f"{ICON_ERROR} Số tiền gửi phải lớn hơn 0.")
            return
        if original_balance < amount:
            logger.warning(f"User {ctx.author.id} không đủ tiền để deposit {amount}. Số dư ví: {original_balance}")
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ tiền trong ví. {ICON_MONEY_BAG} Ví của bạn: {original_balance:,} {CURRENCY_SYMBOL}")
            return
        
        user_data["balance"] -= amount
        user_data["bank_balance"] += amount
        save_data(data)

        # Ghi log hành động của người chơi (sẽ vào cả general log và player_actions.log)
        logger.info(f"User {ctx.author.display_name} ({ctx.author.id}) đã deposit {amount:,} {CURRENCY_SYMBOL}. "
                    f"Ví: {original_balance:,} -> {user_data['balance']:,}. "
                    f"Ngân hàng: {original_bank_balance:,} -> {user_data['bank_balance']:,}.")
        
        await try_send(ctx, content=f"{ICON_SUCCESS} Bạn đã gửi **{amount:,}** {CURRENCY_SYMBOL} vào ngân hàng.\n{ICON_MONEY_BAG} Ví: **{user_data['balance']:,}** | {ICON_BANK} Ngân hàng: **{user_data['bank_balance']:,}**")
        logger.debug(f"Lệnh 'deposit' cho {ctx.author.name} đã xử lý xong.")

def setup(bot: commands.Bot):
    bot.add_cog(DepositCommandCog(bot))
