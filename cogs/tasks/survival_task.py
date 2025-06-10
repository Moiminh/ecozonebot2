# bot/cogs/tasks/survival_task.py
import nextcord
from nextcord.ext import commands, tasks
import logging

from core.icons import ICON_WARNING, ICON_ECOIN

logger = logging.getLogger(__name__)

# Các hằng số cho sự suy giảm
HUNGER_DECAY_PER_HOUR = 2
ENERGY_DECAY_PER_HOUR = 3
HEALTH_DECAY_WHEN_STARVING = 5
FAINT_PENALTY_PERCENTAGE = 0.05 # Phạt 5%

class SurvivalTaskCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Chỉ chạy task nếu bot dùng SQLite
        if getattr(self.bot, 'db_type', 'json') == 'sqlite':
            self.stat_decay_loop.start()
            logger.info("SurvivalTaskCog (SQLite Ready) initialized and stat decay task started.")
        else:
            logger.info("SurvivalTaskCog is INACTIVE (Non-SQLite mode).")


    def cog_unload(self):
        if self.stat_decay_loop.is_running():
            self.stat_decay_loop.cancel()
            logger.info("SurvivalTaskCog unloaded and stat decay task cancelled.")

    @tasks.loop(hours=1)
    async def stat_decay_loop(self):
        """
        Tác vụ chạy nền để giảm chỉ số sinh tồn của tất cả người chơi (phiên bản SQLite).
        """
        logger.info("Survival Decay Task (SQLite): Running...")
        
        try:
            conn = self.bot.db.get_db_connection()
            cursor = conn.cursor()

            # Lấy tất cả dữ liệu người dùng-server đang hoạt động (chỉ số > 0)
            cursor.execute("SELECT * FROM user_guild_data WHERE health > 0 OR hunger > 0 OR energy > 0")
            active_users = cursor.fetchall()

            for user_row in active_users:
                user_id = user_row['user_id']
                guild_id = user_row['guild_id']
                
                health = user_row['health']
                hunger = user_row['hunger']
                energy = user_row['energy']
                earned_balance = user_row['local_balance_earned']

                # --- Logic suy giảm ---
                new_hunger = max(0, hunger - HUNGER_DECAY_PER_HOUR)
                new_energy = max(0, energy - ENERGY_DECAY_PER_HOUR)
                new_health = health

                # --- Hậu quả khi đói ---
                if new_hunger == 0:
                    new_health = max(0, health - HEALTH_DECAY_WHEN_STARVING)

                # --- Hậu quả khi ngất xỉu ---
                if new_health == 0:
                    penalty = int(earned_balance * FAINT_PENALTY_PERCENTAGE)
                    final_earned_balance = earned_balance - penalty
                    
                    # Reset chỉ số sinh tồn và cập nhật tiền
                    cursor.execute("""
                        UPDATE user_guild_data 
                        SET health = 50, hunger = 50, energy = 50, local_balance_earned = ?
                        WHERE user_id = ? AND guild_id = ?
                    """, (final_earned_balance, user_id, guild_id))
                    
                    try:
                        user = await self.bot.fetch_user(int(user_id))
                        guild = self.bot.get_guild(int(guild_id))
                        guild_name = guild.name if guild else f"ID: {guild_id}"
                        
                        await user.send(
                            f"{ICON_WARNING} Bạn đã ngất xỉu vì kiệt sức tại server **{guild_name}**!\n"
                            f"Bạn đã bị trừ **{penalty:,}** {ICON_ECOIN} và các chỉ số đã được hồi phục một phần."
                        )
                        logger.warning(f"User {user_id} fainted in guild {guild_id}, fined {penalty}.")
                    except Exception as dm_error:
                        logger.error(f"Could not send faint DM to {user_id}: {dm_error}")
                else:
                    # Cập nhật chỉ số bình thường
                    cursor.execute("""
                        UPDATE user_guild_data 
                        SET health = ?, hunger = ?, energy = ?
                        WHERE user_id = ? AND guild_id = ?
                    """, (new_health, new_hunger, new_energy, user_id, guild_id))
            
            conn.commit()
            conn.close()
            logger.info("Survival Decay Task (SQLite): Finished.")

        except Exception as e:
            logger.error(f"Error in Survival Decay Task (SQLite): {e}", exc_info=True)
            if 'conn' in locals() and conn:
                conn.close()

    @stat_decay_loop.before_loop
    async def before_decay_task(self):
        await self.bot.wait_until_ready()

def setup(bot: commands.Bot):
    bot.add_cog(SurvivalTaskCog(bot))
