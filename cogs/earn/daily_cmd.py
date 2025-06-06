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
from core.config import CURRENCY_SYMBOL, DAILY_COOLDOWN
from core.icons import ICON_LOADING, ICON_GIFT, ICON_MONEY_BAG, ICON_INFO, ICON_ERROR

logger = logging.getLogger(__name__)

class DailyCommandCog(commands.Cog, name="Daily Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"DailyCommandCog initialized for Ecoworld Economy.")

    @commands.command(name='daily', aliases=['d'])
    async def daily(self, ctx: commands.Context):
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server.")
            return

        author_id = ctx.author.id
        guild_id = ctx.guild.id
        
        logger.debug(f"Lệnh 'daily' được gọi bởi {ctx.author.name} ({author_id}) tại guild '{ctx.guild.name}' ({guild_id}).")
        
        economy_data = load_economy_data()
        global_profile = get_or_create_global_user_profile(economy_data, author_id)
        
        time_left = get_time_left_str(global_profile.get("last_daily_global"), DAILY_COOLDOWN)
        if time_left:
            await try_send(ctx, content=f"{ICON_LOADING} Thưởng ngày (toàn cục) của bạn chưa sẵn sàng! Chờ: **{time_left}**.")
            return
            
        bonus = random.randint(500, 1500)
        xp_earned_local = random.randint(15, 40)
        xp_earned_global = random.randint(25, 60)
        
        server_data = get_or_create_user_server_data(global_profile, guild_id)
        
        original_local_earned = server_data["local_balance"].get("earned", 0)
        original_xp_local = server_data.get("xp_local", 0)
        original_xp_global = global_profile.get("xp_global", 0)
        
        server_data["local_balance"]["earned"] = original_local_earned + bonus
        server_data["xp_local"] = original_xp_local + xp_earned_local
        global_profile["xp_global"] = original_xp_global + xp_earned_global
        global_profile["last_daily_global"] = datetime.now().timestamp()
        
        save_economy_data(economy_data)

        logger.info(f"Guild: {ctx.guild.name} ({guild_id}) - User: {ctx.author.display_name} ({author_id}) đã nhận 'daily'. "
                    f"Result: +{bonus:,} {CURRENCY_SYMBOL} vào Ví Local (Earned). "
                    f"XP Local: +{xp_earned_local}. XP Global: +{xp_earned_global}.")
        
        new_total_local_balance = server_data["local_balance"]["earned"] + server_data["local_balance"]["admin_added"]

        await try_send(ctx, content=f"{ICON_GIFT} {ctx.author.mention}, bạn đã nhận thưởng ngày **{bonus:,}** {CURRENCY_SYMBOL} vào Ví Local! {ICON_MONEY_BAG} Ví Local của bạn giờ là: **{new_total_local_balance:,}** {CURRENCY_SYMBOL}")
        
def setup(bot: commands.Bot):
    bot.add_cog(DailyCommandCog(bot))
