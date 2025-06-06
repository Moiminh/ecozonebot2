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
from core.icons import ICON_SUCCESS, ICON_ERROR, ICON_WARNING, ICON_INFO, ICON_BANK

logger = logging.getLogger(__name__)

class AddMoneyCommandCog(commands.Cog, name="ServerAdmin AddMoney"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"ServerAdmin AddMoneyCommandCog initialized for Ecoworld Economy.")

    @commands.command(name='addmoney', aliases=['am', 'ecoadd'])
    @commands.check(is_guild_owner_check)
    async def add_money(self, ctx: commands.Context, member: nextcord.Member, amount: int):
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server.")
            return

        target_user_id = member.id
        guild_id = ctx.guild.id
        
        logger.debug(f"Lệnh 'addmoney' (server admin) được gọi bởi {ctx.author.name} ({ctx.author.id}) cho member {member.name} ({target_user_id}) với amount {amount} tại guild '{ctx.guild.name}' ({guild_id}).")
        
        if amount <= 0:
            logger.warning(f"Admin Server {ctx.author.id} cố gắng addmoney với số tiền không dương: {amount} cho user {target_user_id} tại guild {guild_id}.")
            await try_send(ctx, content=f"{ICON_ERROR} Số tiền cộng thêm phải là số dương.")
            return
        
        economy_data = load_economy_data()
        global_profile = get_or_create_global_user_profile(economy_data, target_user_id)
        server_data = get_or_create_user_server_data(global_profile, guild_id)
        
        original_admin_added = server_data["local_balance"].get("admin_added", 0)
        
        server_data["local_balance"]["admin_added"] = original_admin_added + amount

        save_economy_data(economy_data)

        logger.info(f"SERVER ADMIN ACTION: {ctx.author.display_name} ({ctx.author.id}) tại guild '{ctx.guild.name}' ({guild_id}) đã dùng 'addmoney', cộng {amount:,} {CURRENCY_SYMBOL} "
                    f"vào VÍ LOCAL (ADMIN-ADDED) của {member.display_name} ({target_user_id}). "
                    f"Số dư admin-added: {original_admin_added:,} -> {server_data['local_balance']['admin_added']:,}.")
        
        await try_send(ctx, content=f"{ICON_SUCCESS} Đã cộng **{amount:,}** {CURRENCY_SYMBOL} vào quỹ **Admin-add** trong Ví Local của {member.mention} tại server này.")
        
    @add_money.error 
    async def add_money_error(self, ctx: commands.Context, error):
        command_name_for_log = ctx.command.name if ctx.command else "addmoney"
        if isinstance(error, commands.CheckFailure): 
            logger.warning(f"CheckFailure cho lệnh '{command_name_for_log}' bởi user {ctx.author.id}: {error}")
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ dành cho Chủ Server (người tạo ra server).")
        elif isinstance(error, commands.MissingRequiredArgument):
            await try_send(ctx, content=f"{ICON_WARNING} Sử dụng đúng: `{COMMAND_PREFIX}{command_name_for_log} <@người_dùng> <số_tiền>`")
        elif isinstance(error, commands.BadArgument): 
            await try_send(ctx, content=f"{ICON_ERROR} Đối số không hợp lệ. Hãy tag một người dùng và nhập một số tiền là số nguyên.")
        else:
            logger.error(f"Lỗi không xác định trong lệnh '{command_name_for_log}' bởi {ctx.author.name}:", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi thực hiện lệnh cộng tiền.")

def setup(bot: commands.Bot):
    bot.add_cog(AddMoneyCommandCog(bot))
