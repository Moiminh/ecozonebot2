# bot/cogs/earn/daily_cmd.py
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
from core.config import DAILY_COOLDOWN # Lấy cooldown từ file config
from core.icons import ICON_LOADING, ICON_GIFT, ICON_MONEY_BAG, ICON_ERROR, ICON_TIEN_SACH

# Lấy logger cho module này
logger = logging.getLogger(__name__)

class DailyCommandCog(commands.Cog, name="Daily Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("DailyCommandCog (v2) initialized.")

    @commands.command(name='daily', aliases=['d'])
    async def daily(self, ctx: commands.Context):
        """Nhận phần thưởng hàng ngày của bạn."""
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server.")
            return

        author_id = ctx.author.id
        guild_id = ctx.guild.id
        
        try:
            # Tải dữ liệu
            economy_data = load_economy_data()
            global_profile = get_or_create_global_user_profile(economy_data, author_id)
            local_data = get_or_create_user_local_data(global_profile, guild_id)

            # --- Kiểm tra Cooldown ---
            now = datetime.now().timestamp()
            last_daily = global_profile.get("cooldowns", {}).get("daily", 0)
            
            if now - last_daily < DAILY_COOLDOWN:
                time_left = str(datetime.fromtimestamp(last_daily + DAILY_COOLDOWN) - datetime.now()).split('.')[0]
                await try_send(ctx, content=f"{ICON_LOADING} Bạn đã nhận thưởng ngày hôm nay rồi! Lệnh `daily` còn chờ: **{time_left}**.")
                return
            
            # --- Thực hiện hành động ---
            bonus = random.randint(500, 1500)
            xp_earned_local = random.randint(15, 50)
            xp_earned_global = random.randint(25, 75)

            # Cập nhật dữ liệu
            local_data["local_balance"]["earned"] += bonus
            local_data["xp_local"] += xp_earned_local
            global_profile["xp_global"] += xp_earned_global
            global_profile["cooldowns"]["daily"] = now
            
            # Lưu lại toàn bộ dữ liệu
            save_economy_data(economy_data)

            # Gửi thông báo cho người dùng
            total_local_balance = local_data["local_balance"]["earned"] + local_data["local_balance"]["adadd"]
            
            logger.info(f"User {author_id} tại guild {guild_id} đã nhận 'daily', nhận {bonus} earned và {xp_earned_local} xp_local.")

            await try_send(
                ctx, 
                content=(
                    f"{ICON_GIFT} {ctx.author.mention}, bạn đã nhận phần thưởng hàng ngày:\n"
                    f"  {ICON_TIEN_SACH} **{bonus:,}** Tiền Sạch\n"
                    f"  ✨ **{xp_earned_local}** XP (Server) & **{xp_earned_global}** XP (Global)\n"
                    f"Tổng Ví Local của bạn giờ là: **{total_local_balance:,}** {ICON_MONEY_BAG}"
                )
            )

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'daily' (v2) cho user {author_id}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi khi bạn nhận thưởng hàng ngày.")


def setup(bot: commands.Bot):
    bot.add_cog(DailyCommandCog(bot))
