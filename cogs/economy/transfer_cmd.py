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
from core.icons import ICON_GIFT, ICON_ERROR, ICON_MONEY_BAG, ICON_INFO

logger = logging.getLogger(__name__)

class TransferCommandCog(commands.Cog, name="Transfer Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"TransferCommandCog initialized.")

    @commands.command(name='transfer', aliases=['give', 'pay'])
    async def transfer(self, ctx: commands.Context, recipient: nextcord.User, amount: int):
        """Chuyển một số tiền từ Ví Toàn Cục của bạn cho người dùng khác (toàn cục)."""
        
        sender = ctx.author
        guild_name_for_log = ctx.guild.name if ctx.guild else "DM"
        guild_id_for_log = ctx.guild.id if ctx.guild else "N/A"
        
        logger.debug(f"Lệnh 'transfer' được gọi bởi {sender.name} ({sender.id}) "
                     f"đến {recipient.name} ({recipient.id}) với số tiền {amount} "
                     f"từ guild '{guild_name_for_log}' ({guild_id_for_log}).")

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
        
        # Lấy profile toàn cục của người gửi
        sender_profile = get_or_create_global_user_profile(economy_data, sender.id)
        original_sender_global_balance = sender_profile.get("global_balance", 0)

        if original_sender_global_balance < amount:
            logger.warning(f"User {sender.id} không đủ tiền trong Ví Toàn Cục để transfer {amount} cho {recipient.id}. "
                           f"Số dư ví: {original_sender_global_balance}")
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ tiền trong Ví Toàn Cục! {ICON_MONEY_BAG} Ví của bạn: **{original_sender_global_balance:,}** {CURRENCY_SYMBOL}.")
            save_economy_data(economy_data) # Lưu nếu get_or_create_global_user_profile có tạo mới sender
            return 
        
        # Lấy profile toàn cục của người nhận
        recipient_profile = get_or_create_global_user_profile(economy_data, recipient.id)
        original_recipient_global_balance = recipient_profile.get("global_balance", 0)
        
        # Thực hiện giao dịch trên Ví Toàn Cục
        sender_profile["global_balance"] = original_sender_global_balance - amount
        recipient_profile["global_balance"] = original_recipient_global_balance + amount
        
        save_economy_data(economy_data) # Lưu lại tất cả thay đổi (cả sender và recipient)

        logger.info(f"GLOBAL TRANSFER: User {sender.display_name} ({sender.id}) đã transfer {amount:,} {CURRENCY_SYMBOL} "
                    f"cho {recipient.display_name} ({recipient.id}). "
                    f"Sender global_balance: {original_sender_global_balance:,} -> {sender_profile['global_balance']:,}. "
                    f"Recipient global_balance: {original_recipient_global_balance:,} -> {recipient_profile['global_balance']:,}. "
                    f"(Lệnh gọi từ guild: '{guild_name_for_log}' ({guild_id_for_log}))")
        
        await try_send(ctx, content=f"{ICON_GIFT} {sender.mention} đã chuyển **{amount:,}** {CURRENCY_SYMBOL} vào Ví Toàn Cục cho {recipient.mention}!")
        logger.debug(f"Lệnh 'transfer' từ {sender.name} đến {recipient.name} đã xử lý xong.")

def setup(bot: commands.Bot):
    bot.add_cog(TransferCommandCog(bot))
