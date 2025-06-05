# bot/cogs/moderation/access_test_cmd.py
import nextcord
from nextcord.ext import commands
import logging

# Import hàm check và các icon cần thiết
from core.utils import is_bot_moderator # Hàm check quyền moderator chúng ta vừa tạo
from core.icons import ICON_SUCCESS, ICON_ERROR, ICON_INFO, ICON_ADMIN # Đảm bảo các icon này có trong core/icons.py

logger = logging.getLogger(__name__)

class ModeratorAccessTestCog(commands.Cog, name="Moderator Access Test"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info(f"{ICON_INFO} ModeratorAccessTestCog initialized.")

    @commands.command(name="mod_ping")
    @commands.check(is_bot_moderator) # <<< SỬ DỤNG HÀM CHECK Ở ĐÂY
    async def mod_ping_command(self, ctx: commands.Context):
        """
        (Moderator/Owner Only) Một lệnh ping đơn giản để kiểm tra quyền moderator.
        """
        logger.info(f"MODERATOR ACTION: {ctx.author.display_name} ({ctx.author.id}) tại guild '{ctx.guild.name}' ({ctx.guild.id}) đã sử dụng 'mod_ping' thành công.")
        await ctx.send(f"{ICON_ADMIN} {ctx.author.mention}, bạn có quyền Moderator/Owner! Ping thành công!")

    @mod_ping_command.error # Xử lý lỗi riêng cho lệnh này
    async def mod_ping_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CheckFailure): # Lỗi khi check is_bot_moderator thất bại
            logger.warning(f"User {ctx.author.name} ({ctx.author.id}) không có quyền dùng 'mod_ping' tại guild '{ctx.guild.name}' ({ctx.guild.id}). Lỗi: {error}")
            await ctx.send(f"{ICON_ERROR} Bạn không có đủ quyền (Moderator/Owner) để sử dụng lệnh này.")
        else:
            logger.error(f"Lỗi không xác định trong lệnh 'mod_ping' bởi {ctx.author.name} tại guild '{ctx.guild.name}' ({ctx.guild.id}):", exc_info=True)
            await ctx.send(f"{ICON_ERROR} Đã có lỗi xảy ra với lệnh `mod_ping`.")

# Hàm setup để bot có thể load cog này
def setup(bot: commands.Bot):
    bot.add_cog(ModeratorAccessTestCog(bot))
