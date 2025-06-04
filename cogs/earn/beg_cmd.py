# bot/cogs/earn/beg_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime

from core.database import get_user_data, save_data
from core.utils import try_send, get_time_left_str
from core.config import CURRENCY_SYMBOL, BEG_COOLDOWN
from core.icons import ICON_LOADING, ICON_GIFT, ICON_MONEY_BAG, ICON_WARNING

class BegCommandCog(commands.Cog, name="Beg Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='beg', aliases=['b'])
    async def beg(self, ctx: commands.Context):
        """Xin tiền từ những người qua đường. May rủi!"""
        data = get_user_data(ctx.guild.id, ctx.author.id)
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]
        
        time_left = get_time_left_str(user_data.get("last_beg"), BEG_COOLDOWN)
        if time_left:
            await try_send(ctx, content=f"{ICON_LOADING} Đừng xin liên tục thế chứ! Lệnh `beg` chờ: **{time_left}**.")
            return
            
        user_data["last_beg"] = datetime.now().timestamp()
        if random.random() < 0.7: 
            earnings = random.randint(10, 100)
            user_data["balance"] = user_data.get("balance", 0) + earnings
            save_data(data) 
            await try_send(ctx, content=f"{ICON_GIFT} Một người tốt bụng đã cho {ctx.author.mention} **{earnings:,}** {CURRENCY_SYMBOL}! {ICON_MONEY_BAG} Ví: **{user_data['balance']:,}**")
        else:
            save_data(data) 
            await try_send(ctx, content=f"{ICON_WARNING} Không ai cho {ctx.author.mention} tiền cả. Thử lại vận may sau nhé! 😢")

def setup(bot: commands.Bot):
    bot.add_cog(BegCommandCog(bot))
