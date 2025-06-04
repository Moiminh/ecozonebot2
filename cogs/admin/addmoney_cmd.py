# bot/cogs/admin/addmoney_cmd.py
import nextcord
from nextcord.ext import commands

from core.database import get_user_data, save_data
from core.utils import try_send, is_guild_owner_check
from core.config import CURRENCY_SYMBOL, COMMAND_PREFIX
from core.icons import ICON_SUCCESS, ICON_ERROR, ICON_WARNING

class AddMoneyCommandCog(commands.Cog, name="AddMoney Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='addmoney', aliases=['am', 'ecoadd'])
    @commands.check(is_guild_owner_check) 
    async def add_money(self, ctx: commands.Context, member: nextcord.Member, amount: int):
        """(Chỉ Chủ Server) Cộng tiền vào tài khoản của một thành viên."""
        if amount <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Số tiền cộng thêm phải là số dương.")
            return
        
        data = get_user_data(ctx.guild.id, member.id)
        user_data = data[str(ctx.guild.id)][str(member.id)]
        
        user_data["balance"] = user_data.get("balance", 0) + amount
        save_data(data)
        await try_send(ctx, content=f"{ICON_SUCCESS} Đã cộng **{amount:,}** {CURRENCY_SYMBOL} cho {member.mention}. Số dư mới của họ: **{user_data['balance']:,}**")

    @add_money.error 
    async def add_money_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CheckFailure): 
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ dành cho Chủ Server (người tạo ra server).")
        elif isinstance(error, commands.MissingRequiredArgument):
            # Lấy tên lệnh từ context để thông báo được chính xác
            command_name = ctx.command.name if ctx.command else "addmoney"
            await try_send(ctx, content=f"{ICON_WARNING} Sử dụng đúng: `{COMMAND_PREFIX}{command_name} <@người_dùng> <số_tiền>`")
        elif isinstance(error, commands.BadArgument): 
            await try_send(ctx, content=f"{ICON_ERROR} Đối số không hợp lệ. Hãy tag một người dùng và nhập một số tiền là số nguyên.")
        else:
            # In lỗi ra console để dev có thể xem xét
            command_name_for_log = ctx.command.name if ctx.command else "addmoney"
            print(f"Lỗi không xác định trong lệnh {command_name_for_log}: {error}")
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi thực hiện lệnh cộng tiền.")

def setup(bot: commands.Bot):
    bot.add_cog(AddMoneyCommandCog(bot))
