# bot/cogs/earn/fish_cmd.py
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
from core.config import CURRENCY_SYMBOL, FISH_COOLDOWN, FISH_CATCHES
from core.icons import ICON_LOADING, ICON_FISH, ICON_INFO, ICON_ERROR

logger = logging.getLogger(__name__)

class FishCommandCog(commands.Cog, name="Fish Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"FishCommandCog initialized for Ecoworld Economy.")

    @commands.command(name='fish')
    async def fish(self, ctx: commands.Context):
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server.")
            return

        author_id = ctx.author.id
        guild_id = ctx.guild.id
        
        logger.debug(f"Lệnh 'fish' được gọi bởi {ctx.author.name} ({author_id}) tại guild '{ctx.guild.name}' ({guild_id}).")
        
        economy_data = load_economy_data()
        global_profile = get_or_create_global_user_profile(economy_data, author_id)
        
        time_left = get_time_left_str(global_profile.get("last_fish_global"), FISH_COOLDOWN)
        if time_left:
            await try_send(ctx, content=f"{ICON_LOADING} Cá cần thời gian để cắn câu! Lệnh `fish` (toàn cục) chờ: **{time_left}**.")
            return
            
        global_profile["last_fish_global"] = datetime.now().timestamp()
        
        catch_emoji, price = random.choice(list(FISH_CATCHES.items())) 
        
        xp_earned_local = random.randint(3, 15)
        xp_earned_global = random.randint(5, 25)
        
        server_data = get_or_create_user_server_data(global_profile, guild_id)
        
        original_local_earned = server_data["local_balance"].get("earned", 0)
        
        server_data["local_balance"]["earned"] = original_local_earned + price
        server_data["xp_local"] += xp_earned_local
        global_profile["xp_global"] += xp_earned_global
        
        save_economy_data(economy_data)

        logger.info(f"Guild: {ctx.guild.name} ({guild_id}) - User: {ctx.author.display_name} ({author_id}) đã 'fish'. "
                    f"Result: câu được '{catch_emoji}' trị giá {price} {CURRENCY_SYMBOL}, +{xp_earned_local} xp_local, +{xp_earned_global} xp_global. "
                    f"Earned Balance: {original_local_earned:,} -> {server_data['local_balance']['earned']:,}.")

        message_to_send = ""
        if price >= 50: 
            message_to_send = f"{ICON_FISH} Chúc mừng! Bạn câu được một con {catch_emoji} và bán nó được **{price:,}** {CURRENCY_SYMBOL} vào Ví Local!"
        elif price > 5: 
            message_to_send = f"{ICON_FISH} Bạn câu được {catch_emoji}, bán được **{price:,}** {CURRENCY_SYMBOL} vào Ví Local. Cũng không tệ!"
        else: 
            message_to_send = f"{ICON_FISH} Ôi không! Bạn câu được rác {catch_emoji}... nhưng may là vẫn bán được **{price:,}** {CURRENCY_SYMBOL} vào Ví Local."
        
        await try_send(ctx, content=message_to_send)

def setup(bot: commands.Bot):
    bot.add_cog(FishCommandCog(bot))
