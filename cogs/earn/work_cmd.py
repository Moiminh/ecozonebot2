# bot/cogs/earn/work_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime
import logging

# [SỬA] không cần import database trực tiếp nữa
from core.utils import try_send, require_travel_check
from core.config import WORK_COOLDOWN, WORK_ENERGY_COST, WORK_HUNGER_COST
from core.leveling import check_and_process_levelup
from core.icons import (
    ICON_LOADING, ICON_WORK, ICON_MONEY_BAG, ICON_ERROR, 
    ICON_ECOIN, ICON_SURVIVAL
)

logger = logging.getLogger(__name__)

class WorkCommandCog(commands.Cog, name="Work Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("WorkCommandCog (v5 - SQLite Ready) initialized.")

    @commands.command(name='work', aliases=['w'])
    @commands.guild_only()
    @require_travel_check
    async def work(self, ctx: commands.Context):
        """Làm việc chăm chỉ để kiếm tiền sạch và kinh nghiệm (tiêu tốn năng lượng và độ no)."""
        author_id = ctx.author.id
        guild_id = ctx.guild.id
        
        try:
            # [NÂNG CẤP] Sử dụng self.bot.db đã được thiết lập ở main.py
            # Không dùng `bot.economy_data` nữa
            global_profile = self.bot.db.get_or_create_global_user_profile(author_id)
            local_data = self.bot.db.get_or_create_user_local_data(author_id, guild_id)

            # Giờ đây `local_data` là một đối tượng sqlite3.Row, truy cập bằng key như dict
            if local_data["energy"] < WORK_ENERGY_COST:
                await try_send(ctx, content=f"{ICON_SURVIVAL} Bạn quá mệt mỏi để làm việc! Hãy nghỉ ngơi hoặc dùng vật phẩm hồi phục.")
                return
            if local_data["hunger"] < WORK_HUNGER_COST:
                await try_send(ctx, content=f"{ICON_SURVIVAL} Bạn quá đói để làm việc! Hãy ăn gì đó trước đã.")
                return

            now = datetime.now().timestamp()
            # [NÂNG CẤP] Lấy cooldown từ CSDL
            last_work = self.bot.db.get_cooldown(author_id, 'work')
            if now - last_work < WORK_COOLDOWN:
                time_left = str(datetime.fromtimestamp(last_work + WORK_COOLDOWN) - datetime.now()).split('.')[0]
                await try_send(ctx, content=f"{ICON_LOADING} Bạn cần nghỉ ngơi! Lệnh `work` còn chờ: **{time_left}**.")
                return
            
            earnings = random.randint(150, 500)
            xp_earned_local = random.randint(5, 20)
            xp_earned_global = random.randint(10, 30)

            # [NÂNG CẤP] Gọi các hàm cập nhật riêng lẻ
            self.bot.db.update_balance(author_id, guild_id, 'local_balance_earned', local_data['local_balance_earned'] + earnings)
            self.bot.db.update_xp(author_id, guild_id, xp_earned_local, xp_earned_global)
            self.bot.db.set_cooldown(author_id, 'work', now)
            self.bot.db.update_user_stats(author_id, guild_id, WORK_ENERGY_COST, WORK_HUNGER_COST)
            
            await try_send(
                ctx, 
                content=(
                    f"{ICON_WORK} {ctx.author.mention}, bạn làm việc chăm chỉ và nhận được:\n"
                    f"  {ICON_ECOIN} **{earnings:,}** Ecoin (Tiền Sạch)\n"
                    f"  ✨ **{xp_earned_local}** XP (Server) & **{xp_earned_global}** XP (Global)"
                )
            )

            # check_and_process_levelup cần được điều chỉnh để nhận sqlite3.Row
            # Tạm thời, chúng ta sẽ truyền một dict giả để nó hoạt động
            # Về lâu dài, nên sửa hàm này để tương thích
            fake_local_dict = dict(local_data)
            fake_local_dict['xp_local'] += xp_earned_local # Cập nhật giá trị mới nhất
            fake_global_dict = dict(global_profile)
            fake_global_dict['xp_global'] += xp_earned_global

            await check_and_process_levelup(ctx, fake_local_dict, 'local')
            await check_and_process_levelup(ctx, fake_global_dict, 'global')

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'work' (SQLite mode) cho user {author_id}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi bạn đang làm việc.")

def setup(bot: commands.Bot):
    bot.add_cog(WorkCommandCog(bot))
