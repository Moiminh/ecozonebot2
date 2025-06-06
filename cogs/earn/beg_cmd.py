# bot/cogs/earn/beg_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime
import logging

from core.database import (
    load_economy_data,
    get_or_create_global_user_profile,
    save_economy_data
)
from core.utils import try_send, get_time_left_str
from core.config import CURRENCY_SYMBOL, BEG_COOLDOWN
from core.icons import ICON_LOADING, ICON_GIFT, ICON_MONEY_BAG, ICON_WARNING, ICON_INFO

logger = logging.getLogger(__name__)

class BegCommandCog(commands.Cog, name="Beg Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info(f"{ICON_INFO} BegCommandCog initialized.")

    @commands.command(name='beg', aliases=['b'])
    async def beg(self, ctx: commands.Context):
        author_id = ctx.author.id
        guild_name_for_log = ctx.guild.name if ctx.guild else "DM"
        guild_id_for_log = ctx.guild.id if ctx.guild else "N/A"

        logger.debug(f"Lệnh 'beg' được gọi bởi {ctx.author.name} ({author_id}) tại context guild '{guild_name_for_log}' ({guild_id_for_log}).")
        
        economy_data = load_economy_data()
        user_profile = get_or_create_global_user_profile(economy_data, author_id)
        original_global_balance = user_profile.get("global_balance", 0)
        
        time_left = get_time_left_str(user_profile.get("last_beg_global"), BEG_COOLDOWN)
        if time_left:
            logger.debug(f"User {author_id} dùng lệnh 'beg' khi đang cooldown. Còn lại: {time_left}")
            await try_send(ctx, content=f"{ICON_LOADING} Đừng xin liên tục thế chứ! Lệnh `beg` (toàn cục) chờ: **{time_left}**.")
            return
            
        user_profile["last_beg_global"] = datetime.now().timestamp()
        
        if random.random() < 0.7: 
            earnings = random.randint(10, 100)
            user_profile["global_balance"] = original_global_balance + earnings
            
            logger.info(f"User: {ctx.author.display_name} ({author_id}) - Guild Context: '{guild_name_for_log}' ({guild_id_for_log}) - Action: 'beg' - Result: thành công, nhận được {earnings:,} {CURRENCY_SYMBOL}. "
                        f"Ví Toàn Cục: {original_global_balance:,} -> {user_profile['global_balance']:,}.")
            
            await try_send(ctx, content=f"{ICON_GIFT} Một người tốt bụng đã cho {ctx.author.mention} **{earnings:,}** {CURRENCY_SYMBOL}! {ICON_MONEY_BAG} Ví Toàn Cục: **{user_profile['global_balance']:,}**")
        else:
            logger.info(f"User: {ctx.author.display_name} ({author_id}) - Guild Context: '{guild_name_for_log}' ({guild_id_for_log}) - Action: 'beg' - Result: thất bại.")
            
            await try_send(ctx, content=f"{ICON_WARNING} Không ai cho {ctx.author.mention} tiền cả. Thử lại vận may sau nhé! 😢")
            
        save_economy_data(economy_data)
        logger.debug(f"Lệnh 'beg' cho {ctx.author.name} tại context guild '{guild_name_for_log}' ({guild_id_for_log}) đã xử lý xong.")

def setup(bot: commands.Bot):
    bot.add_cog(BegCommandCog(bot))
