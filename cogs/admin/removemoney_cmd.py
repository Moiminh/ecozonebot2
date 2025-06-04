# bot/cogs/admin/removemoney_cmd.py
import nextcord
from nextcord.ext import commands
import logging # <<< THÊM IMPORT NÀY

from core.database import get_user_data, save_data
from core.utils import try_send, is_guild_owner_check
from core.config import CURRENCY_SYMBOL, COMMAND_PREFIX
from core.icons import ICON_SUCCESS, ICON_ERROR, ICON_WARNING, ICON_INFO # Đảm bảo các icon này có trong core/icons.py

logger = logging.getLogger(__name__) # <<< LẤY LOGGER CHO MODULE NÀY

class RemoveMoneyCommandCog(commands.Cog, name="RemoveMoney Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"RemoveMoneyCommandCog initialized.")

    @commands.command(name='removemoney', aliases=['rm', 'ecotake', 'submoney'])
    @commands.check(is_guild_owner_check) 
    async def remove_money(self, ctx: commands.Context, member: nextcord.Member, amount: int):
        """(Chỉ Chủ Server) Trừ tiền từ tài khoản của một thành viên."""
        logger.debug(f"Lệnh 'removemoney' được gọi bởi {ctx.author.name} (ID: {ctx.author.id}) đối với member {member.name} (ID: {member.id}) với amount {amount} tại guild {ctx.guild.id}.")
        
        if amount <= 0:
            logger.warning(f"Admin {ctx.author.id} cố gắng removemoney với số tiền không hợp lệ (<=0): {amount} cho user {member.id}")
            await try_send(ctx, content=f"{ICON_ERROR} Số tiền trừ đi phải là số dương.")
            return

        data = get_user_data(ctx.guild.id, member.id)
        user_data = data[str(ctx.guild.id)][str(member.id)]
        original_balance = user_data.get("balance", 0)
        
        amount_removed = min(amount, original_balance) # Không trừ quá số tiền hiện có
        user_data["balance"] -= amount_removed # user_data["balance"] = original_balance - amount_removed
        
        save_data(data)

        # Ghi log hành động admin
        logger.info(f"ADMIN ACTION: {ctx.author.display_name} ({ctx.author.id}) đã dùng 'removemoney', trừ {amount_removed:,} {CURRENCY_SYMBOL} "
                    f"từ {member.display_name} ({member.id}). Yêu cầu gốc: {amount:,}. "
                    f"Số dư của {member.display_name}: {original_balance:,} -> {user_data['balance']:,}.")
        
        msg_content = f"{ICON_SUCCESS} Đã trừ **{amount_removed:,}** {CURRENCY_SYMBOL} từ {member.mention}. Số dư mới của họ: **{user_data['balance']:,}**"
        if amount > original_balance and original_balance > 0: 
            logger.info(f"Admin {ctx.author.id} yêu cầu trừ {amount} từ {member.id} nhưng user chỉ có {original_balance}. Đã trừ {amount_removed}.")
            msg_content = f"{ICON_WARNING} {member.mention} không đủ tiền như yêu cầu ({amount:,}). " + msg_content
        elif original_balance == 0 and amount > 0: 
            logger.info(f"Admin {ctx.author.id} yêu cầu trừ {amount} từ {member.id} nhưng user có 0 tiền.")
            msg_content = f"{ICON_INFO} {member.mention} không có tiền để trừ."
        
        await try_send(ctx, content=msg_content)
        logger.debug(f"Lệnh 'removemoney' cho {member.name} bởi {ctx.author.name} đã xử lý xong.")
        
    @remove_money.error 
    async def remove_money_error(self, ctx: commands.Context, error):
        command_name_for_log = ctx.command.name if ctx.command else "removemoney"
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
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi thực hiện lệnh trừ tiền.")

def setup(bot: commands.Bot):
    bot.add_cog(RemoveMoneyCommandCog(bot))
