# bot/cogs/misc/leaderboard_cmd.py
import nextcord
from nextcord.ext import commands
import math
import logging
from core.utils import try_send, format_large_number
from core.icons import ICON_LEADERBOARD, ICON_INFO, ICON_MONEY_BAG, ICON_PROFILE, ICON_ERROR

logger = logging.getLogger(__name__)
ITEMS_PER_PAGE = 10

class LeaderboardView(nextcord.ui.View):
    # Class View không thay đổi logic, giữ nguyên
    def __init__(self, *, sorted_users_data: list, original_author: nextcord.User, bot_instance: commands.Bot, guild_name: str):
        super().__init__(timeout=180)
        self.sorted_users_data = sorted_users_data
        self.original_author = original_author
        self.bot = bot_instance
        self.guild_name = guild_name
        self.current_page = 1
        self.total_pages = math.ceil(len(self.sorted_users_data) / ITEMS_PER_PAGE) if ITEMS_PER_PAGE > 0 else 1
        # ... (Toàn bộ phần còn lại của class View giữ nguyên) ...

class LeaderboardCommandCog(commands.Cog, name="Leaderboard Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug("LeaderboardCommandCog (SQLite Ready) initialized.")

    @commands.command(name='leaderboard', aliases=['lb', 'top', 'serverlb'])
    @commands.guild_only()
    async def server_leaderboard(self, ctx: commands.Context):
        logger.info(f"Lệnh 'leaderboard' được gọi bởi {ctx.author.name} tại guild '{ctx.guild.name}'.")
        await ctx.message.add_reaction("⏳")
        
        sorted_users = self.bot.db.get_server_leaderboard(ctx.guild.id)
        
        await ctx.message.remove_reaction("⏳", self.bot.user)

        if not sorted_users:
            await try_send(ctx, content=f"{ICON_INFO} Không có ai trong server này có dữ liệu để xếp hạng!")
            return

        author_local_wealth = 0
        author_rank = "N/A"
        for i, user_row in enumerate(sorted_users):
            if ctx.author.id == user_row['user_id']:
                author_rank = f"#{i + 1}"
                author_local_wealth = user_row['total_local_wealth']
                break
        
        user_rank_message = f"{ICON_PROFILE} {ctx.author.mention}, bạn đang ở **hạng {author_rank}** trên server này với **{format_large_number(author_local_wealth)}** tại Ví Local."
        await try_send(ctx, content=user_rank_message)

        view = LeaderboardView(sorted_users_data=sorted_users, original_author=ctx.author, bot_instance=self.bot, guild_name=str(ctx.guild.name))
        initial_embed = await view.generate_embed_for_current_page()
        
        try:
            sent_message = await ctx.send(embed=initial_embed, view=view)
            view.message = sent_message
        except nextcord.HTTPException:
            await ctx.send(f"{ICON_ERROR} Không thể hiển thị bảng xếp hạng lúc này.")

def setup(bot: commands.Bot):
    bot.add_cog(LeaderboardCommandCog(bot))
