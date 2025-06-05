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

# --- Discord Webhook Handler (ĐÃ SỬA LỖI ASYNCIO.RUN) ---
class DiscordWebhookHandler(logging.Handler):
    def __init__(self, webhook_url: str):
        super().__init__()
        self.webhook_url = webhook_url
        self.loop = None # Sẽ được lấy khi cần thiết

    async def _send_payload_async(self, payload: dict):
        """Hàm riêng để gửi payload một cách không đồng bộ."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    if response.status >= 400:
                        # Ghi lỗi này vào console/file log chính qua print để không tạo vòng lặp logging
                        print(f"[CRITICAL][WebhookSendError] Lỗi HTTP {response.status} khi gửi webhook: {await response.text()}")
                    # else:
                        # print(f"[DEBUG][WebhookSend] Webhook sent successfully, status: {response.status}") # Debug nếu cần
        except aiohttp.ClientError as e:
            print(f"[CRITICAL][WebhookSendError] Lỗi kết nối ClientError khi gửi webhook: {e}")
        except Exception as e:
            print(f"[CRITICAL][WebhookSendError] Lỗi không xác định khi gửi webhook: {e}")
            traceback.print_exc(file=open(os.path.join(LOG_DIRECTORY, "webhook_send_errors.log"), "a", encoding="utf-8")) # Ghi traceback vào file riêng

    def emit(self, record: logging.LogRecord):
        payload = None 
        log_time = datetime.fromtimestamp(record.created)

        try:
            if record.levelno >= logging.ERROR:
                message_content = record.getMessage() 
                description_parts = [
                    f"**Logger:** `{record.name}`",
                    f"**Thông điệp:**\n```\n{message_content[:1000]}\n```" # Giới hạn message
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
            
            if payload:
                if self.loop is None: # Lấy loop lần đầu nếu chưa có
                    try:
                        self.loop = asyncio.get_running_loop()
                    except RuntimeError:
                        # print("[WARNING][DiscordWebhookHandler] Không tìm thấy event loop đang chạy khi emit lần đầu.")
                        # Nếu không có loop, không thể gửi async.
                        # Trong ngữ cảnh bot Nextcord, điều này rất hiếm khi xảy ra khi emit được gọi.
                        # Hàm handleError sẽ được gọi nếu có lỗi ở đây.
                        self.handleError(record) 
                        return

                if self.loop.is_running():
                    # Sử dụng create_task để lên lịch coroutine chạy trên event loop
                    self.loop.create_task(self._send_payload_async(payload))
                else:
                    # print("[WARNING][DiscordWebhookHandler] Event loop không ở trạng thái running khi cố gắng gửi webhook.")
                    self.handleError(record) # Log lỗi nếu loop không chạy
        except Exception:
            self.handleError(record) # Bắt tất cả các lỗi khác trong quá trình chuẩn bị payload

# --- Hàm setup_logging (Giữ nguyên logic thiết lập các handler khác) ---
def setup_logging():
    if not os.path.exists(LOG_DIRECTORY):
        try:
            os.makedirs(LOG_DIRECTORY)
        except OSError as e:
            # Dùng print ở đây vì logger có thể chưa sẵn sàng hoàn toàn
            print(f"Không thể tạo thư mục logs: {e}") 
            return 

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # Dòng print debug này bạn có thể giữ lại hoặc xóa đi sau khi đã xác nhận URL webhook được đọc đúng
    webhook_url_for_debug = os.getenv("DISCORD_WEBHOOK_URL")
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
            maxBytes=5*1024*1024, backupCount=5
        )
        general_file_handler.setFormatter(file_log_formatter)
        general_file_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(general_file_handler)
    except Exception as e:
        print(f"Không thể thiết lập general_file_handler: {e}")

    # Action Log File Handler
    try:
        action_file_handler = logging.handlers.RotatingFileHandler(
            filename=action_log_filename, encoding='utf-8',
            maxBytes=2*1024*1024, backupCount=3
        )
        action_file_handler.setFormatter(file_log_formatter)
        action_file_handler.setLevel(logging.INFO)
        action_file_handler.addFilter(CogInfoFilter(prefix='cogs.', level=logging.INFO))
        root_logger.addHandler(action_file_handler)
    except Exception as e:
        print(f"Không thể thiết lập action_file_handler: {e}")

    # Console Handler
    try:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO) 
        root_logger.addHandler(console_handler)
    except Exception as e:
        print(f"Không thể thiết lập console_handler: {e}")

    # Webhook Handler
    webhook_url_from_env = os.getenv("DISCORD_WEBHOOK_URL") # Lấy lại URL, hoặc dùng biến đã lấy ở trên
    if webhook_url_from_env:
        try:
            webhook_handler = DiscordWebhookHandler(webhook_url_from_env)
            webhook_handler.setLevel(logging.INFO) 
            root_logger.addHandler(webhook_handler)
            logging.getLogger("BotSetup").info("Discord Webhook logging handler đã được thiết lập cho INFO (từ cogs) và ERROR/CRITICAL.")
        except Exception as e:
            logging.getLogger("BotSetup").error(f"Không thể thiết lập DiscordWebhookHandler: {e}", exc_info=True)
    else:
        logging.getLogger("BotSetup").warning("DISCORD_WEBHOOK_URL không được tìm thấy trong .env (kiểm tra từ logger.py). Logging qua Webhook bị vô hiệu hóa.")
    
    logging.getLogger("BotSetup").info("Hệ thống Logging đã được thiết lập (hoặc cố gắng thiết lập).")
    logging.getLogger("BotSetup").debug(f"General logs sẽ được ghi vào: {general_log_filename}")
    logging.getLogger("BotSetup").debug(f"Player action logs (INFO từ cogs) sẽ được ghi vào: {action_log_filename}")
