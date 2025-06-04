# bot/main.py
import sys
import nextcord 
import os
from dotenv import load_dotenv 

# --- BƯỚC 1: TẢI BIẾN MÔI TRƯỜNG TRƯỚC TIÊN ---
load_dotenv() 
# -----------------------------------------

# --- BƯỚC 2: THIẾT LẬP LOGGING SAU KHI ĐÃ LOAD .ENV ---
# Import hàm setup_logging từ module logger trong package core
# Việc import này nên diễn ra sau load_dotenv() nếu logger.py cũng có thể os.getenv()
# tuy nhiên, logger.py của chúng ta lấy URL webhook từ os.getenv bên trong setup_logging,
# nên thứ tự này vẫn ổn.
from core.logger import setup_logging 
setup_logging() # Gọi hàm này để thiết lập logging
# ----------------------------------------------

# Import các thành phần khác của bot SAU KHI logging đã được thiết lập
from core.bot import bot, load_all_cogs
import logging # Import module logging để sử dụng

# Tạo một logger riêng cho file main.py này
main_logger = logging.getLogger(__name__) # Sẽ có tên là '__main__'

# === KIỂM TRA WEBHOOK URL NGAY SAU KHI LOAD_DOTENV VÀ SETUP LOGGING ===
# Dùng main_logger.debug để nó chỉ vào file general log, không làm rối console
webhook_url_in_main = os.getenv("DISCORD_WEBHOOK_URL")
if webhook_url_in_main:
    main_logger.debug(f"Webhook URL được tìm thấy bởi main.py: '{webhook_url_in_main[:30]}...' (phần đầu)")
else:
    main_logger.debug("Webhook URL KHÔNG được tìm thấy bởi main.py sau khi load_dotenv().")
# ===================================================================

if __name__ == "__main__":
    main_logger.info("==================================================")
    main_logger.info("Bắt đầu khởi chạy Bot Kinh Tế!")
    main_logger.info("==================================================")

    actual_bot_token = os.getenv("BOT_TOKEN")

    if not actual_bot_token:
        main_logger.critical("CRITICAL: BOT_TOKEN không được tìm thấy trong file .env hoặc biến môi trường!")
        main_logger.critical("Hãy chắc chắn bạn đã tạo file .env ở thư mục gốc của dự án (ngang hàng với thư mục 'bot') và đặt BOT_TOKEN='your_token_here' vào đó.")
        main_logger.critical("Bot sẽ dừng hoạt động.")
        sys.exit(1) 
    else:
        main_logger.info("BOT_TOKEN đã được tải thành công.")

    # Thông báo về Webhook URL dựa trên giá trị đã lấy được ở trên (chủ yếu để debug)
    # Hàm setup_logging() trong logger.py cũng đã có thông báo tương tự rồi.
    # Dòng này trong main.py chỉ để xác nhận lại lần nữa nếu cần.
    if webhook_url_in_main: # Sử dụng biến đã lấy ở trên
        main_logger.info(f"DISCORD_WEBHOOK_URL có vẻ đã được tải (kiểm tra từ main.py).")
    else:
        main_logger.warning("DISCORD_WEBHOOK_URL không tìm thấy trong .env (kiểm tra từ main.py). Logging qua Webhook có thể không hoạt động.")

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
