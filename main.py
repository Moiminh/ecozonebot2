# bot/main.py
import sys
import nextcord 
import os
from dotenv import load_dotenv 

# --- BƯỚC 1: TẢI BIẾN MÔI TRƯỜNG TRƯỚC TIÊN ---
load_dotenv() 

# Import module logging để có thể tạo main_logger sớm
import logging 

from core.logger import setup_logging 
# [CẢI TIẾN] Import thêm hàm load/save economy data
from core.database import load_economy_data, save_economy_data

# Import đối tượng bot và hàm load_all_cogs TỪ core.bot
from core.bot import bot, load_all_cogs 

setup_logging(bot_event_loop=bot.loop) 

# Bây giờ mới lấy main_logger, sau khi root logger đã được cấu hình bởi setup_logging
main_logger = logging.getLogger(__name__) 

if __name__ == "__main__":
    main_logger.info("==================================================")
    main_logger.info("Bắt đầu khởi chạy Bot Kinh Tế! (main.py)")
    main_logger.info("==================================================")
    
    # [CẢI TIẾN] Load dữ liệu kinh tế vào cache của bot MỘT LẦN DUY NHẤT
    try:
        main_logger.info("Đang tải dữ liệu kinh tế vào bộ nhớ cache...")
        bot.economy_data = load_economy_data()
        main_logger.info("Tải dữ liệu kinh tế vào cache thành công.")
    except Exception as e:
        main_logger.critical(f"Không thể tải dữ liệu kinh tế ban đầu: {e}", exc_info=True)
        sys.exit(1)

    actual_bot_token = os.getenv("BOT_TOKEN")
    if not actual_bot_token:
        main_logger.critical("CRITICAL: BOT_TOKEN không được tìm thấy!")
        sys.exit(1) 
    else:
        main_logger.info("BOT_TOKEN đã được tải thành công.")

    main_logger.info("Đang kiểm tra và tải các Cogs...")
    try:
        load_all_cogs() 
    except Exception as e:
        main_logger.critical(f"Không thể tải Cogs: {e}", exc_info=True)
    
    main_logger.info("Đang cố gắng kết nối với Discord...")
    try:
        bot.run(actual_bot_token)
    except nextcord.errors.LoginFailure:
        main_logger.critical("LỖI ĐĂNG NHẬP: Token không hợp lệ.", exc_info=False) 
    except KeyboardInterrupt: 
        main_logger.info("Bot đã được dừng bởi người dùng (KeyboardInterrupt).")
    except Exception as e:
        main_logger.critical(f"LỖI KHÔNG XÁC ĐỊNH KHI CHẠY BOT: {type(e).__name__} - {e}", exc_info=True)
    finally:
        # [CẢI TIẾN] Lưu lại dữ liệu từ cache vào file lần cuối trước khi tắt
        main_logger.info("Đang lưu dữ liệu kinh tế lần cuối từ cache...")
        try:
            if hasattr(bot, 'economy_data'):
                save_economy_data(bot.economy_data)
                main_logger.info("Lưu dữ liệu lần cuối thành công.")
        except Exception as e:
            main_logger.error(f"Lỗi khi lưu dữ liệu lần cuối: {e}", exc_info=True)
            
        main_logger.info("==================================================")
        main_logger.info("Bot đã dừng hoạt động.")
        main_logger.info("==================================================")
