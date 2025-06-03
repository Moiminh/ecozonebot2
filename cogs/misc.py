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

        if guild_id not in data or not data[guild_id] or all(key == "config" for key in data[guild_id]):
            await try_send(ctx, content="Chưa có ai trên bảng xếp hạng của server này!")
            return

        guild_user_data = {
            uid: udata for uid, udata in data[guild_id].items()
            if uid != "config" and isinstance(udata, dict) and ("balance" in udata or "bank_balance" in udata)
        }
        
        if not guild_user_data: 
            await try_send(ctx, content="Chưa có ai trên bảng xếp hạng của server này!")
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
            await try_send(ctx, content="Không có ai để xếp hạng!")
            return
        if (page < 1 or page > total_pages) and total_pages > 0 :
            await try_send(ctx, content=f"Số trang không hợp lệ. Server này chỉ có {total_pages} trang bảng xếp hạng.")
            return
        elif page < 1 and total_pages == 0 : 
             await try_send(ctx, content="Chưa có ai trên bảng xếp hạng!")
             return

        embed = nextcord.Embed(
            title=f"🏆 Bảng Xếp Hạng Giàu Nhất - {ctx.guild.name} 🏆",
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
        
        if not description_parts and total_pages > 0 and page <= total_pages :
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

        if not sorted_users: 
            await try_send(ctx, content="Chưa có ai để xếp hạng trên server này!")
            return

        top_user_id, top_user_data_dict = sorted_users[0] 
        try:
            user_obj = await self.bot.fetch_user(int(top_user_id))
            total_wealth = top_user_data_dict.get('balance', 0) + top_user_data_dict.get('bank_balance', 0)
            await try_send(ctx, content=f"👑 Người giàu nhất server là **{user_obj.name}** với tổng tài sản **{total_wealth:,}** {CURRENCY_SYMBOL}!")
        except (nextcord.NotFound, ValueError, KeyError) as e:
            print(f"Richest: Không thể fetch/xử lý user ID {top_user_id}. Lỗi: {e}")
            await try_send(ctx, content="Không thể tìm thấy thông tin người giàu nhất (có thể do lỗi fetch user).")
    
    @nextcord.slash_command(name="help", description="ℹ️ Hiển thị thông tin trợ giúp cho các lệnh của bot.")
    async def help_slash_command(self,
                                 interaction: nextcord.Interaction,
                                 command_name: str = nextcord.SlashOption(
                                     name="lệnh", 
                                     description="Tên lệnh prefix bạn muốn xem chi tiết (ví dụ: work, balance).",
                                     required=False,
                                     default=None
                                 )):
        """Hiển thị danh sách các lệnh hoặc thông tin chi tiết về một lệnh (prefix) cụ thể."""
        prefix = COMMAND_PREFIX
        
        if not command_name: # Hiển thị menu trợ giúp chung
            embed = nextcord.Embed(
                title="📜 Menu Trợ Giúp - Bot Kinh Tế 📜",
                description=(
                    f"Chào mừng bạn đến với Bot Kinh Tế! Dưới đây là các lệnh bạn có thể sử dụng.\n"
                    f"Để xem chi tiết một lệnh, dùng `/help lệnh <tên_lệnh>` (ví dụ: `/help lệnh work`).\n"
                    f"*Lưu ý: Hầu hết các lệnh đều có tên gọi tắt (alias) được liệt kê trong chi tiết lệnh.*\n"
                    f"Quản trị viên có thể dùng `{prefix}auto` để bật/tắt lệnh không cần prefix trong một kênh."
                ),
                color=nextcord.Color.dark_theme(), # <<< ĐÃ SỬA Ở ĐÂY (từ dark_embed() thành dark_theme())
            )
            
            embed.add_field(name="🏦 Tài Khoản & Tổng Quan",
                            value="`balance` `bank` `deposit` `withdraw` `transfer` `leaderboard` `richest` `inventory`",
                            inline=False)
            embed.add_field(name="💸 Kiếm Tiền & Cơ Hội",
                            value="`work` `daily` `beg` `crime` `fish` `rob`",
                            inline=False)
            embed.add_field(name="🎲 Giải Trí & Cờ Bạc",
                            value="`slots` `coinflip` `dice`",
                            inline=False)
            embed.add_field(name="🏪 Cửa Hàng Vật Phẩm",
                            value="`shop` `buy` `sell`",
                            inline=False)
            embed.add_field(name="👑 Quản Trị Server (Lệnh Prefix)",
                            value=f"`{prefix}addmoney` `{prefix}removemoney` `{prefix}auto` `{prefix}mutebot` `{prefix}unmutebot`",
                            inline=False)
            
            embed.set_footer(text=f"Bot được phát triển bởi [Tên của bạn hoặc Bot]. Gõ /help lệnh <tên_lệnh> để biết thêm chi tiết.")
            await try_send(interaction, embed=embed, ephemeral=True)
        else:
            cmd_name_to_find = command_name.lower().lstrip(prefix) 
            command_obj = self.bot.get_command(cmd_name_to_find)
            
            if not command_obj:
                await try_send(interaction, content=f"⚠️ Không tìm thấy lệnh prefix nào có tên là `{command_name}`. Hãy chắc chắn bạn nhập đúng tên lệnh (ví dụ: `work`, `balance` hoặc tên gọi tắt của nó).", ephemeral=True)
                return

            embed = nextcord.Embed(title=f"📘 Chi tiết lệnh: {prefix}{command_obj.name}", color=nextcord.Color.green())
            
            help_text = command_obj.help 
            if not help_text:
                help_text = command_obj.short_doc or "Lệnh này chưa có mô tả chi tiết." 
            embed.description = help_text

            usage = f"`{prefix}{command_obj.name} {command_obj.signature}`".strip()
            embed.add_field(name="📝 Cách sử dụng", value=usage, inline=False)

            if command_obj.aliases:
                aliases_str = ", ".join([f"`{prefix}{alias}`" for alias in command_obj.aliases])
                embed.add_field(name="🏷️ Tên gọi khác (Aliases)", value=aliases_str, inline=False)
            else:
                embed.add_field(name="🏷️ Tên gọi khác (Aliases)", value="Lệnh này không có tên gọi tắt.", inline=False)

            manual_cooldown_commands = {
                "work": WORK_COOLDOWN, "daily": DAILY_COOLDOWN, "beg": BEG_COOLDOWN,
                "rob": ROB_COOLDOWN, "crime": CRIME_COOLDOWN, "fish": FISH_COOLDOWN,
                "slots": SLOTS_COOLDOWN, "coinflip": CF_COOLDOWN, "dice": DICE_COOLDOWN
            }
            if command_obj.name in manual_cooldown_commands:
                cd_seconds = manual_cooldown_commands[command_obj.name]
                if cd_seconds >= 3600 and cd_seconds % 3600 == 0: cd_text = f"{cd_seconds // 3600} giờ"
                elif cd_seconds >= 60 and cd_seconds % 60 == 0: cd_text = f"{cd_seconds // 60} phút"
                else: cd_text = f"{cd_seconds} giây"
                embed.add_field(name="⏳ Thời gian chờ (Cooldown)", value=cd_text, inline=False)

            if command_obj.name in ["addmoney", "removemoney"]:
                embed
