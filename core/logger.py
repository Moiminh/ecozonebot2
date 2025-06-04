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

# --- Discord Webhook Handler (CẬP NHẬT ĐỂ XỬ LÝ 2 LOẠI THÔNG BÁO) ---
class DiscordWebhookHandler(logging.Handler):
    def __init__(self, webhook_url: str):
        super().__init__()
        self.webhook_url = webhook_url
        self.loop = None
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError: # No running event loop
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
        # Không cần setFormatter cho handler này vì chúng ta sẽ tự định dạng trong emit

    async def _send_payload_async(self, payload: dict):
        """Hàm riêng để gửi payload một cách không đồng bộ."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.webhook_url, json=payload) as response:
                    if response.status >= 400:
                        # Ghi lỗi này vào console/file log chính, không gửi lại qua webhook để tránh vòng lặp
                        print(f"[ERROR][DiscordWebhookHandler] Lỗi khi gửi webhook: {response.status} - {await response.text()}")
            except aiohttp.ClientError as e:
                print(f"[ERROR][DiscordWebhookHandler] Lỗi kết nối khi gửi webhook: {e}")
            except Exception as e:
                print(f"[ERROR][DiscordWebhookHandler] Lỗi không xác định khi gửi webhook: {e}")

    def emit(self, record: logging.LogRecord):
        # Handler này sẽ nhận tất cả log từ level đã set cho nó (sẽ là INFO trong setup_logging)
        # Chúng ta sẽ quyết định gửi gì dựa trên record.levelno và record.name
        payload = None
        log_time = datetime.fromtimestamp(record.created)

        if record.levelno >= logging.ERROR: # Xử lý lỗi ERROR và CRITICAL
            # Định dạng Embed chi tiết cho lỗi
            embed_color = 0xff0000 if record.levelno == logging.ERROR else 0xcc0000 
            
            # Lấy thông điệp gốc, không qua formatter của handler (nếu có)
            message_content = record.getMessage() 
            
            description_parts = [
                f"**Logger:** `{record.name}`",
                f"**Thông điệp:**\n```\n{message_content[:1000]}\n```" # Giới hạn message
            ]
            
            if record.exc_info:
                tb = "".join(traceback.format_exception(*record.exc_info))
                if len(tb) > 1000: tb = tb[:990] + "\n... (traceback bị cắt bớt)"
                description_parts.append(f"**Traceback:**\n```python\n{tb}\n```")

            embed = {
                "title": f"🚨 Lỗi Bot: {record.levelname}",
                "description": "\n".join(description_parts),
                "color": embed_color,
                "timestamp": log_time.isoformat()
            }
            payload = {"embeds": [embed]}

        elif record.levelno == logging.INFO and record.name.startswith('cogs.'): # Xử lý thao tác người dùng
            # Định dạng text đơn giản cho thao tác người dùng
            formatted_time = log_time.strftime("%d/%m/%y (%H:%M:%S)") # Thêm giây cho rõ ràng
            
            # record.getMessage() đã chứa thông tin user, hành động từ logger.info() trong Cogs
            action_message = record.getMessage()
            
            # Kết hợp thành định dạng bạn muốn
            # Ví dụ: "[dd/mm/yy (HH:MM:SS)] User MinhBeo8 (12345) đã câu được cá 🐟..."
            final_log_string = f"[{formatted_time}] {action_message}"
            
            if len(final_log_string) > 1990: # Giới hạn ký tự Discord
                final_log_string = final_log_string[:1987] + "..."
            payload = {"content": final_log_string}
        
        # Nếu payload đã được tạo (tức là log này cần gửi đi)
        if payload:
            try:
                if self.loop and self.loop.is_running():
                    asyncio.ensure_future(self._send_payload_async(payload), loop=self.loop)
                else:
                    # Fallback nếu không có loop (ít khi xảy ra khi bot đang chạy)
                    # Cách này có thể không ổn định, chỉ là nỗ lực cuối cùng
                    asyncio.run(self._send_payload_async(payload)) 
            except Exception as e:
                # Lỗi này sẽ được bắt bởi handleError của logging.Handler
                # và sẽ được ghi vào các handler khác (ví dụ file log chính)
                self.handleError(record) # Gọi handler lỗi mặc định của logging
                # In thêm ra console để dễ thấy ngay
                print(f"[CRITICAL][DiscordWebhookHandler] Lỗi nghiêm trọng khi gửi log qua webhook: {e}")
                traceback.print_exc()


# --- Hàm setup_logging (CẬP NHẬT) ---
def setup_logging():
    # ... (phần tạo thư mục, tên file, formatter giữ nguyên như trước) ...
    if not os.path.exists(LOG_DIRECTORY):
        try:
            os.makedirs(LOG_DIRECTORY)
        except OSError as e:
            print(f"Không thể tạo thư mục logs: {e}")
            return 

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
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

    # General File Handler (Giữ nguyên)
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


    # Action Log File Handler (Giữ nguyên - để vẫn có file log action riêng)
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

    # Console Handler (Giữ nguyên)
    try:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO) 
        root_logger.addHandler(console_handler)
    except Exception as e:
        print(f"Không thể thiết lập console_handler: {e}")

    # --- CẬP NHẬT WEBHOOK HANDLER ---
    webhook_url_from_env = os.getenv("DISCORD_WEBHOOK_URL")
    if webhook_url_from_env:
        try:
            webhook_handler = DiscordWebhookHandler(webhook_url_from_env)
            # Webhook handler sẽ nhận INFO trở lên, 
            # bên trong emit() sẽ quyết định gửi gì dựa trên level và name
            webhook_handler.setLevel(logging.INFO) 
            # Không cần set formatter cho webhook_handler vì emit tự định dạng
            root_logger.addHandler(webhook_handler)
            logging.getLogger("BotSetup").info("Discord Webhook logging handler đã được thiết lập cho INFO (từ cogs) và ERROR/CRITICAL.")
        except Exception as e:
            logging.getLogger("BotSetup").error(f"Không thể thiết lập DiscordWebhookHandler: {e}", exc_info=True)
    else:
        logging.getLogger("BotSetup").warning("DISCORD_WEBHOOK_URL không được tìm thấy trong .env. Logging qua Webhook bị vô hiệu hóa.")
    # ----------------------------

    logging.getLogger("BotSetup").info("Hệ thống Logging đã được thiết lập đầy đủ.")
    # ... (các dòng debug về tên file log giữ nguyên) ...
