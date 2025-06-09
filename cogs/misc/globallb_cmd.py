# bot/cogs/misc/globallb_cmd.py
import nextcord
from nextcord.ext import commands
import math
import logging
from core.utils import try_send, format_large_number
from core.icons import ICON_LEADERBOARD, ICON_INFO, ICON_ERROR, ICON_BANK_MAIN

logger = logging.getLogger(__name__)
ITEMS_PER_PAGE = 10

class GlobalLeaderboardView(nextcord.ui.View):
    # Class View không thay đổi logic, giữ nguyên
    def __init__(self, *, sorted_users_data: list, original_author: nextcord.User, bot_instance: commands.Bot):
        super().__init__(timeout=180)
        self.sorted_users_data = sorted_users_data
        self.original_author = original_author
        self.bot = bot_instance
        self.current_page = 1
        self.total_pages = math.ceil(len(self.sorted_users_data) / ITEMS_PER_PAGE) if ITEMS_PER_PAGE > 0 else 1
        self.message = None
        # ... (Toàn bộ phần còn lại của class View giữ nguyên) ...

class GlobalLeaderboardCog(commands.Cog, name="Global Leaderboard"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("GlobalLeaderboardCog (SQLite Ready) initialized.")

    @commands.command(name="globallb", aliases=["glb", "globaltop", "topglobal"])
    async def global_leaderboard(self, ctx: commands.Context):
        logger.info(f"Lệnh 'globallb' được gọi bởi {ctx.author.name}.")
        await ctx.message.add_reaction("⏳")
        
        sorted_users = self.bot.db.get_global_leaderboard()
        
        await ctx.message.remove_reaction("⏳", self.bot.user)

        if not sorted_users:
            await try_send(ctx, content=f"{ICON_INFO} Không có ai trên bảng xếp hạng toàn cục!")
            return

        view = GlobalLeaderboardView(sorted_users_data=sorted_users, original_author=ctx.author, bot_instance=self.bot)
        initial_embed = await view.generate_embed_for_current_page()
        
        try:
            sent_message = await ctx.send(embed=initial_embed, view=view)
            view.message = sent_message
        except nextcord.HTTPException:
            await ctx.send(f"{ICON_ERROR} Không thể hiển thị bảng xếp hạng lúc này.")

def setup(bot: commands.Bot):
    bot.add_cog(GlobalLeaderboardCog(bot))
