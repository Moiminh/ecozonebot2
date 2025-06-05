# bot/main.py
import sys
import nextcord 
import os
from dotenv import load_dotenv 

# --- BƯỚC 1: TẢI BIẾN MÔI TRƯỜNG TRƯỚC TIÊN ---
# Điều này đảm bảo os.getenv() có thể truy cập các biến từ .env ở bất kỳ đâu sau đó.
load_dotenv() 
# -----------------------------------------

# Import module logging để có thể tạo main_logger sớm
import logging 

from core.logger import setup_logging 

# Import đối tượng bot và hàm load_all_cogs TỪ core.bot
# Việc này cần thiết để lấy bot.loop TRƯỚC KHI gọi setup_logging nếu muốn truyền loop
from core.bot import bot, load_all_cogs 

setup_logging(bot_event_loop=bot.loop) 
# -------------------------------------------------------------

# Bây giờ mới lấy main_logger, sau khi root logger đã được cấu hình bởi setup_logging
main_logger = logging.getLogger(__name__) 

# === KIỂM TRA LẠI CÁC BIẾN MÔI TRƯỜNG SAU KHI LOGGING ĐÃ SETUP ===
# (Các dòng print debug trước đó trong logger.py cũng đã làm việc này)
if os.getenv("DISCORD_WEBHOOK_URL"):
    main_logger.debug(f"Webhook URL được tìm thấy bởi main.py (sau setup_logging): '{os.getenv('DISCORD_WEBHOOK_URL')[:30]}...'")
else:
    main_logger.debug("Webhook URL KHÔNG được tìm thấy bởi main.py (sau setup_logging).")
# =====================================================================

if __name__ == "__main__":
    main_logger.info("==================================================")
    main_logger.info("Bắt đầu khởi chạy Bot Kinh Tế! (main.py)") # Thêm (main.py) để rõ nguồn
    main_logger.info("==================================================")

    actual_bot_token = os.getenv("BOT_TOKEN")

    if not actual_bot_token:
        main_logger.critical("CRITICAL: BOT_TOKEN không được tìm thấy trong file .env hoặc biến môi trường!")
        main_logger.critical("Hãy chắc chắn bạn đã tạo file .env ở thư mục gốc của dự án (ngang hàng với thư mục 'bot') và đặt BOT_TOKEN='your_token_here' vào đó.")
        main_logger.critical("Bot sẽ dừng hoạt động.")
        sys.exit(1) 
    else:
        main_logger.info("BOT_TOKEN đã được tải thành công.")

    # Thông báo về Webhook URL (logger.py cũng đã có thông báo tương tự từ BotSetup)
    if os.getenv("DISCORD_WEBHOOK_URL"):
        main_logger.info(f"DISCORD_WEBHOOK_URL có vẻ đã được tải (kiểm tra từ main.py). Webhook logging nên hoạt động.")
    else:
        main_logger.warning("DISCORD_WEBHOOK_URL không tìm thấy trong .env (kiểm tra từ main.py). Logging qua Webhook sẽ bị vô hiệu hóa.")

    main_logger.info("Đang kiểm tra và tải các Cogs...")
    try:
        load_all_cogs() 
    except Exception as e:
        main_logger.critical(f"Không thể tải Cogs: {e}", exc_info=True) 
        main_logger.info("Bot có thể không hoạt động đúng nếu thiếu Cogs. Vui lòng kiểm tra lại.")
    
    main_logger.info("Đang cố gắng kết nối với Discord...")
    try:
        bot.run(actual_bot_token)
    except nextcord.errors.LoginFailure:
        main_logger.critical("LỖI ĐĂNG NHẬP: Token không hợp lệ hoặc có vấn đề với kết nối.", exc_info=False) 
        main_logger.critical("Vui lòng kiểm tra lại BOT_TOKEN trong file .env và kết nối mạng của bạn.")
    except KeyboardInterrupt: 
        main_logger.info("Bot đã được dừng bởi người dùng (KeyboardInterrupt).")
    except Exception as e:
        main_logger.critical(f"LỖI KHÔNG XÁC ĐỊNH KHI CHẠY BOT: {type(e).__name__} - {e}", exc_info=True)
    finally: 
        main_logger.info("==================================================")
        main_logger.info("Bot đã dừng hoạt động.")
        main_logger.info("==================================================")
