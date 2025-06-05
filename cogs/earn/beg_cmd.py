# bot/cogs/earn/beg_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime
import logging # <<< Đảm bảo đã import logging

from core.database import get_user_data, save_data
from core.utils import try_send, get_time_left_str
from core.config import CURRENCY_SYMBOL, BEG_COOLDOWN
from core.icons import ICON_LOADING, ICON_GIFT, ICON_MONEY_BAG, ICON_WARNING, ICON_INFO # Đảm bảo có ICON_INFO

logger = logging.getLogger(__name__) # <<< Đã có logger

class BegCommandCog(commands.Cog, name="Beg Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info(f"{ICON_INFO} BegCommandCog initialized.") # Sử dụng INFO để thấy trên console

    @commands.command(name='beg', aliases=['b'])
    async def beg(self, ctx: commands.Context):
        """Xin tiền từ những người qua đường. May rủi!"""
        logger.debug(f"Lệnh 'beg' được gọi bởi {ctx.author.name} (ID: {ctx.author.id}) tại guild {ctx.guild.id}.")
        
        data = get_user_data(ctx.guild.id, ctx.author.id)
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]
        original_balance = user_data.get("balance", 0)
        
        time_left = get_time_left_str(user_data.get("last_beg"), BEG_COOLDOWN)
        if time_left:
            logger.debug(f"User {ctx.author.id} dùng lệnh 'beg' khi đang cooldown. Còn lại: {time_left}")
            # Có thể thêm logger.info nếu muốn log cả việc bị cooldown qua webhook
            # logger.info(f"User {ctx.author.display_name} ({ctx.author.id}) thử 'beg' nhưng đang cooldown ({time_left}).")
            await try_send(ctx, content=f"{ICON_LOADING} Đừng xin liên tục thế chứ! Lệnh `beg` chờ: **{time_left}**.")
            return
            
        user_data["last_beg"] = datetime.now().timestamp()
        if random.random() < 0.7: 
            earnings = random.randint(10, 100)
            user_data["balance"] = original_balance + earnings
            save_data(data) 
            # --- GHI LOG INFO CHO HÀNH ĐỘNG THÀNH CÔNG ---
            logger.info(f"User {ctx.author.display_name} ({ctx.author.id}) đã 'beg' thành công, nhận được {earnings:,} {CURRENCY_SYMBOL}. Số dư: {original_balance:,} -> {user_data['balance']:,}.")
            # ---------------------------------------------
            await try_send(ctx, content=f"{ICON_GIFT} Một người tốt bụng đã cho {ctx.author.mention} **{earnings:,}** {CURRENCY_SYMBOL}! {ICON_MONEY_BAG} Ví: **{user_data['balance']:,}**")
        else:
            save_data(data) # Vẫn lưu vì last_beg đã được cập nhật
            # --- GHI LOG INFO CHO HÀNH ĐỘNG THẤT BẠI ---
            logger.info(f"User {ctx.author.display_name} ({ctx.author.id}) đã 'beg' thất bại.")
            # -------------------------------------------
            await try_send(ctx, content=f"{ICON_WARNING} Không ai cho {ctx.author.mention} tiền cả. Thử lại vận may sau nhé! 😢")
        logger.debug(f"Lệnh 'beg' cho {ctx.author.name} đã xử lý xong.")

def setup(bot: commands.Bot):
    bot.add_cog(BegCommandCog(bot))
