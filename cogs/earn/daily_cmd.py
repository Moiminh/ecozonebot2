# bot/cogs/earn/daily_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime

from core.database import get_user_data, save_data
from core.utils import try_send, get_time_left_str
from core.config import CURRENCY_SYMBOL, DAILY_COOLDOWN
from core.icons import ICON_LOADING, ICON_GIFT, ICON_MONEY_BAG # Đảm bảo các icon này có trong core/icons.py

class DailyCommandCog(commands.Cog, name="Daily Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"{ICON_INFO} [COG LOADED] DailyCommandCog initialized.") # Thêm dòng này để xác nhận Cog init

    @commands.command(name='daily', aliases=['d'])
    async def daily(self, ctx: commands.Context):
        print(f"--- Lệnh DAILY được gọi bởi {ctx.author.name} ---") # Dòng debug
        """Nhận phần thưởng hàng ngày của bạn."""
        data = get_user_data(ctx.guild.id, ctx.author.id)
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]
        
        time_left = get_time_left_str(user_data.get("last_daily"), DAILY_COOLDOWN)
        if time_left:
            await try_send(ctx, content=f"{ICON_LOADING} Thưởng ngày của bạn chưa sẵn sàng! Chờ: **{time_left}**.")
            return
            
        bonus = random.randint(500, 1500)
        user_data["balance"] = user_data.get("balance", 0) + bonus
        user_data["last_daily"] = datetime.now().timestamp()
        save_data(data)
        await try_send(ctx, content=f"{ICON_GIFT} {ctx.author.mention}, bạn đã nhận thưởng ngày: **{bonus:,}** {CURRENCY_SYMBOL}! {ICON_MONEY_BAG} Ví: **{user_data['balance']:,}**")

def setup(bot: commands.Bot):
    bot.add_cog(DailyCommandCog(bot))
