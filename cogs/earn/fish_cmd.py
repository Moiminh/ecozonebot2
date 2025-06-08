# bot/cogs/earn/fish_cmd.py
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
from core.config import (
    FISH_COOLDOWN, FISH_CATCHES,
    FISH_ENERGY_COST, FISH_HUNGER_COST
)
from core.icons import (
    ICON_LOADING, ICON_FISH, ICON_ERROR, ICON_TIEN_SACH,
    ICON_MONEY_BAG, ICON_SURVIVAL
)
from core.leveling import check_and_process_levelup

logger = logging.getLogger(__name__)

class FishCommandCog(commands.Cog, name="Fish Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("FishCommandCog (v3 - with Survival) initialized.")

    @commands.command(name='fish')
    async def fish(self, ctx: commands.Context):
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server.")
            return

        author_id = ctx.author.id
        guild_id = ctx.guild.id

        try:
            economy_data = load_economy_data()
            global_profile = get_or_create_global_user_profile(economy_data, author_id)
            if global_profile.get("last_active_guild_id") != guild_id:
            await handle_travel_event(ctx, self.bot)
            logger.info(f"User {author_id} has 'traveled' to guild {guild_id}. (Travel event)")
        global_profile["last_active_guild_id"] = guild_id

            local_data = get_or_create_user_local_data(global_profile, guild_id)

            # --- KIỂM TRA CHỈ SỐ SINH TỒN ---
            stats = local_data.get("survival_stats")
            if stats["energy"] < FISH_ENERGY_COST:
                await try_send(ctx, content=f"{ICON_SURVIVAL} Bạn không đủ năng lượng để câu cá!")
                return
            if stats["hunger"] < FISH_HUNGER_COST:
                await try_send(ctx, content=f"{ICON_SURVIVAL} Đói quá, cá kéo bạn xuống nước mất!")
                return

            # --- Kiểm tra Cooldown ---
            now = datetime.now().timestamp()
            last_fish = global_profile.get("cooldowns", {}).get("fish", 0)
            if now - last_fish < FISH_COOLDOWN:
                time_left = str(datetime.fromtimestamp(last_fish + FISH_COOLDOWN) - datetime.now()).split('.')[0]
                await try_send(ctx, content=f"{ICON_LOADING} Cá chưa cắn câu đâu! Chờ: **{time_left}**.")
                return

            # --- Trừ chỉ số sinh tồn ---
            stats["energy"] = max(0, stats["energy"] - FISH_ENERGY_COST)
            stats["hunger"] = max(0, stats["hunger"] - FISH_HUNGER_COST)

            # --- Thực hiện hành động ---
            global_profile["cooldowns"]["fish"] = now
            catch_emoji, price = random.choice(list(FISH_CATCHES.items()))
            xp_earned_local = random.randint(3, 15)
            xp_earned_global = random.randint(5, 25)

            local_data["local_balance"]["earned"] += price
            local_data["xp_local"] += xp_earned_local
            global_profile["xp_global"] += xp_earned_global

            await check_and_process_levelup(ctx, local_data, 'local')
            await check_and_process_levelup(ctx, global_profile, 'global')

            save_economy_data(economy_data)
            total_local_balance = local_data["local_balance"]["earned"] + local_data["local_balance"]["adadd"]
            await try_send(
                ctx,
                content=(
                    f"{ICON_FISH} {ctx.author.mention}, bạn câu được {catch_emoji} bán được **{price:,}** {ICON_TIEN_SACH}!\n"
                    f"✨ **{xp_earned_local}** XP (Server) & **{xp_earned_global}** XP (Global).\n"
                    f"Tổng Ví Local: **{total_local_balance:,}** {ICON_MONEY_BAG}"
                )
            )

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'fish' cho user {author_id}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi khi bạn đi câu.")

def setup(bot: commands.Bot):
    bot.add_cog(FishCommandCog(bot))
