# bot/cogs/earn/rob_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime

from core.database import get_user_data, save_data, check_user # check_user cần thiết
from core.utils import try_send, get_time_left_str
from core.config import CURRENCY_SYMBOL, ROB_COOLDOWN, ROB_SUCCESS_RATE, ROB_FINE_RATE
from core.icons import ICON_LOADING, ICON_ERROR, ICON_INFO, ICON_ROB

class RobCommandCog(commands.Cog, name="Rob Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='rob', aliases=['steal'])
    async def rob(self, ctx: commands.Context, target: nextcord.Member):
        """Cố gắng cướp tiền từ ví của một người dùng khác."""
        author = ctx.author
        if target.id == author.id:
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không thể tự cướp mình!")
            return
        if target.bot:
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không thể cướp bot!")
            return

        full_data = get_user_data(ctx.guild.id, author.id)
        author_data = full_data[str(ctx.guild.id)][str(author.id)]

        time_left = get_time_left_str(author_data.get("last_rob"), ROB_COOLDOWN)
        if time_left:
            await try_send(ctx, content=f"{ICON_LOADING} Bạn vừa mới đi cướp xong! Lệnh `rob` chờ: **{time_left}**.")
            return

        # Kiểm tra và đảm bảo dữ liệu của mục tiêu (target) tồn tại trong full_data
        full_data = check_user(full_data, ctx.guild.id, target.id)
        # Truy cập target_data sau khi đã check_user
        target_data = full_data.get(str(ctx.guild.id), {}).get(str(target.id))


        author_data["last_rob"] = datetime.now().timestamp() # Đặt cooldown ngay khi bắt đầu lệnh

        # Phải kiểm tra target_data sau khi đã gọi check_user
        if not target_data or target_data.get("balance", 0) < 100:
            await try_send(ctx, content=f"{ICON_INFO} {target.mention} quá nghèo để cướp hoặc không có dữ liệu.")
            save_data(full_data) # Lưu vì last_rob của author đã được cập nhật
            return
        
        if random.random() < ROB_SUCCESS_RATE:
            min_rob_amount = int(target_data.get("balance", 0) * 0.10)
            max_rob_amount = int(target_data.get("balance", 0) * 0.40)
            max_rob_amount = max(min_rob_amount, max_rob_amount) # Đảm bảo max >= min
            
            if max_rob_amount <= 0 : # Nếu mục tiêu có quá ít tiền
                 await try_send(ctx,content=f"{ICON_INFO} {target.mention} có quá ít tiền để cướp có ý nghĩa.")
                 save_data(full_data) # Lưu vì last_rob của author đã được cập nhật
                 return

            robbed_amount = random.randint(min_rob_amount, max_rob_amount)
            
            author_data["balance"] = author_data.get("balance", 0) + robbed_amount
            target_data["balance"] -= robbed_amount # Trừ tiền của mục tiêu
            await try_send(ctx, content=f"{ICON_ROB} Bạn đã cướp thành công **{robbed_amount:,}** {CURRENCY_SYMBOL} từ {target.mention}! Mwahaha!")
        else:
            fine_amount = min(int(author_data.get("balance", 0) * ROB_FINE_RATE), author_data.get("balance", 0))
            author_data["balance"] -= fine_amount
            await try_send(ctx, content=f"👮 {ICON_ERROR} Bạn đã bị bắt khi cố cướp {target.mention} và bị phạt **{fine_amount:,}** {CURRENCY_SYMBOL}.")
        save_data(full_data)

def setup(bot: commands.Bot):
    bot.add_cog(RobCommandCog(bot))
