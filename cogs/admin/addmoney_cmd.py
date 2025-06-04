# bot/cogs/admin/addmoney_cmd.py
import nextcord
from nextcord.ext import commands
import logging # <<< THÊM IMPORT NÀY

from core.database import get_user_data, save_data
from core.utils import try_send, is_guild_owner_check
from core.config import CURRENCY_SYMBOL, COMMAND_PREFIX
from core.icons import ICON_SUCCESS, ICON_ERROR, ICON_WARNING, ICON_INFO # Đảm bảo có ICON_INFO

logger = logging.getLogger(__name__) # <<< LẤY LOGGER CHO MODULE NÀY

class AddMoneyCommandCog(commands.Cog, name="AddMoney Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"AddMoneyCommandCog initialized.")

    @commands.command(name='addmoney', aliases=['am', 'ecoadd'])
    @commands.check(is_guild_owner_check) 
    async def add_money(self, ctx: commands.Context, member: nextcord.Member, amount: int):
        """(Chỉ Chủ Server) Cộng tiền vào tài khoản của một thành viên."""
        logger.debug(f"Lệnh 'addmoney' được gọi bởi {ctx.author.name} (ID: {ctx.author.id}) cho member {member.name} (ID: {member.id}) với amount {amount} tại guild {ctx.guild.id}.")
        
        if amount <= 0:
            logger.warning(f"Admin {ctx.author.id} cố gắng addmoney với số tiền không hợp lệ (<=0): {amount} cho user {member.id}")
            await try_send(ctx, content=f"{ICON_ERROR} Số tiền cộng thêm phải là số dương.")
            return
        
        data = get_user_data(ctx.guild.id, member.id)
        user_data = data[str(ctx.guild.id)][str(member.id)]
        original_balance = user_data.get("balance", 0)
        
        user_data["balance"] = original_balance + amount
        save_data(data)

        # Ghi log hành động admin (sẽ vào cả general log và player_actions.log do là INFO từ cogs.*)
        logger.info(f"ADMIN ACTION: {ctx.author.display_name} ({ctx.author.id}) đã dùng 'addmoney', cộng {amount:,} {CURRENCY_SYMBOL} "
                    f"cho {member.display_name} ({member.id}). "
                    f"Số dư của {member.display_name}: {original_balance:,} -> {user_data['balance']:,}.")
        
        await try_send(ctx, content=f"{ICON_SUCCESS} Đã cộng **{amount:,}** {CURRENCY_SYMBOL} cho {member.mention}. Số dư mới của họ: **{user_data['balance']:,}**")
        logger.debug(f"Lệnh 'addmoney' cho {member.name} bởi {ctx.author.name} đã xử lý xong.")

    @add_money.error 
    async def add_money_error(self, ctx: commands.Context, error):
        command_name_for_log = ctx.command.name if ctx.command else "addmoney"
        if isinstance(error, commands.CheckFailure): 
            logger.warning(f"CheckFailure cho lệnh '{command_name_for_log}' bởi user {ctx.author.id}: {error}")
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ dành cho Chủ Server (người tạo ra server).")
        elif isinstance(error, commands.MissingRequiredArgument):
            logger.warning(f"MissingRequiredArgument cho lệnh '{command_name_for_log}' bởi user {ctx.author.id}: {error.param.name}")
            await try_send(ctx, content=f"{ICON_WARNING} Sử dụng đúng: `{COMMAND_PREFIX}{command_name_for_log} <@người_dùng> <số_tiền>`")
        elif isinstance(error, commands.BadArgument): 
            logger.warning(f"BadArgument cho lệnh '{command_name_for_log}' bởi user {ctx.author.id}: {error}")
            await try_send(ctx, content=f"{ICON_ERROR} Đối số không hợp lệ. Hãy tag một người dùng và nhập một số tiền là số nguyên.")
        else:
            logger.error(f"Lỗi không xác định trong lệnh '{command_name_for_log}' bởi user {ctx.author.id}: {error}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi thực hiện lệnh cộng tiền.")

def setup(bot: commands.Bot):
    bot.add_cog(AddMoneyCommandCog(bot))
