# bot/cogs/economy/deposit_cmd.py
import nextcord
from nextcord.ext import commands
import logging

from core.database import (
    load_economy_data,
    save_economy_data,
    get_or_create_global_user_profile,
    get_or_create_user_local_data
)
from core.utils import try_send
from core.config import DEPOSIT_FEE_PERCENTAGE, LAUNDER_EXCHANGE_RATE
# bot/cogs/economy/deposit_cmd.py
import nextcord
from nextcord.ext import commands
import logging

from core.database import get_or_create_global_user_profile, get_or_create_user_local_data
from core.utils import try_send, require_travel_check
from core.config import DEPOSIT_FEE_PERCENTAGE, LAUNDER_EXCHANGE_RATE
from core.icons import ICON_BANK_MAIN, ICON_MONEY_BAG, ICON_SUCCESS, ICON_ERROR, ICON_WARNING, ICON_INFO, ICON_ECOIN

logger = logging.getLogger(__name__)

class DepositCommandCog(commands.Cog, name="Deposit Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("DepositCommandCog (v5 - Refactored) initialized.")

    @commands.command(name='deposit', aliases=['dep'])
    @commands.guild_only()
    @require_travel_check
    async def deposit(self, ctx: commands.Context, amount_str: str):
        """Gửi 🪙Ecoin (Tiền Sạch) từ Ví Local vào Bank trung tâm (phí 5%)."""
        author_id = ctx.author.id
        
        try:
            economy_data = self.bot.economy_data
            global_profile = get_or_create_global_user_profile(economy_data, author_id)
            local_data = get_or_create_user_local_data(global_profile, ctx.guild.id)
            earned_balance = local_data["local_balance"].get("earned", 0)

            # --- Xử lý số tiền muốn gửi ---
            amount_to_deposit = 0
            if amount_str.lower() == 'all':
                amount_to_deposit = earned_balance
            else:
                try:
                    amount_to_deposit = int(amount_str)
                except ValueError:
                    await try_send(ctx, content=f"{ICON_WARNING} Vui lòng nhập một số tiền hợp lệ hoặc 'all'.")
                    return

            if amount_to_deposit <= 0:
                await try_send(ctx, content=f"{ICON_ERROR} Số tiền gửi phải lớn hơn 0.")
                return

            if earned_balance < amount_to_deposit:
                await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ {ICON_ECOIN} để gửi. Bạn có: **{earned_balance:,}**")
                return

            # --- Tính phí và kiểm tra lần cuối ---
            fee = int(amount_to_deposit * DEPOSIT_FEE_PERCENTAGE)
            total_cost = amount_to_deposit + fee

            if earned_balance < total_cost:
                await try_send(ctx, content=(
                    f"{ICON_ERROR} Không đủ {ICON_ECOIN} để trả phí!\n"
                    f"- Muốn gửi: `{amount_to_deposit:,}`\n"
                    f"- Phí ({DEPOSIT_FEE_PERCENTAGE*100}%): `{fee:,}`\n"
                    f"- **Tổng cộng cần: `{total_cost:,}`**\n"
                    f"- {ICON_ECOIN} Bạn chỉ có: **{earned_balance:,}**"))
                return

            # --- Thực hiện giao dịch ---
            local_data["local_balance"]["earned"] -= total_cost
            global_profile["bank_balance"] += amount_to_deposit
            
            # --- Logic giảm tội (wanted_level) ---
            original_wanted_level = global_profile.get("wanted_level", 0.0)
            reduction_amount = (amount_to_deposit / LAUNDER_EXCHANGE_RATE) * 0.5 
            new_wanted_level = max(0.0, original_wanted_level - reduction_amount)
            global_profile["wanted_level"] = new_wanted_level
            
            logger.info(f"User {author_id} đã deposit {amount_to_deposit} Ecoin. Wanted level: {original_wanted_level:.2f} -> {new_wanted_level:.2f}.")

            # --- Gửi thông báo thành công ---
            msg = (
                f"{ICON_SUCCESS} Giao dịch thành công!\n"
                f"- Đã gửi vào Bank: **{amount_to_deposit:,}** {ICON_BANK_MAIN}\n"
                f"- Phí giao dịch: **{fee:,}** {ICON_MONEY_BAG}\n"
                f"Số dư mới:\n"
                f"- {ICON_ECOIN} Ecoin (trong Ví Local): **{local_data['local_balance']['earned']:,}**\n"
                f"- {ICON_BANK_MAIN} Bank: **{global_profile['bank_balance']:,}**"
            )
            
            if new_wanted_level < original_wanted_level:
                msg += f"\n\n{ICON_INFO} Hành động tốt của bạn đã giúp **giảm Điểm Nghi ngờ**!"

            await try_send(ctx, content=msg)

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'deposit' cho user {author_id}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi bạn gửi tiền.")

def setup(bot: commands.Bot):
    bot.add_cog(DepositCommandCog(bot))
      await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi bạn gửi tiền.")

def setup(bot: commands.Bot):
    bot.add_cog(DepositCommandCog(bot))
