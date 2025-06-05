# bot/cogs/earn/daily_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime
import logging # Đã có

from core.database import get_user_data, save_data
from core.utils import try_send, get_time_left_str
from core.config import CURRENCY_SYMBOL, DAILY_COOLDOWN
from core.icons import ICON_LOADING, ICON_GIFT, ICON_MONEY_BAG, ICON_INFO # Đảm bảo có ICON_INFO

logger = logging.getLogger(__name__) # Đã có

class DailyCommandCog(commands.Cog, name="Daily Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info(f"{ICON_INFO} DailyCommandCog initialized.")

    @commands.command(name='daily', aliases=['d'])
    async def daily(self, ctx: commands.Context):
        """Nhận phần thưởng hàng ngày của bạn."""
        logger.debug(f"Lệnh 'daily' được gọi bởi {ctx.author.name} (ID: {ctx.author.id}) tại guild {ctx.guild.id}.")
        
        data = get_user_data(ctx.guild.id, ctx.author.id)
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]
        original_balance = user_data.get("balance", 0)
        
        time_left = get_time_left_str(user_data.get("last_daily"), DAILY_COOLDOWN)
        if time_left:
            logger.debug(f"User {ctx.author.id} dùng lệnh 'daily' khi đang cooldown. Còn lại: {time_left}")
            # Nếu muốn log cả việc bị cooldown qua webhook, đổi logger.debug ở dòng trên thành logger.info
            # logger.info(f"User {ctx.author.display_name} ({ctx.author.id}) thử 'daily' nhưng đang cooldown ({time_left}).")
            await try_send(ctx, content=f"{ICON_LOADING} Thưởng ngày của bạn chưa sẵn sàng! Chờ: **{time_left}**.")
            return
            
        bonus = random.randint(500, 1500)
        user_data["balance"] = original_balance + bonus
        user_data["last_daily"] = datetime.now().timestamp()
        save_data(data)

        # --- GHI LOG INFO CHO HÀNH ĐỘNG THÀNH CÔNG ---
        logger.info(f"User {ctx.author.display_name} ({ctx.author.id}) đã nhận thưởng 'daily' là {bonus:,} {CURRENCY_SYMBOL}. Số dư: {original_balance:,} -> {user_data['balance']:,}.")
        # ---------------------------------------------
        
        await try_send(ctx, content=f"{ICON_GIFT} {ctx.author.mention}, bạn đã nhận thưởng ngày: **{bonus:,}** {CURRENCY_SYMBOL}! {ICON_MONEY_BAG} Ví: **{user_data['balance']:,}**")
        logger.debug(f"Lệnh 'daily' cho {ctx.author.name} đã xử lý xong.")

def setup(bot: commands.Bot):
    bot.add_cog(DailyCommandCog(bot))
