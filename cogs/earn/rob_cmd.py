# bot/cogs/earn/rob_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime
import logging

from core.utils import try_send, require_travel_check
from core.config import ROB_COOLDOWN, ROB_SUCCESS_RATE, ROB_FINE_RATE, ROB_ENERGY_COST, ROB_HUNGER_COST
from core.icons import ICON_LOADING, ICON_ERROR, ICON_INFO, ICON_ROB, ICON_MONEY_BAG, ICON_SURVIVAL

logger = logging.getLogger(__name__)

class RobCommandCog(commands.Cog, name="Rob Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("RobCommandCog (SQLite Ready) initialized.")

    @commands.command(name='rob', aliases=['steal'])
    @commands.guild_only()
    @require_travel_check
    async def rob(self, ctx: commands.Context, target: nextcord.Member):
        if target.bot or target.id == ctx.author.id:
            await try_send(ctx, content=f"{ICON_ERROR} Không thể cướp người chơi này.")
            return

        author_id = ctx.author.id
        target_id = target.id
        guild_id = ctx.guild.id

        try:
            author_local_data = self.bot.db.get_or_create_user_local_data(author_id, guild_id)

            if author_local_data['energy'] < ROB_ENERGY_COST or author_local_data['hunger'] < ROB_HUNGER_COST:
                await try_send(ctx, content=f"{ICON_SURVIVAL} Bạn không đủ sức để đi cướp!")
                return

            now = datetime.now().timestamp()
            last_rob = self.bot.db.get_cooldown(author_id, "rob")
            if now - last_rob < ROB_COOLDOWN:
                time_left = str(datetime.fromtimestamp(last_rob + ROB_COOLDOWN) - datetime.now()).split('.')[0]
                await try_send(ctx, content=f"{ICON_LOADING} Cảnh sát đang rình! Chờ: **{time_left}**.")
                return

            self.bot.db.update_user_stats(author_id, guild_id, energy=author_local_data['energy'] - ROB_ENERGY_COST, hunger=author_local_data['hunger'] - ROB_HUNGER_COST)
            self.bot.db.set_cooldown(author_id, "rob", now)

            target_local_data = self.bot.db.get_or_create_user_local_data(target_id, guild_id)
            victim_balance = target_local_data['local_balance_earned'] + target_local_data['local_balance_adadd']
            
            if victim_balance < 200:
                await try_send(ctx, content=f"{ICON_INFO} {target.mention} quá nghèo để cướp.")
                return

            if random.random() < ROB_SUCCESS_RATE:
                robbed_amount = min(random.randint(int(victim_balance * 0.1), int(victim_balance * 0.3)), victim_balance)
                
                # Trừ tiền của nạn nhân
                adadd_deducted = min(target_local_data['local_balance_adadd'], robbed_amount)
                earned_deducted = robbed_amount - adadd_deducted
                self.bot.db.update_balance(target_id, guild_id, 'local_balance_adadd', target_local_data['local_balance_adadd'] - adadd_deducted)
                self.bot.db.update_balance(target_id, guild_id, 'local_balance_earned', target_local_data['local_balance_earned'] - earned_deducted)
                
                # Cộng tiền cho kẻ cướp
                self.bot.db.update_balance(author_id, guild_id, 'local_balance_earned', author_local_data['local_balance_earned'] + robbed_amount)
                
                await try_send(ctx, content=f"{ICON_ROB} Bạn đã cướp được **{robbed_amount:,}** {ICON_MONEY_BAG} từ {target.mention}!")
            else:
                fine_amount = min(int(author_local_data['local_balance_earned'] * ROB_FINE_RATE), author_local_data['local_balance_earned'])
                self.bot.db.update_balance(author_id, guild_id, 'local_balance_earned', author_local_data['local_balance_earned'] - fine_amount)
                await try_send(ctx, content=f"👮 {ICON_ERROR} Bạn đã bị bắt và bị phạt **{fine_amount:,}** {ICON_MONEY_BAG}.")

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'rob' cho user {author_id}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi khi thực hiện hành vi cướp.")

def setup(bot: commands.Bot):
    bot.add_cog(RobCommandCog(bot))
