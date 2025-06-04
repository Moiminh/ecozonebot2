# bot/cogs/misc/leaderboard_cmd.py
import nextcord
from nextcord.ext import commands
import math 
import logging # <<< THÊM IMPORT NÀY

from core.database import load_data
from core.utils import try_send 
from core.config import CURRENCY_SYMBOL
from core.icons import ICON_LEADERBOARD, ICON_INFO, ICON_MONEY_BAG, ICON_PROFILE, ICON_ERROR # Đảm bảo có ICON_ERROR

logger = logging.getLogger(__name__) # <<< LẤY LOGGER CHO MODULE NÀY

ITEMS_PER_PAGE = 10

class LeaderboardView(nextcord.ui.View):
    def __init__(self, *, sorted_users_data: list, original_author: nextcord.User, bot_instance: commands.Bot):
        super().__init__(timeout=180) 
        self.sorted_users_data = sorted_users_data
        self.original_author = original_author
        self.bot = bot_instance
        
        self.current_page = 1
        self.total_pages = math.ceil(len(self.sorted_users_data) / ITEMS_PER_PAGE)
        self.message = None 
        logger.debug(f"LeaderboardView initialized for {original_author.name}. Total pages: {self.total_pages}")

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
        logger.debug(f"Leaderboard buttons updated. Page: {self.current_page}/{self.total_pages}. Prev: {not self.prev_page_button.disabled}, Next: {not self.next_page_button.disabled}")

    async def generate_embed_for_current_page(self) -> nextcord.Embed:
        logger.debug(f"Generating leaderboard embed for page {self.current_page}")
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
                    logger.warning(f"Leaderboard View: Không thể fetch/xử lý user ID {user_id_str} cho trang {self.current_page}. Lỗi: {e}")
                    description_parts.append(f"{rank_display}. *{ICON_WARNING} Không thể tải thông tin user ID: {user_id_str}*")
                    rank_display +=1
                    continue
            
            if not description_parts:
                embed.description = f"{ICON_INFO} Không có dữ liệu cho trang này."
            else:
                embed.description = "\n".join(description_parts)

        embed.set_footer(text=f"Yêu cầu bởi {self.original_author.display_name}")
        return embed

    async def update_message(self, interaction: nextcord.Interaction):
        logger.debug(f"Leaderboard updating message to page {self.current_page} for {interaction.user.name}")
        self._update_button_states()
        new_embed = await self.generate_embed_for_current_page()
        try:
            await interaction.response.edit_message(embed=new_embed, view=self)
            logger.debug(f"Leaderboard message edited successfully for page {self.current_page}.")
        except nextcord.HTTPException as e:
            logger.error(f"Lỗi HTTP khi edit leaderboard message: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Lỗi không xác định khi edit leaderboard message: {e}", exc_info=True)


    async def interaction_check(self, interaction: nextcord.Interaction) -> bool:
        if interaction.user.id != self.original_author.id:
            logger.warning(f"User {interaction.user.id} ({interaction.user.name}) cố gắng tương tác với leaderboard của {self.original_author.id}")
            await interaction.response.send_message(f"{ICON_ERROR} Bạn không phải là người yêu cầu bảng xếp hạng này!", ephemeral=True)
            return False
        return True

    async def go_to_first_page(self, interaction: nextcord.Interaction):
        logger.debug(f"Leaderboard: {interaction.user.name} bấm nút 'Về đầu'. Trang hiện tại: {self.current_page}")
        self.current_page = 1
        await self.update_message(interaction)

    async def go_to_previous_page(self, interaction: nextcord.Interaction):
        logger.debug(f"Leaderboard: {interaction.user.name} bấm nút 'Trước'. Trang hiện tại: {self.current_page}")
        if self.current_page > 1:
            self.current_page -= 1
        await self.update_message(interaction)

    async def go_to_next_page(self, interaction: nextcord.Interaction):
        logger.debug(f"Leaderboard: {interaction.user.name} bấm nút 'Sau'. Trang hiện tại: {self.current_page}")
        if self.current_page < self.total_pages:
            self.current_page += 1
        await self.update_message(interaction)

    async def go_to_last_page(self, interaction: nextcord.Interaction):
        logger.debug(f"Leaderboard: {interaction.user.name} bấm nút 'Đến cuối'. Trang hiện tại: {self.current_page}")
        self.current_page = self.total_pages
        await self.update_message(interaction)
        
    async def on_timeout(self):
        logger.info(f"Leaderboard View cho {self.original_author.name} đã hết hạn (timeout).")
        if self.message: 
            for item in self.children:
                item.disabled = True 
            try:
                current_embed = self.message.embeds[0] if self.message.embeds else None
                await self.message.edit(embed=current_embed, view=self) 
                logger.debug("Đã vô hiệu hóa các nút trên Leaderboard View do timeout.")
            except nextcord.NotFound:
                logger.warning("Leaderboard View Timeout: Không tìm thấy tin nhắn để edit (có thể đã bị xóa).")
            except nextcord.HTTPException as e:
                logger.error(f"Leaderboard View Timeout: Lỗi HTTP khi edit tin nhắn: {e}", exc_info=True)


