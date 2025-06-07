# bot/cogs/moderation/manage_mods_cmd.py
import nextcord
from nextcord.ext import commands
import logging

# Các hàm này đã được chuyển qua database.py mới và hoạt động bình thường
from core.database import add_moderator_id, remove_moderator_id, load_moderator_ids
from core.utils import try_send 
from core.icons import ICON_SUCCESS, ICON_ERROR, ICON_WARNING, ICON_INFO, ICON_ADMIN_PANEL
from core.config import COMMAND_PREFIX

logger = logging.getLogger(__name__)

class ManageModeratorsCog(commands.Cog, name="Manage Moderators"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("ManageModeratorsCog (v2) initialized.")

    @commands.command(name="addmod")
    @commands.is_owner()
    async def add_moderator(self, ctx: commands.Context, user: nextcord.User):
        """(Bot Owner) Thêm một người dùng vào danh sách moderator của bot."""
        if user.id in load_moderator_ids():
            await try_send(ctx, content=f"{ICON_INFO} {user.mention} (`{user.id}`) đã có trong danh sách moderator.")
            return

        if add_moderator_id(user.id):
            logger.info(f"BOT OWNER ACTION: {ctx.author.id} đã thêm {user.id} vào danh sách moderator.")
            await try_send(ctx, content=f"{ICON_SUCCESS} Đã thêm {user.mention} (`{user.id}`) vào danh sách moderator thành công!")
        else:
            logger.error(f"BOT OWNER ACTION: Không thể thêm {user.id} vào danh sách moderator do lỗi lưu file.")
            await try_send(ctx, content=f"{ICON_ERROR} Không thể thêm moderator. Vui lòng kiểm tra log của bot.")

    @commands.command(name="removemod", aliases=["delmod", "rmmod"])
    @commands.is_owner() 
    async def remove_moderator(self, ctx: commands.Context, user: nextcord.User):
        """(Bot Owner) Xóa một người dùng khỏi danh sách moderator của bot."""
        if user.id not in load_moderator_ids():
            await try_send(ctx, content=f"{ICON_ERROR} Không tìm thấy {user.mention} (`{user.id}`) trong danh sách moderator.")
            return

        if remove_moderator_id(user.id):
            logger.info(f"BOT OWNER ACTION: {ctx.author.id} đã xóa {user.id} khỏi danh sách moderator.")
            await try_send(ctx, content=f"{ICON_SUCCESS} Đã xóa {user.mention} (`{user.id}`) khỏi danh sách moderator thành công!")
        else:
            logger.error(f"BOT OWNER ACTION: Không thể xóa {user.id} khỏi danh sách moderator do lỗi lưu file.")
            await try_send(ctx, content=f"{ICON_ERROR} Không thể xóa moderator. Vui lòng kiểm tra log của bot.")

    @commands.command(name="listmods")
    @commands.is_owner() 
    async def list_moderators(self, ctx: commands.Context):
        """(Bot Owner) Hiển thị danh sách các moderator hiện tại của bot."""
        moderator_ids = load_moderator_ids()
        
        if not moderator_ids:
            await try_send(ctx, content=f"{ICON_INFO} Hiện tại không có ai trong danh sách moderator (ngoài Owner).")
            return

        embed = nextcord.Embed(
            title=f"{ICON_ADMIN_PANEL} Danh Sách Moderator Của Bot", 
            color=nextcord.Color.blue()
        )
        
        description_parts = []
        for mod_id in moderator_ids:
            try:
                user_obj = await self.bot.fetch_user(mod_id) 
                description_parts.append(f"- {user_obj.mention} (`{user_obj.name}`, ID: `{mod_id}`)")
            except nextcord.NotFound:
                description_parts.append(f"- {ICON_WARNING} *Không tìm thấy user với ID:* `{mod_id}`")
        
        embed.description = "\n".join(description_parts)
        await try_send(ctx, embed=embed)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.NotOwner):
            # Bot tự động xử lý lỗi này, không cần gửi tin nhắn
            logger.warning(f"User không phải owner {ctx.author.id} đã cố gắng dùng lệnh: {ctx.command.name}")
            return

        if isinstance(error, commands.MissingRequiredArgument):
            await try_send(ctx, content=f"{ICON_WARNING} Bạn thiếu tham số cho lệnh `{ctx.command.name}`.")
        elif isinstance(error, commands.UserNotFound):
            await try_send(ctx, content=f"{ICON_ERROR} Không tìm thấy người dùng được chỉ định: `{error.argument}`.")
        else:
            logger.error(f"Lỗi không mong muốn trong {ctx.command.name} của ManageModeratorsCog: {error}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra với lệnh `{ctx.command.name}`.")

def setup(bot: commands.Bot):
    bot.add_cog(ManageModeratorsCog(bot))
