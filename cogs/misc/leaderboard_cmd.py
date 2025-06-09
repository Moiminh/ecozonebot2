# bot/cogs/misc/leaderboard_cmd.py
import nextcord
from nextcord.ext import commands
import math
import logging

# [SỬA] Import các hàm và hằng số cần thiết từ core
from core.database import get_or_create_global_user_profile
from core.utils import try_send, format_large_number
from core.icons import ICON_LEADERBOARD, ICON_INFO, ICON_MONEY_BAG, ICON_PROFILE, ICON_ERROR, ICON_WARNING

logger = logging.getLogger(__name__)

ITEMS_PER_PAGE = 10

class LeaderboardView(nextcord.ui.View):
    # ... (Class View không thay đổi logic, giữ nguyên) ...
    def __init__(self, *, sorted_users_data: list, original_author: nextcord.User, bot_instance: commands.Bot, guild_name: str):
        super().__init__(timeout=180)
        self.sorted_users_data = sorted_users_data
        self.original_author = original_author
        self.bot = bot_instance
        self.guild_name = guild_name
        self.current_page = 1
        self.total_pages = math.ceil(len(self.sorted_users_data) / ITEMS_PER_PAGE) if ITEMS_PER_PAGE > 0 else 1
        self.message = None

        self.first_page_button = nextcord.ui.Button(label="⏪", style=nextcord.ButtonStyle.blurple)
        self.prev_page_button = nextcord.ui.Button(label="◀️", style=nextcord.ButtonStyle.primary)
        self.page_indicator_button = nextcord.ui.Button(style=nextcord.ButtonStyle.secondary, disabled=True)
        self.next_page_button = nextcord.ui.Button(label="▶️", style=nextcord.ButtonStyle.primary)
        self.last_page_button = nextcord.ui.Button(label="⏩", style=nextcord.ButtonStyle.blurple)

        self.first_page_button.callback = self.go_to_first_page
        self.prev_page_button.callback = self.go_to_previous_page
        self.next_page_button.callback = self.go_to_next_page
        self.last_page_button.callback = self.go_to_last_page
        
        self.add_item(self.first_page_button)
        self.add_item(self.prev_page_button)
        self.add_item(self.page_indicator_button)
        self.add_item(self.next_page_button)
        self.add_item(self.last_page_button)
        self._update_button_states()

    def _update_button_states(self):
        self.page_indicator_button.label = f"Trang {self.current_page}/{self.total_pages}"
        is_first_page = self.current_page == 1
        is_last_page = self.current_page >= self.total_pages
        
        self.first_page_button.disabled = is_first_page
        self.prev_page_button.disabled = is_first_page
        self.next_page_button.disabled = is_last_page
        self.last_page_button.disabled = is_last_page
        if self.total_pages <= 1:
            for item in self.children: item.disabled = True

    async def generate_embed_for_current_page(self) -> nextcord.Embed:
        start_index = (self.current_page - 1) * ITEMS_PER_PAGE
        end_index = start_index + ITEMS_PER_PAGE
        
        embed = nextcord.Embed(
            title=f"{ICON_LEADERBOARD} Bảng Xếp Hạng Server - {self.guild_name}",
            color=nextcord.Color.gold()
        )
        description_parts = []
        rank_display = start_index + 1

        for user_id_str, local_wealth in self.sorted_users_data[start_index:end_index]:
            try:
                user_obj = await self.bot.fetch_user(int(user_id_str))
                description_parts.append(f"{rank_display}. {user_obj.name} - {ICON_MONEY_BAG} **{format_large_number(local_wealth)}**")
                rank_display += 1
            except nextcord.NotFound:
                description_parts.append(f"{rank_display}. *User không tồn tại (ID: {user_id_str})*")
                rank_display += 1
            except Exception as e:
                logger.error(f"Leaderboard View: Lỗi khi fetch user ID {user_id_str}:", exc_info=True)
                description_parts.append(f"{rank_display}. *Lỗi tải user ID: {user_id_str}*")
                rank_display += 1

        if not description_parts:
             embed.description = f"{ICON_INFO} Không có dữ liệu cho trang này."
        else:
            embed.description = "\n".join(description_parts)

        embed.set_footer(text=f"Xếp hạng dựa trên tổng Ví Local. Yêu cầu bởi {self.original_author.display_name}")
        return embed

    async def update_message(self, interaction: nextcord.Interaction):
        self._update_button_states()
        new_embed = await self.generate_embed_for_current_page()
        await interaction.response.edit_message(embed=new_embed, view=self)

    async def interaction_check(self, interaction: nextcord.Interaction) -> bool:
        if interaction.user.id != self.original_author.id:
            await interaction.response.send_message(f"{ICON_ERROR} Bạn không phải là người yêu cầu bảng xếp hạng này!", ephemeral=True)
            return False
        return True

    async def go_to_first_page(self, interaction: nextcord.Interaction): await self.go_to_page(interaction, 1)
    async def go_to_previous_page(self, interaction: nextcord.Interaction): await self.go_to_page(interaction, self.current_page - 1)
    async def go_to_next_page(self, interaction: nextcord.Interaction): await self.go_to_page(interaction, self.current_page + 1)
    async def go_to_last_page(self, interaction: nextcord.Interaction): await self.go_to_page(interaction, self.total_pages)
    
    async def go_to_page(self, interaction: nextcord.Interaction, page_num: int):
        self.current_page = max(1, min(page_num, self.total_pages))
        logger.info(f"User {interaction.user.display_name} xem trang {self.current_page}/{self.total_pages} của leaderboard server '{self.guild_name}'.")
        await self.update_message(interaction)
        
    async def on_timeout(self):
        if self.message:
            for item in self.children: item.disabled = True
            try:
                current_embed = self.message.embeds[0] if self.message.embeds else None
                await self.message.edit(embed=current_embed, view=self) 
            except Exception: pass

