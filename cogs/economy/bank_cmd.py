import nextcord
from nextcord.ext import commands
import logging

from core.database import (
    load_economy_data,
    get_or_create_global_user_profile,
    get_server_bank_balance,
    save_economy_data
)
from core.utils import try_send
from core.config import CURRENCY_SYMBOL
from core.icons import ICON_BANK, ICON_ERROR, ICON_INFO

logger = logging.getLogger(__name__)

class BankCommandCog(commands.Cog, name="Bank Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"BankCommandCog initialized for Hybrid-Split-Economy.")

    @commands.command(name='bank')
    async def bank(self, ctx: commands.Context, user: nextcord.Member = None):
        target_user = user or ctx.author
        
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server để xem ngân hàng của server đó.")
            return

        author_id = target_user.id
        guild_id = ctx.guild.id
        
        logger.debug(f"Lệnh 'bank' được gọi cho {target_user.name} ({author_id}) tại guild '{ctx.guild.name}' ({guild_id}).")

        try:
            economy_data = load_economy_data()
            global_profile = get_or_create_global_user_profile(economy_data, author_id)
            
            server_bank_balance = get_server_bank_balance(global_profile, guild_id)
            
            await try_send(ctx, content=f"{ICON_BANK} Ngân hàng của {target_user.mention} tại server **{ctx.guild.name}**: **{server_bank_balance:,}** {CURRENCY_SYMBOL}.")
            
            logger.info(f"User {ctx.author.display_name} ({ctx.author.id}) đã xem ngân hàng của {target_user.display_name} ({target_user.id}) tại guild '{ctx.guild.name}' ({guild_id}). Số dư: {server_bank_balance:,} {CURRENCY_SYMBOL}.")
            
            save_economy_data(economy_data)

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'bank' cho user {target_user.name}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi không xác định khi xem số dư ngân hàng của {target_user.mention}.")

def setup(bot: commands.Bot):
    bot.add_cog(BankCommandCog(bot))
