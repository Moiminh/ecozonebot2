# bot/cogs/earn/crime_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime

from core.database import get_user_data, save_data
from core.utils import try_send, get_time_left_str
from core.config import CURRENCY_SYMBOL, CRIME_COOLDOWN, CRIME_SUCCESS_RATE
from core.icons import ICON_LOADING, ICON_CRIME, ICON_ERROR, ICON_MONEY_BAG

class CrimeCommandCog(commands.Cog, name="Crime Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='crime')
    async def crime(self, ctx: commands.Context):
        """Thực hiện một hành vi phạm tội ngẫu nhiên để kiếm tiền."""
        data = get_user_data(ctx.guild.id, ctx.author.id)
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]

        time_left = get_time_left_str(user_data.get("last_crime"), CRIME_COOLDOWN)
        if time_left:
            await try_send(ctx, content=f"{ICON_LOADING} Cảnh sát đang theo dõi! Lệnh `crime` chờ: **{time_left}**.")
            return
            
        user_data["last_crime"] = datetime.now().timestamp()
        crimes = ["trộm vặt", "buôn lậu", "hack tài khoản", "tổ chức đua xe đường phố", "giả danh quan chức", "lừa đảo qua mạng", "in tiền giả"]
        chosen_crime = random.choice(crimes)

        if random.random() < CRIME_SUCCESS_RATE:
            earnings = random.randint(300, 1000) # Số tiền kiếm được có thể đa dạng hơn
            user_data["balance"] = user_data.get("balance", 0) + earnings
            save_data(data) 
            await try_send(ctx, content=f"{ICON_CRIME} Bạn đã thực hiện thành công phi vụ **'{chosen_crime}'** và kiếm được **{earnings:,}** {CURRENCY_SYMBOL}! {ICON_MONEY_BAG} Ví: {user_data['balance']:,}")
        else:
            fine_percentage = random.uniform(0.05, 0.15) # Phạt từ 5% đến 15% số tiền đang có
            fine = min(int(user_data.get("balance",0) * fine_percentage) , user_data.get("balance",0)) # Đảm bảo không phạt quá số tiền có
            fine = max(fine, random.randint(50, 250)) # Phạt ít nhất 50-250 nếu % quá nhỏ hoặc balance = 0
            fine = min(fine, user_data.get("balance",0)) # Kiểm tra lại để không phạt quá số tiền có sau khi có min_fine

            user_data["balance"] -= fine
            save_data(data) 
            await try_send(ctx, content=f"{ICON_ERROR} Bạn đã thất bại thảm hại khi thực hiện **'{chosen_crime}'** và bị phạt **{fine:,}** {CURRENCY_SYMBOL}! {ICON_MONEY_BAG} Ví còn: {user_data['balance']:,}")

def setup(bot: commands.Bot):
    bot.add_cog(CrimeCommandCog(bot))
