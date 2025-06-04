# bot/core/logger.py
import logging
import logging.handlers
import os
from datetime import datetime

LOG_DIRECTORY = "logs"
GENERAL_LOG_FILENAME_FORMAT = "bot_general_{timestamp}.log" # Đổi tên để phân biệt
ACTION_LOG_FILENAME_FORMAT = "player_actions_{timestamp}.log" # File log cho hành động người chơi

# --- Filter tùy chỉnh cho Action Log ---
class CogInfoFilter(logging.Filter):
    def filter(self, record):
        # Chỉ cho phép log từ các logger có tên bắt đầu bằng 'cogs.' 
        # và có cấp độ là INFO
        return record.name.startswith('cogs.') and record.levelno == logging.INFO

def setup_logging():
    if not os.path.exists(LOG_DIRECTORY):
        os.makedirs(LOG_DIRECTORY)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    general_log_filename = os.path.join(LOG_DIRECTORY, GENERAL_LOG_FILENAME_FORMAT.format(timestamp=timestamp))
    action_log_filename = os.path.join(LOG_DIRECTORY, ACTION_LOG_FILENAME_FORMAT.format(timestamp=timestamp))

    # Định dạng chung cho file log (bao gồm tên logger để biết từ module nào)
    file_log_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)-8s] [%(name)-30s] %(message)s', # Tăng độ rộng cho name
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_formatter = logging.Formatter(
        '[%(levelname)-8s] [%(name)-20s] %(message)s' # Giữ console formatter cũ hoặc tùy chỉnh
    )

    logger = logging.getLogger() # Lấy root logger
    logger.setLevel(logging.DEBUG) # Root logger bắt tất cả từ DEBUG trở lên

    # --- General File Handler: Ghi tất cả log (từ DEBUG trở lên) vào file chung ---
    general_file_handler = logging.handlers.RotatingFileHandler(
        filename=general_log_filename,
        encoding='utf-8',
        maxBytes=5*1024*1024,
        backupCount=5
    )
    general_file_handler.setFormatter(file_log_formatter)
    general_file_handler.setLevel(logging.DEBUG) # File này ghi tất cả debug
    logger.addHandler(general_file_handler)

    # --- Action Log File Handler: Ghi INFO từ cogs vào file hành động người chơi ---
    action_file_handler = logging.handlers.RotatingFileHandler(
        filename=action_log_filename,
        encoding='utf-8',
        maxBytes=2*1024*1024, # Có thể đặt kích thước nhỏ hơn cho file action log
        backupCount=3
    )
    action_file_handler.setFormatter(file_log_formatter) # Dùng chung formatter chi tiết
    action_file_handler.setLevel(logging.INFO) # Chỉ quan tâm đến INFO level cho action log
    action_file_handler.addFilter(CogInfoFilter()) # Thêm filter tùy chỉnh
    logger.addHandler(action_file_handler) # Thêm handler này vào root logger

    # --- Console (Stream) Handler: Hiển thị log (từ INFO trở lên) ra terminal ---
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO) 
    logger.addHandler(console_handler)

    initial_logger = logging.getLogger("BotSetup") # Logger riêng cho thông báo setup
    initial_logger.info("Hệ thống Logging đã được thiết lập.")
    initial_logger.debug(f"General logs: {general_log_filename}")
    initial_logger.debug(f"Player action logs: {action_log_filename}")
