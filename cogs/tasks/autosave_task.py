# bot/cogs/tasks/autosave_task.py
import nextcord
from nextcord.ext import commands, tasks
import logging
import os # Thêm import os

from core.database import save_economy_data

logger = logging.getLogger(__name__)

class AutoSaveTaskCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Chỉ khởi động task nếu đang ở chế độ JSON
        self.db_type = os.getenv("DATABASE_TYPE", "json").lower()
        if self.db_type == 'json':
            self.autosave_loop.start()
            logger.info("AutoSaveTaskCog initialized and autosave task started (JSON mode).")
        else:
            logger.info("AutoSaveTaskCog initialized, autosave task is INACTIVE (SQLite mode).")


    def cog_unload(self):
        # Khi unload cog, chạy save lần cuối nếu là JSON mode
        if self.db_type == 'json' and self.autosave_loop.is_running():
            self.autosave_loop.cancel()
            logger.info("Auto-saving data before unloading cog (JSON mode)...")
            if hasattr(self.bot, 'economy_data'):
                # Ở đây, self.bot.db sẽ là db_json do logic ở main.py
                self.bot.db.save_economy_data(self.bot.economy_data)

    @tasks.loop(minutes=2)
    async def autosave_loop(self):
        """Tác vụ chạy nền để tự động lưu dữ liệu kinh tế từ cache vào file (chỉ cho JSON)."""
        if not hasattr(self.bot, 'economy_data'):
            logger.warning("AUTOSAVE_TASK: 'economy_data' not found in bot object. Skipping save.")
            return

        logger.info("AUTOSAVE_TASK: Saving economy data from cache to file...")
        try:
            # Ở đây, self.bot.db sẽ là db_json
            self.bot.db.save_economy_data(self.bot.economy_data)
            logger.info("AUTOSAVE_TASK: Data saved successfully.")
        except Exception as e:
            logger.error(f"Error in Auto-Save Task: {e}", exc_info=True)

    @autosave_loop.before_loop
    async def before_autosave_task(self):
        await self.bot.wait_until_ready()

def setup(bot: commands.Bot):
    bot.add_cog(AutoSaveTaskCog(bot))
