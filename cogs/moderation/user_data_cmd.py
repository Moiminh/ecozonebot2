import nextcord
from nextcord.ext import commands
import logging
from typing import Optional

from core.database import (
    load_economy_data,
    get_or_create_global_user_profile,
    get_or_create_user_server_data,
    save_economy_data
)
from core.utils import try_send, is_bot_moderator
from core.config import CURRENCY_SYMBOL, SHOP_ITEMS as MASTER_ITEM_LIST, COMMAND_PREFIX
from core.icons import ICON_PROFILE, ICON_ERROR, ICON_WARNING, ICON_INFO, ICON_MONEY_BAG, ICON_BANK, ICON_INVENTORY, ICON_SUCCESS

logger = logging.getLogger(__name__)

async def resolve_user_and_guild(bot_instance, ctx, target_user_identifier: str, guild_id_str: Optional[str] = None):
    target_guild = None
    if guild_id_str:
        try:
            guild_id = int(guild_id_str)
            target_guild = bot_instance.get_guild(guild_id)
            if not target_guild:
                await try_send(ctx, content=f"{ICON_ERROR} Không tìm thấy server (guild) với ID: `{guild_id}`.")
                return None, None
        except ValueError:
            await try_send(ctx, content=f"{ICON_ERROR} Guild ID phải là một con số."); return None, None
    else:
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Vui lòng cung cấp Guild ID khi dùng lệnh này trong DM."); return None, None
        target_guild = ctx.guild

    target_user_obj = None
    try:
        if target_user_identifier.isdigit():
            user_id_to_fetch = int(target_user_identifier)
            target_user_obj = await bot_instance.fetch_user(user_id_to_fetch)
        else: 
            converter = commands.UserConverter()
            temp_user = await converter.convert(ctx, target_user_identifier)
            target_user_obj = await bot_instance.fetch_user(temp_user.id)
    except (ValueError, nextcord.NotFound, commands.BadArgument) as e:
        await try_send(ctx, content=f"{ICON_ERROR} Không thể xác định/tìm thấy người dùng '{target_user_identifier}': {e}"); return None, None

    if not target_user_obj:
        await try_send(ctx, content=f"{ICON_ERROR} Không tìm thấy người dùng `{target_user_identifier}`."); return None, None
        
    return target_user_obj, target_guild

class UserDataModCog(commands.Cog, name="User Data Moderator Tools"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info(f"{ICON_INFO} UserDataModCog initialized.")

    @commands.command(name="mod_viewuser", aliases=["mod_getdata"])
    @commands.check(is_bot_moderator)
    async def mod_viewuser(self, ctx: commands.Context, target_user_identifier: str, guild_id_str: Optional[str] = None):
        target_user, target_guild = await resolve_user_and_guild(self.bot, ctx, target_user_identifier, guild_id_str)
        if not target_user or not target_guild: return

        economy_data = load_economy_data()
        global_profile = get_or_create_global_user_profile(economy_data, target_user.id)
        server_data = get_or_create_user_server_data(global_profile, target_guild.id)
        
        save_economy_data(economy_data)

        local_balance_dict = server_data.get("local_balance", {})
        earned_amount = local_balance_dict.get("earned", 0)
        admin_added_amount = local_balance_dict.get("admin_added", 0)
        total_local_balance = earned_amount + admin_added_amount
        global_balance = global_profile.get("global_balance", 0)
        
        embed = nextcord.Embed(title=f"{ICON_PROFILE} Thông tin kinh tế của {target_user.display_name}",
                                description=f"Trong Server: `{target_guild.name}` (ID: `{target_guild.id}`)\nUser ID: `{target_user.id}`",
                                color=nextcord.Color.teal())
        embed.set_thumbnail(url=target_user.display_avatar.url)
        embed.add_field(name=f"Ví Local (Server: {target_guild.name})", value=f"`{total_local_balance:,}` {CURRENCY_SYMBOL}", inline=True)
        embed.add_field(name=f"Ví Global (GOL)", value=f"`{global_balance:,}` {CURRENCY_SYMBOL}", inline=True)

        await try_send(ctx, embed=embed)
        logger.info(f"MODERATOR ACTION: {ctx.author.display_name} ({ctx.author.id}) đã xem dữ liệu của user {target_user.display_name} ({target_user.id}) trong guild {target_guild.name} ({target_guild.id}).")

    @commands.command(name="mod_addlocalmoney")
    @commands.check(is_bot_moderator)
    async def mod_addlocalmoney(self, ctx: commands.Context, guild_id_str: str, target_user_identifier: str, amount: int):
        target_user, target_guild = await resolve_user_and_guild(self.bot, ctx, target_user_identifier, guild_id_str)
        if not target_user or not target_guild: return

        if amount <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Số tiền cộng thêm phải là số dương.")
            return

        economy_data = load_economy_data()
        global_profile = get_or_create_global_user_profile(economy_data, target_user.id)
        server_data = get_or_create_user_server_data(global_profile, target_guild.id)

        original_admin_added = server_data["local_balance"].get("admin_added", 0)
        server_data["local_balance"]["admin_added"] = original_admin_added + amount

        save_economy_data(economy_data)
        
        logger.info(f"MODERATOR ACTION: {ctx.author.display_name} ({ctx.author.id}) đã 'mod_addlocalmoney', cộng {amount:,} {CURRENCY_SYMBOL} "
                    f"vào VÍ LOCAL (ADMIN-ADDED) của {target_user.display_name} ({target_user.id}) tại guild {target_guild.name} ({target_guild.id}).")
        
        await try_send(ctx, content=f"{ICON_SUCCESS} Đã cộng **{amount:,}** {CURRENCY_SYMBOL} vào quỹ **Admin-add** trong Ví Local của {target_user.mention} tại server `{target_guild.name}`.")

    @mod_viewuser.error
    @mod_addlocalmoney.error
    async def mod_data_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CheckFailure):
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ quyền (Moderator/Owner) để sử dụng lệnh này.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await try_send(ctx, content=f"{ICON_WARNING} Thiếu tham số cho lệnh `{ctx.command.name}`.")
        elif isinstance(error, commands.BadArgument):
             await try_send(ctx, content=f"{ICON_ERROR} Tham số không hợp lệ. Vui lòng kiểm tra lại.")
        else:
            logger.error(f"Lỗi không xác định trong lệnh '{ctx.command.name}' của UserDataModCog:", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra với lệnh `{ctx.command.name}`.")

def setup(bot: commands.Bot):
    bot.add_cog(UserDataModCog(bot))
