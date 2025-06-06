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
from core.icons import ICON_BANK, ICON_MONEY_BAG, ICON_SUCCESS, ICON_ERROR, ICON_WARNING, ICON_INFO

logger = logging.getLogger(__name__)

class WithdrawCommandCog(commands.Cog, name="Withdraw Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"WithdrawCommandCog initialized for Ecoworld Economy.")

    @commands.command(name='withdraw', aliases=['wd'])
    async def withdraw(self, ctx: commands.Context, amount_str: str):
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server.")
            return

        author_id = ctx.author.id
        guild_id = ctx.guild.id
        
        logger.debug(f"Lệnh 'withdraw' được gọi bởi {ctx.author.name} ({author_id}) với amount_str='{amount_str}' tại guild '{ctx.guild.name}' ({guild_id}).")
        
        economy_data = load_economy_data()
        global_profile = get_or_create_global_user_profile(economy_data, author_id)
        server_data = get_or_create_user_server_data(global_profile, guild_id)

        local_balance_dict = server_data.get("local_balance", {"earned": 0, "admin_added": 0})
        total_local_balance = local_balance_dict.get("earned", 0) + local_balance_dict.get("admin_added", 0)

        original_global_balance = global_profile.get("global_balance", 0)
        
        amount_to_withdraw = 0

        try:
            if amount_str.lower() == 'all':
                amount_to_withdraw = total_local_balance
            else:
                amount_to_withdraw = int(amount_str)
        except ValueError:
            await try_send(ctx, content=f"{ICON_WARNING} Vui lòng nhập một số tiền hợp lệ hoặc 'all'.")
            return
            
        if amount_to_withdraw <= 0:
            if not (amount_str.lower() == 'all' and amount_to_withdraw == 0):
                await try_send(ctx, content=f"{ICON_ERROR} Số tiền rút phải lớn hơn 0.")
                return
            else:
                await try_send(ctx, content=f"{ICON_INFO} Ví Local của bạn tại server này đang rỗng, không có gì để rút.")
                return
            
        if total_local_balance < amount_to_withdraw:
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ tiền trong Ví Local tại server này. {ICON_MONEY_BAG} Ví Local của bạn: {total_local_balance:,} {CURRENCY_SYMBOL}")
            return
        
        admin_money_to_withdraw = min(local_balance_dict.get("admin_added", 0), amount_to_withdraw)
        earned_money_to_withdraw = amount_to_withdraw - admin_money_to_withdraw

        local_balance_dict["admin_added"] -= admin_money_to_withdraw
        local_balance_dict["earned"] -= earned_money_to_withdraw
        
        global_profile["global_balance"] = original_global_balance + earned_money_to_withdraw
        
        save_economy_data(economy_data) 

        logger.info(f"Guild: {ctx.guild.name} ({guild_id}) - User: {ctx.author.display_name} ({author_id}) đã rút {amount_to_withdraw:,} {CURRENCY_SYMBOL} từ Ví Local. "
                    f"Trong đó, {earned_money_to_withdraw:,} được chuyển thành GOL. {admin_money_to_withdraw:,} tiền admin-added bị 'đốt cháy'. "
                    f"Ví Global: {original_global_balance:,} -> {global_profile['global_balance']:,}.")
        
        await try_send(ctx, content=f"{ICON_SUCCESS} Bạn đã rút **{amount_to_withdraw:,}** {CURRENCY_SYMBOL} từ Ví Local tại server này.\n"
                                    f"Trong đó, **{earned_money_to_withdraw:,}** {CURRENCY_SYMBOL} đã được chuyển đổi và cộng vào Ví Global (GOL) của bạn!")