class LeaderboardCommandCog(commands.Cog, name="Leaderboard Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug("LeaderboardCommandCog initialized.")

    @commands.command(name='leaderboard', aliases=['lb', 'top'])
    async def leaderboard(self, ctx: commands.Context):
        logger.debug(f"Lệnh 'leaderboard' được gọi bởi {ctx.author.name} (ID: {ctx.author.id}) tại guild {ctx.guild.id}.")
        data = load_data()
        guild_id = str(ctx.guild.id)

        if guild_id not in data or not data[guild_id] or all(key == "config" for key in data[guild_id]):
            logger.info(f"Không có dữ liệu leaderboard cho guild {guild_id}.")
            await try_send(ctx, content=f"{ICON_INFO} Hiện tại chưa có ai trên bảng xếp hạng của server này!")
            return

        guild_user_data = {
            uid: udata for uid, udata in data[guild_id].items()
            if uid != "config" and isinstance(udata, dict) and ("balance" in udata or "bank_balance" in udata)
        }
        
        if not guild_user_data: 
            logger.info(f"Không có user data hợp lệ cho leaderboard guild {guild_id}.")
            await try_send(ctx, content=f"{ICON_INFO} Hiện tại chưa có ai trên bảng xếp hạng của server này!")
            return
            
        sorted_users_with_data = sorted(
            guild_user_data.items(), 
            key=lambda item: item[1].get('balance', 0) + item[1].get('bank_balance', 0),
            reverse=True 
        )

        if not sorted_users_with_data: 
            logger.info(f"Không có user nào sau khi sắp xếp cho leaderboard guild {guild_id}.")
            await try_send(ctx, content=f"{ICON_INFO} Không có ai để xếp hạng!")
            return

        user_rank_message = None
        author_id_str = str(ctx.author.id)
        
        for i, (user_id_str, user_data_dict) in enumerate(sorted_users_with_data):
            if user_id_str == author_id_str:
                user_rank = i + 1
                user_total_wealth = user_data_dict.get('balance', 0) + user_data_dict.get('bank_balance', 0)
                user_rank_message = f"{ICON_PROFILE} {ctx.author.mention}, bạn đang ở **hạng #{user_rank}** với tổng tài sản là **{user_total_wealth:,}** {CURRENCY_SYMBOL}."
                logger.debug(f"User {ctx.author.name} tìm thấy ở hạng {user_rank} với tài sản {user_total_wealth}.")
                break 
        
        if user_rank_message is None: 
            user_rank_message = f"{ICON_INFO} {ctx.author.mention}, bạn hiện chưa có mặt trên bảng xếp hạng. Hãy cố gắng kiếm thêm {CURRENCY_SYMBOL} nhé!"
            logger.debug(f"User {ctx.author.name} không có trên bảng xếp hạng.")
        
        await try_send(ctx, content=user_rank_message)
        
        view = LeaderboardView(sorted_users_data=sorted_users_with_data, original_author=ctx.author, bot_instance=self.bot)
        initial_embed = await view.generate_embed_for_current_page()
        
        try:
            sent_message = await ctx.send(embed=initial_embed, view=view)
            view.message = sent_message 
            logger.debug(f"Leaderboard ban đầu đã được gửi cho {ctx.author.name}.")
        except nextcord.HTTPException as e:
            logger.error(f"Lỗi khi gửi tin nhắn leaderboard ban đầu cho {ctx.author.name}: {e}", exc_info=True)
            await ctx.send(f"{ICON_ERROR} Không thể hiển thị bảng xếp hạng lúc này.")


def setup(bot: commands.Bot):
    bot.add_cog(LeaderboardCommandCog(bot))
