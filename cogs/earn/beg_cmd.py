# bot/cogs/earn/beg_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime
import logging

from core.database import get_or_create_global_user_profile, get_or_create_user_local_data
from core.utils import try_send, get_time_left_str, require_travel_check
from core.config import BEG_COOLDOWN
# [SỬA] Import ICON_ECOIN thay cho CURRENCY_SYMBOL
from core.icons import ICON_LOADING, ICON_GIFT, ICON_MONEY_BAG, ICON_WARNING, ICON_INFO, ICON_ERROR, ICON_ECOIN
from core.travel_manager import handle_travel_event

logger = logging.getLogger(__name__)

class BegCommandCog(commands.Cog, name="Beg Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info(f"{ICON_INFO} BegCommandCog (Refactored) initialized.")

    @commands.command(name='beg', aliases=['b'])
    @commands.guild_only()
    # [THÊM] Thêm decorator để nhất quán với các lệnh guild_only khác
    @require_travel_check
    async def beg(self, ctx: commands.Context):
        author_id = ctx.author.id
        
        # [SỬA] Dùng cache của bot
        economy_data = self.bot.economy_data
        user_profile = get_or_create_global_user_profile(economy_data, author_id)
        # Lệnh beg tác động vào global_balance, không cần local_data
        
        time_left = get_time_left_str(user_profile.get("cooldowns", {}).get("beg", 0), BEG_COOLDOWN)
        if time_left:
            await try_send(ctx, content=f"{ICON_LOADING} Đừng xin liên tục thế chứ! Lệnh `beg` chờ: **{time_left}**.")
            return

        user_profile.setdefault("cooldowns", {})["beg"] = datetime.now().timestamp()

        # Lệnh beg hiện đang cộng tiền vào bank_balance (ví toàn cục)
        # Nếu muốn cộng vào ví local, bạn cần thay đổi logic ở đây
        if random.random() < 0.7: 
            earnings = random.randint(10, 100)
            user_profile["bank_balance"] = user_profile.get("bank_balance", 0) + earnings
            
            # [SỬA] Thay CURRENCY_SYMBOL bằng ICON_ECOIN
            await try_send(ctx, content=f"{ICON_GIFT} Một người tốt bụng đã cho {ctx.author.mention} **{earnings:,}** {ICON_ECOIN}! Số dư Bank của bạn giờ là: **{user_profile['bank_balance']:,}**")
        else:
            await try_send(ctx, content=f"{ICON_WARNING} Không ai cho {ctx.author.mention} tiền cả. Thử lại vận may sau nhé! 😢")
            
def setup(bot: commands.Bot):
    bot.add_cog(BegCommandCog(bot))
