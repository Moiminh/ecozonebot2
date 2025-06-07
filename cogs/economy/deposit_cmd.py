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
from core.config import DEPOSIT_FEE_PERCENTAGE # Giả sử đã thêm vào config.py
from core.icons import (
    ICON_BANK, ICON_MONEY_BAG, ICON_SUCCESS, ICON_ERROR,
    ICON_WARNING, ICON_INFO, ICON_TIEN_SACH
)

logger = logging.getLogger(__name__)

class DepositCommandCog(commands.Cog, name="Deposit Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("DepositCommandCog (v2) initialized.")

    @commands.command(name='deposit', aliases=['dep'])
    async def deposit(self, ctx: commands.Context, amount_str: str):
        """Gửi Tiền Sạch (earned) từ Ví Local vào Bank để bảo toàn tài sản."""
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server.")
            return

        author_id = ctx.author.id
        guild_id = ctx.guild.id
        
        try:
            economy_data = load_economy_data()
            global_profile = get_or_create_global_user_profile(economy_data, author_id)
            local_data = get_or_create_user_local_data(global_profile, guild_id)
            
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

            # --- Kiểm tra điều kiện ---
            if amount_to_deposit <= 0:
                await try_send(ctx, content=f"{ICON_ERROR} Số tiền gửi phải lớn hơn 0.")
                return

            if earned_balance < amount_to_deposit:
                await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ 'Tiền Sạch' để gửi. {ICON_TIEN_SACH} Bạn có: **{earned_balance:,}**")
                return

            # --- Tính phí và kiểm tra lần cuối ---
            fee = int(amount_to_deposit * DEPOSIT_FEE_PERCENTAGE)
            total_cost = amount_to_deposit + fee

            if earned_balance < total_cost:
                await try_send(
                    ctx,
                    content=(
                        f"{ICON_ERROR} Không đủ 'Tiền Sạch' để trả phí!\n"
                        f"  - Muốn gửi: `{amount_to_deposit:,}`\n"
                        f"  - Phí ({DEPOSIT_FEE_PERCENTAGE*100}%): `{fee:,}`\n"
                        f"  - **Tổng cộng cần: `{total_cost:,}`**\n"
                        f"  - {ICON_TIEN_SACH} Bạn chỉ có: **{earned_balance:,}**"
                    )
                )
                return

            # --- Thực hiện giao dịch ---
            local_data["local_balance"]["earned"] -= total_cost
            global_profile["bank_balance"] += amount_to_deposit
            
            # Lưu lại dữ liệu
            save_economy_data(economy_data)

            logger.info(f"User {author_id} tại guild {guild_id} đã deposit {amount_to_deposit} earned vào Bank, phí {fee}.")

            # Gửi thông báo thành công
            new_bank_balance = global_profile["bank_balance"]
            new_earned_balance = local_data["local_balance"]["earned"]
            await try_send(
                ctx,
                content=(
                    f"{ICON_SUCCESS} Giao dịch thành công!\n"
                    f"  - Đã gửi vào Bank: **{amount_to_deposit:,}** {ICON_BANK}\n"
                    f"  - Phí giao dịch: **{fee:,}** {ICON_MONEY_BAG}\n"
                    f"Số dư mới:\n"
                    f"  - {ICON_TIEN_SACH} Tiền Sạch: **{new_earned_balance:,}**\n"
                    f"  - {ICON_BANK} Bank: **{new_bank_balance:,}**"
                )
            )

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'deposit' (v2) cho user {author_id}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi khi bạn gửi tiền.")

def setup(bot: commands.Bot):
    bot.add_cog(DepositCommandCog(bot))
