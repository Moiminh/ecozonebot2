import nextcord
from nextcord.ext import commands
import math
import logging

from core.database import load_economy_data
from core.utils import try_send, format_large_number
from core.config import CURRENCY_SYMBOL
from core.icons import ICON_LEADERBOARD, ICON_INFO, ICON_ERROR

ITEMS_PER_PAGE = 10
logger = logging.getLogger(__name__)

class GlobalLeaderboardView(nextcord.ui.View):
    def __init__(self, *, sorted_users_data: list, original_author: nextcord.User, bot_instance: commands.Bot):
        super().__init__(timeout=180)
        self.sorted_users_data = sorted_users_data
        self.original_author = original_author
        self.bot = bot_instance
        
        self.current_page = 1
        self.total_pages = math.ceil(len(self.sorted_users_data) / ITEMS_PER_PAGE)
        self.message = None

        self.first_page_button = nextcord.ui.Button(label="⏪ Về đầu", style=nextcord.ButtonStyle.blurple, custom_id="glb_first")
        self.prev_page_button = nextcord.ui.Button(label="◀️ Trước", style=nextcord.ButtonStyle.primary, custom_id="glb_prev")
        self.page_indicator_button = nextcord.ui.Button(label=f"Trang {self.current_page}/{self.total_pages}", style=nextcord.ButtonStyle.secondary, disabled=True, custom_id="glb_page_indicator")
        self.next_page_button = nextcord.ui.Button(label="▶️ Sau", style=nextcord.ButtonStyle.primary, custom_id="glb_next")
        self.last_page_button = nextcord.ui.Button(label="⏩ Đến cuối", style=nextcord.ButtonStyle.blurple, custom_id="glb_last")

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
        is_last_page = self.current_page == self.total_pages
        
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
            title=f"{ICON_LEADERBOARD} Bảng Xếp Hạng Toàn Cục Ecoworld",
            color=nextcord.Color.purple()
        )
        description_parts = []
        rank_display = start_index + 1

        if not self.sorted_users_data:
             embed.description = f"{ICON_INFO} Chưa có ai trên bảng xếp hạng toàn cục."
        else:
            for user_id_str, total_wealth in self.sorted_users_data[start_index:end_index]:
                try:
                    user_obj = await self.bot.fetch_user(int(user_id_str))
                    username = str(user_obj)
                    if len(username) > 25:
                        username = username[:22] + "..."
                    
                    formatted_wealth = format_large_number(total_wealth)
                    description_parts.append(f"{rank_display}. `{username}` - **{formatted_wealth}** {CURRENCY_SYMBOL}")
                    rank_display += 1
                except nextcord.NotFound:
                    logger.warning(f"Global LB: Không tìm thấy user ID {user_id_str}.")
                    description_parts.append(f"{rank_display}. `User không tồn tại (ID: {user_id_str})`")
                    rank_display += 1
                except Exception as e:
                    logger.error(f"Global LB: Lỗi khi fetch user ID {user_id_str}: {e}", exc_info=True)
                    description_parts.append(f"{rank_display}. `Lỗi tải user (ID: {user_id_str})`")
                    rank_display += 1
            
            embed.description = "\n".join(description_parts)

        embed.set_footer(text=f"Yêu cầu bởi {self.original_author.display_name}")
        return embed

    async def update_message(self, interaction: nextcord.Interaction):
        logger.info(f"User {interaction.user.display_name} ({interaction.user.id}) xem trang {self.current_page}/{self.total_pages} của bảng xếp hạng toàn cục.")
        self._update_button_states()
        new_embed = await self.generate_embed_for_current_page()
        await interaction.response.edit_message(embed=new_embed, view=self)

    async def interaction_check(self, interaction: nextcord.Interaction) -> bool:
        if interaction.user.id != self.original_author.id:
            await interaction.response.send_message(f"{ICON_ERROR} Bạn không phải là người yêu cầu bảng xếp hạng này!", ephemeral=True)
            return False
        return True

    async def go_to_first_page(self, interaction: nextcord.Interaction):
        self.current_page = 1
        await self.update_message(interaction)
    async def go_to_previous_page(self, interaction: nextcord.Interaction):
        if self.current_page > 1: self.current_page -= 1
        await self.update_message(interaction)
    async def go_to_next_page(self, interaction: nextcord.Interaction):
        if self.current_page < self.total_pages: self.current_page += 1
        await self.update_message(interaction)
    async def go_to_last_page(self, interaction: nextcord.Interaction):
        self.current_page = self.total_pages
        await self.update_message(interaction)
        
    async def on_timeout(self):
        if self.message:
            for item in self.children: item.disabled = True
            try:
                current_embed = self.message.embeds[0] if self.message.embeds else None
                await self.message.edit(embed=current_embed, view=self) 
            except Exception as e: logger.warning(f"Global LB Timeout: Lỗi khi vô hiệu hóa nút: {e}")

class GlobalLeaderboardCog(commands.Cog, name="Global Leaderboard"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info(f"{ICON_INFO} GlobalLeaderboardCog initialized.")

    @commands.command(name="globallb", aliases=["glb", "globaltop", "topglobal"])
    async def global_leaderboard(self, ctx: commands.Context):
        logger.info(f"Lệnh 'globallb' được gọi bởi {ctx.author.name} ({ctx.author.id}) tại guild '{ctx.guild.name if ctx.guild else 'DM'}'.")
        
        await ctx.message.add_reaction("⏳")
        
        economy_data = load_economy_data()
        all_users_data = economy_data.get("users", {})

        if not all_users_data:
            await try_send(ctx, content=f"{ICON_INFO} Chưa có người dùng nào trong hệ thống để xếp hạng.")
            return

        user_wealth_list = []
        for user_id, user_profile in all_users_data.items():
            if not isinstance(user_profile, dict): continue
            
            global_bal = user_profile.get("global_balance", 0)
            total_bank_bal = sum(user_profile.get("bank_accounts", {}).values())
            total_wealth = global_bal + total_bank_bal
            
            user_wealth_list.append((user_id, total_wealth))

        sorted_users = sorted(user_wealth_list, key=lambda x: x[1], reverse=True)
        
        await ctx.message.remove_reaction("⏳", self.bot.user)

        if not sorted_users:
            await try_send(ctx, content=f"{ICON_INFO} Không có ai để xếp hạng!")
            return

        view = GlobalLeaderboardView(sorted_users_data=sorted_users, original_author=ctx.author, bot_instance=self.bot)
        initial_embed = await view.generate_embed_for_current_page()
        
        try:
            sent_message = await ctx.send(embed=initial_embed, view=view)
            view.message = sent_message
        except nextcord.HTTPException as e:
            logger.error(f"Lỗi khi gửi tin nhắn globallb ban đầu cho {ctx.author.name}: {e}", exc_info=True)
            await ctx.send(f"{ICON_ERROR} Không thể hiển thị bảng xếp hạng toàn cục lúc này.")

def setup(bot: commands.Bot):
    bot.add_cog(GlobalLeaderboardCog(bot))
