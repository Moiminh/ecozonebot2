# bot/core/database.py
import json
import os
# Dùng relative import để import ECONOMY_FILE từ file config.py trong cùng package 'core'
from .config import ECONOMY_FILE

# --- JSON Data System ---
def load_data():
    if not os.path.exists(ECONOMY_FILE):
        # Nếu file không tồn tại, tạo một file rỗng với cấu trúc JSON cơ bản
        with open(ECONOMY_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=4, ensure_ascii=False)
        return {}
    try:
        with open(ECONOMY_FILE, 'r', encoding='utf-8') as f:
            # Kiểm tra file có rỗng không
            content = f.read()
            if not content:
                return {} # Trả về dict rỗng nếu file rỗng
            return json.loads(content) # Sử dụng json.loads thay vì json.load
    except json.JSONDecodeError:
        print(f"CẢNH BÁO: File {ECONOMY_FILE} bị lỗi hoặc trống. Đang tạo cấu trúc mới nếu cần.")
        # Có thể bạn muốn tạo lại file với cấu trúc mặc định ở đây nếu lỗi
        # Hoặc đơn giản là trả về dữ liệu rỗng và để check_user xử lý
        return {}
    except FileNotFoundError: # Trường hợp này ít xảy ra do đã có os.path.exists ở trên
        print(f"CẢNH BÁO: File {ECONOMY_FILE} không tìm thấy. Đang tạo file mới.")
        with open(ECONOMY_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=4, ensure_ascii=False)
        return {}


def save_data(data):
    with open(ECONOMY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_guild_config(guild_id):
    data = load_data()
    guild_id_str = str(guild_id)
    if guild_id_str not in data:
        # Khởi tạo guild và config mặc định nếu chưa có
        data[guild_id_str] = {"config": {"bare_command_active_channels": [], "muted_channels": []}}
        # Không lưu ngay ở đây, để check_user hoặc các hàm khác quyết định khi nào lưu tổng thể
    elif "config" not in data[guild_id_str] or not isinstance(data[guild_id_str]["config"], dict):
        # Khởi tạo lại config nếu thiếu hoặc sai định dạng
        data[guild_id_str]["config"] = {"bare_command_active_channels": [], "muted_channels": []}
    else:
        # Đảm bảo các key list cần thiết tồn tại trong config đã có
        data[guild_id_str]["config"].setdefault("bare_command_active_channels", [])
        data[guild_id_str]["config"].setdefault("muted_channels", [])
    # Trả về bản sao của config để tránh sửa đổi trực tiếp data gốc ngoài ý muốn
    return data[guild_id_str]["config"].copy()


def save_guild_config(guild_id, config_data_to_save):
    data = load_data()
    guild_id_str = str(guild_id)
    if guild_id_str not in data: # Nếu guild chưa tồn tại, tạo mới
        data[guild_id_str] = {}
    data[guild_id_str]["config"] = config_data_to_save # Gán hoặc cập nhật config
    save_data(data)


def check_user(data, guild_id, user_id):
    """
    Kiểm tra và khởi tạo dữ liệu cho guild và user nếu chưa có.
    LƯU Ý: Hàm này giờ sẽ chỉnh sửa trực tiếp `data` được truyền vào.
    """
    guild_id_str, user_id_str = str(guild_id), str(user_id)

    # Đảm bảo cấu trúc guild và config tồn tại
    if guild_id_str not in data:
        data[guild_id_str] = {"config": {"bare_command_active_channels": [], "muted_channels": []}}
    elif "config" not in data[guild_id_str] or not isinstance(data[guild_id_str]["config"], dict):
        data[guild_id_str]["config"] = {"bare_command_active_channels": [], "muted_channels": []}
    else:
        data[guild_id_str]["config"].setdefault("bare_command_active_channels", [])
        data[guild_id_str]["config"].setdefault("muted_channels", [])

    # Khởi tạo dữ liệu người dùng nếu user_id không phải là 'config' và chưa tồn tại
    if user_id_str != "config" and user_id_str not in data[guild_id_str]:
        data[guild_id_str][user_id_str] = {
            "balance": 100,  # Số dư mặc định khi tạo mới
            "bank_balance": 0,
            "inventory": [],
            "last_work": 0,
            "last_daily": 0,
            "last_beg": 0,
            "last_rob": 0,
            "last_crime": 0,
            "last_fish": 0,
            "last_slots": 0,
            "last_cf": 0,
            "last_dice": 0
        }
    
    # Đảm bảo các key mặc định tồn tại cho người dùng đã có (trừ 'config')
    defaults_user = {
        "balance": 0, "bank_balance": 0, "inventory": [],
        "last_work": 0, "last_daily": 0, "last_beg": 0, "last_rob": 0,
        "last_crime": 0, "last_fish": 0, "last_slots": 0, "last_cf": 0, "last_dice": 0
    }

    if user_id_str != "config" and user_id_str in data[guild_id_str] and isinstance(data[guild_id_str][user_id_str], dict):
        for key, value in defaults_user.items():
            data[guild_id_str][user_id_str].setdefault(key, value)
    
    return data # Trả về `data` đã được chỉnh sửa


def get_user_data(guild_id, user_id):
    """
    Lấy dữ liệu người dùng, đảm bảo dữ liệu được khởi tạo nếu cần.
    Hàm này sẽ load, check_user, và trả về toàn bộ cấu trúc `data`.
    Các lệnh sẽ truy cập vào data[guild_id_str][user_id_str] từ đây.
    """
    data = load_data()
    # check_user sẽ chỉnh sửa `data` trực tiếp
    data = check_user(data, guild_id, user_id)
    # Không cần save_data() ngay ở đây, để các lệnh tự quyết định khi nào cần lưu sau khi thay đổi
    return data
