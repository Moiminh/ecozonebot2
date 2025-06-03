# bot/main.py
import sys # Để kiểm tra phiên bản Python nếu cần
import nextcord # Để bắt lỗi LoginFailure

# Import bot instance và hàm load_all_cogs từ core.bot
# Đường dẫn import dựa trên việc main.py nằm trong thư mục 'bot'
# và 'core' là một thư mục con của 'bot'
from core.bot import bot, load_all_cogs
# Chúng ta không import BOT_TOKEN từ config nữa vì sẽ nhập thủ công

def get_bot_token():
    """Yêu cầu người dùng nhập token bot."""
    token = None
    while not token:
        try:
            token = input("Vui lòng nhập BOT TOKEN của bạn: ").strip()
            if not token:
                print("Token không được để trống. Vui lòng nhập lại.")
            # Kiểm tra cơ bản xem token có vẻ hợp lệ không (có dấu chấm)
            # Đây không phải là kiểm tra đầy đủ nhưng giúp bắt lỗi nhập liệu sớm
            elif '.' not in token:
                print("Token không hợp lệ (thiếu định dạng chuẩn). Vui lòng kiểm tra và nhập lại.")
                token = None # Reset token để vòng lặp tiếp tục
        except KeyboardInterrupt:
            print("\nĐã hủy nhập token. Bot sẽ không khởi động.")
            sys.exit(0) # Thoát chương trình
    return token

if __name__ == "__main__":
    print("--------------------------------------------------")
    print("Chào mừng bạn đến với Bot Kinh Tế!")
    print("--------------------------------------------------")

    # Yêu cầu nhập token từ người dùng
    actual_bot_token = get_bot_token()

    if actual_bot_token:
        print("Đang kiểm tra và tải các Cogs...")
        try:
            load_all_cogs() # Tải tất cả các cogs đã định nghĩa
        except Exception as e:
            print(f"[LỖI NGHIÊM TRỌNG] Không thể tải Cogs: {e}")
            print("Bot sẽ không thể hoạt động đúng nếu thiếu Cogs. Vui lòng kiểm tra lại.")
            # Bạn có thể quyết định thoát ở đây nếu việc tải Cogs thất bại là nghiêm trọng
            # sys.exit(1)

        print("Đang cố gắng kết nối với Discord...")
        try:
            # Chạy bot với token đã nhập
            bot.run(actual_bot_token)
        except nextcord.errors.LoginFailure:
            print("[LỖI ĐĂNG NHẬP] Token không hợp lệ hoặc có vấn đề với kết nối.")
            print("Vui lòng kiểm tra lại BOT TOKEN và kết nối mạng của bạn.")
        except Exception as e:
            print(f"[LỖI KHÔNG XÁC ĐỊNH KHI CHẠY BOT]: {type(e).__name__} - {e}")
            print("Đã có lỗi xảy ra khiến bot không thể tiếp tục chạy.")
    else:
        # Trường hợp này ít khi xảy ra nếu get_bot_token() hoạt động đúng
        print("Không nhận được token. Bot không thể khởi động.")

    print("--------------------------------------------------")
    print("Bot đã dừng hoạt động (nếu có lỗi) hoặc đang tắt.")
    print("--------------------------------------------------")
