# bot/cogs/earn/work_cmd.py
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
from core.config import CURRENCY_SYMBOL, WORK_COOLDOWN # WORK_COOLDOWN này giờ sẽ là global
from core.icons import ICON_LOADING, ICON_WORK, ICON_MONEY_BAG, ICON_INFO

logger = logging.getLogger(__name__) 

class WorkCommandCog(commands.Cog, name="Work Command"): 
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"WorkCommandCog initialized.")

    @commands.command(name='work', aliases=['w'])
    async def work(self, ctx: commands.Context):
        author_id = ctx.author.id
        guild_id = ctx.guild.id if ctx.guild else None # Lấy guild_id nếu có
        guild_name_for_log = ctx.guild.name if ctx.guild else "DM"

        logger.debug(f"Lệnh 'work' được gọi bởi {ctx.author.name} ({author_id}) tại guild '{guild_name_for_log}' ({guild_id}).")
        
        economy_data = load_economy_data()
        user_profile = get_or_create_global_user_profile(economy_data, author_id)
        
        original_global_balance = user_profile.get("global_balance", 0)
        
        # Sử dụng cooldown toàn cục
        time_left = get_time_left_str(user_profile.get("last_work_global"), WORK_COOLDOWN)
        if time_left:
            log_msg_cooldown = f"Guild: {guild_name_for_log} ({guild_id}) - User: {ctx.author.display_name} ({author_id}) thử 'work' nhưng đang cooldown ({time_left})."
            # Quyết định log INFO hay DEBUG cho cooldown tùy bạn
            logger.debug(log_msg_cooldown) 
            # if you want this on webhook: logger.info(log_msg_cooldown)
            await try_send(ctx, content=f"{ICON_LOADING} Bạn cần nghỉ ngơi! Lệnh `work` (toàn cục) chờ: **{time_left}**.")
            return # Không cần save_economy_data vì user_profile chưa thay đổi (chỉ get)
            
        earnings = random.randint(100, 500) # Số tiền kiếm được
        
        # Cập nhật Ví Toàn Cục và cooldown toàn cục
        user_profile["global_balance"] = original_global_balance + earnings
        user_profile["last_work_global"] = datetime.now().timestamp()
        

        save_economy_data(economy_data) 

        logger.info(f"Guild: {guild_name_for_log} ({guild_id}) - User: {ctx.author.display_name} ({author_id}) thực hiện 'work', kiếm được {earnings:,} {CURRENCY_SYMBOL} vào Ví Toàn Cục. "
                    f"Ví Toàn Cục: {original_global_balance:,} -> {user_profile['global_balance']:,}.")
        
        await try_send(ctx, content=f"{ICON_WORK} {ctx.author.mention}, bạn làm việc chăm chỉ và kiếm được **{earnings:,}** {CURRENCY_SYMBOL} vào Ví Toàn Cục! {ICON_MONEY_BAG} Ví Toàn Cục của bạn: **{user_profile['global_balance']:,}**")
        logger.debug(f"Lệnh 'work' cho {ctx.author.name} tại guild '{guild_name_for_log}' ({guild_id}) đã xử lý xong.")

def setup(bot: commands.Bot):
    bot.add_cog(WorkCommandCog(bot))
