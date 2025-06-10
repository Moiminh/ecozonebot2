# bot/cogs/earn/beg_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime
import logging

from core.utils import try_send, get_time_left_str, require_travel_check
from core.config import BEG_COOLDOWN
logger = logging.getLogger(__name__)

class BegCommandCog(commands.Cog, name="Beg Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("BegCommandCog (SQLite Ready) initialized.")

    @commands.command(name='beg', aliases=['b'])
    @commands.guild_only()
    @require_travel_check
    async def beg(self, ctx: commands.Context):
        author_id = ctx.author.id
        
        last_beg = self.bot.db.get_cooldown(author_id, "beg")
        time_left = get_time_left_str(last_beg, BEG_COOLDOWN)
        if time_left:
            await try_send(ctx, content=f"{ICON_LOADING} Đừng xin liên tục thế chứ! Chờ: **{time_left}**.")
            return

        self.bot.db.set_cooldown(author_id, "beg", datetime.now().timestamp())
        
        if random.random() < 0.7: 
            earnings = random.randint(10, 100)
            user_profile = self.bot.db.get_or_create_global_user_profile(author_id)
            new_balance = user_profile['bank_balance'] + earnings
            self.bot.db.update_balance(author_id, None, 'bank_balance', new_balance)
            
            await try_send(ctx, content=f"{ICON_GIFT} Một người tốt bụng đã cho {ctx.author.mention} **{earnings:,}**! Số dư {ICON_BANK_MAIN} của bạn giờ là: **{new_balance:,}**")
        else:
            await try_send(ctx, content=f"{ICON_WARNING} Không ai cho {ctx.author.mention} tiền cả. 😢")
            
def setup(bot: commands.Bot):
    bot.add_cog(BegCommandCog(bot))
