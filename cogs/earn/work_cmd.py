# bot/cogs/earn/work_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime
import logging

from core.database import (
    get_or_create_global_user_profile,
    get_or_create_user_local_data
)
from core.utils import try_send, require_travel_check
from core.config import WORK_COOLDOWN, WORK_ENERGY_COST, WORK_HUNGER_COST
from core.leveling import check_and_process_levelup
from core.icons import (
    ICON_LOADING, ICON_WORK, ICON_ERROR, 
    ICON_ECOIN, ICON_SURVIVAL
)

logger = logging.getLogger(__name__)

class WorkCommandCog(commands.Cog, name="Work Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("WorkCommandCog (v4 - Refactored) initialized.")

    @commands.command(name='work', aliases=['w'])
    @commands.guild_only()
    @require_travel_check
    async def work(self, ctx: commands.Context):
        """Làm việc chăm chỉ để kiếm tiền sạch và kinh nghiệm (tiêu tốn năng lượng và độ no)."""
        author_id = ctx.author.id
        guild_id = ctx.guild.id
        
        try:
            economy_data = self.bot.economy_data
            global_profile = get_or_create_global_user_profile(economy_data, author_id)
            local_data = get_or_create_user_local_data(global_profile, guild_id)

            # --- KIỂM TRA CHỈ SỐ SINH TỒN ---
            stats = local_data.get("survival_stats")
            if stats["energy"] < WORK_ENERGY_COST:
                await try_send(ctx, content=f"{ICON_SURVIVAL} Bạn quá mệt mỏi để làm việc! Hãy nghỉ ngơi hoặc dùng vật phẩm hồi phục.")
                return
            if stats["hunger"] < WORK_HUNGER_COST:
                await try_send(ctx, content=f"{ICON_SURVIVAL} Bạn quá đói để làm việc! Hãy ăn gì đó trước đã.")
                return

            # --- Kiểm tra Cooldown ---
            now = datetime.now().timestamp()
            last_work = global_profile.get("cooldowns", {}).get("work", 0)
            if now - last_work < WORK_COOLDOWN:
                time_left = str(datetime.fromtimestamp(last_work + WORK_COOLDOWN) - datetime.now()).split('.')[0]
                await try_send(ctx, content=f"{ICON_LOADING} Bạn cần nghỉ ngơi! Lệnh `work` còn chờ: **{time_left}**.")
                return
            
            # --- Thực hiện hành động ---
            earnings = random.randint(150, 500)
            xp_earned_local = random.randint(5, 20)
            xp_earned_global = random.randint(10, 30)

            # Cập nhật dữ liệu kinh tế
            local_data["local_balance"]["earned"] += earnings
            local_data["xp_local"] += xp_earned_local
            global_profile["xp_global"] += xp_earned_global
            global_profile["cooldowns"]["work"] = now
            
            # Trừ chỉ số sinh tồn
            stats["energy"] = max(0, stats["energy"] - WORK_ENERGY_COST)
            stats["hunger"] = max(0, stats["hunger"] - WORK_HUNGER_COST)
            
            # Gửi thông báo cho người dùng
            await try_send(
                ctx, 
                content=(
                    f"{ICON_WORK} {ctx.author.mention}, bạn làm việc chăm chỉ và nhận được:\n"
                    f"  {ICON_ECOIN} **{earnings:,}** Ecoin (Tiền Sạch)\n"
                    f"  ✨ **{xp_earned_local}** XP (Server) & **{xp_earned_global}** XP (Global)"
                )
            )

            # --- KIỂM TRA LEVEL UP ---
            await check_and_process_levelup(ctx, local_data, 'local')
            await check_and_process_levelup(ctx, global_profile, 'global')

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'work' (v4) cho user {author_id}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi bạn đang làm việc.")

def setup(bot: commands.Bot):
    bot.add_cog(WorkCommandCog(bot))# bot/cogs/earn/work_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime
import logging
_cog(WorkCommandCog(bot))
