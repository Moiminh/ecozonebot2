# bot/cogs/moderation/user_data_cmd.py
import nextcord
from nextcord.ext import commands
import logging
import json 
from typing import Optional # Để dùng cho tham số tùy chọn

from core.database import get_user_data 
from core.utils import try_send, is_bot_moderator 
from core.config import CURRENCY_SYMBOL, SHOP_ITEMS, COMMAND_PREFIX 
from core.icons import ICON_PROFILE, ICON_ERROR, ICON_WARNING, ICON_INFO, ICON_MONEY_BAG, ICON_BANK, ICON_INVENTORY

logger = logging.getLogger(__name__)

class UserDataModCog(commands.Cog, name="User Data Moderator Tools"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info(f"{ICON_INFO} UserDataModCog initialized.")

    @commands.command(name="mod_viewuser", aliases=["mod_getdata"])
    @commands.check(is_bot_moderator)
    async def mod_viewuser(self, ctx: commands.Context, target_user_identifier: str, guild_id_str: Optional[str] = None):
        """
        (Moderator/Owner Only) Xem dữ liệu kinh tế của người dùng.
        Nếu Guild ID được cung cấp, sẽ xem ở guild đó. Nếu không, xem ở guild hiện tại.
        Sử dụng: !mod_viewuser <UserID hoặc @UserMention> [Guild_ID_Tùy_Chọn]
        """
        logger.debug(f"Lệnh 'mod_viewuser' được gọi bởi Mod/Owner {ctx.author.name} ({ctx.author.id}) cho target '{target_user_identifier}'. Guild ID cung cấp: '{guild_id_str}'.")

        guild_to_check_id = None
        target_guild = None

        if guild_id_str: # Nếu Guild ID được cung cấp
            try:
                guild_to_check_id = int(guild_id_str)
                target_guild = self.bot.get_guild(guild_to_check_id)
                if not target_guild:
                    await try_send(ctx, content=f"{ICON_ERROR} Không tìm thấy server (guild) với ID: `{guild_to_check_id}`. Bot có thể không ở trong server đó hoặc ID sai.")
                    logger.warning(f"Mod/Owner {ctx.author.id} yêu cầu dữ liệu cho guild ID không tồn tại/bot không ở trong: {guild_to_check_id}")
                    return
            except ValueError:
                await try_send(ctx, content=f"{ICON_ERROR} Guild ID phải là một con số nếu được cung cấp.")
                logger.warning(f"Mod/Owner {ctx.author.id} cung cấp Guild ID không phải số: '{guild_id_str}'")
                return
        else: # Nếu không cung cấp Guild ID, dùng guild hiện tại
            if not ctx.guild: # Lệnh này không nên dùng trong DM nếu không có Guild ID
                await try_send(ctx, content=f"{ICON_ERROR} Vui lòng cung cấp Guild ID khi dùng lệnh này trong DM, hoặc dùng trong một server.")
                logger.warning(f"Mod/Owner {ctx.author.id} dùng 'mod_viewuser' trong DM mà không có Guild ID.")
                return
            target_guild = ctx.guild
            guild_to_check_id = target_guild.id
        
        logger.debug(f"Sẽ kiểm tra dữ liệu trong guild: {target_guild.name} ({guild_to_check_id})")

        # Xử lý target_user_identifier để lấy đối tượng user/member
        target_user_obj = None # Sẽ là nextcord.User hoặc nextcord.Member
        try:
            if target_user_identifier.isdigit():
                user_id_to_fetch = int(target_user_identifier)
                # Ưu tiên lấy Member object nếu user có trong target_guild
                member_in_target_guild = target_guild.get_member(user_id_to_fetch)
                if member_in_target_guild:
                    target_user_obj = member_in_target_guild
                else: # Nếu không phải member của target_guild (ví dụ đã rời), fetch user data chung
                    target_user_obj = await self.bot.fetch_user(user_id_to_fetch)
            else: 
                # Thử convert từ mention. MemberConverter hoạt động trong ctx.guild.
                # Nếu target_guild khác ctx.guild, cách này có thể không chính xác cho việc lấy member của target_guild.
                # Trong trường hợp đó, yêu cầu User ID là tốt nhất.
                if target_guild.id == ctx.guild.id: # Nếu target_guild là guild hiện tại, có thể dùng MemberConverter
                    converter = commands.MemberConverter()
                    target_user_obj = await converter.convert(ctx, target_user_identifier)
                else: # Nếu target_guild khác, và người dùng không nhập ID, yêu cầu ID
                    await try_send(ctx, content=f"{ICON_WARNING} Để xem người dùng ở server khác (`{target_guild.name}`), vui lòng cung cấp User ID của họ thay vì mention.")
                    logger.warning(f"Mod/Owner {ctx.author.id} dùng mention cho user ở guild khác với target_guild mà không cung cấp ID.")
                    return
        except ValueError:
             await try_send(ctx, content=f"{ICON_ERROR} User ID phải là dạng số nếu bạn không mention.")
             logger.warning(f"Mod/Owner {ctx.author.id} cung cấp User ID không phải số: '{target_user_identifier}'")
             return
        except nextcord.NotFound:
            await try_send(ctx, content=f"{ICON_ERROR} Không tìm thấy người dùng với ID `{target_user_identifier}` trên Discord.")
            logger.warning(f"Mod/Owner {ctx.author.id} cung cấp User ID không tìm thấy trên Discord: '{target_user_identifier}'")
            return
        except commands.BadArgument: # Lỗi từ MemberConverter nếu không phải mention hợp lệ
            await try_send(ctx, content=f"{ICON_ERROR} Không thể xác định người dùng từ '{target_user_identifier}'. Vui lòng cung cấp User ID hoặc mention một người dùng (nếu xem trong server hiện tại).")
            logger.warning(f"Mod/Owner {ctx.author.id} cung cấp target_user_identifier không hợp lệ: '{target_user_identifier}'")
            return
        except Exception as e:
            await try_send(ctx, content=f"{ICON_ERROR} Có lỗi khi tìm người dùng: {e}")
            logger.error(f"Lỗi khi tìm target_user cho 'mod_viewuser': {e}", exc_info=True)
            return

        if not target_user_obj:
            await try_send(ctx, content=f"{ICON_ERROR} Không tìm thấy người dùng `{target_user_identifier}`.")
            return

        # Lấy dữ liệu từ database.py
        full_data = get_user_data(guild_to_check_id, target_user_obj.id)
        user_data = full_data.get(str(guild_to_check_id), {}).get(str(target_user_obj.id))

        if not user_data: 
            await try_send(ctx, content=f"{ICON_INFO} Không tìm thấy dữ liệu kinh tế cho {target_user_obj.mention} trong server `{target_guild.name}`.")
            logger.info(f"MODERATOR ACTION: Không tìm thấy dữ liệu kinh tế cho User {target_user_obj.name} ({target_user_obj.id}) trong guild {target_guild.name} ({guild_to_check_id}) khi {ctx.author.name} gọi mod_viewuser.")
            return

        # Tạo Embed để hiển thị thông tin (giữ nguyên logic tạo embed)
        embed = nextcord.Embed(
            title=f"{ICON_PROFILE} Thông tin kinh tế của {target_user_obj.display_name}",
            description=f"Trong Server: `{target_guild.name}` (ID: `{target_guild.id}`)\nUser ID: `{target_user_obj.id}`",
            color=nextcord.Color.teal()
        )
        # ... (phần add_field cho balance, bank_balance, inventory, cooldowns giữ nguyên như trước) ...
        embed.set_thumbnail(url=target_user_obj.display_avatar.url)
        embed.add_field(name=f"{ICON_MONEY_BAG} Số dư Ví", value=f"`{user_data.get('balance', 0):,}` {CURRENCY_SYMBOL}", inline=True)
        embed.add_field(name=f"{ICON_BANK} Số dư Ngân Hàng", value=f"`{user_data.get('bank_balance', 0):,}` {CURRENCY_SYMBOL}", inline=True)
        inventory_list = user_data.get("inventory", [])
        if inventory_list:
            item_counts = {}
            for item_id_in_inv in inventory_list: item_counts[item_id_in_inv] = item_counts.get(item_id_in_inv, 0) + 1
            inv_display_parts = []
            for item_id, count in item_counts.items():
                item_details = SHOP_ITEMS.get(item_id, {}); item_display_name = item_details.get("name", item_id.replace("_", " ").capitalize())
                inv_display_parts.append(f"- {item_display_name} (x{count})")
            embed.add_field(name=f"{ICON_INVENTORY} Túi Đồ ({len(inventory_list)} vật phẩm)", value="\n".join(inv_display_parts) if inv_display_parts else "Trống", inline=False)
        else:
            embed.add_field(name=f"{ICON_INVENTORY} Túi Đồ", value="Trống", inline=False)
        cooldown_info = []; last_work = user_data.get('last_work', 0)
        if last_work != 0: cooldown_info.append(f"Làm việc lần cuối: <t:{int(last_work)}:R>")
        if cooldown_info: embed.add_field(name="🕒 Cooldowns (Gần đây)", value="\n".join(cooldown_info), inline=False)

        await try_send(ctx, embed=embed)
        logger.info(f"MODERATOR ACTION: {ctx.author.display_name} ({ctx.author.id}) đã xem dữ liệu của user {target_user_obj.display_name} ({target_user_obj.id}) trong guild {target_guild.name} ({target_guild.id}).")

    @mod_viewuser.error
    async def mod_viewuser_error(self, ctx: commands.Context, error):
        # ... (Hàm error handler có thể cần cập nhật một chút cho MissingRequiredArgument) ...
        if isinstance(error, commands.CheckFailure):
            logger.warning(f"User {ctx.author.name} ({ctx.author.id}) không có quyền dùng 'mod_viewuser'.")
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ quyền (Moderator/Owner) để sử dụng lệnh này.")
        elif isinstance(error, commands.MissingRequiredArgument):
            param_name = error.param.name if hasattr(error.param, 'name') else "tham_số_bị_thiếu"
            # Cập nhật hướng dẫn sử dụng
            await try_send(ctx, content=f"{ICON_WARNING} Bạn thiếu tham số `{param_name}`. Sử dụng: `{COMMAND_PREFIX}mod_viewuser <UserID hoặc @UserMention> [GuildID_Tùy_Chọn]`")
        elif isinstance(error, commands.BadArgument): 
             await try_send(ctx, content=f"{ICON_ERROR} Guild ID hoặc User/Mention không hợp lệ. Vui lòng kiểm tra lại.")
        else:
            logger.error(f"Lỗi không xác định trong lệnh 'mod_viewuser' bởi {ctx.author.name}:", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra với lệnh `mod_viewuser`.")

def setup(bot: commands.Bot):
    bot.add_cog(UserDataModCog(bot))
