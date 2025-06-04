# bot/cogs/misc/leaderboard_cmd.py
import nextcord
from nextcord.ext import commands
import math # Để dùng math.ceil cho total_pages

from core.database import load_data
from core.utils import try_send # try_send vẫn dùng để gửi tin nhắn ban đầu
from core.config import CURRENCY_SYMBOL
from core.icons import ICON_LEADERBOARD, ICON_INFO, ICON_MONEY_BAG # Đảm bảo các icon này có trong core/icons.py

ITEMS_PER_PAGE = 10 # Có thể đặt ở config.py nếu muốn

# --- Lớp View cho Leaderboard ---
class LeaderboardView(nextcord.ui.View):
    def __init__(self, *, sorted_users_data: list, original_author: nextcord.User, bot_instance: commands.Bot):
        super().__init__(timeout=180) # View sẽ hết hạn sau 180 giây không tương tác
        self.sorted_users_data = sorted_users_data
        self.original_author = original_author
        self.bot = bot_instance # Cần bot instance để fetch_user
        
        self.current_page = 1
        self.total_pages = math.ceil(len(self.sorted_users_data) / ITEMS_PER_PAGE)
        self.message = None # Sẽ được gán sau khi tin nhắn đầu tiên được gửi

        # Khởi tạo các nút bấm
        self.first_page_button = nextcord.ui.Button(label="⏪ Về đầu", style=nextcord.ButtonStyle.blurple, custom_id="lb_first")
        self.prev_page_button = nextcord.ui.Button(label="◀️ Trước", style=nextcord.ButtonStyle.primary, custom_id="lb_prev")
        self.page_indicator_button = nextcord.ui.Button(label=f"Trang {self.current_page}/{self.total_pages}", style=nextcord.ButtonStyle.secondary, disabled=True, custom_id="lb_page_indicator") # Nút hiển thị trang, không bấm được
        self.next_page_button = nextcord.ui.Button(label="▶️ Sau", style=nextcord.ButtonStyle.primary, custom_id="lb_next")
        self.last_page_button = nextcord.ui.Button(label="⏩ Đến cuối", style=nextcord.ButtonStyle.blurple, custom_id="lb_last")

        # Gán callback cho các nút
        self.first_page_button.callback = self.go_to_first_page
        self.prev_page_button.callback = self.go_to_previous_page
        self.next_page_button.callback = self.go_to_next_page
        self.last_page_button.callback = self.go_to_last_page
        
        # Thêm các nút vào View
        self.add_item(self.first_page_button)
        self.add_item(self.prev_page_button)
        self.add_item(self.page_indicator_button)
        self.add_item(self.next_page_button)
        self.add_item(self.last_page_button)

        self._update_button_states()

    def _update_button_states(self):
        """Cập nhật trạng thái (enable/disable) của các nút dựa trên trang hiện tại."""
        self.page_indicator_button.label = f"Trang {self.current_page}/{self.total_pages}"
        
        if self.total_pages <= 1: # Nếu chỉ có 1 trang hoặc không có trang nào
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
        """Tạo Embed cho trang hiện tại."""
        start_index = (self.current_page - 1) * ITEMS_PER_PAGE
        end_index = start_index + ITEMS_PER_PAGE
        
        embed = nextcord.Embed(
            title=f"{ICON_LEADERBOARD} Bảng Xếp Hạng Giàu Nhất", # Bỏ tên server khỏi đây nếu footer có
            color=nextcord.Color.gold()
        )
        description_parts = []
        rank = start_index + 1

        if not self.sorted_users_data:
             embed.description = f"{ICON_INFO} Không có ai trên bảng xếp hạng."
        else:
            for user_id_str, user_data_dict in self.sorted_users_data[start_index:end_index]:
                try:
                    user_obj = await self.bot.fetch_user(int(user_id_str))
                    total_wealth = user_data_dict.get('balance', 0) + user_data_dict.get('bank_balance', 0)
                    description_parts.append(f"{rank}. {user_obj.name} - {ICON_MONEY_BAG} **{total_wealth:,}** {CURRENCY_SYMBOL}")
                    rank += 1
                except (nextcord.NotFound, ValueError, KeyError) as e:
                    print(f"Leaderboard View: Không thể fetch/xử lý user ID {user_id_str}. Lỗi: {e}")
                    description_parts.append(f"{rank}. *Không thể tải thông tin user ID: {user_id_str}*")
                    rank +=1
                    continue
            
            if not description_parts:
                embed.description = f"{ICON_INFO} Không có dữ liệu cho trang này."
            else:
                embed.description = "\n".join(description_parts)

        embed.set_footer(text=f"Yêu cầu bởi {self.original_author.display_name}") # Hiển thị người yêu cầu gốc
        return embed

    async def update_message(self, interaction: nextcord.Interaction):
        """Cập nhật tin nhắn với embed và view mới."""
        self._update_button_states()
        new_embed = await self.generate_embed_for_current_page()
        await interaction.response.edit_message(embed=new_embed, view=self)

    async def interaction_check(self, interaction: nextcord.Interaction) -> bool:
        """Kiểm tra xem người tương tác có phải là người gọi lệnh gốc không."""
        if interaction.user.id != self.original_author.id:
            await interaction.response.send_message(f"{ICON_ERROR} Bạn không phải là người yêu cầu bảng xếp hạng này!", ephemeral=True)
            return False
        return True

    # --- Callbacks cho các nút ---
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
        """Xử lý khi View hết hạn (không có tương tác)."""
        if self.message: # Đảm bảo self.message đã được gán
            for item in self.children:
                item.disabled = True # Vô hiệu hóa tất cả các nút
            try:
                # Cố gắng chỉnh sửa tin nhắn cuối cùng để hiển thị các nút bị vô hiệu hóa
                # Không cần embed mới vì nội dung không đổi, chỉ có view (nút) thay đổi trạng thái
                current_embed = self.message.embeds[0] if self.message.embeds else None
                await self.message.edit(embed=current_embed, view=self) 
            except nextcord.NotFound:
                print("Leaderboard View Timeout: Không tìm thấy tin nhắn để edit (có thể đã bị xóa).")
            except nextcord.HTTPException as e:
                print(f"Leaderboard View Timeout: Lỗi HTTP khi edit tin nhắn: {e}")


