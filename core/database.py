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
