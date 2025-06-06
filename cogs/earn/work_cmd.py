import nextcord
from nextcord.ext import commands
import random
from datetime import datetime
import logging

from core.database import (
    load_economy_data,
    get_or_create_global_user_profile,
    get_or_create_user_server_data,
    save_economy_data
)
from core.utils import try_send, get_time_left_str
from core.config import CURRENCY_SYMBOL, WORK_COOLDOWN
from core.icons import ICON_LOADING, ICON_WORK, ICON_MONEY_BAG, ICON_INFO, ICON_ERROR

logger = logging.getLogger(__name__)

class WorkCommandCog(commands.Cog, name="Work Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"WorkCommandCog initialized for Hybrid-Split-Economy.")

    @commands.command(name='work', aliases=['w'])
    async def work(self, ctx: commands.Context):
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server.")
            return

        author_id = ctx.author.id
        guild_id = ctx.guild.id
        
        logger.debug(f"Lệnh 'work' được gọi bởi {ctx.author.name} ({author_id}) tại guild '{ctx.guild.name}' ({guild_id}).")
        
        economy_data = load_economy_data()
        user_profile = get_or_create_global_user_profile(economy_data, author_id)
        
        time_left = get_time_left_str(user_profile.get("last_work_global"), WORK_COOLDOWN)
        if time_left:
            await try_send(ctx, content=f"{ICON_LOADING} Bạn cần nghỉ ngơi! Lệnh `work` (toàn cục) chờ: **{time_left}**.")
            return
            
        earnings = random.randint(100, 500)
        xp_earned_local = random.randint(5, 25)
        xp_earned_global = random.randint(10, 50)
        
        user_server_data = get_or_create_user_server_data(user_profile, guild_id)
        
        original_local_earned = user_server_data["local_balance"].get("earned", 0)
        original_xp_local = user_server_data.get("xp_local", 0)
        original_xp_global = user_profile.get("xp_global", 0)

        user_server_data["local_balance"]["earned"] = original_local_earned + earnings
        user_server_data["xp_local"] = original_xp_local + xp_earned_local
        user_profile["xp_global"] = original_xp_global + xp_earned_global
        user_profile["last_work_global"] = datetime.now().timestamp()
        
        save_economy_data(economy_data) 

        logger.info(f"Guild: {ctx.guild.name} ({guild_id}) - User: {ctx.author.display_name} ({author_id}) thực hiện 'work'. "
                    f"Result: +{earnings:,} {CURRENCY_SYMBOL} vào Ví Local (Earned). "
                    f"Earned Balance: {original_local_earned:,} -> {user_server_data['local_balance']['earned']:,}. "
                    f"XP Local: +{xp_earned_local}. XP Global: +{xp_earned_global}.")
        
        new_total_local_balance = user_server_data["local_balance"]["earned"] + user_server_data["local_balance"]["admin_added"]
        
        await try_send(ctx, content=f"{ICON_WORK} {ctx.author.mention}, bạn làm việc chăm chỉ và kiếm được **{earnings:,}** {CURRENCY_SYMBOL} vào Ví Local! {ICON_MONEY_BAG} Ví Local của bạn giờ là: **{new_total_local_balance:,}** {CURRENCY_SYMBOL}")

def setup(bot: commands.Bot):
    bot.add_cog(WorkCommandCog(bot))
