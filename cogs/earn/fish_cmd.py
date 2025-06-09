# bot/cogs/earn/fish_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime
import logging

from core.utils import try_send, require_travel_check
from core.config import FISH_COOLDOWN, FISH_CATCHES, FISH_ENERGY_COST, FISH_HUNGER_COST
from core.icons import ICON_LOADING, ICON_FISH, ICON_ERROR, ICON_TIEN_SACH, ICON_MONEY_BAG, ICON_SURVIVAL
from core.leveling import check_and_process_levelup

logger = logging.getLogger(__name__)

class FishCommandCog(commands.Cog, name="Fish Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("FishCommandCog (SQLite Ready) initialized.")

    @commands.command(name='fish')
    @commands.guild_only()
    @require_travel_check
    async def fish(self, ctx: commands.Context):
        author_id = ctx.author.id
        guild_id = ctx.guild.id

        try:
            local_data = self.bot.db.get_or_create_user_local_data(author_id, guild_id)

            if local_data['energy'] < FISH_ENERGY_COST:
                await try_send(ctx, content=f"{ICON_SURVIVAL} Bạn không đủ năng lượng để câu cá!")
                return
            if local_data['hunger'] < FISH_HUNGER_COST:
                await try_send(ctx, content=f"{ICON_SURVIVAL} Đói quá, cá kéo bạn xuống nước mất!")
                return

            now = datetime.now().timestamp()
            last_fish = self.bot.db.get_cooldown(author_id, "fish")
            if now - last_fish < FISH_COOLDOWN:
                time_left = str(datetime.fromtimestamp(last_fish + FISH_COOLDOWN) - datetime.now()).split('.')[0]
                await try_send(ctx, content=f"{ICON_LOADING} Cá chưa cắn câu đâu! Chờ: **{time_left}**.")
                return

            self.bot.db.update_user_stats(author_id, guild_id, energy=local_data['energy'] - FISH_ENERGY_COST, hunger=local_data['hunger'] - FISH_HUNGER_COST)
            self.bot.db.set_cooldown(author_id, "fish", now)

            catch_emoji, price = random.choice(list(FISH_CATCHES.items()))
            xp_earned_local = random.randint(3, 15)
            xp_earned_global = random.randint(5, 25)

            self.bot.db.update_balance(author_id, guild_id, 'local_balance_earned', local_data['local_balance_earned'] + price)
            self.bot.db.update_xp(author_id, guild_id, xp_earned_local, xp_earned_global)
            
            await try_send(ctx, content=f"{ICON_FISH} {ctx.author.mention}, bạn câu được {catch_emoji} bán được **{price:,}** {ICON_TIEN_SACH} và nhận XP!")
            
            updated_local = self.bot.db.get_or_create_user_local_data(author_id, guild_id)
            updated_global = self.bot.db.get_or_create_global_user_profile(author_id)
            await check_and_process_levelup(ctx, dict(updated_local), 'local')
            await check_and_process_levelup(ctx, dict(updated_global), 'global')

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'fish' cho user {author_id}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi khi bạn đi câu.")

def setup(bot: commands.Bot):
    bot.add_cog(FishCommandCog(bot))
