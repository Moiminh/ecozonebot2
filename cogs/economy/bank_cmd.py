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
        # Thêm thông tin guild vào log debug
        guild_name_for_log = ctx.guild.name if ctx.guild else "DM (Không áp dụng cho bank server)"
        guild_id_for_log = ctx.guild.id if ctx.guild else None # Lệnh bank server cần guild
        
        if not guild_id_for_log:
            logger.warning(f"Lệnh 'bank' được gọi trong DM bởi {ctx.author.name}. Lệnh này cần được gọi trong server.")
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server để xem ngân hàng của server đó.")
            return

        logger.debug(f"Lệnh 'bank' được gọi bởi {ctx.author.name} cho target {target_user.name} (ID: {target_user.id}) tại guild '{guild_name_for_log}' ({guild_id_for_log}).")

        try:
            economy_data = load_economy_data()
            target_user_profile = get_or_create_global_user_profile(economy_data, target_user.id)
            
            # Lấy số dư ngân hàng của người dùng tại server hiện tại
            server_bank_bal = get_server_bank_balance(target_user_profile, guild_id_for_log)
            
            await try_send(ctx, content=f"{ICON_BANK} Ngân hàng của {target_user.mention} tại server **{ctx.guild.name}**: **{server_bank_bal:,}** {CURRENCY_SYMBOL}.")
            
            # Log hành động xem bank (có thể dùng INFO nếu muốn nó vào player_actions.log)
            logger.debug(f"Hiển thị server_bank_balance cho {target_user.display_name} ({target_user.id}) tại guild {guild_id_for_log}: {server_bank_bal:,} {CURRENCY_SYMBOL}.")

            # Lưu lại economy_data nếu get_or_create_global_user_profile có thể đã tạo mới user
            # hoặc cập nhật các key mặc định (bao gồm cả việc tạo bank_accounts: {} nếu chưa có)
            save_economy_data(economy_data)

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'bank' cho user {target_user.name} ({target_user.id}) tại guild '{guild_name_for_log}': {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi không xác định khi xem số dư ngân hàng của {target_user.mention}.")

def setup(bot: commands.Bot):
    bot.add_cog(BankCommandCog(bot))
