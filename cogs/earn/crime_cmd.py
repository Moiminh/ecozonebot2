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
from core.config import CURRENCY_SYMBOL, CRIME_COOLDOWN, CRIME_SUCCESS_RATE
from core.icons import ICON_LOADING, ICON_CRIME, ICON_ERROR, ICON_MONEY_BAG, ICON_INFO

logger = logging.getLogger(__name__)

class CrimeCommandCog(commands.Cog, name="Crime Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"CrimeCommandCog initialized for Ecoworld Economy.")

    @commands.command(name='crime')
    async def crime(self, ctx: commands.Context):
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server.")
            return

        author_id = ctx.author.id
        guild_id = ctx.guild.id
        
        logger.debug(f"Lệnh 'crime' được gọi bởi {ctx.author.name} ({author_id}) tại guild '{ctx.guild.name}' ({guild_id}).")
        
        economy_data = load_economy_data()
        user_profile = get_or_create_global_user_profile(economy_data, author_id)
        
        time_left = get_time_left_str(user_profile.get("last_crime_global"), CRIME_COOLDOWN)
        if time_left:
            await try_send(ctx, content=f"{ICON_LOADING} Cảnh sát đang theo dõi! Lệnh `crime` (toàn cục) chờ: **{time_left}**.")
            return
            
        user_profile["last_crime_global"] = datetime.now().timestamp()
        
        user_server_data = get_or_create_user_server_data(user_profile, guild_id)
        local_balance = user_server_data.get("local_balance", {})
        original_earned_amount = local_balance.get("earned", 0)
        original_admin_added_amount = local_balance.get("admin_added", 0)
        original_total_local_balance = original_earned_amount + original_admin_added_amount

        crimes_list = ["trộm vặt", "buôn lậu", "hack tài khoản", "tổ chức đua xe đường phố", "giả danh quan chức", "lừa đảo qua mạng", "in tiền giả"]
        chosen_crime = random.choice(crimes_list)
        logger.debug(f"User {author_id} tại guild {guild_id} thực hiện tội '{chosen_crime}'.")

        if random.random() < CRIME_SUCCESS_RATE:
            earnings = random.randint(300, 1000)
            user_server_data["local_balance"]["earned"] = original_earned_amount + earnings
            
            logger.info(f"CRIME SUCCESS: Guild: {ctx.guild.name} ({guild_id}) - User: {ctx.author.display_name} ({author_id}) thực hiện '{chosen_crime}' thành công, +{earnings:,} {CURRENCY_SYMBOL} vào Ví Local (Earned). "
                        f"Earned Balance: {original_earned_amount:,} -> {user_server_data['local_balance']['earned']:,}.")
            
            await try_send(ctx, content=f"{ICON_CRIME} Bạn đã thực hiện thành công phi vụ **'{chosen_crime}'** và kiếm được **{earnings:,}** {CURRENCY_SYMBOL} vào Ví Local!")
        else:
            fine_percentage = random.uniform(0.05, 0.20)
            potential_fine_from_percentage = int(original_total_local_balance * fine_percentage)
            min_random_fine = random.randint(100, 500)
            
            fine = max(potential_fine_from_percentage, min_random_fine)
            fine = min(fine, original_total_local_balance)
            
            admin_money_deducted = min(original_admin_added_amount, fine)
            earned_money_deducted = fine - admin_money_deducted

            user_server_data["local_balance"]["admin_added"] -= admin_money_deducted
            user_server_data["local_balance"]["earned"] -= earned_money_deducted

            logger.info(f"CRIME FAILED: Guild: {ctx.guild.name} ({guild_id}) - User: {ctx.author.display_name} ({author_id}) thực hiện '{chosen_crime}' thất bại, bị phạt {fine:,} {CURRENCY_SYMBOL} từ Ví Local. "
                        f"Số dư local cũ: {original_total_local_balance:,} -> mới: {user_server_data['local_balance']['earned'] + user_server_data['local_balance']['admin_added']:,}.")

            await try_send(ctx, content=f"{ICON_ERROR} Bạn đã thất bại thảm hại khi thực hiện **'{chosen_crime}'** và bị phạt **{fine:,}** {CURRENCY_SYMBOL} từ Ví Local!")
        
        save_economy_data(economy_data)
        
        new_total_local_balance = user_server_data['local_balance']['earned'] + user_server_data['local_balance']['admin_added']
        await try_send(ctx, content=f"{ICON_MONEY_BAG} Ví Local của bạn giờ là: **{new_total_local_balance:,}** {CURRENCY_SYMBOL}")
        logger.debug(f"Lệnh 'crime' cho {ctx.author.name} tại guild '{ctx.guild.name}' ({guild_id}) đã xử lý xong.")

def setup(bot: commands.Bot):
    bot.add_cog(CrimeCommandCog(bot))
