import nextcord
from nextcord.ext import commands
import logging

from core.database import (
    load_economy_data,
    get_or_create_global_user_profile,
    get_or_create_user_server_data,
    save_economy_data
)
from core.utils import try_send, is_guild_owner_check
from core.config import CURRENCY_SYMBOL, COMMAND_PREFIX
from core.icons import ICON_SUCCESS, ICON_ERROR, ICON_WARNING, ICON_INFO

logger = logging.getLogger(__name__)

class RemoveMoneyCommandCog(commands.Cog, name="ServerAdmin RemoveMoney"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"ServerAdmin RemoveMoneyCommandCog initialized for Ecoworld Economy.")

    @commands.command(name='removemoney', aliases=['rm', 'ecotake', 'submoney'])
    @commands.check(is_guild_owner_check)
    async def remove_money(self, ctx: commands.Context, member: nextcord.Member, amount: int):
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server.")
            return

        target_user_id = member.id
        guild_id = ctx.guild.id

        logger.debug(f"Lệnh 'removemoney' (server admin) được gọi bởi {ctx.author.name} ({ctx.author.id}) đối với member {member.name} ({target_user_id}) với amount {amount} tại guild '{ctx.guild.name}' ({guild_id}).")
        
        if amount <= 0:
            logger.warning(f"Admin Server {ctx.author.id} cố gắng removemoney với số tiền không dương: {amount} cho user {target_user_id} tại guild {guild_id}.")
            await try_send(ctx, content=f"{ICON_ERROR} Số tiền trừ đi phải là số dương.")
            return
            
        economy_data = load_economy_data()
        global_profile = get_or_create_global_user_profile(economy_data, target_user_id)
        server_data = get_or_create_user_server_data(global_profile, guild_id)
        
        local_balance_dict = server_data.get("local_balance", {"earned": 0, "admin_added": 0})
        original_earned_amount = local_balance_dict.get("earned", 0)
        original_admin_added_amount = local_balance_dict.get("admin_added", 0)
        original_total_local_balance = original_earned_amount + original_admin_added_amount

        if original_total_local_balance == 0:
            await try_send(ctx, content=f"{ICON_INFO} {member.mention} không có tiền trong Ví Local tại server này để trừ.")
            return

        amount_to_remove = min(amount, original_total_local_balance)
        
        admin_money_deducted = min(original_admin_added_amount, amount_to_remove)
        earned_money_deducted = amount_to_remove - admin_money_deducted

        server_data["local_balance"]["admin_added"] -= admin_money_deducted
        server_data["local_balance"]["earned"] -= earned_money_deducted
        
        save_economy_data(economy_data)

        new_total_local_balance = server_data["local_balance"]["earned"] + server_data["local_balance"]["admin_added"]

        logger.info(f"SERVER ADMIN ACTION: {ctx.author.display_name} ({ctx.author.id}) tại guild '{ctx.guild.name}' ({guild_id}) đã dùng 'removemoney', trừ {amount_to_remove:,} {CURRENCY_SYMBOL} "
                    f"từ VÍ LOCAL của {member.display_name} ({target_user_id}). Yêu cầu gốc: {amount:,}. "
                    f"Số dư local cũ: {original_total_local_balance:,} -> mới: {new_total_local_balance:,}. "
                    f"(Trừ từ admin_added: {admin_money_deducted:,}, từ earned: {earned_money_deducted:,})")
        
        msg_content = f"{ICON_SUCCESS} Đã trừ **{amount_to_remove:,}** {CURRENCY_SYMBOL} từ Ví Local của {member.mention} tại server này. Số dư Ví Local mới của họ: **{new_total_local_balance:,}**"
        if amount > original_total_local_balance:
            msg_content = f"{ICON_WARNING} {member.mention} chỉ có {original_total_local_balance:,} {CURRENCY_SYMBOL} trong Ví Local. Đã trừ hết. " + msg_content
        
        await try_send(ctx, content=msg_content)
        
    @remove_money.error 
    async def remove_money_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CheckFailure):
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ dành cho Chủ Server (người tạo ra server).")
        elif isinstance(error, commands.MissingRequiredArgument):
            await try_send(ctx, content=f"{ICON_WARNING} Sử dụng đúng: `{COMMAND_PREFIX}{ctx.command.name} <@người_dùng> <số_tiền>`")
        elif isinstance(error, commands.BadArgument):
            await try_send(ctx, content=f"{ICON_ERROR} Đối số không hợp lệ. Hãy tag một người dùng và nhập một số tiền là số nguyên.")
        else:
            logger.error(f"Lỗi không xác định trong lệnh 'removemoney' bởi {ctx.author.name}:", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi thực hiện lệnh trừ tiền.")

def setup(bot: commands.Bot):
    bot.add_cog(RemoveMoneyCommandCog(bot))
