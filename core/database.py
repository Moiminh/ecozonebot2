# bot/core/database.py
import json
import os
from . import config # <<< THAY ĐỔI CHÍNH Ở ĐÂY

# --- JSON Data System ---
def load_data():
    if not os.path.exists(config.ECONOMY_FILE): # Sử dụng config.ECONOMY_FILE
        with open(config.ECONOMY_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=4, ensure_ascii=False)
        return {}
    try:
        with open(config.ECONOMY_FILE, 'r', encoding='utf-8') as f: # Sử dụng config.ECONOMY_FILE
            content = f.read()
            if not content.strip(): 
                return {} 
            return json.loads(content)
    except json.JSONDecodeError:
        print(f"CẢNH BÁO: File {config.ECONOMY_FILE} bị lỗi JSON hoặc trống hoàn toàn. Tạo lại nếu cần.") # Sử dụng config.ECONOMY_FILE
        with open(config.ECONOMY_FILE, 'w', encoding='utf-8') as f: # Sử dụng config.ECONOMY_FILE
            json.dump({}, f, indent=4, ensure_ascii=False)
        return {}
    except FileNotFoundError: 
        print(f"CẢNH BÁO: File {config.ECONOMY_FILE} không tìm thấy. Đang tạo file mới.") # Sử dụng config.ECONOMY_FILE
        with open(config.ECONOMY_FILE, 'w', encoding='utf-8') as f: # Sử dụng config.ECONOMY_FILE
            json.dump({}, f, indent=4, ensure_ascii=False)
        return {}

def save_data(data):
    with open(config.ECONOMY_FILE, 'w', encoding='utf-8') as f: # Sử dụng config.ECONOMY_FILE
        json.dump(data, f, indent=4, ensure_ascii=False)

# Các hàm get_guild_config, save_guild_config, check_user, get_user_data giữ nguyên
# vì chúng không trực tiếp gọi ECONOMY_FILE, mà gọi load_data/save_data đã được sửa.

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
    return data[guild_id_str]["config"].copy()

def save_guild_config(guild_id, config_data_to_save):
    data = load_data()
    guild_id_str = str(guild_id)
    if guild_id_str not in data: 
        data[guild_id_str] = {}
    data[guild_id_str]["config"] = config_data_to_save 
    save_data(data)

def check_user(data, guild_id, user_id):
    guild_id_str, user_id_str = str(guild_id), str(user_id)
    if guild_id_str not in data:
        data[guild_id_str] = {"config": {"bare_command_active_channels": [], "muted_channels": []}}
    elif "config" not in data[guild_id_str] or not isinstance(data[guild_id_str]["config"], dict):
        data[guild_id_str]["config"] = {"bare_command_active_channels": [], "muted_channels": []}
    else:
        data[guild_id_str]["config"].setdefault("bare_command_active_channels", [])
        data[guild_id_str]["config"].setdefault("muted_channels", [])

    defaults_user = {
        "balance": 100, 
        "bank_balance": 0,
        "inventory": [],
        "last_work": 0, "last_daily": 0, "last_beg": 0, "last_rob": 0,
        "last_crime": 0, "last_fish": 0, "last_slots": 0, "last_cf": 0, "last_dice": 0
    }
    if user_id_str != "config":
        if user_id_str not in data[guild_id_str]:
            data[guild_id_str][user_id_str] = defaults_user.copy()
        elif not isinstance(data[guild_id_str][user_id_str], dict):
             data[guild_id_str][user_id_str] = defaults_user.copy()
        else: 
            for key, default_value in defaults_user.items():
                data[guild_id_str][user_id_str].setdefault(key, default_value)
    return data

def get_user_data(guild_id, user_id):
    data = load_data()
    data = check_user(data, guild_id, user_id)
    return data
# bot/core/database.py
import json
import os
# from . import config # Bạn đã có dòng này để lấy config.ECONOMY_FILE
# --- Đảm bảo bạn import MODERATORS_FILE từ config ---
from .config import MODERATORS_FILE, ECONOMY_FILE # Thêm MODERATORS_FILE vào đây nếu chưa có, hoặc sửa dòng import config
# Hoặc nếu bạn đã import 'config' rồi thì dùng config.MODERATORS_FILE
# from . import config # Nếu dùng cách này, thì ở dưới sẽ là config.MODERATORS_FILE

