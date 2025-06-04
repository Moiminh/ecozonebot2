# bot/cogs/misc/leaderboard_cmd.py
import nextcord
from nextcord.ext import commands
import math 

from core.database import load_data
from core.utils import try_send 
from core.config import CURRENCY_SYMBOL
from core.icons import ICON_LEADERBOARD, ICON_INFO, ICON_MONEY_BAG, ICON_PROFILE # Thêm ICON_PROFILE nếu muốn

ITEMS_PER_PAGE = 10

# --- Lớp LeaderboardView (Giữ nguyên như phiên bản có nút bấm) ---
class LeaderboardView(nextcord.ui.View):
    def __init__(self, *, sorted_users_data: list, original_author: nextcord.User, bot_instance: commands.Bot):
        super().__init__(timeout=180) 
        self.sorted_users_data = sorted_users_data
        self.original_author = original_author
        self.bot = bot_instance
        
        self.current_page = 1
        self.total_pages = math.ceil(len(self.sorted_users_data) / ITEMS_PER_PAGE)
        self.message = None 

        self.first_page_button = nextcord.ui.Button(label="⏪ Về đầu", style=nextcord.ButtonStyle.blurple, custom_id="lb_first")
        self.prev_page_button = nextcord.ui.Button(label="◀️ Trước", style=nextcord.ButtonStyle.primary, custom_id="lb_prev")
        self.page_indicator_button = nextcord.ui.Button(label=f"Trang {self.current_page}/{self.total_pages}", style=nextcord.ButtonStyle.secondary, disabled=True, custom_id="lb_page_indicator")
        self.next_page_button = nextcord.ui.Button(label="▶️ Sau", style=nextcord.ButtonStyle.primary, custom_id="lb_next")
        self.last_page_button = nextcord.ui.Button(label="⏩ Đến cuối", style=nextcord.ButtonStyle.blurple, custom_id="lb_last")

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
        if self.total_pages <= 1:
            self.first_page_button.disabled = True
            self.prev_page_button.disabled = True
            self.next_page_button.disabled = True
            self.last_page_button.disabled = True
        else:
            self.first_page_button.disabled = (self.current_page == 1)
            self.prev_page_button.disabled = (self.current_page == 1)
            self.next_page_button.disabled = (self.current_page == self.total_pages)
            self.last_page_button.disabled = (self.current_page == self.total_pages)

    async def generate_embed_for_current_page(self) -> nextcord.Embed:
        start_index = (self.current_page - 1) * ITEMS_PER_PAGE
        end_index = start_index + ITEMS_PER_PAGE
        
        embed = nextcord.Embed(
            title=f"{ICON_LEADERBOARD} Bảng Xếp Hạng Giàu Nhất",
            color=nextcord.Color.gold()
        )
        description_parts = []
        rank_display = start_index + 1

        if not self.sorted_users_data:
             embed.description = f"{ICON_INFO} Không có ai trên bảng xếp hạng."
        else:
            for user_id_str, user_data_dict in self.sorted_users_data[start_index:end_index]:
                try:
                    user_obj = await self.bot.fetch_user(int(user_id_str))
                    total_wealth = user_data_dict.get('balance', 0) + user_data_dict.get('bank_balance', 0)
                    description_parts.append(f"{rank_display}. {user_obj.name} - {ICON_MONEY_BAG} **{total_wealth:,}** {CURRENCY_SYMBOL}")
                    rank_display += 1
                except (nextcord.NotFound, ValueError, KeyError) as e:
                    print(f"Leaderboard View: Không thể fetch/xử lý user ID {user_id_str}. Lỗi: {e}")
                    description_parts.append(f"{rank_display}. *Không thể tải thông tin user ID: {user_id_str}*")
                    rank_display +=1
                    continue
            
            if not description_parts:
                embed.description = f"{ICON_INFO} Không có dữ liệu cho trang này."
            else:
                embed.description = "\n".join(description_parts)

        embed.set_footer(text=f"Yêu cầu bởi {self.original_author.display_name}")
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

    async def go_to_first_page(self, interaction: nextcord.Interaction):
        self.current_page = 1
        await self.update_message(interaction)

    async def go_to_previous_page(self, interaction: nextcord.Interaction):
        if self.current_page > 1:
            self.current_page -= 1
        await self.update_message(interaction)

    async def go_to_next_page(self, interaction: nextcord.Interaction):
        if self.current_page < self.total_pages:
            self.current_page += 1
        await self.update_message(interaction)

    async def go_to_last_page(self, interaction: nextcord.Interaction):
        self.current_page = self.total_pages
        await self.update_message(interaction)
        
    async def on_timeout(self):
        if self.message:
            for item in self.children:
                item.disabled = True
            try:
                current_embed = self.message.embeds[0] if self.message.embeds else None
                await self.message.edit(embed=current_embed, view=self) 
            except nextcord.NotFound:
                print("Leaderboard View Timeout: Không tìm thấy tin nhắn để edit.")
            except nextcord.HTTPException as e:
                print(f"Leaderboard View Timeout: Lỗi HTTP khi edit tin nhắn: {e}")


