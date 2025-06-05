# bot/core/logger.py
import logging
import logging.handlers
import os
from datetime import datetime
import asyncio
import aiohttp
import traceback # Cần thiết để format traceback cho lỗi

LOG_DIRECTORY = "logs"
GENERAL_LOG_FILENAME_FORMAT = "bot_general_{timestamp}.log"
ACTION_LOG_FILENAME_FORMAT = "player_actions_{timestamp}.log"

# --- Filter tùy chỉnh cho Action Log File (Giữ nguyên) ---
class CogInfoFilter(logging.Filter):
    def __init__(self, prefix='cogs.', level=logging.INFO):
        super().__init__()
        self.prefix = prefix
        self.level = level
    def filter(self, record):
        return record.name.startswith(self.prefix) and record.levelno == self.level

# --- Discord Webhook Handler (Đã sửa lỗi asyncio.run và cải thiện việc lấy loop) ---
class DiscordWebhookHandler(logging.Handler):
    def __init__(self, webhook_url: str, bot_event_loop=None): # Nhận bot_event_loop
        super().__init__()
        self.webhook_url = webhook_url
        self.bot_event_loop = bot_event_loop # Lưu lại event loop của bot

    async def _send_payload_async(self, payload: dict):
        """Hàm riêng để gửi payload một cách không đồng bộ."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    if response.status >= 400:
                        print(f"[CRITICAL][WebhookSendError] Lỗi HTTP {response.status} khi gửi webhook: {await response.text()}")
                    # else:
                        # print(f"[DEBUG][WebhookSend] Webhook sent successfully, status: {response.status}")
        except aiohttp.ClientError as e:
            print(f"[CRITICAL][WebhookSendError] Lỗi kết nối ClientError khi gửi webhook: {e}")
        except Exception as e:
            print(f"[CRITICAL][WebhookSendError] Lỗi không xác định khi gửi webhook: {e}")
            # Ghi traceback vào file riêng để không làm ngập log chính nếu có lỗi liên tục
            log_dir_exists = os.path.exists(LOG_DIRECTORY)
            if not log_dir_exists:
                try: os.makedirs(LOG_DIRECTORY)
                except: pass # Bỏ qua nếu không tạo được ở đây
            
            if os.path.exists(LOG_DIRECTORY): # Chỉ ghi nếu thư mục tồn tại
                with open(os.path.join(LOG_DIRECTORY, "webhook_send_errors.log"), "a", encoding="utf-8") as f_err:
                    f_err.write(f"--- Webhook Send Error at {datetime.now()} ---\n")
                    traceback.print_exc(file=f_err)
                    f_err.write("\n")

    def emit(self, record: logging.LogRecord):
        payload = None 
        log_time = datetime.fromtimestamp(record.created)

        try: 
            if record.levelno >= logging.ERROR:
                message_content = record.getMessage() 
                description_parts = [
                    f"**Logger:** `{record.name}`",
                    f"**Thông điệp:**\n```\n{message_content[:1000]}\n```"
                ]
                if record.exc_info:
                    tb = "".join(traceback.format_exception(*record.exc_info))
                    if len(tb) > 1000: tb = tb[:990] + "\n... (traceback bị cắt bớt)"
                    description_parts.append(f"**Traceback:**\n```python\n{tb}\n```")
                embed_color = 0xff0000 if record.levelno == logging.ERROR else 0xcc0000
                embed = {
                    "title": f"🚨 Lỗi Bot: {record.levelname}",
                    "description": "\n".join(description_parts),
                    "color": embed_color,
                    "timestamp": log_time.isoformat()
                }
                payload = {"embeds": [embed]}
            elif record.levelno == logging.INFO and record.name.startswith('cogs.'):
                formatted_time = log_time.strftime("%d/%m/%y (%H:%M:%S)")
                action_message = record.getMessage()
                final_log_string = f"[{formatted_time}] {action_message}"
                if len(final_log_string) > 1990:
                    final_log_string = final_log_string[:1987] + "..."
                payload = {"content": final_log_string}
        except Exception as e_format:
            print(f"[ERROR][DiscordWebhookHandler] Lỗi khi định dạng log record: {e_format}")
            self.handleError(record)
            return

        if payload:
            loop_to_use = self.bot_event_loop
            if loop_to_use is None: # Nếu bot_event_loop không được truyền vào lúc khởi tạo
                try:
                    loop_to_use = asyncio.get_running_loop()
                except RuntimeError:
                    print("[WARNING][DiscordWebhookHandler] Không tìm thấy event loop đang chạy để gửi webhook. Log có thể bị mất.")
                    return # Không thể gửi nếu không có loop

            if loop_to_use and loop_to_use.is_running():
                try:
                    # asyncio.run_coroutine_threadsafe an toàn khi gọi từ một luồng khác (logging có thể chạy trên thread riêng)
                    # hoặc khi bạn không chắc chắn về ngữ cảnh luồng.
                    asyncio.run_coroutine_threadsafe(self._send_payload_async(payload), loop_to_use)
                except Exception as e_task:
                    print(f"[ERROR][DiscordWebhookHandler] Lỗi khi lên lịch gửi webhook: {e_task}")
                    self.handleError(record)
            else:
                print("[WARNING][DiscordWebhookHandler] Event loop không ở trạng thái running hoặc không tồn tại khi cố gắng gửi webhook.")
        # else:
            # print(f"Skipping webhook for record: {record.name} - {record.levelname}")

# --- Hàm setup_logging ---
# Tham số bot_event_loop sẽ được truyền từ main.py
def setup_logging(bot_event_loop=None): 
    if not os.path.exists(LOG_DIRECTORY):
        try:
            os.makedirs(LOG_DIRECTORY)
        except OSError as e:
            print(f"Không thể tạo thư mục logs: {e}") 
            return 

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    webhook_url_for_debug = os.getenv("DISCORD_WEBHOOK_URL")
    # Dòng print này có thể comment lại sau khi xác nhận URL được đọc đúng
    print(f"\n[DEBUG FROM LOGGER.PY] Webhook URL from env at setup_logging start: '{webhook_url_for_debug}'\n") 

    general_log_filename = os.path.join(LOG_DIRECTORY, GENERAL_LOG_FILENAME_FORMAT.format(timestamp=timestamp))
    action_log_filename = os.path.join(LOG_DIRECTORY, ACTION_LOG_FILENAME_FORMAT.format(timestamp=timestamp))

    file_log_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)-8s] [%(name)-35s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_formatter = logging.Formatter(
        '[%(levelname)-8s] [%(name)-25s] %(message)s'
    )

    root_logger = logging.getLogger() 
    root_logger.setLevel(logging.DEBUG)
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # General File Handler
    try: 
        general_file_handler = logging.handlers.RotatingFileHandler(
            filename=general_log_filename, encoding='utf-8',
            maxBytes=5*1024*1024, backupCount=5)
        general_file_handler.setFormatter(file_log_formatter)
        general_file_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(general_file_handler)
    except Exception as e: print(f"Không thể thiết lập general_file_handler: {e}")
    
    # Action Log File Handler
    try: 
        action_file_handler = logging.handlers.RotatingFileHandler(
            filename=action_log_filename, encoding='utf-8',
            maxBytes=2*1024*1024, backupCount=3)
        action_file_handler.setFormatter(file_log_formatter)
        action_file_handler.setLevel(logging.INFO)
        action_file_handler.addFilter(CogInfoFilter(prefix='cogs.', level=logging.INFO))
        root_logger.addHandler(action_file_handler)
    except Exception as e: print(f"Không thể thiết lập action_file_handler: {e}")
    
    # Console Handler
    try: 
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO) 
        root_logger.addHandler(console_handler)
    except Exception as e: print(f"Không thể thiết lập console_handler: {e}")

    # Webhook Handler
    if webhook_url_for_debug:
        try:
            # Truyền bot_event_loop vào handler khi khởi tạo
            webhook_handler = DiscordWebhookHandler(webhook_url_for_debug, bot_event_loop=bot_event_loop) 
            webhook_handler.setLevel(logging.INFO) # Webhook sẽ nhận INFO trở lên, emit sẽ lọc chi tiết
            root_logger.addHandler(webhook_handler)
            logging.getLogger("BotSetup").info("Discord Webhook logging handler đã được thiết lập.")
        except Exception as e:
            logging.getLogger("BotSetup").error(f"Không thể thiết lập DiscordWebhookHandler: {e}", exc_info=True)
    else:
        logging.getLogger("BotSetup").warning("DISCORD_WEBHOOK_URL không được tìm thấy trong .env. Logging qua Webhook bị vô hiệu hóa.")
    
    logging.getLogger("BotSetup").info("Hệ thống Logging đã được thiết lập (hoặc cố gắng thiết lập).")
    logging.getLogger("BotSetup").debug(f"General logs sẽ được ghi vào: {general_log_filename}")
    logging.getLogger("BotSetup").debug(f"Player action logs (INFO từ cogs) sẽ được ghi vào: {action_log_filename}")
