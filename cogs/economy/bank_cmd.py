# bot/cogs/economy/bank_cmd.py
import nextcord
from nextcord.ext import commands
import logging
from core.utils import try_send, format_large_number
from core.icons import ICON_BANK, ICON_ERROR

logger = logging.getLogger(__name__)

class BankCommandCog(commands.Cog, name="Bank Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("BankCommandCog (SQLite Ready) initialized.")

    @commands.command(name='bank')
    async def bank_balance(self, ctx: commands.Context, user: nextcord.Member = None):
        """Xem số dư trong ngân hàng (bank) của bạn hoặc người khác."""
        target_user = user or ctx.author
        
        try:
            global_profile = self.bot.db.get_or_create_global_user_profile(target_user.id)
            bank_balance = global_profile['bank_balance']
            
            embed = nextcord.Embed(
                title=f"{ICON_BANK} Số Dư Ngân Hàng của {target_user.display_name}",
                description=f"**Số dư hiện tại:** `{format_large_number(bank_balance)}`",
                color=nextcord.Color.blue()
            )
            embed.set_thumbnail(url=target_user.display_avatar.url)
            await try_send(ctx, embed=embed)
            
        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'bank' cho user {target_user.name}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi khi xem số dư ngân hàng.")

def setup(bot: commands.Bot):
    bot.add_cog(BankCommandCog(bot))
