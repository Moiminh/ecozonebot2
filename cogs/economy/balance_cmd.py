import nextcord
from nextcord.ext import commands
import logging

from core.database import (
    load_economy_data,
    get_or_create_global_user_profile,
    get_or_create_user_server_data,
    save_economy_data
)
from core.utils import try_send
from core.config import CURRENCY_SYMBOL
from core.icons import ICON_PROFILE, ICON_ERROR, ICON_INFO, ICON_MONEY_BAG, ICON_BANK

logger = logging.getLogger(__name__)

class BalanceCommandCog(commands.Cog, name="Balance Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"BalanceCommandCog initialized for Hybrid-Split-Economy.")

    @commands.command(name='balance', aliases=['bal', 'cash', 'money', '$'])
    async def balance(self, ctx: commands.Context, user: nextcord.Member = None):
        target_user = user or ctx.author
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Vui lòng sử dụng lệnh này trong một server để xem các loại ví.")
            return

        author_id = target_user.id
        guild_id = ctx.guild.id

        logger.debug(f"Lệnh 'balance' được gọi cho {target_user.name} ({author_id}) tại guild '{ctx.guild.name}' ({guild_id}).")

        try:
            economy_data = load_economy_data()
            global_profile = get_or_create_global_user_profile(economy_data, author_id)
            server_profile = get_or_create_user_server_data(global_profile, guild_id)

            global_balance = global_profile.get("global_balance", 0)
            local_balance_dict = server_profile.get("local_balance", {})
            earned_amount = local_balance_dict.get("earned", 0)
            admin_added_amount = local_balance_dict.get("admin_added", 0)
            total_local_balance = earned_amount + admin_added_amount

            embed = nextcord.Embed(
                title=f"{ICON_PROFILE} Tổng Quan Tài Sản của {target_user.display_name}",
                color=nextcord.Color.gold()
            )
            embed.set_thumbnail(url=target_user.display_avatar.url)
            
            embed.add_field(
                name=f"{ICON_MONEY_BAG} Ví Local (tại Server: {ctx.guild.name})",
                value=f"**Tổng cộng:** `{total_local_balance:,}` {CURRENCY_SYMBOL}\n"
                      f"  (Tiền kiếm được: `{earned_amount:,}`)\n"
                      f"  (Tiền từ Admin: `{admin_added_amount:,}`)",
                inline=False
            )
            embed.add_field(
                name=f"💎 Ví Global (GOL)",
                value=f"`{global_balance:,}` {CURRENCY_SYMBOL}",
                inline=False
            )

            await try_send(ctx, embed=embed)
            
            logger.info(f"User {ctx.author.display_name} ({ctx.author.id}) đã xem tài sản của {target_user.display_name} ({target_user.id}) tại guild '{ctx.guild.name}' ({guild_id}).")

            save_economy_data(economy_data)

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'balance' cho user {target_user.name}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi không xác định khi xem số dư của {target_user.mention}.")

def setup(bot: commands.Bot):
    bot.add_cog(BalanceCommandCog(bot))
