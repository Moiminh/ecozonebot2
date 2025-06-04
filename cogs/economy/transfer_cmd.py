# bot/cogs/economy/transfer_cmd.py
import nextcord
from nextcord.ext import commands
import logging # <<< THÊM IMPORT NÀY

# Import các thành phần cần thiết từ package 'core'
from core.database import get_user_data, save_data, check_user 
from core.utils import try_send
from core.config import CURRENCY_SYMBOL
from core.icons import ICON_GIFT, ICON_ERROR, ICON_MONEY_BAG, ICON_INFO # Đảm bảo có ICON_INFO

logger = logging.getLogger(__name__) # <<< LẤY LOGGER CHO MODULE NÀY

class TransferCommandCog(commands.Cog, name="Transfer Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"TransferCommandCog initialized.")

    @commands.command(name='transfer', aliases=['give', 'pay'])
    async def transfer(self, ctx: commands.Context, recipient: nextcord.Member, amount: int):
        """Chuyển một số tiền từ ví của bạn cho người dùng khác."""
        logger.debug(f"Lệnh 'transfer' được gọi bởi {ctx.author.name} (ID: {ctx.author.id}) "
                     f"đến {recipient.name} (ID: {recipient.id}) với số tiền {amount} tại guild {ctx.guild.id}.")

        if amount <= 0:
            logger.warning(f"User {ctx.author.id} cố gắng transfer số tiền không hợp lệ (<=0): {amount}")
            await try_send(ctx, content=f"{ICON_ERROR} Số tiền chuyển phải lớn hơn 0!")
            return
        if recipient.id == ctx.author.id:
            logger.warning(f"User {ctx.author.id} cố gắng transfer cho chính mình.")
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không thể tự chuyển tiền cho mình!")
            return
        if recipient.bot:
            logger.warning(f"User {ctx.author.id} cố gắng transfer cho bot {recipient.name}.")
            await try_send(ctx, content=f"{ICON_ERROR} Không thể chuyển tiền cho bot!")
            return

        full_data = get_user_data(ctx.guild.id, ctx.author.id)
        full_data = check_user(full_data, ctx.guild.id, recipient.id) # Đảm bảo người nhận có dữ liệu

        sender_data = full_data[str(ctx.guild.id)][str(ctx.author.id)]
        recipient_data = full_data[str(ctx.guild.id)][str(recipient.id)]

        original_sender_balance = sender_data.get("balance", 0)
        original_recipient_balance = recipient_data.get("balance", 0)

        if original_sender_balance < amount:
            logger.warning(f"User {ctx.author.id} không đủ tiền để transfer {amount}. Số dư ví: {original_sender_balance}")
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ tiền! {ICON_MONEY_BAG} Ví của bạn: **{original_sender_balance:,}** {CURRENCY_SYMBOL}.")
            return
        
        sender_data["balance"] -= amount
        recipient_data["balance"] += amount # recipient_data.get("balance", 0) đã được xử lý bởi check_user
        save_data(full_data)

        # Ghi log hành động của người chơi
        logger.info(f"User {ctx.author.display_name} ({ctx.author.id}) đã transfer {amount:,} {CURRENCY_SYMBOL} "
                    f"cho {recipient.display_name} ({recipient.id}). "
                    f"Sender balance: {original_sender_balance:,} -> {sender_data['balance']:,}. "
                    f"Recipient balance: {original_recipient_balance:,} -> {recipient_data['balance']:,}.")
        
        await try_send(ctx, content=f"{ICON_GIFT} {ctx.author.mention} đã chuyển **{amount:,}** {CURRENCY_SYMBOL} cho {recipient.mention}!")
        logger.debug(f"Lệnh 'transfer' từ {ctx.author.name} đến {recipient.name} đã xử lý xong.")

def setup(bot: commands.Bot):
    bot.add_cog(TransferCommandCog(bot))
