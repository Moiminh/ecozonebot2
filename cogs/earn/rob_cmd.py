# bot/cogs/earn/rob_cmd.py
import nextcord
from nextcord.ext import commands
import random
# bot/cogs/earn/rob_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime
import logging

from core.database import (
    load_economy_data,
    save_economy_data,
# bot/cogs/earn/rob_cmd.py
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
    ROB_COOLDOWN, ROB_SUCCESS_RATE, ROB_FINE_RATE,
    ROB_ENERGY_COST, ROB_HUNGER_COST
# bot/cogs/earn/rob_cmd.py
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
    ROB_COOLDOWN, ROB_SUCCESS_RATE, ROB_FINE_RATE,
    ROB_ENERGY_COST, ROB_HUNGER_COST
)
from core.icons import (
    ICON_LOADING, ICON_ERROR, ICON_INFO, ICON_ROB,
    ICON_MONEY_BAG, ICON_SURVIVAL
)
# [SỬA LỖI] Thêm import còn thiếu
from core.travel_manager import handle_travel_event

logger = logging.getLogger(__name__)

class RobCommandCog(commands.Cog, name="Rob Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("RobCommandCog (v3 - with Survival) initialized.")

    @commands.command(name='rob', aliases=['steal'])
    async def rob(self, ctx: commands.Context, target: nextcord.Member):
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Bạn chỉ có thể thực hiện hành vi phạm tội này trong một server!")
            return

        if target.bot or target.id == ctx.author.id:
            await try_send(ctx, content=f"{ICON_ERROR} Không thể cướp người chơi này.")
            return

        author_id = ctx.author.id
        target_id = target.id
        guild_id = ctx.guild.id

        try:
            economy_data = load_economy_data()
            author_global_profile = get_or_create_global_user_profile(economy_data, author_id)
            # --- Kiểm tra Last Active Guild ---
            if author_global_profile.get("last_active_guild_id") != guild_id:
                await handle_travel_event(ctx, self.bot)
                logger.info(f"User {author_id} has 'traveled' to guild {guild_id}. (Travel event)")
                # Thêm return để ngăn lệnh chạy tiếp trước khi travel hoàn tất
                return
            author_global_profile["last_active_guild_id"] = guild_id

            target_global_profile = get_or_create_global_user_profile(economy_data, target_id)
            author_local_data = get_or_create_user_local_data(author_global_profile, guild_id)
            target_local_data = get_or_create_user_local_data(target_global_profile, guild_id)

            # --- KIỂM TRA CHỈ SỐ SINH TỒN ---
            stats = author_local_data.get("survival_stats")
            if stats["energy"] < ROB_ENERGY_COST:
                await try_send(ctx, content=f"{ICON_SURVIVAL} Bạn quá mệt để cướp!")
                return
            if stats["hunger"] < ROB_HUNGER_COST:
                await try_send(ctx, content=f"{ICON_SURVIVAL} Đói quá, không chạy nổi để cướp!")
                return

            # --- Kiểm tra Cooldown ---
            now = datetime.now().timestamp()
            last_rob = author_global_profile.get("cooldowns", {}).get("rob", 0)
            if now - last_rob < ROB_COOLDOWN:
                time_left = str(datetime.fromtimestamp(last_rob + ROB_COOLDOWN) - datetime.now()).split('.')[0]
                await try_send(ctx, content=f"{ICON_LOADING} Cảnh sát đang rình! Lệnh `rob` còn chờ: **{time_left}**.")
                return

            # --- Trừ chỉ số sinh tồn ---
            stats["energy"] = max(0, stats["energy"] - ROB_ENERGY_COST)
            stats["hunger"] = max(0, stats["hunger"] - ROB_HUNGER_COST)

            # --- Thực hiện hành động ---
            victim_balance = target_local_data["local_balance"]["earned"] + target_local_data["local_balance"]["adadd"]
            author_global_profile["cooldowns"]["rob"] = now

            if victim_balance < 200:
                await try_send(ctx, content=f"{ICON_INFO} {target.mention} quá nghèo để cướp.")
                save_economy_data(economy_data)
                return

            if random.random() < ROB_SUCCESS_RATE:
                robbed_amount = random.randint(int(victim_balance * 0.1), int(victim_balance * 0.3))
                robbed_amount = min(robbed_amount, victim_balance)
                author_local_data["local_balance"]["earned"] += robbed_amount

                earned_deducted = min(target_local_data["local_balance"]["earned"], robbed_amount)
                adadd_deducted = robbed_amount - earned_deducted
                target_local_data["local_balance"]["earned"] -= earned_deducted
                target_local_data["local_balance"]["adadd"] -= adadd_deducted

                await try_send(ctx, content=f"{ICON_ROB} Bạn đã cướp được **{robbed_amount:,}** {ICON_MONEY_BAG} từ {target.mention}!")
            else:
                fine_amount = int(author_local_data["local_balance"]["earned"] * ROB_FINE_RATE)
                fine_amount = min(fine_amount, author_local_data["local_balance"]["earned"])
                author_local_data["local_balance"]["earned"] -= fine_amount

                await try_send(ctx, content=f"👮 {ICON_ERROR} Bạn đã bị bắt và bị phạt **{fine_amount:,}** {ICON_MONEY_BAG} từ Ví Local của bạn.")

            save_economy_data(economy_data)

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'rob' cho user {author_id}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi khi thực hiện hành vi cướp.")

def setup(bot: commands.Bot):
    bot.add_cog(RobCommandCog(bot))

# [SỬA LỖI] Loại bỏ khối code bị trùng lặp
e_amount

                await try_send(ctx, content=f"👮 {ICON_ERROR} Bạn đã bị bắt và bị phạt **{fine_amount:,}** {ICON_MONEY_BAG} từ Ví Local của bạn.")

            save_economy_data(economy_data)

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'rob' cho user {author_id}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi khi thực hiện hành vi cướp.")

def setup(bot: commands.Bot):
    bot.add_cog(RobCommandCog(bot))


            logger.error(f"Lỗi trong lệnh 'rob' cho user {author_id}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi khi thực hiện hành vi cướp.")

def setup(bot: commands.Bot):
    bot.add_cog(RobCommandCog(bot))

