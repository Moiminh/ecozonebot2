# bot/cogs/economy/transfer_cmd.py
import nextcord
from nextcord.ext import commands
import logging

from core.database import get_or_create_global_user_profile
from core.utils import try_send
from core.icons import ICON_GIFT, ICON_ERROR, ICON_BANK, ICON_INFO

logger = logging.getLogger(__name__)

class TransferCommandCog(commands.Cog, name="Transfer Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("TransferCommandCog (v3 - Refactored) initialized.")

    @commands.command(name='transfer', aliases=['give', 'pay', 'tf'])
    async def transfer(self, ctx: commands.Context, recipient: nextcord.User, amount: int):
        """Chuyển tiền từ Bank của bạn cho người chơi khác (miễn phí)."""
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
            # [SỬA] Sử dụng cache từ bot
            economy_data = self.bot.economy_data
            
            sender_profile = get_or_create_global_user_profile(economy_data, sender.id)
            recipient_profile = get_or_create_global_user_profile(economy_data, recipient.id)
            
            sender_bank_balance = sender_profile.get("bank_balance", 0)

            if sender_bank_balance < amount:
                await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ tiền trong Bank! {ICON_BANK} Bank của bạn có: **{sender_bank_balance:,}**")
                return
            
            sender_profile["bank_balance"] -= amount
            recipient_profile["bank_balance"] += amount
            
            # [XÓA] Không cần save thủ công
            # save_economy_data(economy_data)

            logger.info(f"GLOBAL TRANSFER: User {sender.id} đã chuyển {amount} từ Bank cho User {recipient.id}.")

            await try_send(
                ctx,
                content=(
                    f"{ICON_GIFT} {sender.mention} đã chuyển thành công **{amount:,}** từ Bank của bạn cho {recipient.mention}!\n"
                    f"Số dư Bank mới của bạn: **{sender_profile['bank_balance']:,}** {ICON_BANK}"
                )
            )

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'transfer' (v3) từ {sender.id} đến {recipient.id}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi khi bạn chuyển tiền.")

def setup(bot: commands.Bot):
    bot.add_cog(TransferCommandCog(bot))
