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
            now = datetime.now().timestamp()

            # Lấy dữ liệu từ DB
            author_global_profile = self.bot.db.get_or_create_global_user_profile(author_id)
            target_global_profile = self.bot.db.get_or_create_global_user_profile(target_id)
            author_local_data = self.bot.db.get_or_create_user_local_data(author_id, guild_id)
            target_local_data = self.bot.db.get_or_create_user_local_data(target_id, guild_id)

            # Kiểm tra chỉ số sinh tồn
            stats = author_local_data.get("survival_stats", {})
            if stats.get("energy", 0) < ROB_ENERGY_COST:
                await try_send(ctx, content=f"{ICON_SURVIVAL} Bạn quá mệt để cướp!")
                return
            if stats.get("hunger", 0) < ROB_HUNGER_COST:
                await try_send(ctx, content=f"{ICON_SURVIVAL} Đói quá, không chạy nổi để cướp!")
                return

            # Kiểm tra Cooldown
            last_rob = self.bot.db.get_cooldown(author_id, 'rob')
            if now - last_rob < ROB_COOLDOWN:
                time_left = str(datetime.fromtimestamp(last_rob + ROB_COOLDOWN) - datetime.now()).split('.')[0]
                await try_send(ctx, content=f"{ICON_LOADING} Cảnh sát đang rình! Lệnh `rob` còn chờ: **{time_left}**.")
                return

            # Trừ chỉ số, đặt cooldown
            new_energy = max(0, stats.get("energy", 0) - ROB_ENERGY_COST)
            new_hunger = max(0, stats.get("hunger", 0) - ROB_HUNGER_COST)
            self.bot.db.update_survival_stats(author_id, guild_id, energy=new_energy, hunger=new_hunger)
            self.bot.db.set_cooldown(author_id, 'rob', now)

            victim_balance = target_local_data['local_balance_earned'] + target_local_data['local_balance_adadd']
            if victim_balance < 200:
                await try_send(ctx, content=f"{ICON_INFO} {target.mention} quá nghèo để cướp.")
                return

            if random.random() < ROB_SUCCESS_RATE:
                robbed_amount = random.randint(int(victim_balance * 0.1), int(victim_balance * 0.3))
                robbed_amount = min(robbed_amount, victim_balance)

                # Cộng cho author
                self.bot.db.update_balance(author_id, guild_id, 'local_balance_earned', author_local_data['local_balance_earned'] + robbed_amount)

                # Trừ tiền của target (ưu tiên earned, còn thiếu trừ tiếp adadd)
                earned_deducted = min(target_local_data['local_balance_earned'], robbed_amount)
                adadd_deducted = robbed_amount - earned_deducted
                self.bot.db.update_balance(target_id, guild_id, 'local_balance_earned', target_local_data['local_balance_earned'] - earned_deducted)
                self.bot.db.update_balance(target_id, guild_id, 'local_balance_adadd', target_local_data['local_balance_adadd'] - adadd_deducted)

                await try_send(ctx, content=f"{ICON_ROB} Bạn đã cướp được **{robbed_amount:,}** {ICON_MONEY_BAG} từ {target.mention}!")
            else:
                fine_amount = int(author_local_data['local_balance_earned'] * ROB_FINE_RATE)
                fine_amount = min(fine_amount, author_local_data['local_balance_earned'])
                self.bot.db.update_balance(author_id, guild_id, 'local_balance_earned', author_local_data['local_balance_earned'] - fine_amount)
                await try_send(ctx, content=f"👮 {ICON_ERROR} Bạn đã bị bắt và bị phạt **{fine_amount:,}** {ICON_MONEY_BAG} từ Ví Local của bạn.")

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'rob' cho user {author_id}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi khi thực hiện hành vi cướp.")

def setup(bot: commands.Bot):
    bot.add_cog(RobCommandCog(bot))
