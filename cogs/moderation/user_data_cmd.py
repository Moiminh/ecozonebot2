# bot/cogs/moderation/user_data_cmd.py
import nextcord
from nextcord.ext import commands
import logging
import json # Để format output JSON cho đẹp nếu cần, hoặc tạo Embed

from core.database import get_user_data # Dùng get_user_data để đảm bảo user được khởi tạo nếu chưa có
from core.utils import try_send, is_bot_moderator # Hàm check quyền moderator
from core.config import CURRENCY_SYMBOL, SHOP_ITEMS, COMMAND_PREFIX # Cần SHOP_ITEMS để hiển thị tên vật phẩm
from core.icons import ICON_PROFILE, ICON_ERROR, ICON_WARNING, ICON_INFO, ICON_MONEY_BAG, ICON_BANK, ICON_INVENTORY

logger = logging.getLogger(__name__)

class UserDataModCog(commands.Cog, name="User Data Moderator Tools"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info(f"{ICON_INFO} UserDataModCog initialized.")

    @commands.command(name="mod_viewuser", aliases=["mod_getdata"])
    @commands.check(is_bot_moderator) # Chỉ Moderator hoặc Owner mới dùng được
    async def mod_viewuser(self, ctx: commands.Context, guild_id_str: str, target_user_identifier: str):
        """
        (Moderator/Owner Only) Xem dữ liệu kinh tế của một người dùng trong một guild cụ thể.
        Sử dụng: !mod_viewuser <Guild_ID> <UserID hoặc @UserMention>
        """
        logger.debug(f"Lệnh 'mod_viewuser' được gọi bởi Mod/Owner {ctx.author.name} ({ctx.author.id}) cho target '{target_user_identifier}' trong guild '{guild_id_str}'.")

        guild_id = None
        try:
            guild_id = int(guild_id_str)
        except ValueError:
            await try_send(ctx, content=f"{ICON_ERROR} Guild ID phải là một con số.")
            logger.warning(f"Mod/Owner {ctx.author.id} cung cấp Guild ID không phải số: '{guild_id_str}'")
            return

        target_guild = self.bot.get_guild(guild_id)
        if not target_guild:
            await try_send(ctx, content=f"{ICON_ERROR} Không tìm thấy server (guild) với ID: `{guild_id}`. Bot có thể không ở trong server đó.")
            logger.warning(f"Mod/Owner {ctx.author.id} yêu cầu dữ liệu cho guild ID không tồn tại hoặc bot không ở trong: {guild_id}")
            return

        target_member = None
        try:
            # Thử chuyển đổi target_user_identifier thành ID nếu nó là số
            if target_user_identifier.isdigit():
                user_id_to_fetch = int(target_user_identifier)
                target_member = target_guild.get_member(user_id_to_fetch) # Thử lấy member nếu user ở trong guild
                if not target_member: # Nếu không phải member (ví dụ user đã rời), thử fetch_user
                    target_member = await self.bot.fetch_user(user_id_to_fetch) 
            else:
                # Nếu không phải số, thử dùng converter của nextcord để lấy member từ mention (ví dụ: <@!ID> hoặc <@ID>)
                # Hoặc nếu họ chỉ nhập tên (việc này phức tạp hơn, tạm thời yêu cầu ID hoặc Mention)
                try:
                    converter = commands.MemberConverter() # Hoặc commands.UserConverter() nếu muốn chấp nhận user không trong guild
                    target_member = await converter.convert(ctx, target_user_identifier) # Cần ctx để convert mention
                    # Nếu convert từ mention trong guild khác với target_guild, cần cẩn thận
                    # Để đơn giản, nếu là mention, nó sẽ lấy từ guild của ctx.
                    # Nếu muốn lấy member từ target_guild bằng mention, cần phải ctx được truyền vào từ guild đó
                    # hoặc bot phải có cách lấy member từ một guild cụ thể bằng tên/mention.
                    # Hiện tại, nếu là mention, nó sẽ là member của guild hiện tại của ctx.
                    # Nếu Guild ID khác với ctx.guild.id, thì UserID là lựa chọn tốt nhất.
                    if target_member.guild.id != target_guild.id and not target_user_identifier.isdigit():
                         await try_send(ctx, content=f"{ICON_WARNING} Nếu xem người dùng ở server khác, vui lòng cung cấp User ID của họ thay vì mention.")
                         logger.warning(f"Mod/Owner {ctx.author.id} dùng mention cho user ở guild khác với target_guild.")
                         return
                except commands.BadArgument: # Không phải mention hợp lệ và không phải ID
                    await try_send(ctx, content=f"{ICON_ERROR} Không thể xác định người dùng từ '{target_user_identifier}'. Vui lòng cung cấp User ID hoặc mention một người dùng hợp lệ trong server hiện tại (nếu Guild ID là của server này).")
                    logger.warning(f"Mod/Owner {ctx.author.id} cung cấp target_user_identifier không hợp lệ: '{target_user_identifier}'")
                    return
        
        except ValueError: # Lỗi khi int(target_user_identifier) nếu nó không hoàn toàn là số
             await try_send(ctx, content=f"{ICON_ERROR} User ID phải là dạng số nếu bạn không mention.")
             logger.warning(f"Mod/Owner {ctx.author.id} cung cấp User ID không phải số: '{target_user_identifier}'")
             return
        except nextcord.NotFound:
            await try_send(ctx, content=f"{ICON_ERROR} Không tìm thấy người dùng với ID được cung cấp trong Discord: `{target_user_identifier}`")
            logger.warning(f"Mod/Owner {ctx.author.id} cung cấp User ID không tìm thấy trên Discord: '{target_user_identifier}'")
            return
        except Exception as e:
            await try_send(ctx, content=f"{ICON_ERROR} Có lỗi khi tìm người dùng: {e}")
            logger.error(f"Lỗi khi tìm target_user cho 'mod_viewuser': {e}", exc_info=True)
            return

        if not target_member: # Nếu sau tất cả các bước vẫn không tìm được
            await try_send(ctx, content=f"{ICON_ERROR} Không tìm thấy người dùng `{target_user_identifier}` trong server `{target_guild.name}` hoặc trên Discord.")
            return

        # Lấy dữ liệu từ database.py cho guild_id và user_id đã xác định
        # get_user_data sẽ tự tạo nếu chưa có, nhưng ở đây ta chỉ muốn xem, nên có thể dùng load_data và truy cập trực tiếp
        # Tuy nhiên, để nhất quán và đảm bảo có các key mặc định, dùng get_user_data vẫn tốt.
        full_data = get_user_data(target_guild.id, target_member.id)
        user_data = full_data.get(str(target_guild.id), {}).get(str(target_member.id))

        if not user_data: # Trường hợp này ít xảy ra nếu get_user_data hoạt động đúng
            await try_send(ctx, content=f"{ICON_INFO} Không tìm thấy dữ liệu kinh tế cho User ID: `{target_member.id}` trong Guild: `{target_guild.name}`.")
            logger.info(f"MODERATOR ACTION: Không tìm thấy dữ liệu kinh tế cho User {target_member.name} ({target_member.id}) trong guild {target_guild.name} ({target_guild.id}) khi {ctx.author.name} gọi mod_viewuser.")
            return

        # Tạo Embed để hiển thị thông tin
        embed = nextcord.Embed(
            title=f"{ICON_PROFILE} Thông tin kinh tế của {target_member.display_name}",
            description=f"Trong Server: `{target_guild.name}` (ID: `{target_guild.id}`)\nUser ID: `{target_member.id}`",
            color=nextcord.Color.teal()
        )
        embed.set_thumbnail(url=target_member.display_avatar.url)

        embed.add_field(name=f"{ICON_MONEY_BAG} Số dư Ví", value=f"`{user_data.get('balance', 0):,}` {CURRENCY_SYMBOL}", inline=True)
        embed.add_field(name=f"{ICON_BANK} Số dư Ngân Hàng", value=f"`{user_data.get('bank_balance', 0):,}` {CURRENCY_SYMBOL}", inline=True)
        
        inventory_list = user_data.get("inventory", [])
        if inventory_list:
            item_counts = {}
            for item_id_in_inv in inventory_list:
                item_counts[item_id_in_inv] = item_counts.get(item_id_in_inv, 0) + 1
            
            inv_display_parts = []
            for item_id, count in item_counts.items():
                item_details = SHOP_ITEMS.get(item_id, {})
                item_display_name = item_details.get("name", item_id.replace("_", " ").capitalize())
                inv_display_parts.append(f"- {item_display_name} (x{count})")
            embed.add_field(name=f"{ICON_INVENTORY} Túi Đồ ({len(inventory_list)} vật phẩm)", value="\n".join(inv_display_parts) if inv_display_parts else "Trống", inline=False)
        else:
            embed.add_field(name=f"{ICON_INVENTORY} Túi Đồ", value="Trống", inline=False)

        # Thêm thông tin cooldown (tùy chọn)
        cooldown_info = []
        last_work = user_data.get('last_work', 0)
        if last_work != 0: cooldown_info.append(f"Làm việc lần cuối: <t:{int(last_work)}:R>")
        # ... có thể thêm các cooldown khác nếu muốn ...
        if cooldown_info:
            embed.add_field(name="🕒 Cooldowns (Gần đây)", value="\n".join(cooldown_info), inline=False)
        
        await try_send(ctx, embed=embed)
        logger.info(f"MODERATOR ACTION: {ctx.author.display_name} ({ctx.author.id}) đã xem dữ liệu của user {target_member.display_name} ({target_member.id}) trong guild {target_guild.name} ({target_guild.id}).")


    @mod_viewuser.error
    async def mod_viewuser_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CheckFailure):
            logger.warning(f"User {ctx.author.name} ({ctx.author.id}) không có quyền dùng 'mod_viewuser'.")
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ quyền (Moderator/Owner) để sử dụng lệnh này.")
        elif isinstance(error, commands.MissingRequiredArgument):
            param_name = error.param.name if hasattr(error.param, 'name') else "tham_số_bị_thiếu"
            await try_send(ctx, content=f"{ICON_WARNING} Bạn thiếu tham số `{param_name}`. Sử dụng: `{COMMAND_PREFIX}mod_viewuser <GuildID> <UserID/@UserMention>`")
        elif isinstance(error, commands.BadArgument): # Ví dụ như không convert được UserID/GuildID
             await try_send(ctx, content=f"{ICON_ERROR} Guild ID hoặc User/Mention không hợp lệ. Vui lòng kiểm tra lại.")
        else:
            logger.error(f"Lỗi không xác định trong lệnh 'mod_viewuser' bởi {ctx.author.name}:", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra với lệnh `mod_viewuser`.")


def setup(bot: commands.Bot):
    bot.add_cog(UserDataModCog(bot))
