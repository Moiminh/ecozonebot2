# bot/cogs/earn/crime_cmd.py
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
from core.config import CRIME_COOLDOWN, CRIME_SUCCESS_RATE
from core.icons import (
    ICON_LOADING, ICON_CRIME, ICON_ERROR, ICON_MONEY_BAG,
    ICON_TIEN_SACH, ICON_TIEN_LAU
)
from core.leveling import check_and_process_levelup  # ✅ Thêm dòng này

logger = logging.getLogger(__name__)

class CrimeCommandCog(commands.Cog, name="Crime Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("CrimeCommandCog (v2) initialized.")

    @commands.command(name='crime')
    async def crime(self, ctx: commands.Context):
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server.")
            return

        author_id = ctx.author.id
        guild_id = ctx.guild.id

        try:
            economy_data = load_economy_data()
            global_profile = get_or_create_global_user_profile(economy_data, author_id)
            local_data = get_or_create_user_local_data(global_profile, guild_id)

            now = datetime.now().timestamp()
            last_crime = global_profile.get("cooldowns", {}).get("crime", 0)

            if now - last_crime < CRIME_COOLDOWN:
                time_left = str(datetime.fromtimestamp(last_crime + CRIME_COOLDOWN) - datetime.now()).split('.')[0]
                await try_send(ctx, content=f"{ICON_LOADING} Cảnh sát đang theo dõi! Lệnh `crime` còn chờ: **{time_left}**.")
                return

            global_profile["cooldowns"]["crime"] = now

            crimes_list = ["trộm vặt", "buôn lậu", "hack tài khoản", "tổ chức đua xe", "lừa đảo qua mạng"]
            chosen_crime = random.choice(crimes_list)

            if random.random() < CRIME_SUCCESS_RATE:
                earnings = random.randint(400, 1200)
                xp_earned_local = random.randint(10, 30)
                xp_earned_global = random.randint(20, 50)

                local_data["local_balance"]["earned"] += earnings
                local_data["xp_local"] += xp_earned_local
                global_profile["xp_global"] += xp_earned_global

                await check_and_process_levelup(ctx, local_data, 'local')  # ✅ Thêm
                await check_and_process_levelup(ctx, global_profile, 'global')  # ✅ Thêm

                await try_send(
                    ctx,
                    content=(
                        f"{ICON_CRIME} Bạn đã thực hiện thành công phi vụ **'{chosen_crime}'** và nhận được:
"
                        f"  {ICON_TIEN_SACH} **{earnings:,}** Tiền Sạch
"
                        f"  ✨ **{xp_earned_local}** XP (Server) & **{xp_earned_global}** XP (Global)"
                    )
                )
            else:
                fine = random.randint(200, 800)
                adadd_balance = local_data["local_balance"]["adadd"]
                earned_balance = local_data["local_balance"]["earned"]
                total_local_balance = adadd_balance + earned_balance

                actual_fine = min(fine, total_local_balance)
                adadd_deducted = min(adadd_balance, actual_fine)
                earned_deducted = actual_fine - adadd_deducted

                local_data["local_balance"]["adadd"] -= adadd_deducted
                local_data["local_balance"]["earned"] -= earned_deducted

                await try_send(
                    ctx,
                    content=(
                        f"{ICON_ERROR} Bạn đã thất bại thảm hại khi **'{chosen_crime}'** và bị phạt **{actual_fine:,}** {ICON_MONEY_BAG}.
"
                        f"  (Trừ từ Tiền Lậu: {adadd_deducted:,} {ICON_TIEN_LAU} | Trừ từ Tiền Sạch: {earned_deducted:,} {ICON_TIEN_SACH})"
                    )
                )

            save_economy_data(economy_data)

            final_total_balance = local_data["local_balance"]["earned"] + local_data["local_balance"]["adadd"]
            await ctx.send(f"Tổng Ví Local của bạn hiện tại: **{final_total_balance:,}** {ICON_MONEY_BAG}")

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'crime' (v2) cho user {author_id}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi khi bạn đang thực hiện phi vụ.")

def setup(bot: commands.Bot):
    bot.add_cog(CrimeCommandCog(bot))
