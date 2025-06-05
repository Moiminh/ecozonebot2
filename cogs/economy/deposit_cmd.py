# bot/cogs/economy/deposit_cmd.py
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

class DepositCommandCog(commands.Cog, name="Deposit Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"DepositCommandCog initialized.")

    @commands.command(name='deposit', aliases=['dep'])
    async def deposit(self, ctx: commands.Context, amount_str: str):
        author_id = ctx.author.id
        guild_id = ctx.guild.id 
        
        logger.debug(f"Lệnh 'deposit' được gọi bởi {ctx.author.name} ({author_id}) với amount_str='{amount_str}' tại guild '{ctx.guild.name}' ({guild_id}).")
        
        economy_data = load_economy_data()
        user_profile = get_or_create_global_user_profile(economy_data, author_id)
        
        original_global_balance = user_profile.get("global_balance", 0)
        original_server_bank_balance = get_server_bank_balance(user_profile, guild_id)
        
        amount_to_deposit = 0

        try:
            if amount_str.lower() == 'all':
                amount_to_deposit = original_global_balance
                logger.debug(f"User {author_id} chọn deposit 'all', số tiền: {amount_to_deposit}")
            else:
                amount_to_deposit = int(amount_str)
                logger.debug(f"User {author_id} chọn deposit số tiền: {amount_to_deposit}")

        except ValueError:
            logger.warning(f"Lỗi ValueError khi user {author_id} nhập amount_str='{amount_str}' cho lệnh 'deposit'.")
            await try_send(ctx, content=f"{ICON_WARNING} Vui lòng nhập một số tiền hợp lệ hoặc 'all'.")
            return 
            
        if amount_to_deposit <= 0:
            logger.warning(f"User {author_id} nhập số tiền deposit không hợp lệ (<=0): {amount_to_deposit}")
            await try_send(ctx, content=f"{ICON_ERROR} Số tiền gửi phải lớn hơn 0.")
            return 
            
        if original_global_balance < amount_to_deposit:
            logger.warning(f"User {author_id} không đủ tiền trong Ví Toàn Cục để deposit {amount_to_deposit}. Số dư ví: {original_global_balance}")
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ tiền trong Ví Toàn Cục. {ICON_MONEY_BAG} Ví của bạn: {original_global_balance:,} {CURRENCY_SYMBOL}")
            return 
        
        user_profile["global_balance"] = original_global_balance - amount_to_deposit
        new_server_bank_balance = original_server_bank_balance + amount_to_deposit
        set_server_bank_balance(user_profile, guild_id, new_server_bank_balance)
        
        save_economy_data(economy_data) 

        logger.info(f"Guild: {ctx.guild.name} ({guild_id}) - User: {ctx.author.display_name} ({author_id}) đã deposit {amount_to_deposit:,} {CURRENCY_SYMBOL} vào ngân hàng server. "
                    f"Ví Toàn Cục: {original_global_balance:,} -> {user_profile['global_balance']:,}. "
                    f"Ngân Hàng Server ({ctx.guild.name}): {original_server_bank_balance:,} -> {new_server_bank_balance:,}.")
        
        await try_send(ctx, content=f"{ICON_SUCCESS} Bạn đã gửi **{amount_to_deposit:,}** {CURRENCY_SYMBOL} từ Ví Toàn Cục vào Ngân Hàng tại server này.\n"
                                    f"{ICON_MONEY_BAG} Ví Toàn Cục: **{user_profile['global_balance']:,}** {CURRENCY_SYMBOL}\n"
                                    f"{ICON_BANK} Ngân Hàng Server ({ctx.guild.name}): **{new_server_bank_balance:,}** {CURRENCY_SYMBOL}")
        logger.debug(f"Lệnh 'deposit' cho {ctx.author.name} tại guild '{ctx.guild.name}' ({guild_id}) đã xử lý xong.")

def setup(bot: commands.Bot):
    bot.add_cog(DepositCommandCog(bot))
