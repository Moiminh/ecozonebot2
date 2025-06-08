# bot/cogs/earn/daily_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime
import logging

from core.database import (
    get_or_create_global_user_profile,
    get_or_create_user_local_data
)
from core.utils import try_send
from core.config import DAILY_COOLDOWN
from core.leveling import check_and_process_levelup
from core.icons import ICON_LOADING, ICON_GIFT, ICON_MONEY_BAG, ICON_ERROR, ICON_TIEN_SACH

logger = logging.getLogger(__name__)

class DailyCommandCog(commands.Cog, name="Daily Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("DailyCommandCog (v3 - Refactored) initialized.")

    @commands.command(name='daily', aliases=['d'])
    @commands.guild_only()
    async def daily(self, ctx: commands.Context):
        author_id = ctx.author.id
        guild_id = ctx.guild.id
        
        try:
            # [SỬA] Sử dụng cache từ bot
            economy_data = self.bot.economy_data
            global_profile = get_or_create_global_user_profile(economy_data, author_id)
            local_data = get_or_create_user_local_data(global_profile, guild_id)

            now = datetime.now().timestamp()
            last_daily = global_profile.get("cooldowns", {}).get("daily", 0)
            
            if now - last_daily < DAILY_COOLDOWN:
                time_left = str(datetime.fromtimestamp(last_daily + DAILY_COOLDOWN) - datetime.now()).split('.')[0]
                await try_send(ctx, content=f"{ICON_LOADING} Bạn đã nhận thưởng ngày hôm nay rồi! Lệnh `daily` còn chờ: **{time_left}**.")
                return
            
            bonus = random.randint(500, 1500)
            xp_earned_local = random.randint(15, 50)
            xp_earned_global = random.randint(25, 75)

            local_data["local_balance"]["earned"] += bonus
            local_data["xp_local"] += xp_earned_local
            global_profile["xp_global"] += xp_earned_global
            global_profile.setdefault("cooldowns", {})["daily"] = now
            
            total_local_balance = local_data["local_balance"]["earned"] + local_data["local_balance"]["adadd"]
            await try_send(
                ctx, 
                content=(
                    f"{ICON_GIFT} {ctx.author.mention}, bạn đã nhận phần thưởng hàng ngày:\n"
                    f"  {ICON_TIEN_SACH} **{bonus:,}** Tiền Sạch\n"
                    f"  ✨ **{xp_earned_local}** XP (Server) & **{xp_earned_global}** XP (Global)\n"
                    f"Tổng Ví Local của bạn giờ là: **{total_local_balance:,}** {ICON_MONEY_BAG}"
                )
            )

            await check_and_process_levelup(ctx, local_data, 'local')
            await check_and_process_levelup(ctx, global_profile, 'global')
            
            # [XÓA] Không cần save thủ công
            # save_economy_data(economy_data)

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'daily' (v3) cho user {author_id}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi khi bạn nhận thưởng hàng ngày.")

def setup(bot: commands.Bot):
    bot.add_cog(DailyCommandCog(bot))
