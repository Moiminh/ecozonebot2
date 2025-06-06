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
        logger.debug(f"TransferCommandCog initialized for Ecoworld Economy.")

    @commands.command(name='transfer', aliases=['give', 'pay', 'tf'])
    async def transfer(self, ctx: commands.Context, recipient: nextcord.User, amount: int):
        sender = ctx.author
        
        logger.debug(f"Lệnh 'transfer' được gọi bởi {sender.name} ({sender.id}) đến {recipient.name} ({recipient.id}) với số tiền {amount}.")

        if amount <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Số tiền chuyển phải lớn hơn 0!")
            return
        if recipient.id == sender.id:
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không thể tự chuyển tiền cho mình!")
            return
        if recipient.bot:
            await try_send(ctx, content=f"{ICON_ERROR} Không thể chuyển tiền cho bot!")
            return

        economy_data = load_economy_data()
        
        sender_profile = get_or_create_global_user_profile(economy_data, sender.id)
        original_sender_global_balance = sender_profile.get("global_balance", 0)

        if original_sender_global_balance < amount:
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ tiền trong Ví Global (GOL)! {ICON_MONEY_BAG} Ví GOL của bạn: **{original_sender_global_balance:,}** {CURRENCY_SYMBOL}.")
            return
        
        recipient_profile = get_or_create_global_user_profile(economy_data, recipient.id)
        original_recipient_global_balance = recipient_profile.get("global_balance", 0)
        
        sender_profile["global_balance"] = original_sender_global_balance - amount
        recipient_profile["global_balance"] = original_recipient_global_balance + amount
        
        save_economy_data(economy_data)

        logger.info(f"GLOBAL TRANSFER: User {sender.display_name} ({sender.id}) đã transfer {amount:,} {CURRENCY_SYMBOL} GOL "
                    f"cho {recipient.display_name} ({recipient.id}). "
                    f"Sender global_balance: {original_sender_global_balance:,} -> {sender_profile['global_balance']:,}. "
                    f"Recipient global_balance: {original_recipient_global_balance:,} -> {recipient_profile['global_balance']:,}.")
        
        await try_send(ctx, content=f"{ICON_GIFT} {sender.mention} đã chuyển thành công **{amount:,}** {CURRENCY_SYMBOL} từ Ví Global của bạn sang Ví Global của {recipient.mention}!")
        
def setup(bot: commands.Bot):
    bot.add_cog(TransferCommandCog(bot))
