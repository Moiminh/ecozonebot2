# bot/cogs/earn/work_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime
import logging

from core.database import (
    load_economy_data,
    save_economy_data,
    get_or_create_global_user_profile,
    get_or_create_user_local_data
)
from core.utils import try_send
from core.config import WORK_COOLDOWN
# Import hàm xử lý level up mới
from core.leveling import check_and_process_levelup
from core.icons import ICON_LOADING, ICON_WORK, ICON_MONEY_BAG, ICON_ERROR, ICON_TIEN_SACH

logger = logging.getLogger(__name__)

class WorkCommandCog(commands.Cog, name="Work Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("WorkCommandCog (v2) - with Leveling - initialized.")

    @commands.command(name='work', aliases=['w'])
    async def work(self, ctx: commands.Context):
        """Làm việc chăm chỉ để kiếm tiền sạch và kinh nghiệm."""
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server.")
            return

        author_id = ctx.author.id
        guild_id = ctx.guild.id
        
        try:
            economy_data = load_economy_data()
            global_profile = get_or_create_global_user_profile(economy_data, author_id)
            local_data = get_or_create_user_local_data(global_profile, guild_id)

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

            # Cập nhật dữ liệu
            local_data["local_balance"]["earned"] += earnings
            local_data["xp_local"] += xp_earned_local
            global_profile["xp_global"] += xp_earned_global
            global_profile["cooldowns"]["work"] = now
            
            # Gửi thông báo cho người dùng
            total_local_balance = local_data["local_balance"]["earned"] + local_data["local_balance"]["adadd"]
            
            logger.info(f"User {author_id} tại guild {guild_id} đã 'work', nhận {earnings} earned và {xp_earned_local} xp_local.")

            await try_send(
                ctx, 
                content=(
                    f"{ICON_WORK} {ctx.author.mention}, bạn làm việc chăm chỉ và nhận được:\n"
                    f"  {ICON_TIEN_SACH} **{earnings:,}** Tiền Sạch\n"
                    f"  ✨ **{xp_earned_local}** XP (Server) & **{xp_earned_global}** XP (Global)\n"
                    f"Tổng Ví Local của bạn giờ là: **{total_local_balance:,}** {ICON_MONEY_BAG}"
                )
            )

            # --- KIỂM TRA LEVEL UP (TÍCH HỢP MỚI) ---
            await check_and_process_levelup(ctx, local_data, 'local')
            await check_and_process_levelup(ctx, global_profile, 'global')

            # Lưu lại toàn bộ dữ liệu sau khi đã kiểm tra level up
            save_economy_data(economy_data)

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'work' (v2) cho user {author_id}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi khi bạn đang làm việc.")


def setup(bot: commands.Bot):
    bot.add_cog(WorkCommandCog(bot))
