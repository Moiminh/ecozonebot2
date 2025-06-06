import nextcord
from nextcord.ext import commands
import logging

from core.database import (
    load_economy_data,
    get_or_create_global_user_profile,
    get_or_create_user_server_data,
    get_server_bank_balance,
    set_server_bank_balance,
    save_economy_data
)
from core.utils import try_send
from core.config import CURRENCY_SYMBOL
from core.icons import ICON_BANK, ICON_MONEY_BAG, ICON_SUCCESS, ICON_ERROR, ICON_WARNING, ICON_INFO

logger = logging.getLogger(__name__)

class DepositCommandCog(commands.Cog, name="Deposit Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"DepositCommandCog initialized for Ecoworld Economy.")

    @commands.command(name='deposit', aliases=['dep'])
    async def deposit(self, ctx: commands.Context, amount_str: str):
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server.")
            return

        author_id = ctx.author.id
        guild_id = ctx.guild.id
        
        logger.debug(f"Lệnh 'deposit' được gọi bởi {ctx.author.name} ({author_id}) với amount_str='{amount_str}' tại guild '{ctx.guild.name}' ({guild_id}).")
        
        economy_data = load_economy_data()
        global_profile = get_or_create_global_user_profile(economy_data, author_id)
        server_data = get_or_create_user_server_data(global_profile, guild_id)
        
        local_balance_dict = server_data.get("local_balance", {"earned": 0, "admin_added": 0})
        earned_amount = local_balance_dict.get("earned", 0)
        admin_added_amount = local_balance_dict.get("admin_added", 0)
        total_local_balance = earned_amount + admin_added_amount

        original_server_bank_balance = get_server_bank_balance(global_profile, guild_id)
        
        amount_to_deposit = 0

        try:
            if amount_str.lower() == 'all':
                amount_to_deposit = total_local_balance
            else:
                amount_to_deposit = int(amount_str)
        except ValueError:
            await try_send(ctx, content=f"{ICON_WARNING} Vui lòng nhập một số tiền hợp lệ hoặc 'all'.")
            return
            
        if amount_to_deposit <= 0:
            if not (amount_str.lower() == 'all' and amount_to_deposit == 0):
                await try_send(ctx, content=f"{ICON_ERROR} Số tiền gửi phải lớn hơn 0.")
                return
            else:
                await try_send(ctx, content=f"{ICON_INFO} Ví Local của bạn đang rỗng, không có gì để gửi.")
                return

        if total_local_balance < amount_to_deposit:
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không đủ tiền trong Ví Local. {ICON_MONEY_BAG} Ví Local của bạn: {total_local_balance:,} {CURRENCY_SYMBOL}")
            return
        
        admin_money_to_deposit = min(admin_added_amount, amount_to_deposit)
        earned_money_to_deposit = amount_to_deposit - admin_money_to_deposit

        server_data["local_balance"]["admin_added"] -= admin_money_to_deposit
        server_data["local_balance"]["earned"] -= earned_money_to_deposit

        new_server_bank_balance = original_server_bank_balance + amount_to_deposit
        set_server_bank_balance(global_profile, guild_id, new_server_bank_balance)
        
        save_economy_data(economy_data)

        logger.info(f"Guild: {ctx.guild.name} ({guild_id}) - User: {ctx.author.display_name} ({author_id}) đã deposit {amount_to_deposit:,} {CURRENCY_SYMBOL} vào ngân hàng server. "
                    f"Nguồn tiền: {earned_money_to_deposit:,} từ 'earned', {admin_money_to_deposit:,} từ 'admin_added'. "
                    f"Ngân Hàng Server: {original_server_bank_balance:,} -> {new_server_bank_balance:,}.")
        
        await try_send(ctx, content=f"{ICON_SUCCESS} Bạn đã gửi **{amount_to_deposit:,}** {CURRENCY_SYMBOL} từ Ví Local vào Ngân Hàng tại server này.\n"
                                    f"{ICON_BANK} Ngân Hàng Server ({ctx.guild.name}): **{new_server_bank_balance:,}** {CURRENCY_SYMBOL}")
        
def setup(bot: commands.Bot):
    bot.add_cog(DepositCommandCog(bot))
