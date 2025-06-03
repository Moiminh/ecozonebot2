# bot/cogs/misc.py
import nextcord
from nextcord.ext import commands

# Import các thành phần cần thiết từ package 'core'
from core.database import load_data # Leaderboard/richest thường load toàn bộ data để sắp xếp
from core.utils import try_send
from core.config import (
    COMMAND_PREFIX, CURRENCY_SYMBOL, WORK_COOLDOWN, DAILY_COOLDOWN,
    BEG_COOLDOWN, ROB_COOLDOWN, CRIME_COOLDOWN, FISH_COOLDOWN,
    SLOTS_COOLDOWN, CF_COOLDOWN, DICE_COOLDOWN
)

class MiscCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='leaderboard', aliases=['lb', 'top'])
    async def leaderboard(self, ctx: commands.Context, page: int = 1):
        """Hiển thị bảng xếp hạng những người giàu nhất server."""
        data = load_data() # Load toàn bộ dữ liệu từ file
        guild_id = str(ctx.guild.id)

        # Kiểm tra xem guild có dữ liệu không, và dữ liệu đó có phải chỉ là 'config' không
        if guild_id not in data or not data[guild_id] or all(key == "config" for key in data[guild_id]):
            await try_send(ctx, content="Chưa có ai trên bảng xếp hạng của server này!")
            return

        # Lọc ra chỉ dữ liệu người dùng, loại bỏ 'config' và các entry không phải dict
        guild_user_data = {
            uid: udata for uid, udata in data[guild_id].items()
            if uid != "config" and isinstance(udata, dict) and ("balance" in udata or "bank_balance" in udata)
        }
        
        if not guild_user_data: # Nếu sau khi lọc không còn user nào
            await try_send(ctx, content="Chưa có ai trên bảng xếp hạng của server này!")
            return
            
        # Sắp xếp người dùng theo tổng tài sản (ví + ngân hàng)
        sorted_users = sorted(
            guild_user_data.items(), # items() trả về list các (user_id, user_data_dict)
            key=lambda item: item[1].get('balance', 0) + item[1].get('bank_balance', 0),
            reverse=True # Sắp xếp giảm dần
        )

        items_per_page = 10 # Số người dùng hiển thị trên mỗi trang
        start_index = (page - 1) * items_per_page
        end_index = start_index + items_per_page
        total_pages = (len(sorted_users) + items_per_page - 1) // items_per_page # Tính tổng số trang

        if not sorted_users and page == 1: # Trường hợp này đã được xử lý ở trên
            await try_send(ctx, content="Không có ai để xếp hạng!")
            return
        if (page < 1 or page > total_pages) and total_pages > 0 :
            await try_send(ctx, content=f"Số trang không hợp lệ. Server này chỉ có {total_pages} trang bảng xếp hạng.")
            return
        elif page < 1 and total_pages == 0 : # Trường hợp không có ai và page < 1
             await try_send(ctx, content="Chưa có ai trên bảng xếp hạng!")
             return

        embed = nextcord.Embed(
            title=f"🏆 Bảng Xếp Hạng Giàu Nhất - {ctx.guild.name} 🏆",
            color=nextcord.Color.gold()
        )
        description_parts = []
        rank = start_index + 1 # Thứ hạng bắt đầu từ trang hiện tại

        for user_id_str, user_data_dict in sorted_users[start_index:end_index]:
            try:
                user_obj = await self.bot.fetch_user(int(user_id_str)) # Lấy đối tượng user từ ID
                total_wealth = user_data_dict.get('balance', 0) + user_data_dict.get('bank_balance', 0)
                description_parts.append(f"{rank}. {user_obj.name} - **{total_wealth:,}** {CURRENCY_SYMBOL}")
                rank += 1
            except (nextcord.NotFound, ValueError, KeyError) as e:
                print(f"Leaderboard: Không thể fetch/xử lý user ID {user_id_str}. Lỗi: {e}")
                continue # Bỏ qua user này nếu có lỗi
        
        if not description_parts and total_pages > 0 and page <= total_pages :
            # Có thể xảy ra nếu tất cả user trên trang này đều không fetch được
            await try_send(ctx, content="Không thể tạo bảng xếp hạng cho trang này (có thể do lỗi fetch thông tin người dùng).")
            return
        if not description_parts and (total_pages == 0 or page > total_pages) :
             await try_send(ctx, content="Chưa có ai trên bảng xếp hạng hoặc trang không tồn tại.")
             return

        embed.description = "\n".join(description_parts)
        embed.set_footer(text=f"Trang {page}/{total_pages} | Yêu cầu bởi {ctx.author.name}")
        await try_send(ctx, embed=embed)

    @commands.command(name='richest')
    async def richest(self, ctx: commands.Context):
        """Hiển thị người giàu nhất trên server."""
        data = load_data()
        guild_id = str(ctx.guild.id)

        if guild_id not in data or not data[guild_id] or all(key == "config" for key in data[guild_id]):
            await try_send(ctx, content="Chưa có ai để xếp hạng trên server này!")
            return
        
        guild_user_data = {
            uid: udata for uid, udata in data[guild_id].items()
            if uid != "config" and isinstance(udata, dict) and ("balance" in udata or "bank_balance" in udata)
        }
        if not guild_user_data:
            await try_send(ctx, content="Chưa có ai để xếp hạng trên server này!")
            return
            
        sorted_users = sorted(
            guild_user_data.items(),
            key=lambda item: item[1].get('balance', 0) + item[1].get('bank_balance', 0),
            reverse=True
        )

        if not sorted_users: # Nếu không có ai sau khi sắp xếp (dù đã kiểm tra guild_user_data)
            await try_send(ctx, content="Chưa có ai để xếp hạng trên server này!")
            return

        top_user_id, top_user_data_dict = sorted_users[0] # Lấy người đứng đầu
        try:
            user_obj = await self.bot.fetch_user(int(top_user_id))
            total_wealth = top_user_data_dict.get('balance', 0) + top_user_data_dict.get('bank_balance', 0)
            await try_send(ctx, content=f"👑 Người giàu nhất server là **{user_obj.name}** với tổng tài sản **{total_wealth:,}** {CURRENCY_SYMBOL}!")
        except (nextcord.NotFound, ValueError, KeyError) as e:
            print(f"Richest: Không thể fetch/xử lý user ID {top_user_id}. Lỗi: {e}")
            await try_send(ctx, content="Không thể tìm thấy thông tin người giàu nhất (có thể do lỗi fetch user).")


    @nextcord.slash_command(name="help", description="Hiển thị thông tin trợ giúp cho các lệnh của bot.")
    async def help_slash_command(self,
                                 interaction: nextcord.Interaction,
                                 command_name: str = nextcord.SlashOption(
                                     name="tên_lệnh", # Tên tham số hiển thị cho người dùng
                                     description="Tên lệnh (có prefix) bạn muốn xem chi tiết.",
                                     required=False, # Tham số này không bắt buộc
                                     default=None    # Giá trị mặc định nếu không được cung cấp
                                 )):
        """Hiển thị danh sách các lệnh hoặc thông tin chi tiết về một lệnh (prefix) cụ thể."""
        prefix = COMMAND_PREFIX # Lấy prefix từ config
        
        if not command_name: # Nếu không có tên lệnh cụ thể, hiển thị help chung
            embed = nextcord.Embed(
                title="📜 Menu Trợ Giúp - Bot Kinh Tế 📜",
                description=(
                    f"Các lệnh của bot sử dụng prefix `{prefix}`. \n"
                    f"Để xem chi tiết một lệnh, gõ `/help tên_lệnh <tên_lệnh_prefix>` (ví dụ: `/help tên_lệnh work`).\n"
                    f"Quản trị viên có thể bật lệnh không cần prefix cho kênh bằng lệnh `{prefix}auto`."
                ),
                color=nextcord.Color.blurple()
            )
            # Phân loại lệnh cho dễ nhìn
            embed.add_field(name="🏦 Tài Khoản & Kinh Tế", value="`balance` (bal, $, cash, money), `bank`, `deposit` (dep), `withdraw` (wd), `transfer` (give, pay), `leaderboard` (lb, top), `richest`", inline=False)
            embed.add_field(name="💸 Kiếm Tiền", value="`work` (w), `daily` (d), `beg` (b
