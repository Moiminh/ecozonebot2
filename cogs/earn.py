# bot/cogs/earn.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime # Cần thiết cho việc cập nhật timestamp

# Import các thành phần cần thiết từ package 'core'
from core.database import get_user_data, save_data, check_user # check_user có thể cần cho rob
from core.utils import try_send, get_time_left_str
from core.config import (
    CURRENCY_SYMBOL, WORK_COOLDOWN, DAILY_COOLDOWN, BEG_COOLDOWN,
    ROB_COOLDOWN, ROB_SUCCESS_RATE, ROB_FINE_RATE, CRIME_COOLDOWN,
    CRIME_SUCCESS_RATE, FISH_COOLDOWN, FISH_CATCHES
)

class EarnCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='work', aliases=['w'])
    async def work(self, ctx: commands.Context):
        """Làm việc để kiếm một khoản tiền ngẫu nhiên."""
        data = get_user_data(ctx.guild.id, ctx.author.id)
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]
        
        time_left = get_time_left_str(user_data.get("last_work"), WORK_COOLDOWN)
        if time_left:
            await try_send(ctx, content=f"Bạn cần nghỉ ngơi! Lệnh `work` chờ: **{time_left}**.")
            return
            
        earnings = random.randint(100, 500)
        user_data["balance"] = user_data.get("balance", 0) + earnings
        user_data["last_work"] = datetime.now().timestamp()
        save_data(data)
        await try_send(ctx, content=f"{ctx.author.mention}, bạn làm việc và kiếm được **{earnings:,}** {CURRENCY_SYMBOL}! Ví: **{user_data['balance']:,}**")

    @commands.command(name='daily', aliases=['d'])
    async def daily(self, ctx: commands.Context):
        """Nhận phần thưởng hàng ngày của bạn."""
        data = get_user_data(ctx.guild.id, ctx.author.id)
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]
        
        time_left = get_time_left_str(user_data.get("last_daily"), DAILY_COOLDOWN)
        if time_left:
            await try_send(ctx, content=f"Thưởng ngày chờ: **{time_left}**.")
            return
            
        bonus = random.randint(500, 1500)
        user_data["balance"] = user_data.get("balance", 0) + bonus
        user_data["last_daily"] = datetime.now().timestamp()
        save_data(data)
        await try_send(ctx, content=f"{ctx.author.mention}, thưởng ngày: **{bonus:,}** {CURRENCY_SYMBOL}! Ví: **{user_data['balance']:,}**")

    @commands.command(name='beg', aliases=['b'])
    async def beg(self, ctx: commands.Context):
        """Xin tiền từ những người qua đường. May rủi!"""
        data = get_user_data(ctx.guild.id, ctx.author.id)
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]
        
        time_left = get_time_left_str(user_data.get("last_beg"), BEG_COOLDOWN)
        if time_left:
            await try_send(ctx, content=f"Đừng xin liên tục! Lệnh `beg` chờ: **{time_left}**.")
            return
            
        user_data["last_beg"] = datetime.now().timestamp()
        if random.random() < 0.7: # 70% cơ hội thành công
            earnings = random.randint(10, 100)
            user_data["balance"] = user_data.get("balance", 0) + earnings
            await try_send(ctx, content=f"Có người cho {ctx.author.mention} **{earnings:,}** {CURRENCY_SYMBOL}! Ví: **{user_data['balance']:,}**")
        else:
            await try_send(ctx, content=f"Không ai cho {ctx.author.mention} tiền cả. 😢")
        save_data(data)

    @commands.command(name='rob', aliases=['steal'])
    async def rob(self, ctx: commands.Context, target: nextcord.Member):
        """Cố gắng cướp tiền từ ví của một người dùng khác."""
        author = ctx.author
        if target.id == author.id:
            await try_send(ctx, content="Bạn không thể tự cướp mình!")
            return
        if target.bot:
            await try_send(ctx, content="Bạn không thể cướp bot!")
            return

        # Lấy dữ liệu của người thực hiện lệnh (author)
        full_data = get_user_data(ctx.guild.id, author.id)
        author_data = full_data[str(ctx.guild.id)][str(author.id)]

        time_left = get_time_left_str(author_data.get("last_rob"), ROB_COOLDOWN)
        if time_left:
            await try_send(ctx, content=f"Bạn vừa mới đi cướp xong! Lệnh `rob` chờ: **{time_left}**.")
            return

        # Kiểm tra và đảm bảo dữ liệu của mục tiêu (target) tồn tại trong full_data
        full_data = check_user(full_data, ctx.guild.id, target.id)
        target_data = full_data[str(ctx.guild.id)].get(str(target.id)) # Phải là .get() phòng trường hợp target.id không có (dù check_user đã xử lý)

        # Kiểm tra mục tiêu có đủ tiền để cướp không (ví dụ: ít nhất 100)
        if not target_data or target_data.get("balance", 0) < 100:
            await try_send(ctx, content=f"{target.mention} quá nghèo để cướp hoặc không có dữ liệu.")
            author_data["last_rob"] = datetime.now().timestamp() # Vẫn tính cooldown cho nỗ lực cướp
            save_data(full_data)
            return
        
        author_data["last_rob"] = datetime.now().timestamp() # Đặt cooldown ngay cả khi thất bại
        
        if random.random() < ROB_SUCCESS_RATE:
            # Cướp từ 10% đến 40% số tiền của mục tiêu
            min_rob_amount = int(target_data.get("balance", 0) * 0.10)
            max_rob_amount = int(target_data.get("balance", 0) * 0.40)
            
            # Đảm bảo max_rob_amount lớn hơn hoặc bằng min_rob_amount và không âm
            max_rob_amount = max(min_rob_amount, max_rob_amount)
            if max_rob_amount <= 0 : # Nếu mục tiêu có quá ít tiền (ví dụ 1 đồng) thì % ra 0
                 await try_send(ctx,content=f"{target.mention} có quá ít tiền để cướp có ý nghĩa.")
                 save_data(full_data) # Vẫn lưu vì cooldown đã được cập nhật
                 return

            robbed_amount = random.randint(min_rob_amount, max_rob_amount)
            
            author_data["balance"] = author_data.get("balance", 0) + robbed_amount
            target_data["balance"] -= robbed_amount # Trừ tiền của mục tiêu
            await try_send(ctx, content=f"🔫 Bạn đã cướp thành công **{robbed_amount:,}** {CURRENCY_SYMBOL} từ {target.mention}!")
        else:
            # Thất bại, bị phạt một phần tiền đang có
            fine_amount = min(int(author_data.get("balance", 0) * ROB_FINE_RATE), author_data.get("balance", 0)) # Phạt không quá số tiền đang có
            author_data["balance"] -= fine_amount
            await try_send(ctx, content=f"👮 Bạn đã bị bắt khi cố cướp {target.mention} và bị phạt **{fine_amount:,}** {CURRENCY_SYMBOL}.")
        save_data(full_data)


    @commands.command(name='crime')
    async def crime(self, ctx: commands.Context):
        """Thực hiện một hành vi phạm tội ngẫu nhiên để kiếm tiền."""
        data = get_user_data(ctx.guild.id, ctx.author.id)
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]

        time_left = get_time_left_str(user_data.get("last_crime"), CRIME_COOLDOWN)
        if time_left:
            await try_send(ctx, content=f"Cảnh sát đang theo dõi! Lệnh `crime` chờ: **{time_left}**.")
            return
            
        user_data["last_crime"] = datetime.now().timestamp()
        crimes = ["trộm vặt", "buôn lậu", "hack tài khoản", "tổ chức đua xe đường phố", "giả danh quan chức"]
        chosen_crime = random.choice(crimes)

        if random.random() < CRIME_SUCCESS_RATE:
            earnings = random.randint(300, 1000)
            user_data["balance"] = user_data.get("balance", 0) + earnings
            await try_send(ctx, content=f"Bạn đã thực hiện thành công **{chosen_crime}** và kiếm được **{earnings:,}** {CURRENCY_SYMBOL}!")
        else:
            fine = min(random.randint(100, 500), user_data.get("balance",0)) # Phạt không quá số tiền đang có
            user_data["balance"] -= fine
            await try_send(ctx, content=f"Bạn đã thất bại khi thực hiện **{chosen_crime}** và bị phạt **{fine:,}** {CURRENCY_SYMBOL}!")
        save_data(data)

    @commands.command(name='fish')
    async def fish(self, ctx: commands.Context):
        """Đi câu cá để kiếm tiền từ việc bán cá (hoặc rác)."""
        data = get_user_data(ctx.guild.id, ctx.author.id)
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]

        time_left = get_time_left_str(user_data.get("last_fish"), FISH_COOLDOWN)
        if time_left:
            await try_send(ctx, content=f"Cá cần thời gian để cắn câu! Lệnh `fish` chờ: **{time_left}**.")
            return
            
        user_data["last_fish"] = datetime.now().timestamp()
        catch, price = random.choice(list(FISH_CATCHES.items())) # Lấy ngẫu nhiên một item từ dictionary FISH_CATCHES
        user_data["balance"] = user_data.get("balance", 0) + price
        save_data(data)

        if price > 20: # Một ngưỡng tùy ý để phân biệt cá "xịn" và rác
            await try_send(ctx, content=f"🎣 Bạn câu được một con **{catch}** và bán nó được **{price:,}** {CURRENCY_SYMBOL}!")
        else:
            await try_send(ctx, content=f"🎣 Bạn câu được rác **{catch}**... chỉ đáng giá **{price:,}** {CURRENCY_SYMBOL}.")

# Hàm setup để bot có thể load cog này
def setup(bot: commands.Bot):
    bot.add_cog(EarnCog(bot))
