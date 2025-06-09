# bot/cogs/economy/deposit_cmd.py
import nextcord
from nextcord.ext import commands
import logging
from core.utils import try_send, require_travel_check
from core.config import DEPOSIT_FEE_PERCENTAGE, LAUNDER_EXCHANGE_RATE
from core.icons import ICON_BANK_MAIN, ICON_MONEY_BAG, ICON_SUCCESS, ICON_ERROR, ICON_WARNING, ICON_INFO, ICON_ECOIN

logger = logging.getLogger(__name__)

class DepositCommandCog(commands.Cog, name="Deposit Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("DepositCommandCog (SQLite Ready) initialized.")

    @commands.command(name='deposit', aliases=['dep'])
    @commands.guild_only()
    @require_travel_check
    async def deposit(self, ctx: commands.Context, amount_str: str):
        author_id = ctx.author.id
        guild_id = ctx.guild.id
        
        try:
            global_profile = self.bot.db.get_or_create_global_user_profile(author_id)
            local_data = self.bot.db.get_or_create_user_local_data(author_id, guild_id)
            earned_balance = local_data['local_balance_earned']

            amount_to_deposit = earned_balance if amount_str.lower() == 'all' else int(amount_str)

            if amount_to_deposit <= 0:
                await try_send(ctx, content=f"{ICON_ERROR} Số tiền gửi phải lớn hơn 0.")
                return

            fee = int(amount_to_deposit * DEPOSIT_FEE_PERCENTAGE)
            total_cost = amount_to_deposit + fee

            if earned_balance < total_cost:
                await try_send(ctx, content=f"{ICON_ERROR} Không đủ {ICON_ECOIN} để trả phí! Cần: `{total_cost:,}`.")
                return

            # Thực hiện giao dịch
            self.bot.db.update_balance(author_id, guild_id, 'local_balance_earned', earned_balance - total_cost)
            self.bot.db.update_balance(author_id, None, 'bank_balance', global_profile['bank_balance'] + amount_to_deposit)
            
            msg = (
                f"{ICON_SUCCESS} Giao dịch thành công!\n"
                f"- Đã gửi vào Bank: **{amount_to_deposit:,}** {ICON_BANK_MAIN}\n"
                f"- Phí giao dịch: **{fee:,}** {ICON_MONEY_BAG}"
            )
            await try_send(ctx, content=msg)

        except ValueError:
            await try_send(ctx, content=f"{ICON_WARNING} Vui lòng nhập một số tiền hợp lệ hoặc 'all'.")
        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'deposit' cho user {author_id}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi bạn gửi tiền.")

def setup(bot: commands.Bot):
    bot.add_cog(DepositCommandCog(bot))
