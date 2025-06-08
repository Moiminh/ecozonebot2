import nextcord
from nextcord.ext import commands, tasks
import logging

from core.database import save_economy_data

logger = logging.getLogger(__name__)

class AutoSaveTaskCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.autosave_loop.start()
        logger.info("AutoSaveTaskCog initialized and autosave task started.")

    def cog_unload(self):
        # Khi unload cog, chạy save lần cuối
        self.autosave_loop.cancel()
        logger.info("Auto-saving data before unloading cog...")
        if hasattr(self.bot, 'economy_data'):
            save_economy_data(self.bot.economy_data)

    @tasks.loop(minutes=2) # Lưu dữ liệu mỗi 2 phút
    async def autosave_loop(self):
        """Tác vụ chạy nền để tự động lưu dữ liệu kinh tế từ cache vào file."""
        if not hasattr(self.bot, 'economy_data'):
            logger.warning("AUTOSAVE_TASK: 'economy_data' not found in bot object. Skipping save.")
            return

        logger.info("AUTOSAVE_TASK: Saving economy data from cache to file...")
        try:
            save_economy_data(self.bot.economy_data)
            logger.info("AUTOSAVE_TASK: Data saved successfully.")
        except Exception as e:
            logger.error(f"Error in Auto-Save Task: {e}", exc_info=True)

    @autosave_loop.before_loop
    async def before_autosave_task(self):
        await self.bot.wait_until_ready()

def setup(bot: commands.Bot):
    bot.add_cog(AutoSaveTaskCog(bot))
