# bot/cogs/admin/eco_admin.py
from discord.ext import commands
import discord # Hoặc thư viện discord.py tương thích bạn đang dùng (nextcord, disnake, etc.)

class EcoAdmin(commands.Cog, name="Quản lý Kinh tế (Admin)"):
    """
    Cog chứa các lệnh quản trị cho hệ thống kinh tế của bot.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Nếu bạn có kết nối database hoặc một module quản lý dữ liệu kinh tế,
        # bạn có thể khởi tạo hoặc truyền nó vào đây.
        # Ví dụ: self.db_manager = bot.db_manager

    @commands.command(name="addmoney", aliases=["addbal", "givemoney"])
    @commands.has_permissions(administrator=True) # Chỉ những người có quyền Administrator mới dùng được
    @commands.guild_only() # Lệnh này chỉ nên dùng trong server
    async def add_money(self, ctx: commands.Context, member: discord.Member, amount: int):
        """
        Thêm một lượng tiền cho thành viên (Admin).
        Ví dụ: !addmoney @User 1000
        """
        if amount <= 0:
            await ctx.send("Số tiền thêm vào phải lớn hơn 0.")
            return

        # --- Logic xử lý thêm tiền ---
        # Đây là phần bạn cần tùy chỉnh dựa trên cách bạn lưu trữ dữ liệu kinh tế.
        # Ví dụ, nếu bạn có một hàm `update_balance(user_id, amount_change)`:
        # success = await self.bot.db_manager.update_balance(member.id, amount)
        # if success:
        #     await ctx.send(f"Đã thêm {amount} tiền cho {member.mention}.")
        #     print(f"Admin {ctx.author} ({ctx.author.id}) đã thêm {amount} tiền cho {member.display_name} ({member.id})")
        # else:
        #     await ctx.send(f"Có lỗi xảy ra khi thêm tiền cho {member.mention}.")

        # Ví dụ đơn giản (thay thế bằng logic thực tế của bạn):
        await ctx.send(f"Lệnh `addmoney` được gọi: Thêm {amount} tiền cho {member.mention}. (Cần implement logic thực tế)")
        print(f"Admin {ctx.author} ({ctx.author.id}) yêu cầu thêm {amount} tiền cho {member.display_name} ({member.id})")


    @commands.command(name="removemoney", aliases=["removebal", "takemoney"])
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def remove_money(self, ctx: commands.Context, member: discord.Member, amount: int):
        """
        Xóa một lượng tiền của thành viên (Admin).
        Ví dụ: !removemoney @User 500
        """
        if amount <= 0:
            await ctx.send("Số tiền cần xóa phải lớn hơn 0.")
            return

        # --- Logic xử lý xóa tiền ---
        # Tương tự như add_money, bạn cần tùy chỉnh phần này.
        # Ví dụ, nếu bạn có một hàm `update_balance(user_id, amount_change)`:
        # current_balance = await self.bot.db_manager.get_balance(member.id)
        # if amount > current_balance:
        #     await ctx.send(f"{member.mention} không có đủ {amount} để xóa. Số dư hiện tại: {current_balance}.")
        #     return
        #
        # success = await self.bot.db_manager.update_balance(member.id, -amount) # Truyền số âm để trừ
        # if success:
        #     await ctx.send(f"Đã xóa {amount} tiền từ {member.mention}.")
        #     print(f"Admin {ctx.author} ({ctx.author.id}) đã xóa {amount} tiền từ {member.display_name} ({member.id})")
        # else:
        #     await ctx.send(f"Có lỗi xảy ra khi xóa tiền của {member.mention}.")

        # Ví dụ đơn giản (thay thế bằng logic thực tế của bạn):
        await ctx.send(f"Lệnh `removemoney` được gọi: Xóa {amount} tiền từ {member.mention}. (Cần implement logic thực tế)")
        print(f"Admin {ctx.author} ({ctx.author.id}) yêu cầu xóa {amount} tiền từ {member.display_name} ({member.id})")

    @commands.command(name="setmoney", aliases=["setbal"])
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def set_money(self, ctx: commands.Context, member: discord.Member, amount: int):
        """
        Thiết lập số tiền của thành viên thành một giá trị cụ thể (Admin).
        Ví dụ: !setmoney @User 10000
        """
        if amount < 0:
            await ctx.send("Số tiền không thể là số âm.")
            return

        # --- Logic xử lý thiết lập tiền ---
        # Ví dụ, nếu bạn có một hàm `set_balance(user_id, new_amount)`:
        # success = await self.bot.db_manager.set_balance(member.id, amount)
        # if success:
        #     await ctx.send(f"Đã thiết lập số tiền của {member.mention} thành {amount}.")
        #     print(f"Admin {ctx.author} ({ctx.author.id}) đã thiết lập tiền của {member.display_name} ({member.id}) thành {amount}")
        # else:
        #     await ctx.send(f"Có lỗi xảy ra khi thiết lập tiền cho {member.mention}.")

        # Ví dụ đơn giản (thay thế bằng logic thực tế của bạn):
        await ctx.send(f"Lệnh `setmoney` được gọi: Thiết lập tiền của {member.mention} thành {amount}. (Cần implement logic thực tế)")
        print(f"Admin {ctx.author} ({ctx.author.id}) yêu cầu thiết lập tiền của {member.display_name} ({member.id}) thành {amount}")

    # Bạn có thể thêm các lệnh kiểm tra lỗi (error handlers) cho cog này
    @add_money.error
    @remove_money.error
    @set_money.error
    async def eco_admin_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Bạn không có quyền sử dụng lệnh này.")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("Không tìm thấy thành viên được chỉ định.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Thiếu thông tin cần thiết. Vui lòng kiểm tra lại cách dùng lệnh bằng `!help {ctx.command.name}`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Giá trị cung cấp không hợp lệ (ví dụ: số tiền không phải là số).")
        else:
            await ctx.send("Có lỗi xảy ra khi thực thi lệnh.")
            print(f"Lỗi trong EcoAdmin cog: {error} (Lệnh: {ctx.command.name})")

# Hàm setup này rất quan trọng để bot có thể nạp cog
async def setup(bot: commands.Bot):
    await bot.add_cog(EcoAdmin(bot))
    print("Cog EcoAdmin đã được nạp.")

