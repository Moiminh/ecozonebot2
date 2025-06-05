# bot/cogs/economy/withdraw_cmd.py
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
        logger.debug(f"WithdrawCommandCog initialized.")

    @commands.command(name='withdraw', aliases=['wd'])
    async def withdraw(self, ctx: commands.Context, amount_str: str):
        """Rút tiền từ Ngân Hàng của bạn tại server này về Ví Toàn Cục."""
        author_id = ctx.author.id
        if not ctx.guild:
            logger.warning(f"Lệnh 'withdraw' được gọi trong DM bởi {ctx.author.name}. Lệnh này cần được gọi trong server.")
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server để rút tiền từ ngân hàng của server đó.")
            return
        guild_id = ctx.guild.id

        logger.debug(f"Lệnh 'withdraw' được gọi bởi {ctx.author.name} ({author_id}) với amount_str='{amount_str}' tại guild '{ctx.guild.name}' ({guild_id}).")
        
        economy_data = load_economy_data()
        user_profile = get_or_create_global_user_profile(economy_data, author_id)
        
        original_global_balance = user_profile.get("global_balance", 0)
        original_server_bank_balance = get_server_bank_balance(user_profile, guild_id)
        
        amount_to_withdraw = 0

        try:
            if amount_str.lower() == 'all':
                amount_to_withdraw = original_server_bank_balance
                logger.debug(f"User {author_id} chọn withdraw 'all' từ ngân hàng server, số tiền: {amount_to_withdraw}")
            else:
                amount_to_withdraw = int(amount_str)
                logger.debug(f"User {author_id} chọn withdraw số tiền: {amount_to_withdraw} từ ngân hàng server")

        except ValueError:
            logger.warning(f"Lỗi ValueError khi user {author_id} nhập amount_str='{amount_str}' cho lệnh 'withdraw'.")
            await try_send(ctx, content=f"{ICON_WARNING} Vui lòng nhập một số tiền hợp lệ hoặc 'all'.")
            return
            
        if amount_to_withdraw <= 0:
            if not (amount_str.lower() == 'all' and amount_to_withdraw == 0):
                logger.warning(f"User {author_id} nhập số tiền withdraw không hợp lệ (<=0): {amount_to_withdraw}")
                await try_send(ctx, content=f"{ICON_ERROR} Số tiền rút phải lớn hơn 0.")
                return
            elif amount_str.lower() == 'all' and amount_to_withdraw == 0:
                 await try_send(ctx, content=f"{ICON_INFO} Ngân hàng của bạn tại server này đang rỗng, không có gì để rút.")
                 return
            
        if original_server_bank_balance < amount_to_withdraw:
            logger.warning(f"User {author_id} không đủ tiền trong Ngân Hàng Server ({ctx.guild.name}) để withdraw {amount_to_withdraw}. Số dư ngân hàng server: {original_server_bank_balance}")
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ tiền trong Ngân Hàng tại server này. {ICON_BANK} Ngân hàng của bạn: {original_server_bank_balance:,} {CURRENCY_SYMBOL}")
            return
        
        user_profile["global_balance"] = original_global_balance + amount_to_withdraw
        new_server_bank_balance = original_server_bank_balance - amount_to_withdraw
        set_server_bank_balance(user_profile, guild_id, new_server_bank_balance)
        
        save_economy_data(economy_data) 

        logger.info(f"Guild: {ctx.guild.name} ({guild_id}) - User: {ctx.author.display_name} ({author_id}) đã withdraw {amount_to_withdraw:,} {CURRENCY_SYMBOL} từ ngân hàng server. "
                    f"Ví Toàn Cục: {original_global_balance:,} -> {user_profile['global_balance']:,}. "
                    f"Ngân Hàng Server ({ctx.guild.name}): {original_server_bank_balance:,} -> {new_server_bank_balance:,}.")
        
        await try_send(ctx, content=f"{ICON_SUCCESS} Bạn đã rút **{amount_to_withdraw:,}** {CURRENCY_SYMBOL} từ Ngân Hàng tại server này về Ví Toàn Cục.\n"
                                    f"{ICON_MONEY_BAG} Ví Toàn Cục: **{user_profile['global_balance']:,}** {CURRENCY_SYMBOL}\n"
                                    f"{ICON_BANK} Ngân Hàng Server ({ctx.guild.name}): **{new_server_bank_balance:,}** {CURRENCY_SYMBOL}")
        logger.debug(f"Lệnh 'withdraw' cho {ctx.author.name} tại guild '{ctx.guild.name}' ({guild_id}) đã xử lý xong.")

def setup(bot: commands.Bot):
    bot.add_cog(WithdrawCommandCog(bot))
