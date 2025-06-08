# bot/cogs/earn/beg_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime
import logging

from core.database import get_or_create_global_user_profile
from core.utils import try_send, get_time_left_str
from core.config import BEG_COOLDOWN, CURRENCY_SYMBOL
from core.icons import ICON_LOADING, ICON_GIFT, ICON_MONEY_BAG, ICON_WARNING, ICON_INFO, ICON_ERROR
from core.travel_manager import handle_travel_event

logger = logging.getLogger(__name__)

class BegCommandCog(commands.Cog, name="Beg Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info(f"{ICON_INFO} BegCommandCog (Refactored) initialized.")

    @commands.command(name='beg', aliases=['b'])
    @commands.guild_only()
    async def beg(self, ctx: commands.Context):
        author_id = ctx.author.id
        guild_id = ctx.guild.id

        # [SỬA] Sử dụng cache từ bot
        economy_data = self.bot.economy_data
        user_profile = get_or_create_global_user_profile(economy_data, author_id)

        if user_profile.get("last_active_guild_id") != guild_id:
            await handle_travel_event(ctx, self.bot)
            return # Dừng lệnh sau khi travel
        user_profile["last_active_guild_id"] = guild_id

        time_left = get_time_left_str(user_profile.get("cooldowns", {}).get("beg", 0), BEG_COOLDOWN)
        if time_left:
            await try_send(ctx, content=f"{ICON_LOADING} Đừng xin liên tục thế chứ! Lệnh `beg` chờ: **{time_left}**.")
            return

        user_profile.setdefault("cooldowns", {})["beg"] = datetime.now().timestamp()

        if random.random() < 0.7: 
            earnings = random.randint(10, 100)
            user_profile["global_balance"] = user_profile.get("global_balance", 0) + earnings

            await try_send(ctx, content=f"{ICON_GIFT} Một người tốt bụng đã cho {ctx.author.mention} **{earnings:,}** {CURRENCY_SYMBOL}! {ICON_MONEY_BAG} Ví Toàn Cục: **{user_profile['global_balance']:,}**")
        else:
            await try_send(ctx, content=f"{ICON_WARNING} Không ai cho {ctx.author.mention} tiền cả. Thử lại vận may sau nhé! 😢")
            
        # [XÓA] Không cần save thủ công
        # save_economy_data(economy_data)

def setup(bot: commands.Bot):
    bot.add_cog(BegCommandCog(bot))
