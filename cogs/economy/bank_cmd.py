# bot/cogs/economy/bank_cmd.py
import nextcord
from nextcord.ext import commands
import logging

# [SỬA] Import các hàm cần thiết
from core.database import get_or_create_global_user_profile
from core.utils import try_send, format_large_number
from core.icons import ICON_BANK, ICON_ERROR, ICON_INFO

logger = logging.getLogger(__name__)

class BankCommandCog(commands.Cog, name="Bank Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("BankCommandCog (Refactored) initialized.")

    @commands.command(name='bank')
    async def bank(self, ctx: commands.Context, user: nextcord.Member = None):
        """Xem số dư Bank trung tâm của bạn hoặc người khác."""
        target_user = user or ctx.author
        
        logger.debug(f"Lệnh 'bank' được gọi cho {target_user.name} ({target_user.id}).")

        try:
            # [SỬA] Sử dụng cache của bot
            economy_data = self.bot.economy_data
            global_profile = get_or_create_global_user_profile(economy_data, target_user.id)
            
            bank_balance = global_profile.get("bank_balance", 0)
            
            await try_send(ctx, content=f"{ICON_BANK} Bank trung tâm của {target_user.mention}: **{format_large_number(bank_balance)}**")
            
            # [XÓA] Không cần save thủ công
            # save_economy_data(economy_data)

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'bank' cho user {target_user.name}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi không xác định khi xem số dư bank của {target_user.mention}.")

def setup(bot: commands.Bot):
    bot.add_cog(BankCommandCog(bot))
