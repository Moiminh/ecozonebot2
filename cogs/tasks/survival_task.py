# bot/cogs/tasks/survival_task.py
import nextcord
from nextcord.ext import commands, tasks
import logging

from core.database import load_economy_data, save_economy_data
from core.icons import ICON_WARNING, ICON_ECOIN

logger = logging.getLogger(__name__)

# Các hằng số cho sự suy giảm, có thể đưa vào config.py
HUNGER_DECAY_PER_HOUR = 2
ENERGY_DECAY_PER_HOUR = 3
HEALTH_DECAY_WHEN_STARVING = 5
FAINT_PENALTY_PERCENTAGE = 0.10 # 10%

class SurvivalTaskCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.stat_decay_loop.start()
        logger.info("SurvivalTaskCog initialized and stat decay task started.")

    def cog_unload(self):
        self.stat_decay_loop.cancel()
        logger.info("SurvivalTaskCog unloaded and stat decay task cancelled.")

    @tasks.loop(hours=1)
    async def stat_decay_loop(self):
        """
        Tác vụ chạy nền để giảm chỉ số sinh tồn của tất cả người chơi.
        """
        logger.info("Survival Decay Task: Running...")
        
        try:
            economy_data = load_economy_data()
            users_data = economy_data.get("users", {})

            # Lặp qua tất cả người chơi và tất cả các server họ đã tham gia
            for user_id, global_profile in users_data.items():
                for guild_id, local_data in global_profile.get("server_data", {}).items():
                    
                    stats = local_data.get("survival_stats")
                    if not stats:
                        continue # Bỏ qua nếu người dùng không có dữ liệu sinh tồn

                    # --- Logic suy giảm ---
                    stats["hunger"] = max(0, stats["hunger"] - HUNGER_DECAY_PER_HOUR)
                    stats["energy"] = max(0, stats["energy"] - ENERGY_DECAY_PER_HOUR)

                    # --- Hậu quả khi đói ---
                    if stats["hunger"] == 0:
                        stats["health"] = max(0, stats["health"] - HEALTH_DECAY_WHEN_STARVING)

                        # --- Hậu quả khi ngất xỉu ---
                        if stats["health"] == 0:
                            # Phạt tiền
                            earned_balance = local_data["local_balance"]["earned"]
                            penalty = int(earned_balance * FAINT_PENALTY_PERCENTAGE)
                            local_data["local_balance"]["earned"] -= penalty
                            
                            # Hồi phục lại một chút để tránh vòng lặp "chết"
                            stats["health"] = 50
                            stats["hunger"] = 50
                            stats["energy"] = 50

                            # Gửi tin nhắn riêng cho người chơi
                            try:
                                user = await self.bot.fetch_user(int(user_id))
                                guild = self.bot.get_guild(int(guild_id))
                                guild_name = guild.name if guild else "không xác định"
                                
                                await user.send(
                                    f"{ICON_WARNING} Bạn đã ngất xỉu vì kiệt sức tại server **{guild_name}**!\n"
                                    f"Bạn đã bị trừ **{penalty:,}** {ICON_ECOIN} và các chỉ số đã được hồi phục một phần."
                                )
                                logger.warning(f"User {user_id} fainted in guild {guild_id}, fined {penalty}.")
                            except Exception as dm_error:
                                logger.error(f"Could not send faint DM to {user_id}: {dm_error}")

            save_economy_data(economy_data)
            logger.info("Survival Decay Task: Finished and data saved.")

        except Exception as e:
            logger.error(f"Error in Survival Decay Task: {e}", exc_info=True)

    @stat_decay_loop.before_loop
    async def before_decay_task(self):
        await self.bot.wait_until_ready()

def setup(bot: commands.Bot):
    bot.add_cog(SurvivalTaskCog(bot))