# --- Cog chính chứa lệnh leaderboard ---
class LeaderboardCommandCog(commands.Cog, name="Leaderboard Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='leaderboard', aliases=['lb', 'top'])
    async def leaderboard(self, ctx: commands.Context):
        """Hiển thị bảng xếp hạng những người giàu nhất server và thứ hạng của bạn."""
        data = load_data()
        guild_id = str(ctx.guild.id)

        if guild_id not in data or not data[guild_id] or all(key == "config" for key in data[guild_id]):
            await try_send(ctx, content=f"{ICON_INFO} Hiện tại chưa có ai trên bảng xếp hạng của server này!")
            return

        guild_user_data = {
            uid: udata for uid, udata in data[guild_id].items()
            if uid != "config" and isinstance(udata, dict) and ("balance" in udata or "bank_balance" in udata)
        }
        
        if not guild_user_data: 
            await try_send(ctx, content=f"{ICON_INFO} Hiện tại chưa có ai trên bảng xếp hạng của server này!")
            return
            
        sorted_users_with_data = sorted( # Đổi tên biến cho rõ ràng
            guild_user_data.items(), 
            key=lambda item: item[1].get('balance', 0) + item[1].get('bank_balance', 0),
            reverse=True 
        )

        if not sorted_users_with_data: # Kiểm tra lại sau khi sắp xếp
            await try_send(ctx, content=f"{ICON_INFO} Không có ai để xếp hạng!")
            return

        # --- PHẦN MỚI: Tìm và thông báo thứ hạng của người dùng ---
        user_rank_message = None
        author_id_str = str(ctx.author.id)
        
        for i, (user_id_str, user_data_dict) in enumerate(sorted_users_with_data):
            if user_id_str == author_id_str:
                user_rank = i + 1
                user_total_wealth = user_data_dict.get('balance', 0) + user_data_dict.get('bank_balance', 0)
                user_rank_message = f"{ICON_PROFILE} {ctx.author.mention}, bạn đang ở **hạng #{user_rank}** với tổng tài sản là **{user_total_wealth:,}** {CURRENCY_SYMBOL}."
                break 
        
        if user_rank_message is None: # Nếu không tìm thấy người dùng trong bảng xếp hạng (ví dụ: chưa có tiền)
            user_rank_message = f"{ICON_INFO} {ctx.author.mention}, bạn hiện chưa có mặt trên bảng xếp hạng. Hãy cố gắng kiếm thêm {CURRENCY_SYMBOL} nhé!"
        
        await try_send(ctx, content=user_rank_message) # Gửi thông báo thứ hạng
        # ---------------------------------------------------------

        # Khởi tạo View
        view = LeaderboardView(sorted_users_data=sorted_users_with_data, original_author=ctx.author, bot_instance=self.bot)
        
        initial_embed = await view.generate_embed_for_current_page()
        
        try:
            sent_message = await ctx.send(embed=initial_embed, view=view)
            view.message = sent_message 
        except nextcord.HTTPException as e:
            print(f"Lỗi khi gửi tin nhắn leaderboard ban đầu: {e}")
            await ctx.send(f"{ICON_ERROR} Không thể hiển thị bảng xếp hạng lúc này.")


def setup(bot: commands.Bot):
    bot.add_cog(LeaderboardCommandCog(bot))
