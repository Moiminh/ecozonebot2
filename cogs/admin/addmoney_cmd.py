# bot/cogs/admin/addmoney_cmd.py
import nextcord
from nextcord.ext import commands
import logging

from core.database import get_or_create_global_user_profile, get_or_create_user_local_data
from core.utils import try_send, is_guild_owner_check
from core.config import COMMAND_PREFIX
from core.icons import ICON_SUCCESS, ICON_ERROR, ICON_WARNING, ICON_TIEN_LAU

logger = logging.getLogger(__name__)

class AddMoneyCommandCog(commands.Cog, name="ServerAdmin AddMoney"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("AddMoneyCommandCog (v3 - Refactored) initialized.")

    @commands.command(name='addmoney', aliases=['am', 'ecoadd'])
    @commands.check(is_guild_owner_check)
    @commands.guild_only()
    async def add_money(self, ctx: commands.Context, member: nextcord.Member, amount: int):
        """(Chủ Server) Cộng 'Tiền Lậu' (adadd) vào Ví Local của một thành viên."""
        if amount <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Số tiền cộng thêm phải là số dương.")
            return

        target_user_id = member.id
        guild_id = ctx.guild.id
        
        try:
            # Use the bot's data cache
            economy_data = self.bot.economy_data
            global_profile = get_or_create_global_user_profile(economy_data, target_user_id)
            local_data = get_or_create_user_local_data(global_profile, guild_id)
            
            # Add to adadd (dirty money) balance
            local_data["local_balance"]["adadd"] += amount

            # No need to save, autosave task handles it

            logger.info(f"SERVER ADMIN ACTION: {ctx.author.id} at guild {guild_id} added {amount} adadd to user {target_user_id}.")
            
            new_adadd_balance = local_data["local_balance"]["adadd"]
            await try_send(ctx, content=f"{ICON_SUCCESS} Đã cộng **{amount:,}** {ICON_TIEN_LAU} (Tiền Lậu) vào Ví Local của {member.mention}.\nSố dư Tiền Lậu mới của họ: **{new_adadd_balance:,}**")

        except Exception as e:
            logger.error(f"Error in 'addmoney' (v3) by {ctx.author.name}:", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi thực hiện lệnh cộng tiền.")

    @add_money.error 
    async def add_money_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CheckFailure): 
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ dành cho Chủ Server (người tạo ra server).")
        elif isinstance(error, commands.MissingRequiredArgument):
            await try_send(ctx, content=f"{ICON_WARNING} Sử dụng đúng: `{COMMAND_PREFIX}{ctx.command.name} <@người_dùng> <số_tiền>`")
        elif isinstance(error, commands.BadArgument): 
            await try_send(ctx, content=f"{ICON_ERROR} Đối số không hợp lệ. Hãy tag một người dùng và nhập một số tiền là số nguyên.")
        else:
            logger.error(f"Unknown error in '{ctx.command.name}' by {ctx.author.name}:", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi thực hiện lệnh cộng tiền.")

def setup(bot: commands.Bot):
    bot.add_cog(AddMoneyCommandCog(bot))
