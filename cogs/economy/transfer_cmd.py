# bot/cogs/economy/transfer_cmd.py
import nextcord
from nextcord.ext import commands
import logging
from core.utils import try_send
from core.icons import ICON_GIFT, ICON_ERROR, ICON_BANK, ICON_INFO

logger = logging.getLogger(__name__)

class TransferCommandCog(commands.Cog, name="Transfer Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("TransferCommandCog (SQLite Ready) initialized.")

    @commands.command(name='transfer', aliases=['give', 'pay', 'tf'])
    async def transfer(self, ctx: commands.Context, recipient: nextcord.User, amount: int):
        sender = ctx.author
        
        if amount <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Số tiền chuyển phải lớn hơn 0!")
            return
        if recipient.id == sender.id:
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không thể tự chuyển tiền cho mình!")
            return
        if recipient.bot:
            await try_send(ctx, content=f"{ICON_ERROR} Không thể chuyển tiền cho bot!")
            return

        try:
            sender_profile = self.bot.db.get_or_create_global_user_profile(sender.id)
            if sender_profile['bank_balance'] < amount:
                await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ tiền trong Bank! Bạn có: **{sender_profile['bank_balance']:,}**")
                return
            
            recipient_profile = self.bot.db.get_or_create_global_user_profile(recipient.id)

            self.bot.db.update_balance(sender.id, None, 'bank_balance', sender_profile['bank_balance'] - amount)
            self.bot.db.update_balance(recipient.id, None, 'bank_balance', recipient_profile['bank_balance'] + amount)
            
            logger.info(f"GLOBAL TRANSFER: User {sender.id} đã chuyển {amount} từ Bank cho User {recipient.id}.")
            new_sender_balance = sender_profile['bank_balance'] - amount
            await try_send(
                ctx,
                content=(
                    f"{ICON_GIFT} {sender.mention} đã chuyển thành công **{amount:,}** từ Bank cho {recipient.mention}!\n"
                    f"Số dư Bank mới của bạn: **{new_sender_balance:,}** {ICON_BANK}"
                )
            )
        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'transfer' từ {sender.id} đến {recipient.id}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi khi bạn chuyển tiền.")

def setup(bot: commands.Bot):
    bot.add_cog(TransferCommandCog(bot))
