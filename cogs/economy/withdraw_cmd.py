# bot/cogs/economy/withdraw_cmd.py
import nextcord
from nextcord.ext import commands
import logging
from core.utils import try_send, require_travel_check
from core.icons import ICON_BANK, ICON_SUCCESS, ICON_ERROR, ICON_WARNING, ICON_TIEN_SACH

logger = logging.getLogger(__name__)

class WithdrawCommandCog(commands.Cog, name="Withdraw Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("WithdrawCommandCog (SQLite Ready) initialized.")

    @commands.command(name='withdraw', aliases=['wd'])
    @commands.guild_only()
    @require_travel_check
    async def withdraw(self, ctx: commands.Context, amount_str: str):
        """Rút tiền từ Bank về Ví Local (Tiền Sạch)."""
        author_id = ctx.author.id
        guild_id = ctx.guild.id
        
        try:
            global_profile = self.bot.db.get_or_create_global_user_profile(author_id)
            local_data = self.bot.db.get_or_create_user_local_data(author_id, guild_id)
            
            bank_balance = global_profile['bank_balance']
            earned_balance = local_data['local_balance_earned']

            if amount_str.lower() == 'all':
                amount_to_withdraw = bank_balance
            else:
                try:
                    amount_to_withdraw = int(amount_str)
                except ValueError:
                    await try_send(ctx, content=f"{ICON_WARNING} Vui lòng nhập một số tiền hợp lệ hoặc 'all'.")
                    return

            if amount_to_withdraw <= 0:
                await try_send(ctx, content=f"{ICON_ERROR} Số tiền rút phải lớn hơn 0.")
                return

            if bank_balance < amount_to_withdraw:
                await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ tiền trong Bank. Bạn có: **{bank_balance:,}**")
                return

            # Thực hiện giao dịch
            new_bank_balance = bank_balance - amount_to_withdraw
            new_earned_balance = earned_balance + amount_to_withdraw
            self.bot.db.update_balance(author_id, None, 'bank_balance', new_bank_balance)
            self.bot.db.update_balance(author_id, guild_id, 'local_balance_earned', new_earned_balance)
            
            logger.info(f"User {author_id} tại guild {guild_id} đã withdraw {amount_to_withdraw} từ Bank.")
            await try_send(
                ctx,
                content=(
                    f"{ICON_SUCCESS} Rút tiền thành công!\n"
                    f"- Đã rút từ Bank: **{amount_to_withdraw:,}** {ICON_BANK}\n"
                    f"Số dư mới:\n"
                    f"  - {ICON_BANK} Bank: **{new_bank_balance:,}**\n"
                    f"  - {ICON_TIEN_SACH} Tiền Sạch (Ví Local): **{new_earned_balance:,}**"
                )
            )
        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'withdraw' cho user {author_id}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi bạn rút tiền.")

def setup(bot: commands.Bot):
    bot.add_cog(WithdrawCommandCog(bot))