class LeaderboardCommandCog(commands.Cog, name="Leaderboard Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug("LeaderboardCommandCog (Refactored) initialized.")

    @commands.command(name='leaderboard', aliases=['lb', 'top', 'serverlb'])
    @commands.guild_only()
    async def server_leaderboard(self, ctx: commands.Context):
        logger.info(f"Lệnh 'leaderboard' (server) được gọi bởi {ctx.author.name} tại guild '{ctx.guild.name}'.")
        await ctx.message.add_reaction("⏳")
        
        # [SỬA] Sử dụng cache của bot
        economy_data = self.bot.economy_data
        all_users_data = economy_data.get("users", {})
        
        if not all_users_data:
            await try_send(ctx, content=f"{ICON_INFO} Chưa có người dùng nào trong hệ thống để xếp hạng.")
            return

        guild_member_ids = {str(member.id) for member in ctx.guild.members}
        user_wealth_list = []
        for user_id, user_profile in all_users_data.items():
            if user_id in guild_member_ids:
                if isinstance(user_profile, dict):
                    # Không cần get_or_create vì chỉ đọc dữ liệu
                    server_data = user_profile.get("server_data", {}).get(str(ctx.guild.id))
                    if server_data and isinstance(server_data.get("local_balance"), dict):
                        local_balance = server_data.get("local_balance", {})
                        total_local_wealth = local_balance.get("earned", 0) + local_balance.get("adadd", 0)
                        user_wealth_list.append((user_id, total_local_wealth))

        sorted_users = sorted(user_wealth_list, key=lambda x: x[1], reverse=True)
        
        await ctx.message.remove_reaction("⏳", self.bot.user)

        if not sorted_users:
            await try_send(ctx, content=f"{ICON_INFO} Không có ai trong server này có dữ liệu Ví Local để xếp hạng!")
            return

        author_local_wealth = 0
        author_rank = "N/A"
        for i, (user_id, wealth) in enumerate(sorted_users):
            if str(ctx.author.id) == user_id:
                author_rank = f"#{i + 1}"
                author_local_wealth = wealth
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
