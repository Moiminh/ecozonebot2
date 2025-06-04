# bot/cogs/misc/leaderboard_cmd.py
import nextcord
from nextcord.ext import commands

from core.database import load_data
from core.utils import try_send
from core.config import CURRENCY_SYMBOL # COMMAND_PREFIX không cần thiết ở đây
from core.icons import ICON_LEADERBOARD, ICON_INFO # Đảm bảo các icon này có trong core/icons.py

class LeaderboardCommandCog(commands.Cog, name="Leaderboard Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='leaderboard', aliases=['lb', 'top'])
    async def leaderboard(self, ctx: commands.Context, page: int = 1):
        """Hiển thị bảng xếp hạng những người giàu nhất server."""
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

        items_per_page = 10 
        start_index = (page - 1) * items_per_page
        end_index = start_index + items_per_page
        total_pages = (len(sorted_users) + items_per_page - 1) // items_per_page 

        if not sorted_users and page == 1: 
            await try_send(ctx, content=f"{ICON_INFO} Không có ai để xếp hạng!") # Dùng ICON_INFO cho thông báo trung tính
            return
        if (page < 1 or page > total_pages) and total_pages > 0 :
            await try_send(ctx, content=f"{ICON_INFO} Số trang không hợp lệ. Server này chỉ có {total_pages} trang bảng xếp hạng.")
            return
        elif page < 1 and total_pages == 0 : 
             await try_send(ctx, content=f"{ICON_INFO} Chưa có ai trên bảng xếp hạng!")
             return

        embed = nextcord.Embed(
            title=f"{ICON_LEADERBOARD} Bảng Xếp Hạng Giàu Nhất - {ctx.guild.name}", # Thêm icon
            color=nextcord.Color.gold()
        )
        description_parts = []
        rank = start_index + 1 

        for user_id_str, user_data_dict in sorted_users[start_index:end_index]:
            try:
                user_obj = await self.bot.fetch_user(int(user_id_str)) 
                total_wealth = user_data_dict.get('balance', 0) + user_data_dict.get('bank_balance', 0)
                description_parts.append(f"{rank}. {user_obj.name} - **{total_wealth:,}** {CURRENCY_SYMBOL}")
                rank += 1
            except (nextcord.NotFound, ValueError, KeyError) as e:
                print(f"Leaderboard: Không thể fetch/xử lý user ID {user_id_str}. Lỗi: {e}")
                continue 
        
        if not description_parts: # Kiểm tra chung nếu không có gì để hiển thị
             # Các điều kiện cụ thể hơn đã được xử lý ở trên, đây là fallback
             await try_send(ctx, content=f"{ICON_INFO} Không có dữ liệu để hiển thị cho trang này.")
             return

        embed.description = "\n".join(description_parts)
        embed.set_footer(text=f"Trang {page}/{total_pages} | Yêu cầu bởi {ctx.author.name}")
        await try_send(ctx, embed=embed)

def setup(bot: commands.Bot):
    bot.add_cog(LeaderboardCommandCog(bot))
