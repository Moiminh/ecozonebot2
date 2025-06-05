# bot/cogs/economy/bank_cmd.py
import nextcord
from nextcord.ext import commands
import logging

from core.database import (
    load_economy_data, 
    get_or_create_global_user_profile, 
    get_server_bank_balance,
    save_economy_data # Cần thiết nếu get_or_create_global_user_profile tạo user mới
)
from core.utils import try_send
from core.config import CURRENCY_SYMBOL
from core.icons import ICON_BANK, ICON_ERROR, ICON_INFO

logger = logging.getLogger(__name__)

class BankCommandCog(commands.Cog, name="Bank Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"BankCommandCog initialized.")

    @commands.command(name='bank')
    async def bank(self, ctx: commands.Context, user: nextcord.Member = None):
        target_user = user or ctx.author
        logger.debug(f"Lệnh 'bank' được gọi bởi {ctx.author.name} cho target {target_user.name} (ID: {target_user.id}) tại guild '{ctx.guild.name}' ({ctx.guild.id}).")

        try:
            economy_data = load_economy_data()
            target_user_profile = get_or_create_global_user_profile(economy_data, target_user.id)
            
            # Lấy số dư ngân hàng của người dùng tại server hiện tại
            # get_server_bank_balance sẽ trả về 0 nếu user chưa có tài khoản bank ở guild này
            # và user_profile["bank_accounts"] đã được đảm bảo là dict bởi get_or_create_global_user_profile
            server_bank_bal = get_server_bank_balance(target_user_profile, ctx.guild.id)
            
            await try_send(ctx, content=f"{ICON_BANK} Ngân hàng của {target_user.mention} tại server này: **{server_bank_bal:,}** {CURRENCY_SYMBOL}.")
            logger.debug(f"Hiển thị server_bank_balance cho {target_user.name} tại guild {ctx.guild.id}: {server_bank_bal} {CURRENCY_SYMBOL}.")

            # Lưu lại economy_data nếu get_or_create_global_user_profile đã tạo mới user
            # Để đảm bảo tính nhất quán, và vì get_or_create_global_user_profile có thể sửa `economy_data`
            # việc save lại là an toàn.
            save_economy_data(economy_data)

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'bank' cho user {target_user.name}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi không xác định khi xem số dư ngân hàng của {target_user.mention}.")

def setup(bot: commands.Bot):
    bot.add_cog(BankCommandCog(bot))
