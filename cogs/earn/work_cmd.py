# bot/cogs/earn/work_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime
import logging # <<< THÊM IMPORT NÀY

from core.database import get_user_data, save_data
from core.utils import try_send, get_time_left_str
from core.config import CURRENCY_SYMBOL, WORK_COOLDOWN
from core.icons import ICON_LOADING, ICON_WORK, ICON_MONEY_BAG, ICON_INFO # Giả sử ICON_INFO đã được import

logger = logging.getLogger(__name__) # <<< LẤY LOGGER CHO MODULE NÀY

class WorkCommandCog(commands.Cog, name="Work Command"): 
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Thay thế print bằng logger.info hoặc logger.debug
        # logger.info(f"{ICON_INFO} WorkCommandCog initialized.") # Thông báo này sẽ vào cả 2 file log và console
        logger.debug(f"WorkCommandCog initialized.") # Thông báo này chỉ vào file general_log

    @commands.command(name='work', aliases=['w'])
    async def work(self, ctx: commands.Context):
        # Thay thế print bằng logger.debug
        logger.debug(f"Lệnh '{ctx.command.name}' được gọi bởi {ctx.author.name} (ID: {ctx.author.id}) tại guild {ctx.guild.id}, kênh {ctx.channel.id}.")
        """Làm việc để kiếm một khoản tiền ngẫu nhiên."""
        data = get_user_data(ctx.guild.id, ctx.author.id)
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]
        
        time_left = get_time_left_str(user_data.get("last_work"), WORK_COOLDOWN)
        if time_left:
            logger.debug(f"Lệnh 'work' của user {ctx.author.id} đang cooldown. Còn lại: {time_left}")
            await try_send(ctx, content=f"{ICON_LOADING} Bạn cần nghỉ ngơi! Lệnh `work` chờ: **{time_left}**.")
            return
            
        earnings = random.randint(100, 500)
        original_balance = user_data.get("balance", 0) # Ghi lại số dư cũ để log (tùy chọn)
        user_data["balance"] = original_balance + earnings
        user_data["last_work"] = datetime.now().timestamp()
        save_data(data)

        # Ghi log hành động của người chơi (sẽ vào cả general log và player_actions.log)
        logger.info(f"User {ctx.author.display_name} ({ctx.author.id}) thực hiện 'work', kiếm được {earnings} {CURRENCY_SYMBOL}. Số dư: {original_balance} -> {user_data['balance']}.")
        
        await try_send(ctx, content=f"{ICON_WORK} {ctx.author.mention}, bạn làm việc chăm chỉ và kiếm được **{earnings:,}** {CURRENCY_SYMBOL}! {ICON_MONEY_BAG} Ví: **{user_data['balance']:,}**")
        logger.debug(f"Lệnh 'work' cho {ctx.author.name} đã xử lý xong.")


def setup(bot: commands.Bot):
    bot.add_cog(WorkCommandCog(bot))
