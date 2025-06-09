# bot/cogs/admin/removemoney_cmd.py
import nextcord
from nextcord.ext import commands
import logging
from core.checks import is_guild_owner_check
from core.config import COMMAND_PREFIX
from core.utils import try_send
from core.icons import ICON_SUCCESS, ICON_ERROR, ICON_WARNING, ICON_INFO, ICON_TIEN_LAU, ICON_TIEN_SACH

logger = logging.getLogger(__name__)

class RemoveMoneyCommandCog(commands.Cog, name="ServerAdmin RemoveMoney"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("RemoveMoneyCommandCog (SQLite Ready) initialized.")

    @commands.command(name='removemoney', aliases=['rm', 'ecotake', 'submoney'])
    @commands.check(is_guild_owner_check)
    async def remove_money(self, ctx: commands.Context, member: nextcord.Member, amount: int):
        """(Chủ Server) Trừ tiền từ Ví Local của một thành viên."""
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server.")
            return

        if amount <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Số tiền trừ đi phải là số dương.")
            return
            
        try:
            local_data = self.bot.db.get_or_create_user_local_data(member.id, ctx.guild.id)
            
            adadd_balance = local_data['local_balance_adadd']
            earned_balance = local_data['local_balance_earned']
            total_local_balance = adadd_balance + earned_balance

            if total_local_balance == 0:
                await try_send(ctx, content=f"{ICON_INFO} {member.mention} không có tiền trong Ví Local để trừ.")
                return

            amount_to_remove = min(amount, total_local_balance)
            
            adadd_deducted = min(adadd_balance, amount_to_remove)
            earned_deducted = amount_to_remove - adadd_deducted
            
            self.bot.db.update_balance(member.id, ctx.guild.id, 'local_balance_adadd', adadd_balance - adadd_deducted)
            self.bot.db.update_balance(member.id, ctx.guild.id, 'local_balance_earned', earned_balance - earned_deducted)
            
            logger.info(f"SERVER ADMIN ACTION: {ctx.author.id} tại guild {ctx.guild.id} đã trừ {amount_to_remove} từ Ví Local của user {member.id}.")
            
            new_total_local_balance = (adadd_balance - adadd_deducted) + (earned_balance - earned_deducted)
            
            await try_send(
                ctx,
                content=(
                    f"{ICON_SUCCESS} Đã trừ **{amount_to_remove:,}** từ Ví Local của {member.mention}.\n"
                    f"  (Trừ từ Tiền Lậu: {adadd_deducted:,} {ICON_TIEN_LAU} | Trừ từ Tiền Sạch: {earned_deducted:,} {ICON_TIEN_SACH})\n"
                    f"Số dư Ví Local mới của họ: **{new_total_local_balance:,}**"
                )
            )

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'removemoney' bởi {ctx.author.name}:", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi thực hiện lệnh trừ tiền.")
        
    @remove_money.error 
    async def remove_money_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CheckFailure):
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ dành cho Chủ Server (người tạo ra server).")
        elif isinstance(error, commands.MissingRequiredArgument):
            await try_send(ctx, content=f"{ICON_WARNING} Sử dụng đúng: `{COMMAND_PREFIX}{ctx.command.name} <@người_dùng> <số_tiền>`")
        elif isinstance(error, commands.BadArgument):
            await try_send(ctx, content=f"{ICON_ERROR} Đối số không hợp lệ. Hãy tag một người dùng và nhập một số tiền là số nguyên.")
        else:
            logger.error(f"Lỗi không xác định trong lệnh '{ctx.command.name}' bởi {ctx.author.name}:", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi thực hiện lệnh trừ tiền.")

def setup(bot: commands.Bot):
    bot.add_cog(RemoveMoneyCommandCog(bot))
