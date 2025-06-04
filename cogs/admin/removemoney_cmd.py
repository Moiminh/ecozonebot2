# bot/cogs/admin/removemoney_cmd.py
import nextcord
from nextcord.ext import commands

from core.database import get_user_data, save_data
from core.utils import try_send, is_guild_owner_check
from core.config import CURRENCY_SYMBOL, COMMAND_PREFIX
from core.icons import ICON_SUCCESS, ICON_ERROR, ICON_WARNING, ICON_INFO # Đảm bảo các icon này có trong core/icons.py

class RemoveMoneyCommandCog(commands.Cog, name="RemoveMoney Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='removemoney', aliases=['rm', 'ecotake', 'submoney'])
    @commands.check(is_guild_owner_check) 
    async def remove_money(self, ctx: commands.Context, member: nextcord.Member, amount: int):
        """(Chỉ Chủ Server) Trừ tiền từ tài khoản của một thành viên."""
        if amount <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Số tiền trừ đi phải là số dương.")
            return

        data = get_user_data(ctx.guild.id, member.id)
        user_data = data[str(ctx.guild.id)][str(member.id)]
        original_balance = user_data.get("balance", 0)
        
        amount_removed = min(amount, original_balance) 
        user_data["balance"] -= amount_removed
        save_data(data)
        
        msg_content = f"{ICON_SUCCESS} Đã trừ **{amount_removed:,}** {CURRENCY_SYMBOL} từ {member.mention}. Số dư mới của họ: **{user_data['balance']:,}**"
        if amount > original_balance and original_balance > 0: 
            msg_content = f"{ICON_WARNING} {member.mention} không đủ tiền như yêu cầu ({amount:,}). " + msg_content
        elif original_balance == 0 and amount > 0: 
            msg_content = f"{ICON_INFO} {member.mention} không có tiền để trừ."
        await try_send(ctx, content=msg_content)
        
    @remove_money.error 
    async def remove_money_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CheckFailure):
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ dành cho Chủ Server (người tạo ra server).")
        elif isinstance(error, commands.MissingRequiredArgument):
            command_name = ctx.command.name if ctx.command else "removemoney"
            await try_send(ctx, content=f"{ICON_WARNING} Sử dụng đúng: `{COMMAND_PREFIX}{command_name} <@người_dùng> <số_tiền>`")
        elif isinstance(error, commands.BadArgument):
            await try_send(ctx, content=f"{ICON_ERROR} Đối số không hợp lệ. Hãy tag một người dùng và nhập một số tiền là số nguyên.")
        else:
            command_name_for_log = ctx.command.name if ctx.command else "removemoney"
            print(f"Lỗi không xác định trong lệnh {command_name_for_log}: {error}")
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi thực hiện lệnh trừ tiền.")

def setup(bot: commands.Bot):
    bot.add_cog(RemoveMoneyCommandCog(bot))
