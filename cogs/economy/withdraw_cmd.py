import nextcord
from nextcord.ext import commands
import logging

from core.database import (
    load_economy_data,
    get_or_create_global_user_profile,
    get_server_bank_balance,
    set_server_bank_balance,
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
        
        original_global_balance = global_profile.get("global_balance", 0)
        original_server_bank_balance = get_server_bank_balance(global_profile, guild_id)
        
        amount_to_withdraw = 0

        try:
            if amount_str.lower() == 'all':
                amount_to_withdraw = original_server_bank_balance
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
                await try_send(ctx, content=f"{ICON_INFO} Ngân hàng của bạn tại server này đang rỗng, không có gì để rút.")
                return
            
        if original_server_bank_balance < amount_to_withdraw:
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ tiền trong Ngân Hàng tại server này. {ICON_BANK} Ngân hàng của bạn: {original_server_bank_balance:,} {CURRENCY_SYMBOL}")
            return
        
        # This part of logic needs to be revisited based on the "Ecoworld Economic Rule Set"
        # For now, let's assume withdrawing from the per-server bank adds to the LOCAL EARNED balance, not global.
        # This makes more sense as it keeps server-generated money (from !addmoney) from becoming global easily.
        
        server_data = get_or_create_user_server_data(global_profile, guild_id)
        
        # Withdraw logic: from per-server bank to local earned wallet.
        set_server_bank_balance(global_profile, guild_id, original_server_bank_balance - amount_to_withdraw)
        server_data["local_balance"]["earned"] += amount_to_withdraw
        
        save_economy_data(economy_data) 

        logger.info(f"Guild: {ctx.guild.name} ({guild_id}) - User: {ctx.author.display_name} ({author_id}) đã withdraw {amount_to_withdraw:,} {CURRENCY_SYMBOL} từ ngân hàng server vào Ví Local (Earned).")
        
        await try_send(ctx, content=f"{ICON_SUCCESS} Bạn đã rút **{amount_to_withdraw:,}** {CURRENCY_SYMBOL} từ Ngân Hàng tại server này về Ví Local của bạn.")

def setup(bot: commands.Bot):
    bot.add_cog(WithdrawCommandCog(bot))
