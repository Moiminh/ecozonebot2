# bot/cogs/moderation/manage_mods_cmd.py
import nextcord
from nextcord.ext import commands
import logging

# Import các hàm quản lý moderator từ database và các icon
from core.database import add_moderator_id, remove_moderator_id, load_moderator_ids
from core.utils import try_send 
from core.icons import ICON_SUCCESS, ICON_ERROR, ICON_WARNING, ICON_INFO, ICON_ADMIN_PANEL # Tạo ICON_ADMIN_PANEL nếu muốn, ví dụ: "🛡️"
from core.config import COMMAND_PREFIX # Cần cho thông báo lỗi

logger = logging.getLogger(__name__)

class ManageModeratorsCog(commands.Cog, name="Manage Moderators"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info(f"{ICON_INFO} ManageModeratorsCog initialized.")

    @commands.command(name="addmod")
    @commands.is_owner() # Chỉ owner của bot mới dùng được lệnh này
    async def add_moderator(self, ctx: commands.Context, user: nextcord.User):
        """(Owner Only) Thêm một User ID vào danh sách moderator.
        Sử dụng: !addmod <@UserMention hoặc UserID>
        """
        logger.debug(f"Lệnh 'addmod' được gọi bởi {ctx.author.name} cho user {user.name} ({user.id}).")
        
        current_ids = load_moderator_ids()
        if user.id in current_ids:
            logger.info(f"OWNER ACTION: {ctx.author.display_name} ({ctx.author.id}) cố gắng thêm {user.display_name} ({user.id}) nhưng đã là moderator.")
            await try_send(ctx, content=f"{ICON_INFO} {user.mention} (`{user.id}`) đã có trong danh sách moderator rồi.")
            return

        if add_moderator_id(user.id): # Hàm này sẽ tự động lưu
            logger.info(f"OWNER ACTION: {ctx.author.display_name} ({ctx.author.id}) đã thêm {user.display_name} ({user.id}) vào danh sách moderator.")
            await try_send(ctx, content=f"{ICON_SUCCESS} Đã thêm {user.mention} (`{user.id}`) vào danh sách moderator thành công!")
        else:
            # add_moderator_id trả về False nếu có lỗi khi lưu file hoặc user_id không hợp lệ
            logger.error(f"OWNER ACTION: {ctx.author.display_name} ({ctx.author.id}) không thể thêm {user.display_name} ({user.id}) vào danh sách moderator do lỗi lưu file hoặc ID không hợp lệ.")
            await try_send(ctx, content=f"{ICON_ERROR} Không thể thêm {user.mention} vào danh sách moderator. Vui lòng kiểm tra log của bot.")


    @commands.command(name="removemod", aliases=["delmod", "rmmod"]) # Thêm alias rmmod
    @commands.is_owner() 
    async def remove_moderator(self, ctx: commands.Context, user: nextcord.User):
        """(Owner Only) Xóa một User ID khỏi danh sách moderator.
        Sử dụng: !removemod <@UserMention hoặc UserID>
        """
        logger.debug(f"Lệnh 'removemod' được gọi bởi {ctx.author.name} cho user {user.name} ({user.id}).")
        if remove_moderator_id(user.id): # Hàm này sẽ tự động lưu
            logger.info(f"OWNER ACTION: {ctx.author.display_name} ({ctx.author.id}) đã xóa {user.display_name} ({user.id}) khỏi danh sách moderator.")
            await try_send(ctx, content=f"{ICON_SUCCESS} Đã xóa {user.mention} (`{user.id}`) khỏi danh sách moderator thành công!")
        else:
            # remove_moderator_id trả về False nếu không tìm thấy user hoặc lỗi lưu file
            logger.warning(f"OWNER ACTION: {ctx.author.display_name} ({ctx.author.id}) cố gắng xóa {user.display_name} ({user.id}) nhưng không tìm thấy trong danh sách hoặc lỗi lưu file.")
            await try_send(ctx, content=f"{ICON_ERROR} Không tìm thấy {user.mention} (`{user.id}`) trong danh sách moderator hoặc có lỗi khi lưu file.")

    @commands.command(name="listmods")
    @commands.is_owner() 
    async def list_moderators(self, ctx: commands.Context):
        """(Owner Only) Hiển thị danh sách các moderator hiện tại."""
        logger.debug(f"Lệnh 'listmods' được gọi bởi {ctx.author.name}.")
        moderator_ids = load_moderator_ids()
        
        if not moderator_ids:
            await try_send(ctx, content=f"{ICON_INFO} Hiện tại không có ai trong danh sách moderator (ngoài Owner).")
            logger.info(f"OWNER ACTION: {ctx.author.display_name} ({ctx.author.id}) xem danh sách moderator (hiện đang trống).")
            return

        embed = nextcord.Embed(
            title=f"{ICON_ADMIN_PANEL if 'ICON_ADMIN_PANEL' in locals() or 'ICON_ADMIN_PANEL' in globals() else '🛡️'} Danh Sách Moderator", 
            color=nextcord.Color.blue() # Hoặc màu bạn thích
        )
        
        description_parts = []
        for mod_id in moderator_ids:
            try:
                user_obj = await self.bot.fetch_user(mod_id) 
                description_parts.append(f"- {user_obj.mention} (`{user_obj.name}#{user_obj.discriminator}`, ID: `{mod_id}`)")
            except nextcord.NotFound:
                description_parts.append(f"- {ICON_WARNING} *Không tìm thấy user với ID:* `{mod_id}`")
                logger.warning(f"Không thể fetch user cho moderator ID: {mod_id} khi listmods.")
            except Exception as e:
                description_parts.append(f"- {ICON_ERROR} *Lỗi khi lấy thông tin user ID:* `{mod_id}`")
                logger.error(f"Lỗi fetch user cho moderator ID {mod_id} khi listmods: {e}", exc_info=True)

        if description_parts:
            embed.description = "\n".join(description_parts)
        else:
            embed.description = "Không thể hiển thị thông tin moderator (có thể do lỗi fetch tất cả user ID trong danh sách)."

        await try_send(ctx, embed=embed)
        logger.info(f"OWNER ACTION: {ctx.author.display_name} ({ctx.author.id}) đã xem danh sách moderator. Số lượng: {len(moderator_ids)}.")

    # Xử lý lỗi chung cho các lệnh trong Cog này
    # Hàm này sẽ bắt lỗi cho cả 3 lệnh addmod, removemod, listmods nếu chúng không có error handler riêng
    # và lỗi đó không phải là commands.CheckFailure (vì is_owner() đã xử lý ngầm)
    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        # Bỏ qua lỗi NotOwner vì is_owner() decorator đã xử lý (không cho lệnh chạy và có thể không báo gì)
        # Tuy nhiên, chúng ta có thể log ở đây nếu muốn
        if isinstance(error, commands.NotOwner):
            logger.warning(f"User {ctx.author.name} ({ctx.author.id}) không phải owner cố gắng dùng lệnh moderator: {ctx.command.name}")
            # Không cần gửi tin nhắn vì is_owner() thường đã có cơ chế riêng
            return

        if isinstance(error, commands.MissingRequiredArgument):
            param_name = error.param.name if hasattr(error.param, 'name') else "tham_số_bị_thiếu"
            await try_send(ctx, content=f"{ICON_WARNING} Bạn thiếu tham số `{param_name}` cho lệnh `{ctx.command.name}`. Dùng `{COMMAND_PREFIX}help {ctx.command.name}` để xem chi tiết.")
        elif isinstance(error, commands.UserNotFound):
            await try_send(ctx, content=f"{ICON_ERROR} Không tìm thấy người dùng được chỉ định: `{error.argument}`.")
        elif isinstance(error, commands.CheckFailure): # Dành cho các check khác is_owner nếu có
            logger.warning(f"CheckFailure cho lệnh '{ctx.command.name}' bởi user {ctx.author.id}: {error}")
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không đáp ứng điều kiện để sử dụng lệnh này.")
        else:
            logger.error(f"Lỗi không mong muốn trong {ctx.command.name} của ManageModeratorsCog: {error}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra với lệnh `{ctx.command.name}`.")


def setup(bot: commands.Bot):
    bot.add_cog(ManageModeratorsCog(bot))
