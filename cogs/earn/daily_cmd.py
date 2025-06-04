# bot/cogs/earn/daily_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime

# Import các thành phần cần thiết từ package 'core'
from core.database import get_user_data, save_data
from core.utils import try_send, get_time_left_str
from core.config import CURRENCY_SYMBOL, DAILY_COOLDOWN
# --- DÒNG IMPORT ICON ĐẦY ĐỦ VÀ CHÍNH XÁC ---
from core.icons import ICON_LOADING, ICON_GIFT, ICON_MONEY_BAG, ICON_INFO 
# (Đảm bảo tất cả các icon này đã được bạn định nghĩa trong bot/core/icons.py)
# --------------------------------------------

class DailyCommandCog(commands.Cog, name="Daily Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Dòng print này sử dụng ICON_INFO, giờ sẽ không lỗi nữa nếu đã import đúng
        print(f"{ICON_INFO} [COG LOADED] DailyCommandCog initialized.") 

    @commands.command(name='daily', aliases=['d'])
    async def daily(self, ctx: commands.Context):
        """Nhận phần thưởng hàng ngày của bạn."""
        # print(f"--- Lệnh DAILY được gọi bởi {ctx.author.name} ---") # Bạn có thể giữ dòng debug này nếu muốn
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
