# bot/cogs/economy/balance_cmd.py
import nextcord
from nextcord.ext import commands
import logging
from core.utils import try_send
from core.icons import ICON_PROFILE, ICON_ERROR, ICON_MONEY_BAG, ICON_TIEN_SACH, ICON_TIEN_LAU, ICON_BANK, ICON_TICKET

logger = logging.getLogger(__name__)

class BalanceCommandCog(commands.Cog, name="Balance Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info(f"BalanceCommandCog (SQLite Ready) initialized.")

    @commands.command(name='balance', aliases=['bal', 'cash', 'money', '$'])
    async def balance(self, ctx: commands.Context, user: nextcord.Member = None):
        """Xem số dư Ví Local và Ví Global (Bank) của bạn hoặc người khác."""
        target_user = user or ctx.author
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Vui lòng sử dụng lệnh này trong một server.")
            return

        try:
            global_profile = self.bot.db.get_or_create_global_user_profile(target_user.id)
            local_data = self.bot.db.get_or_create_user_local_data(target_user.id, ctx.guild.id)
            
            bank_balance = global_profile['bank_balance']
            earned_balance = local_data['local_balance_earned']
            adadd_balance = local_data['local_balance_adadd']
            total_local_balance = earned_balance + adadd_balance
            
            embed = nextcord.Embed(title=f"{ICON_PROFILE} Tổng Quan Tài Sản của {target_user.display_name}", color=nextcord.Color.gold())
            embed.set_thumbnail(url=target_user.display_avatar.url)
            embed.add_field(
                name=f"{ICON_MONEY_BAG} Ví Local (tại Server: {ctx.guild.name})",
                value=f"**Tổng cộng:** `{total_local_balance:,}`\n"
                      f"  {ICON_TIEN_SACH} Tiền Sạch (Earned): `{earned_balance:,}`\n"
                      f"  {ICON_TIEN_LAU} Tiền Lậu (Admin-add): `{adadd_balance:,}`",
                inline=False
            )
            embed.add_field(name=f"{ICON_BANK} Ví Global (Bank)", value=f"`{bank_balance:,}`", inline=True)
            await try_send(ctx, embed=embed)

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'balance' cho user {target_user.name}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi khi xem số dư của {target_user.mention}.")

def setup(bot: commands.Bot):
    bot.add_cog(BalanceCommandCog(bot))
