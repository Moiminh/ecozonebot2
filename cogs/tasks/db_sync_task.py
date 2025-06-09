import nextcord
from nextcord.ext import commands, tasks
import logging
import os
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)
# Đặt khoảng thời gian đồng bộ (phút)
DB_SYNC_INTERVAL_MINUTES = 15

# Đường dẫn tới thư mục git cục bộ (thư mục 'data')
REPO_PATH = "./data"
COMMIT_MSG = "Automatic DB sync"

class DatabaseSyncTaskCog(commands.Cog, name="Database Sync Task"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Chỉ chạy task này nếu bot đang ở chế độ SQLite
        db_type = os.getenv("DATABASE_TYPE", "json").lower()
        if db_type == 'sqlite':
            self.sync_database_task.start()
            logger.info(f"Database Sync Task has been started. Syncing every {DB_SYNC_INTERVAL_MINUTES} minutes.")
        else:
            logger.info("Database Sync Task is INACTIVE (not in SQLite mode).")

    def cog_unload(self):
        self.sync_database_task.cancel()

    async def run_git_command(self, command: str):
        """Chạy một lệnh shell trong thư mục repo và ghi lại kết quả."""
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=REPO_PATH  # Chạy lệnh trong thư mục ./data
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            # Ghi lại lỗi nhưng không dừng task, có thể do không có gì để commit
            error_message = stderr.decode().strip()
            logger.warning(f"Git command '{command}' may have failed. Stderr: {error_message}")
            # Trả về False nếu lỗi là nghiêm trọng
            if "fatal:" in error_message or "error:" in error_message:
                return False
        
        stdout_message = stdout.decode().strip()
        if stdout_message:
            logger.info(f"Git command stdout: {stdout_message}")
            
        return True

    @tasks.loop(minutes=DB_SYNC_INTERVAL_MINUTES)
    async def sync_database_task(self):
        # Đảm bảo file CSDL tồn tại trước khi chạy
        if not os.path.exists(os.path.join(REPO_PATH, 'econzone.sqlite')):
            logger.warning("DB_SYNC_TASK: econzone.sqlite not found. Skipping sync.")
            return

        logger.info("DB_SYNC_TASK: Starting database sync process...")
        
        # 1. Thêm file CSDL vào staging
        await self.run_git_command("git add econzone.sqlite")
        
        # 2. Commit các thay đổi
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Thêm --allow-empty để luôn tạo commit mới, ngay cả khi file không đổi
        await self.run_git_command(f"git commit --allow-empty -m \"{COMMIT_MSG} at {current_time}\"")
        
        # 3. Đẩy các thay đổi lên GitHub
        # Dùng -f (force) để ghi đè, đảm bảo phiên bản của bot luôn là mới nhất
        if await self.run_git_command("git push origin main -f"):
             logger.info("DB_SYNC_TASK: Successfully pushed database to GitHub.")
        else:
             logger.error("DB_SYNC_TASK: Failed to push database to GitHub. Check SSH keys and permissions.")

    @sync_database_task.before_loop
    async def before_sync(self):
        await self.bot.wait_until_ready()

def setup(bot: commands.Bot):
    bot.add_cog(DatabaseSyncTaskCog(bot))
