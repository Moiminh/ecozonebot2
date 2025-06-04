# bot/main.py
import sys
import nextcord
import os              # Import thư viện os
from dotenv import load_dotenv # Import hàm load_dotenv

# Import bot instance và hàm load_all_cogs từ core.bot
from core.bot import bot, load_all_cogs

# --- Tải biến môi trường từ file .env ---
# Gọi load_dotenv() ở đầu chương trình, trước khi truy cập biến môi trường
load_dotenv()
# -----------------------------------------

# Bỏ hàm get_bot_token() cũ đi, vì chúng ta không cần nhập tay nữa

if __name__ == "__main__":
    print("--------------------------------------------------")
    print("Chào mừng bạn đến với Bot Kinh Tế!")
    print("--------------------------------------------------")

    # --- Lấy token từ biến môi trường ---
    actual_bot_token = os.getenv("BOT_TOKEN")
    # ------------------------------------

    if not actual_bot_token: # Kiểm tra xem token có được tải không
        print("[LỖI NGHIÊM TRỌNG] BOT_TOKEN không được tìm thấy trong file .env hoặc biến môi trường!")
        print("Hãy chắc chắn bạn đã tạo file .env ở thư mục gốc của dự án và đặt BOT_TOKEN vào đó.")
        sys.exit(1) # Thoát nếu không có token

    print("Đang kiểm tra và tải các Cogs...")
    try:
        load_all_cogs() 
    except Exception as e:
        print(f"[LỖI NGHIÊM TRỌNG] Không thể tải Cogs: {e}")
        print("Bot sẽ không thể hoạt động đúng nếu thiếu Cogs. Vui lòng kiểm tra lại.")
        # sys.exit(1) # Có thể thoát nếu muốn

    print("Đang cố gắng kết nối với Discord...")
    try:
        bot.run(actual_bot_token)
    except nextcord.errors.LoginFailure:
        print("[LỖI ĐĂNG NHẬP] Token không hợp lệ hoặc có vấn đề với kết nối.")
        print("Vui lòng kiểm tra lại BOT_TOKEN trong file .env và kết nối mạng của bạn.")
    except Exception as e:
        print(f"[LỖI KHÔNG XÁC ĐỊNH KHI CHẠY BOT]: {type(e).__name__} - {e}")
        print("Đã có lỗi xảy ra khiến bot không thể tiếp tục chạy.")
    
    print("--------------------------------------------------")
    print("Bot đã dừng hoạt động (nếu có lỗi) hoặc đang tắt.")
    print("--------------------------------------------------")
