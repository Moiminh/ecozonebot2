# bot/cogs/earn/crime_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime
import logging

from core.utils import try_send, require_travel_check
from core.config import CRIME_COOLDOWN, CRIME_SUCCESS_RATE, CRIME_ENERGY_COST, CRIME_HUNGER_COST
from core.icons import ICON_LOADING, ICON_CRIME, ICON_ERROR, ICON_TIEN_SACH, ICON_MONEY_BAG, ICON_SURVIVAL
from core.leveling import check_and_process_levelup

logger = logging.getLogger(__name__)

class CrimeCommandCog(commands.Cog, name="Crime Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("CrimeCommandCog (SQLite Ready) initialized.")

    @commands.command(name='crime')
    @commands.guild_only()
    @require_travel_check
    async def crime(self, ctx: commands.Context):
        author_id = ctx.author.id
        guild_id = ctx.guild.id

        try:
            local_data = self.bot.db.get_or_create_user_local_data(author_id, guild_id)

            if local_data['energy'] < CRIME_ENERGY_COST:
                await try_send(ctx, content=f"{ICON_SURVIVAL} Bạn quá mệt mỏi để thực hiện phi vụ này!")
                return
            if local_data['hunger'] < CRIME_HUNGER_COST:
                await try_send(ctx, content=f"{ICON_SURVIVAL} Bạn quá đói để tập trung làm phi vụ!")
                return

            last_crime = self.bot.db.get_cooldown(author_id, "crime")
            now = datetime.now().timestamp()
            if now - last_crime < CRIME_COOLDOWN:
                time_left = str(datetime.fromtimestamp(last_crime + CRIME_COOLDOWN) - datetime.now()).split('.')[0]
                await try_send(ctx, content=f"{ICON_LOADING} Cảnh sát đang theo dõi! Chờ: **{time_left}**.")
                return

            self.bot.db.update_user_stats(author_id, guild_id, energy=local_data['energy'] - CRIME_ENERGY_COST, hunger=local_data['hunger'] - CRIME_HUNGER_COST)
            self.bot.db.set_cooldown(author_id, "crime", now)

            crimes_list = ["trộm vặt", "buôn lậu", "hack tài khoản", "tổ chức đua xe", "lừa đảo qua mạng"]
            chosen_crime = random.choice(crimes_list)

            if random.random() < CRIME_SUCCESS_RATE:
                earnings = random.randint(400, 1200)
                xp_earned_local = random.randint(10, 30)
                xp_earned_global = random.randint(20, 50)

                self.bot.db.update_balance(author_id, guild_id, 'local_balance_earned', local_data['local_balance_earned'] + earnings)
                self.bot.db.update_xp(author_id, guild_id, xp_earned_local, xp_earned_global)

                await try_send(ctx, content=f"{ICON_CRIME} Bạn đã thực hiện thành công phi vụ **'{chosen_crime}'** và nhận được **{earnings:,}** {ICON_TIEN_SACH} và XP!")
                
                # Check level up
                updated_local = self.bot.db.get_or_create_user_local_data(author_id, guild_id)
                updated_global = self.bot.db.get_or_create_global_user_profile(author_id)
                await check_and_process_levelup(ctx, dict(updated_local), 'local')
                await check_and_process_levelup(ctx, dict(updated_global), 'global')
            else:
                fine = random.randint(200, 800)
                actual_fine = min(fine, local_data['local_balance_earned'])
                self.bot.db.update_balance(author_id, guild_id, 'local_balance_earned', local_data['local_balance_earned'] - actual_fine)
                await try_send(ctx, content=f"{ICON_ERROR} Bạn đã thất bại với phi vụ **'{chosen_crime}'** và bị phạt **{actual_fine:,}** {ICON_MONEY_BAG}.")
        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'crime' cho user {author_id}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi khi thực hiện phi vụ.")

def setup(bot: commands.Bot):
    bot.add_cog(CrimeCommandCog(bot))
