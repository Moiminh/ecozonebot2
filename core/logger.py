# bot/core/logger.py
import logging
import logging.handlers # Cần thiết cho RotatingFileHandler
import os
from datetime import datetime

LOG_DIRECTORY = "logs" # Thư mục để lưu tất cả các file log
GENERAL_LOG_FILENAME_FORMAT = "bot_general_{timestamp}.log" 
ACTION_LOG_FILENAME_FORMAT = "player_actions_{timestamp}.log"

# --- Filter tùy chỉnh cho Action Log ---
class CogInfoFilter(logging.Filter):
    """
    Filter này chỉ cho phép các log record có cấp độ INFO 
    và được tạo bởi các logger có tên bắt đầu bằng 'cogs.' đi qua.
    """
    def __init__(self, prefix='cogs.', level=logging.INFO): # Thêm level vào init
        super().__init__()
        self.prefix = prefix
        self.level = level

    def filter(self, record):
        return record.name.startswith(self.prefix) and record.levelno == self.level

def setup_logging():
    """Thiết lập hệ thống logging cho toàn bộ bot."""

    # Tạo thư mục logs nếu chưa tồn tại
    if not os.path.exists(LOG_DIRECTORY):
        try:
            os.makedirs(LOG_DIRECTORY)
        except OSError as e:
            print(f"Không thể tạo thư mục logs: {e}")
            # Không thể tiếp tục nếu không tạo được thư mục log
            return 

    # Tạo tên file log động với timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    general_log_filename = os.path.join(LOG_DIRECTORY, GENERAL_LOG_FILENAME_FORMAT.format(timestamp=timestamp))
    action_log_filename = os.path.join(LOG_DIRECTORY, ACTION_LOG_FILENAME_FORMAT.format(timestamp=timestamp))

    # Định dạng chung cho các thông điệp log trong file (chi tiết)
    file_log_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)-8s] [%(name)-35s] %(message)s', # Tăng độ rộng cho name để dễ đọc hơn
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    # Định dạng cho console (có thể đơn giản hơn)
    console_formatter = logging.Formatter(
        '[%(levelname)-8s] [%(name)-25s] %(message)s' # Giảm độ rộng name cho console
    )

    # Lấy root logger để cấu hình chung cho tất cả các logger con
    # (Trừ khi logger con được cấu hình riêng hoặc tắt propagate)
    root_logger = logging.getLogger() 
    root_logger.setLevel(logging.DEBUG) # Root logger sẽ bắt tất cả các thông điệp từ DEBUG trở lên

    # Xóa các handler mặc định có thể đã được thêm vào root logger (nếu có)
    # để tránh log bị lặp lại hoặc ghi bởi handler không mong muốn.
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # --- General File Handler: Ghi tất cả log (từ DEBUG trở lên) vào file chung ---
    try:
        general_file_handler = logging.handlers.RotatingFileHandler(
            filename=general_log_filename,
            encoding='utf-8',
            maxBytes=5*1024*1024,  # Ví dụ: 5MB mỗi file
            backupCount=5  # Giữ lại 5 file backup
        )
        general_file_handler.setFormatter(file_log_formatter)
        general_file_handler.setLevel(logging.DEBUG) # File này ghi tất cả từ DEBUG
        root_logger.addHandler(general_file_handler)
    except Exception as e:
        print(f"Không thể thiết lập general_file_handler: {e}")


    # --- Action Log File Handler: Ghi INFO từ các module trong 'cogs.' vào file hành động ---
    try:
        action_file_handler = logging.handlers.RotatingFileHandler(
            filename=action_log_filename,
            encoding='utf-8',
            maxBytes=2*1024*1024, # File action log có thể nhỏ hơn
            backupCount=3
        )
        action_file_handler.setFormatter(file_log_formatter) # Dùng chung formatter chi tiết
        action_file_handler.setLevel(logging.INFO) # Chỉ quan tâm đến INFO cho action log
        action_file_handler.addFilter(CogInfoFilter(prefix='cogs.', level=logging.INFO)) # Áp dụng filter
        root_logger.addHandler(action_file_handler)
    except Exception as e:
        print(f"Không thể thiết lập action_file_handler: {e}")


    # --- Console (Stream) Handler: Hiển thị log (từ INFO trở lên) ra terminal ---
    try:
        console_handler = logging.StreamHandler() # Mặc định là sys.stderr, có thể đổi sang sys.stdout
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO) # Chỉ hiển thị INFO và các cấp độ cao hơn ra console
        root_logger.addHandler(console_handler)
    except Exception as e:
        print(f"Không thể thiết lập console_handler: {e}")


    # Logger riêng cho thông báo setup để tránh bị filter nếu root logger thay đổi
    # Hoặc đơn giản là dùng logging.info trực tiếp vì root logger đã được cấu hình
    logging.getLogger("BotSetup").info("Hệ thống Logging đã được thiết lập.")
    logging.getLogger("BotSetup").debug(f"General logs sẽ được ghi vào: {general_log_filename}")
    logging.getLogger("BotSetup").debug(f"Player action logs (INFO từ cogs) sẽ được ghi vào: {action_log_filename}")

