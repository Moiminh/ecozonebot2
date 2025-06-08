# bot/cogs/economy/withdraw_cmd.py
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
from core.icons import (
    ICON_BANK, ICON_MONEY_BAG, ICON_SUCCESS, ICON_ERROR,
    ICON_WARNING, ICON_INFO, ICON_TIEN_SACH
)
from core.travel_manager import handle_travel_event

logger = logging.getLogger(__name__)

class WithdrawCommandCog(commands.Cog, name="Withdraw Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("WithdrawCommandCog (v3) initialized.")

    @commands.command(name='withdraw', aliases=['wd'])
    async def withdraw(self, ctx: commands.Context, amount_str: str):
        """Rút tiền từ Bank về Ví Local (sẽ được cộng vào Tiền Sạch)."""
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server.")
            return

        author_id = ctx.author.id
        guild_id = ctx.guild.id
        
        try:
            economy_data = load_economy_data()
            global_profile = get_or_create_global_user_profile(economy_data, author_id)

            # --- Kiểm tra Last Active Guild ---
            if global_profile.get("last_active_guild_id") != guild_id:
                await handle_travel_event(ctx, self.bot)
                logger.info(f"User {author_id} has 'traveled' to guild {guild_id}.")
            global_profile["last_active_guild_id"] = guild_id

            local_data = get_or_create_user_local_data(global_profile, guild_id)
            bank_balance = global_profile.get("bank_balance", 0)
            
            # --- Xử lý số tiền muốn rút ---
            amount_to_withdraw = 0
            if amount_str.lower() == 'all':
                amount_to_withdraw = bank_balance
            else:
                try:
                    amount_to_withdraw = int(amount_str)
                except ValueError:
                    await try_send(ctx, content=f"{ICON_WARNING} Vui lòng nhập một số tiền hợp lệ hoặc 'all'.")
                    return

            # --- Kiểm tra điều kiện ---
            if amount_to_withdraw <= 0:
                await try_send(ctx, content=f"{ICON_ERROR} Số tiền rút phải lớn hơn 0.")
                return

            if bank_balance < amount_to_withdraw:
                await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ tiền trong Bank. {ICON_BANK} Bank của bạn có: **{bank_balance:,}**")
                return

            # --- Thực hiện giao dịch ---
            global_profile["bank_balance"] -= amount_to_withdraw
            local_data["local_balance"]["earned"] += amount_to_withdraw
            
            save_economy_data(economy_data)

            logger.info(f"User {author_id} tại guild {guild_id} đã withdraw {amount_to_withdraw} từ Bank về Ví Local (earned).")

            # Gửi thông báo thành công
            new_bank_balance = global_profile["bank_balance"]
            new_earned_balance = local_data["local_balance"]["earned"]
            await try_send(
                ctx,
                content=(
                    f"{ICON_SUCCESS} Rút tiền thành công (miễn phí)!\n"
                    f"  - Đã rút từ Bank: **{amount_to_withdraw:,}** {ICON_BANK}\n"
                    f"Số dư mới:\n"
                    f"  - {ICON_BANK} Bank: **{new_bank_balance:,}**\n"
                    f"  - {ICON_TIEN_SACH} Tiền Sạch (trong Ví Local): **{new_earned_balance:,}**"
                )
            )

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'withdraw' (v3) cho user {author_id}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi khi bạn rút tiền.")

def setup(bot: commands.Bot):
    bot.add_cog(WithdrawCommandCog(bot))
