# bot/cogs/earn/fish_cmd.py
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
from core.config import CURRENCY_SYMBOL, FISH_COOLDOWN, FISH_CATCHES
from core.icons import ICON_LOADING, ICON_FISH, ICON_INFO # Đảm bảo các icon này có trong core/icons.py

logger = logging.getLogger(__name__)

class FishCommandCog(commands.Cog, name="Fish Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info(f"{ICON_INFO} FishCommandCog initialized.")

    @commands.command(name='fish')
    async def fish(self, ctx: commands.Context):
        author_id = ctx.author.id
        guild_name_for_log = ctx.guild.name if ctx.guild else "DM"
        guild_id_for_log = ctx.guild.id if ctx.guild else "N/A"

        logger.debug(f"Lệnh 'fish' được gọi bởi {ctx.author.name} ({author_id}) tại context guild '{guild_name_for_log}' ({guild_id_for_log}).")
        
        economy_data = load_economy_data()
        user_profile = get_or_create_global_user_profile(economy_data, author_id)
        original_global_balance = user_profile.get("global_balance", 0)

        time_left = get_time_left_str(user_profile.get("last_fish_global"), FISH_COOLDOWN)
        if time_left:
            logger.debug(f"User {author_id} dùng lệnh 'fish' khi đang cooldown. Còn lại: {time_left}")
            await try_send(ctx, content=f"{ICON_LOADING} Cá cần thời gian để cắn câu! Lệnh `fish` (toàn cục) chờ: **{time_left}**.")
            return
            
        user_profile["last_fish_global"] = datetime.now().timestamp()
        
        catch_emoji, price = random.choice(list(FISH_CATCHES.items())) 
        
        user_profile["global_balance"] = original_global_balance + price
        save_economy_data(economy_data)

        logger.info(f"User: {ctx.author.display_name} ({author_id}) - Guild Context: '{guild_name_for_log}' ({guild_id_for_log}) - Action: 'fish' - Result: câu được '{catch_emoji}' trị giá {price} {CURRENCY_SYMBOL}. "
                    f"Ví Toàn Cục: {original_global_balance:,} -> {user_profile['global_balance']:,}.")

        message_to_send = ""
        if price >= 50: 
            message_to_send = f"{ICON_FISH} Chúc mừng! Bạn câu được một con {catch_emoji} và bán nó được **{price:,}** {CURRENCY_SYMBOL} vào Ví Toàn Cục!"
        elif price > 5: 
            message_to_send = f"{ICON_FISH} Bạn câu được {catch_emoji}, bán được **{price:,}** {CURRENCY_SYMBOL} vào Ví Toàn Cục. Cũng không tệ!"
        else: 
            message_to_send = f"{ICON_FISH} Ôi không! Bạn câu được rác {catch_emoji}... nhưng may là vẫn bán được **{price:,}** {CURRENCY_SYMBOL} vào Ví Toàn Cục."
        
        await try_send(ctx, content=message_to_send)
        logger.debug(f"Lệnh 'fish' cho {ctx.author.name} tại context guild '{guild_name_for_log}' ({guild_id_for_log}) đã xử lý xong.")

def setup(bot: commands.Bot):
    bot.add_cog(FishCommandCog(bot))
