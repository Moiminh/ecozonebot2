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
    # get_or_create_user_server_data # Sẽ cần nếu bạn cộng xp_local
)
from core.utils import try_send, get_time_left_str
from core.config import CURRENCY_SYMBOL, WORK_COOLDOWN
from core.icons import ICON_LOADING, ICON_WORK, ICON_MONEY_BAG, ICON_INFO

logger = logging.getLogger(__name__) 

class WorkCommandCog(commands.Cog, name="Work Command"): 
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"WorkCommandCog initialized.")

    @commands.command(name='work', aliases=['w'])
    async def work(self, ctx: commands.Context):
        author_id = ctx.author.id
        # Lấy thông tin guild để log, ngay cả khi logic chính là global
        guild_name_for_log = ctx.guild.name if ctx.guild else "DM"
        guild_id_for_log = ctx.guild.id if ctx.guild else "N/A" # Cooldown là global, không phụ thuộc guild

        logger.debug(f"Lệnh 'work' được gọi bởi {ctx.author.name} ({author_id}) tại context guild '{guild_name_for_log}' ({guild_id_for_log}).")
        
        economy_data = load_economy_data()
        user_profile = get_or_create_global_user_profile(economy_data, author_id)
        
        original_global_balance = user_profile.get("global_balance", 0)
        
        # Sử dụng cooldown toàn cục từ profile người dùng toàn cục
        time_left = get_time_left_str(user_profile.get("last_work_global"), WORK_COOLDOWN)
        if time_left:
            log_msg_cooldown = f"User {ctx.author.display_name} ({author_id}) thử 'work' nhưng đang cooldown (toàn cục: {time_left}). Lệnh gọi từ guild '{guild_name_for_log}' ({guild_id_for_log})."
            logger.debug(log_msg_cooldown) 
            # Nếu muốn log cả việc bị cooldown ra action log/webhook, dùng logger.info:
            # logger.info(log_msg_cooldown)
            await try_send(ctx, content=f"{ICON_LOADING} Bạn cần nghỉ ngơi! Lệnh `work` (toàn cục) chờ: **{time_left}**.")
            # Không cần save_economy_data vì user_profile chỉ được đọc (get) cho cooldown, chưa có thay đổi.
            # Tuy nhiên, get_or_create_global_user_profile có thể đã tạo user mới, nên save vẫn an toàn.
            # Nhưng nếu user không tồn tại, họ cũng sẽ không có last_work_global > 0.
            # Quyết định: Không save ở đây để tránh ghi thừa nếu chỉ là check cooldown.
            return
            
        earnings = random.randint(100, 500) 
        
        # Cập nhật Ví Toàn Cục và cooldown toàn cục
        user_profile["global_balance"] = original_global_balance + earnings
        user_profile["last_work_global"] = datetime.now().timestamp()
        
        # (Tùy chọn) Nếu bạn muốn cộng XP:
        # original_xp_global = user_profile.get("xp_global", 0)
        # xp_earned_global = random.randint(10, 50) 
        # user_profile["xp_global"] = original_xp_global + xp_earned_global
        #
        # if guild_id_for_log != "N/A": # Chỉ cộng xp_local nếu lệnh được dùng trong server
        #     user_server_data = get_or_create_user_server_data(user_profile, guild_id_for_log)
        #     original_xp_local = user_server_data.get("xp_local", 0)
        #     xp_earned_local = random.randint(5, 25) 
        #     user_server_data["xp_local"] = original_xp_local + xp_earned_local
        #     logger.debug(f"User {author_id} nhận {xp_earned_local} xp_local tại guild {guild_id_for_log}. Total xp_local: {user_server_data['xp_local']}")
        
        save_economy_data(economy_data) 

        # Log hành động thành công (sẽ vào player_actions.log và webhook)
        logger.info(f"User: {ctx.author.display_name} ({author_id}) - Guild Context: '{guild_name_for_log}' ({guild_id_for_log}) - Action: 'work' - Result: kiếm được {earnings:,} {CURRENCY_SYMBOL}. "
                    f"Ví Toàn Cục: {original_global_balance:,} -> {user_profile['global_balance']:,}.")
        
        await try_send(ctx, content=f"{ICON_WORK} {ctx.author.mention}, bạn làm việc chăm chỉ và kiếm được **{earnings:,}** {CURRENCY_SYMBOL} vào Ví Toàn Cục! {ICON_MONEY_BAG} Ví Toàn Cục của bạn: **{user_profile['global_balance']:,}**")
        logger.debug(f"Lệnh 'work' cho {ctx.author.name} tại context guild '{guild_name_for_log}' ({guild_id_for_log}) đã xử lý xong.")

def setup(bot: commands.Bot):
    bot.add_cog(WorkCommandCog(bot))
