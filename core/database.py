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
            if not content.strip(): # Kiểm tra nếu content rỗng hoặc chỉ có khoảng trắng
                return {} # Trả về dict rỗng nếu file rỗng
            return json.loads(content) # Sử dụng json.loads với content đã đọc
    except json.JSONDecodeError:
        print(f"CẢNH BÁO: File {ECONOMY_FILE} bị lỗi JSON hoặc trống hoàn toàn. Tạo lại nếu cần.")
        # Nếu file lỗi, có thể tạo lại file rỗng để tránh lỗi liên tục
        with open(ECONOMY_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=4, ensure_ascii=False)
        return {}
    except FileNotFoundError: 
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
        data[guild_id_str] = {"config": {"bare_command_active_channels": [], "muted_channels": []}}
    elif "config" not in data[guild_id_str] or not isinstance(data[guild_id_str]["config"], dict):
        data[guild_id_str]["config"] = {"bare_command_active_channels": [], "muted_channels": []}
    else:
        data[guild_id_str]["config"].setdefault("bare_command_active_channels", [])
        data[guild_id_str]["config"].setdefault("muted_channels", [])
    # Trả về bản sao để tránh thay đổi ngoài ý muốn, nhưng khi save_guild_config thì phải lấy data gốc
    # Trong trường hợp này, các lệnh admin lấy config, sửa rồi gọi save_guild_config,
    # nên việc trả về bản sao là an toàn. save_guild_config sẽ load lại data mới nhất.
    return data[guild_id_str]["config"].copy()


def save_guild_config(guild_id, config_data_to_save):
    data = load_data()
    guild_id_str = str(guild_id)
    if guild_id_str not in data: 
        data[guild_id_str] = {} # Tạo guild nếu chưa có
    data[guild_id_str]["config"] = config_data_to_save 
    save_data(data)


def check_user(data, guild_id, user_id):
    """
    Kiểm tra và khởi tạo dữ liệu cho guild và user nếu chưa có.
    Hàm này chỉnh sửa trực tiếp `data` được truyền vào và trả về nó.
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

    # Dữ liệu mặc định cho người dùng mới hoặc khi thiếu key
    defaults_user = {
        "balance": 100,  # Số dư mặc định khi tạo mới user
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

    # Khởi tạo dữ liệu người dùng nếu user_id không phải là 'config' và chưa tồn tại
    if user_id_str != "config":
        if user_id_str not in data[guild_id_str]:
            data[guild_id_str][user_id_str] = defaults_user.copy() # Tạo mới với đầy đủ default
        elif not isinstance(data[guild_id_str][user_id_str], dict): # Nếu user_data không phải dict (dữ liệu lỗi)
             data[guild_id_str][user_id_str] = defaults_user.copy()
        else: # Nếu user đã tồn tại và là dict, đảm bảo có đủ các key mặc định
            for key, default_value in defaults_user.items():
                data[guild_id_str][user_id_str].setdefault(key, default_value)
    
    return data


def get_user_data(guild_id, user_id):
    """
    Lấy dữ liệu người dùng, đảm bảo dữ liệu được khởi tạo nếu cần.
    Hàm này sẽ load, check_user, và trả về toàn bộ cấu trúc `data`.
    """
    data = load_data()
    data = check_user(data, guild_id, user_id)
    return data