# --- Cog chính chứa lệnh leaderboard ---
class LeaderboardCommandCog(commands.Cog, name="Leaderboard Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='leaderboard', aliases=['lb', 'top'])
    async def leaderboard(self, ctx: commands.Context): # Bỏ tham số page
        """Hiển thị bảng xếp hạng những người giàu nhất server với phân trang bằng nút bấm."""
        data = load_data()
        guild_id = str(ctx.guild.id)

        if guild_id not in data or not data[guild_id] or all(key == "config" for key in data[guild_id]):
            await try_send(ctx, content=f"{ICON_INFO} Chưa có ai trên bảng xếp hạng của server này!")
            return

        guild_user_data = {
            uid: udata for uid, udata in data[guild_id].items()
            if uid != "config" and isinstance(udata, dict) and ("balance" in udata or "bank_balance" in udata)
        }
        
        if not guild_user_data: 
            await try_send(ctx, content=f"{ICON_INFO} Chưa có ai trên bảng xếp hạng của server này!")
            return
            
        sorted_users = sorted(
            guild_user_data.items(), 
            key=lambda item: item[1].get('balance', 0) + item[1].get('bank_balance', 0),
            reverse=True 
        )

        if not sorted_users:
            await try_send(ctx, content=f"{ICON_INFO} Không có ai để xếp hạng!")
            return

        # Khởi tạo View
        view = LeaderboardView(sorted_users_data=sorted_users, original_author=ctx.author, bot_instance=self.bot)
        
        # Tạo embed cho trang đầu tiên
        initial_embed = await view.generate_embed_for_current_page() # Trang 1 là mặc định
        

        try:
            sent_message = await ctx.send(embed=initial_embed, view=view)
            view.message = sent_message # Gán tin nhắn đã gửi cho view để xử lý timeout
        except nextcord.HTTPException as e:
            print(f"Lỗi khi gửi tin nhắn leaderboard ban đầu: {e}")
            await ctx.send(f"{ICON_ERROR} Không thể hiển thị bảng xếp hạng lúc này.")


def setup(bot: commands.Bot):
    bot.add_cog(LeaderboardCommandCog(bot))
