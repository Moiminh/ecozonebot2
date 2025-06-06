# bot/cogs/earn/crime_cmd.py
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
from core.config import CURRENCY_SYMBOL, CRIME_COOLDOWN, CRIME_SUCCESS_RATE
from core.icons import ICON_LOADING, ICON_CRIME, ICON_ERROR, ICON_MONEY_BAG, ICON_INFO

logger = logging.getLogger(__name__)

class CrimeCommandCog(commands.Cog, name="Crime Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info(f"{ICON_INFO} CrimeCommandCog initialized.")

    @commands.command(name='crime')
    async def crime(self, ctx: commands.Context):
        author_id = ctx.author.id
        guild_name_for_log = ctx.guild.name if ctx.guild else "DM"
        guild_id_for_log = ctx.guild.id if ctx.guild else "N/A"

        logger.debug(f"Lệnh 'crime' được gọi bởi {ctx.author.name} ({author_id}) tại context guild '{guild_name_for_log}' ({guild_id_for_log}).")
        
        economy_data = load_economy_data()
        user_profile = get_or_create_global_user_profile(economy_data, author_id)
        original_global_balance = user_profile.get("global_balance", 0)

        time_left = get_time_left_str(user_profile.get("last_crime_global"), CRIME_COOLDOWN)
        if time_left:
            logger.debug(f"User {author_id} dùng lệnh 'crime' khi đang cooldown. Còn lại: {time_left}")
            await try_send(ctx, content=f"{ICON_LOADING} Cảnh sát đang theo dõi! Lệnh `crime` (toàn cục) chờ: **{time_left}**.")
            return
            
        user_profile["last_crime_global"] = datetime.now().timestamp()
        crimes_list = ["trộm vặt", "buôn lậu", "hack tài khoản", "tổ chức đua xe đường phố", "giả danh quan chức", "lừa đảo qua mạng", "in tiền giả"]
        chosen_crime = random.choice(crimes_list)
        logger.debug(f"User {author_id} thực hiện tội '{chosen_crime}'.")

        if random.random() < CRIME_SUCCESS_RATE:
            earnings = random.randint(300, 1000)
            user_profile["global_balance"] = original_global_balance + earnings
            
            logger.info(f"CRIME SUCCESS: User {ctx.author.display_name} ({author_id}) thực hiện '{chosen_crime}' thành công, kiếm được {earnings:,} {CURRENCY_SYMBOL}. "
                        f"Ví Toàn Cục: {original_global_balance:,} -> {user_profile['global_balance']:,}. (Context: {guild_name_for_log})")
            
            await try_send(ctx, content=f"{ICON_CRIME} Bạn đã thực hiện thành công phi vụ **'{chosen_crime}'** và kiếm được **{earnings:,}** {CURRENCY_SYMBOL} vào Ví Toàn Cục! {ICON_MONEY_BAG} Ví: {user_profile['global_balance']:,}")
        else:
            fine_percentage = random.uniform(0.05, 0.20)
            potential_fine_from_percentage = int(original_global_balance * fine_percentage)
            min_random_fine = random.randint(100, 500)
            
            fine = max(potential_fine_from_percentage, min_random_fine)
            fine = min(fine, original_global_balance)
            
            user_profile["global_balance"] = original_global_balance - fine

            logger.info(f"CRIME FAILED: User {ctx.author.display_name} ({author_id}) thực hiện '{chosen_crime}' thất bại, bị phạt {fine:,} {CURRENCY_SYMBOL}. "
                        f"Ví Toàn Cục: {original_global_balance:,} -> {user_profile['global_balance']:,}. (Context: {guild_name_for_log})")

            await try_send(ctx, content=f"{ICON_ERROR} Bạn đã thất bại thảm hại khi thực hiện **'{chosen_crime}'** và bị phạt **{fine:,}** {CURRENCY_SYMBOL}! {ICON_MONEY_BAG} Ví còn: {user_profile['global_balance']:,}")
        
        save_economy_data(economy_data)
        logger.debug(f"Lệnh 'crime' cho {ctx.author.name} tại context guild '{guild_name_for_log}' ({guild_id_for_log}) đã xử lý xong.")

def setup(bot: commands.Bot):
    bot.add_cog(CrimeCommandCog(bot))
