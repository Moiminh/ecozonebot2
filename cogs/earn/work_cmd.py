# bot/cogs/earn/work_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime

from core.database import get_user_data, save_data
from core.utils import try_send, get_time_left_str
from core.config import CURRENCY_SYMBOL, WORK_COOLDOWN
from core.icons import ICON_LOADING, ICON_WORK, ICON_MONEY_BAG # Đảm bảo các icon này có trong core/icons.py

class WorkCommandCog(commands.Cog, name="Work Command"): 
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='work', aliases=['w'])
    async def work(self, ctx: commands.Context):
        # print(f"--- Lệnh WORK được gọi bởi {ctx.author.name} tại kênh {ctx.channel.name} ---") # Bạn có thể giữ dòng debug này nếu muốn
        """Làm việc để kiếm một khoản tiền ngẫu nhiên."""
        data = get_user_data(ctx.guild.id, ctx.author.id)
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]
        
        time_left = get_time_left_str(user_data.get("last_work"), WORK_COOLDOWN)
        if time_left:
            await try_send(ctx, content=f"{ICON_LOADING} Bạn cần nghỉ ngơi! Lệnh `work` chờ: **{time_left}**.")
            return
            
        earnings = random.randint(100, 500)
        user_data["balance"] = user_data.get("balance", 0) + earnings
        user_data["last_work"] = datetime.now().timestamp()
        save_data(data)
        await try_send(ctx, content=f"{ICON_WORK} {ctx.author.mention}, bạn làm việc chăm chỉ và kiếm được **{earnings:,}** {CURRENCY_SYMBOL}! {ICON_MONEY_BAG} Ví: **{user_data['balance']:,}**")

def setup(bot: commands.Bot):
    bot.add_cog(WorkCommandCog(bot))
