# bot/cogs/earn/daily_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime
import logging 

from core.database import (
    load_economy_data,
    get_or_create_global_user_profile,
    save_economy_data
    # get_or_create_user_server_data # Sẽ cần nếu bạn cộng xp_local
)
from core.utils import try_send, get_time_left_str
from core.config import CURRENCY_SYMBOL, DAILY_COOLDOWN # DAILY_COOLDOWN giờ là global
from core.icons import ICON_LOADING, ICON_GIFT, ICON_MONEY_BAG, ICON_INFO

logger = logging.getLogger(__name__) 

class DailyCommandCog(commands.Cog, name="Daily Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info(f"{ICON_INFO} DailyCommandCog initialized.") # Giữ INFO để thấy trên console

    @commands.command(name='daily', aliases=['d'])
    async def daily(self, ctx: commands.Context):
        author_id = ctx.author.id
        guild_name_for_log = ctx.guild.name if ctx.guild else "DM"
        guild_id_for_log = ctx.guild.id if ctx.guild else "N/A"

        logger.debug(f"Lệnh 'daily' được gọi bởi {ctx.author.name} ({author_id}) tại context guild '{guild_name_for_log}' ({guild_id_for_log}).")
        
        economy_data = load_economy_data()
        user_profile = get_or_create_global_user_profile(economy_data, author_id)
        
        original_global_balance = user_profile.get("global_balance", 0)
        
        # Sử dụng cooldown toàn cục
        time_left = get_time_left_str(user_profile.get("last_daily_global"), DAILY_COOLDOWN)
        if time_left:
            log_msg_cooldown = f"User {ctx.author.display_name} ({author_id}) thử 'daily' nhưng đang cooldown (toàn cục: {time_left}). Lệnh gọi từ guild '{guild_name_for_log}' ({guild_id_for_log})."
            logger.debug(log_msg_cooldown)
            # logger.info(log_msg_cooldown) # Tùy chọn nếu muốn log cooldown ra action log/webhook
            await try_send(ctx, content=f"{ICON_LOADING} Thưởng ngày (toàn cục) của bạn chưa sẵn sàng! Chờ: **{time_left}**.")
            return
            
        bonus = random.randint(500, 1500)
        
        # Cập nhật Ví Toàn Cục và cooldown toàn cục
        user_profile["global_balance"] = original_global_balance + bonus
        user_profile["last_daily_global"] = datetime.now().timestamp()
        
        # (Tùy chọn) Nếu bạn muốn cộng XP:
        # original_xp_global = user_profile.get("xp_global", 0)
        # xp_earned_global = random.randint(20, 70) # Ví dụ XP kiếm được từ daily
        # user_profile["xp_global"] = original_xp_global + xp_earned_global
        #
        # if guild_id_for_log != "N/A":
        #     user_server_data = get_or_create_user_server_data(user_profile, guild_id_for_log)
        #     original_xp_local = user_server_data.get("xp_local", 0)
        #     xp_earned_local = random.randint(10, 35) 
        #     user_server_data["xp_local"] = original_xp_local + xp_earned_local
        #     logger.debug(f"User {author_id} nhận {xp_earned_local} xp_local từ daily tại guild {guild_id_for_log}. Total xp_local: {user_server_data['xp_local']}")

        save_economy_data(economy_data) 

        logger.info(f"User: {ctx.author.display_name} ({author_id}) - Guild Context: '{guild_name_for_log}' ({guild_id_for_log}) - Action: 'daily' - Result: nhận {bonus:,} {CURRENCY_SYMBOL} vào Ví Toàn Cục. "
                    f"Ví Toàn Cục: {original_global_balance:,} -> {user_profile['global_balance']:,}.")
        
        await try_send(ctx, content=f"{ICON_GIFT} {ctx.author.mention}, bạn đã nhận thưởng ngày: **{bonus:,}** {CURRENCY_SYMBOL} vào Ví Toàn Cục! {ICON_MONEY_BAG} Ví Toàn Cục của bạn: **{user_profile['global_balance']:,}**")
        logger.debug(f"Lệnh 'daily' cho {ctx.author.name} tại context guild '{guild_name_for_log}' ({guild_id_for_log}) đã xử lý xong.")

def setup(bot: commands.Bot):
    bot.add_cog(DailyCommandCog(bot))
