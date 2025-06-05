# bot/cogs/earn/work_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime
import logging 

from core.database import get_user_data, save_data
from core.utils import try_send, get_time_left_str
from core.config import CURRENCY_SYMBOL, WORK_COOLDOWN
from core.icons import ICON_LOADING, ICON_WORK, ICON_MONEY_BAG, ICON_INFO

logger = logging.getLogger(__name__) 

class WorkCommandCog(commands.Cog, name="Work Command"): 
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"WorkCommandCog initialized.") # Giữ debug cho init Cog

    @commands.command(name='work', aliases=['w'])
    async def work(self, ctx: commands.Context):
        logger.debug(f"Lệnh 'work' được gọi bởi {ctx.author.name} (ID: {ctx.author.id}) tại guild '{ctx.guild.name}' ({ctx.guild.id}).")
        
        data = get_user_data(ctx.guild.id, ctx.author.id)
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]
        
        original_balance = user_data.get("balance", 0)
        
        time_left = get_time_left_str(user_data.get("last_work"), WORK_COOLDOWN)
        if time_left:
            logger.debug(f"Guild: {ctx.guild.name} ({ctx.guild.id}) - User: {ctx.author.id} dùng lệnh 'work' khi đang cooldown. Còn lại: {time_left}")
            # Nếu muốn log cả việc cooldown ra action log/webhook, đổi thành logger.info
            # logger.info(f"Guild: {ctx.guild.name} ({ctx.guild.id}) - User: {ctx.author.display_name} ({ctx.author.id}) thử 'work' nhưng đang cooldown ({time_left}).")
            await try_send(ctx, content=f"{ICON_LOADING} Bạn cần nghỉ ngơi! Lệnh `work` chờ: **{time_left}**.")
            return
            
        earnings = random.randint(100, 500)
        user_data["balance"] = original_balance + earnings
        user_data["last_work"] = datetime.now().timestamp()
        save_data(data)

        # --- CẬP NHẬT DÒNG LOG INFO ---
        logger.info(f"Guild: {ctx.guild.name} ({ctx.guild.id}) - User: {ctx.author.display_name} ({ctx.author.id}) thực hiện 'work', kiếm được {earnings:,} {CURRENCY_SYMBOL}. "
                    f"Số dư: {original_balance:,} -> {user_data['balance']:,}.")
        # -----------------------------
        
        await try_send(ctx, content=f"{ICON_WORK} {ctx.author.mention}, bạn làm việc chăm chỉ và kiếm được **{earnings:,}** {CURRENCY_SYMBOL}! {ICON_MONEY_BAG} Ví: **{user_data['balance']:,}**")
        logger.debug(f"Lệnh 'work' cho {ctx.author.name} tại guild '{ctx.guild.name}' ({ctx.guild.id}) đã xử lý xong.")

def setup(bot: commands.Bot):
    bot.add_cog(WorkCommandCog(bot))
