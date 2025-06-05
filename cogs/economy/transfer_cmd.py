# bot/cogs/economy/transfer_cmd.py
import nextcord
from nextcord.ext import commands
import logging

from core.database import (
    load_economy_data,
    get_or_create_global_user_profile,
    save_economy_data
)
from core.utils import try_send
from core.config import CURRENCY_SYMBOL
from core.icons import ICON_GIFT, ICON_ERROR, ICON_MONEY_BAG, ICON_INFO # Đảm bảo có ICON_INFO

logger = logging.getLogger(__name__)

class TransferCommandCog(commands.Cog, name="Transfer Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"TransferCommandCog initialized.")

    @commands.command(name='transfer', aliases=['give', 'pay'])
    async def transfer(self, ctx: commands.Context, recipient: nextcord.User, amount: int):
        """Chuyển một số tiền từ Ví Toàn Cục của bạn cho người dùng khác."""
        
        sender = ctx.author
        # Thêm thông tin Guild vào log debug ban đầu
        guild_info_for_log = f"tại guild '{ctx.guild.name}' ({ctx.guild.id})" if ctx.guild else "qua DM"
        logger.debug(f"Lệnh 'transfer' được gọi bởi {sender.name} (ID: {sender.id}) "
                     f"đến {recipient.name} (ID: {recipient.id}) với số tiền {amount} {guild_info_for_log}.")

        if amount <= 0:
            logger.warning(f"User {sender.id} cố gắng transfer số tiền không hợp lệ (<=0): {amount} cho {recipient.id}.")
            await try_send(ctx, content=f"{ICON_ERROR} Số tiền chuyển phải lớn hơn 0!")
            return
        if recipient.id == sender.id:
            logger.warning(f"User {sender.id} cố gắng transfer cho chính mình.")
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không thể tự chuyển tiền cho mình!")
            return
        if recipient.bot:
            logger.warning(f"User {sender.id} cố gắng transfer cho bot {recipient.name} ({recipient.id}).")
            await try_send(ctx, content=f"{ICON_ERROR} Không thể chuyển tiền cho bot!")
            return

        economy_data = load_economy_data()
        
        sender_profile = get_or_create_global_user_profile(economy_data, sender.id)
        original_sender_global_balance = sender_profile.get("global_balance", 0)

        if original_sender_global_balance < amount:
            logger.warning(f"User {sender.id} không đủ tiền trong Ví Toàn Cục để transfer {amount} cho {recipient.id}. Số dư ví: {original_sender_global_balance}")
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ tiền trong Ví Toàn Cục! {ICON_MONEY_BAG} Ví của bạn: **{original_sender_global_balance:,}** {CURRENCY_SYMBOL}.")
            return 
        
        recipient_profile = get_or_create_global_user_profile(economy_data, recipient.id)
        original_recipient_global_balance = recipient_profile.get("global_balance", 0)
        
        # Thực hiện giao dịch trên Ví Toàn Cục
        sender_profile["global_balance"] = original_sender_global_balance - amount
        recipient_profile["global_balance"] = original_recipient_global_balance + amount
        
        save_economy_data(economy_data)

        # Log INFO cho hành động này sẽ không có guild_id vì nó là giao dịch toàn cục
        # Tuy nhiên, lệnh được gọi từ một guild, nên có thể log guild nơi lệnh được gọi nếu muốn.
        # Hiện tại, chỉ log thông tin người gửi, người nhận và số tiền.
        logger.info(f"GLOBAL TRANSFER: User {sender.display_name} ({sender.id}) đã transfer {amount:,} {CURRENCY_SYMBOL} "
                    f"cho {recipient.display_name} ({recipient.id}). "
                    f"Sender global_balance: {original_sender_global_balance:,} -> {sender_profile['global_balance']:,}. "
                    f"Recipient global_balance: {original_recipient_global_balance:,} -> {recipient_profile['global_balance']:,}. "
                    f"(Lệnh gọi từ guild: '{ctx.guild.name if ctx.guild else 'DM'}' ({ctx.guild.id if ctx.guild else 'N/A'}))")
        
        await try_send(ctx, content=f"{ICON_GIFT} {sender.mention} đã chuyển **{amount:,}** {CURRENCY_SYMBOL} vào Ví Toàn Cục cho {recipient.mention}!")
        logger.debug(f"Lệnh 'transfer' từ {sender.name} đến {recipient.name} đã xử lý xong.")

def setup(bot: commands.Bot):
    bot.add_cog(TransferCommandCog(bot))