# ... (các hàm load_data, save_data, get_guild_config, save_guild_config, check_user, get_user_data giữ nguyên như trước) ...

# ========== CÁC HÀM MỚI CHO QUẢN LÝ MODERATOR ==========

def load_moderator_ids() -> list:
    """Tải danh sách User ID của moderator từ file MODERATORS_FILE."""
    try:
        # Nếu bạn import 'config' thay vì 'MODERATORS_FILE' trực tiếp:
        # path_to_file = config.MODERATORS_FILE
        path_to_file = MODERATORS_FILE 

        if not os.path.exists(path_to_file):
            # Nếu file không tồn tại, tạo file với danh sách rỗng
            with open(path_to_file, 'w', encoding='utf-8') as f:
                json.dump({"moderator_ids": []}, f, indent=4)
            return []
        
        with open(path_to_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip(): # File trống
                # Ghi lại cấu trúc mặc định nếu file trống
                with open(path_to_file, 'w', encoding='utf-8') as wf:
                    json.dump({"moderator_ids": []}, wf, indent=4)
                return []
            data = json.loads(content)
            return data.get("moderator_ids", []) # Trả về list rỗng nếu key không tồn tại
    except json.JSONDecodeError:
        print(f"CẢNH BÁO: File {MODERATORS_FILE} bị lỗi JSON. Trả về danh sách moderator rỗng.")
        # Có thể tạo lại file với cấu trúc mặc định ở đây
        try:
            with open(MODERATORS_FILE, 'w', encoding='utf-8') as f: # Sửa path_to_file thành MODERATORS_FILE
                json.dump({"moderator_ids": []}, f, indent=4)
        except Exception as e_write:
            print(f"Không thể tạo lại file {MODERATORS_FILE} sau lỗi JSONDecodeError: {e_write}")
        return []
    except Exception as e:
        print(f"Lỗi không xác định khi tải moderator_ids: {e}")
        return []

def save_moderator_ids(ids: list) -> bool:
    """Lưu danh sách User ID của moderator vào file MODERATORS_FILE."""
    try:
        # path_to_file = config.MODERATORS_FILE # Nếu bạn import 'config'
        path_to_file = MODERATORS_FILE
        
        # Đảm bảo các ID trong list là số nguyên (int)
        # và loại bỏ các ID trùng lặp bằng cách chuyển qua set rồi lại list
        cleaned_ids = list(set(int(mod_id) for mod_id in ids if str(mod_id).isdigit()))

        with open(path_to_file, 'w', encoding='utf-8') as f:
            json.dump({"moderator_ids": cleaned_ids}, f, indent=4)
        return True
    except Exception as e:
        print(f"Lỗi khi lưu moderator_ids: {e}")
        return False

def add_moderator_id(user_id: int) -> bool:
    """Thêm một User ID vào danh sách moderator và lưu lại."""
    # Đảm bảo user_id là số nguyên
    try:
        mod_id_to_add = int(user_id)
    except ValueError:
        print(f"Lỗi: User ID '{user_id}' cung cấp cho add_moderator_id không phải là số.")
        return False

    current_ids = load_moderator_ids()
    if mod_id_to_add not in current_ids:
        current_ids.append(mod_id_to_add)
        return save_moderator_ids(current_ids)
    else:
        print(f"Thông tin: User ID {mod_id_to_add} đã có trong danh sách moderator.")
        return True # Coi như thành công vì đã có rồi

def remove_moderator_id(user_id: int) -> bool:
    """Xóa một User ID khỏi danh sách moderator và lưu lại."""
    try:
        mod_id_to_remove = int(user_id)
    except ValueError:
        print(f"Lỗi: User ID '{user_id}' cung cấp cho remove_moderator_id không phải là số.")
        return False
        
    current_ids = load_moderator_ids()
    if mod_id_to_remove in current_ids:
        current_ids.remove(mod_id_to_remove)
        return save_moderator_ids(current_ids)
    else:
        print(f"Thông tin: User ID {mod_id_to_remove} không tìm thấy trong danh sách moderator để xóa.")
        return False # Hoặc True nếu bạn coi việc "không tìm thấy để xóa" là một dạng thành công
