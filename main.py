# bot/main.py
import sys
import nextcord # Vẫn cần để bắt lỗi nextcord.errors.LoginFailure
import os
from dotenv import load_dotenv

# --- BƯỚC 1: THIẾT LẬP LOGGING NGAY TỪ ĐẦU ---
# Import hàm setup_logging từ module logger trong package core
from core.logger import setup_logging 
setup_logging() # Gọi hàm này NGAY LẬP TỨC để thiết lập logging
# ----------------------------------------------

# Import các thành phần khác của bot SAU KHI logging đã được thiết lập
from core.bot import bot, load_all_cogs
import logging # Import module logging để sử dụng

# Tạo một logger riêng cho file main.py này
# Tên logger '__main__' sẽ được sử dụng khi file này được chạy trực tiếp
main_logger = logging.getLogger(__name__) 

# Tải các biến môi trường từ file .env (nếu có)
# Hàm này nên được gọi sau setup_logging để các thông báo của nó (nếu có) cũng được log
load_dotenv()
main_logger.info("Đã tải biến môi trường từ .env (nếu có).")


if __name__ == "__main__":
    main_logger.info("==================================================")
    main_logger.info("Bắt đầu khởi chạy Bot Kinh Tế...")
    main_logger.info("==================================================")

    actual_bot_token = os.getenv("BOT_TOKEN")

    if not actual_bot_token:
        main_logger.critical("CRITICAL: BOT_TOKEN không được tìm thấy trong file .env hoặc biến môi trường!")
        main_logger.critical("Hãy chắc chắn bạn đã tạo file .env ở thư mục gốc của dự án (ngang hàng với thư mục 'bot') và đặt BOT_TOKEN='your_token_here' vào đó.")
        main_logger.critical("Bot sẽ dừng hoạt động.")
        sys.exit(1) # Thoát chương trình nếu không có token
    else:
        main_logger.info("BOT_TOKEN đã được tải thành công.")

    main_logger.info("Đang kiểm tra và tải các Cogs...")
    try:
        load_all_cogs() 
    except Exception as e:
        # Ghi lại lỗi nghiêm trọng và cả traceback vào file log
        main_logger.critical(f"Không thể tải Cogs: {e}", exc_info=True) 
        main_logger.info("Bot có thể không hoạt động đúng nếu thiếu Cogs. Vui lòng kiểm tra lại.")
        # Bạn có thể quyết định sys.exit(1) ở đây nếu việc tải Cogs thất bại là nghiêm trọng

    main_logger.info("Đang cố gắng kết nối với Discord...")
    try:
        bot.run(actual_bot_token)
    except nextcord.errors.LoginFailure:
        main_logger.critical("LỖI ĐĂNG NHẬP: Token không hợp lệ hoặc có vấn đề với kết nối.", exc_info=False) # Không cần exc_info cho lỗi LoginFailure rõ ràng
        main_logger.critical("Vui lòng kiểm tra lại BOT_TOKEN trong file .env và kết nối mạng của bạn.")
    except KeyboardInterrupt: # Xử lý khi người dùng bấm Ctrl+C
        main_logger.info("Bot đã được dừng bởi người dùng (KeyboardInterrupt).")
    except Exception as e:
        main_logger.critical(f"LỖI KHÔNG XÁC ĐỊNH KHI CHẠY BOT: {type(e).__name__} - {e}", exc_info=True)
        main_logger.critical("Đã có lỗi xảy ra khiến bot không thể tiếp tục chạy.")
    finally: # Khối finally sẽ luôn được thực thi, dù có lỗi hay không
        main_logger.info("==================================================")
        main_logger.info("Bot đã dừng hoạt động.")
        main_logger.info("==================================================")
