import json
import os
import logging
from typing import Optional

from . import config

logger = logging.getLogger(__name__)

DEFAULT_LOCAL_BALANCE = {"earned": 0, "admin_added": 0}

DEFAULT_USER_SERVER_DATA = {
    "level_local": 1,
    "xp_local": 0,
    "inventory_local": [],
    "local_balance": DEFAULT_LOCAL_BALANCE.copy()
}

DEFAULT_GLOBAL_USER_PROFILE = {
    "global_balance": 0,
    "inventory_global": [],
    "level_global": 1,
    "xp_global": 0,
    "rebirths": 0,
    "server_data": {},
    "last_work_global": 0,
    "last_daily_global": 0,
    "last_beg_global": 0,
    "last_rob_global": 0,
    "last_crime_global": 0,
    "last_fish_global": 0,
    "last_slots_global": 0,
    "last_cf_global": 0,
    "last_dice_global": 0,
    "preferred_language": "vi"
}

DEFAULT_GUILD_CONFIG = {
    "bare_command_active_channels": [],
    "muted_channels": [],
    "active_events": {}
}

DEFAULT_ECONOMY_STRUCTURE = {
    "users": {},
    "guild_configs": {},
    "global_shop_stock": {},
    "bot_metadata": {
        "data_structure_version": "Ecoworld_v1.0_LoGlo",
        "notes": "Hệ thống kinh tế Ecoworld với Ví Local (earned/admin-added) và Ví Global (GOL)."
    }
}

def load_economy_data() -> dict:
    path_to_file = config.ECONOMY_FILE
    if not os.path.exists(path_to_file):
        data = {k: v.copy() if isinstance(v, (dict, list)) else v for k, v in DEFAULT_ECONOMY_STRUCTURE.items()}
        save_economy_data(data)
        return data
    try:
        with open(path_to_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                data = {k: v.copy() if isinstance(v, (dict, list)) else v for k, v in DEFAULT_ECONOMY_STRUCTURE.items()}
                save_economy_data(data)
                return data
            loaded_data = json.loads(content)
            data_changed_structure = False
            for key, default_value in DEFAULT_ECONOMY_STRUCTURE.items():
                if key not in loaded_data:
                    loaded_data[key] = default_value.copy() if isinstance(default_value, (dict, list)) else default_value
                    data_changed_structure = True
            if data_changed_structure:
                save_economy_data(loaded_data)
            return loaded_data
    except json.JSONDecodeError as e:
        logger.error(f"LỖI JSONDecodeError: File {path_to_file} bị lỗi. Tạo file mới.", exc_info=True)
        data = {k: v.copy() if isinstance(v, (dict, list)) else v for k, v in DEFAULT_ECONOMY_STRUCTURE.items()}
        save_economy_data(data)
        return data
    except Exception as e:
        logger.error(f"Lỗi không xác định khi tải dữ liệu từ {path_to_file}:", exc_info=True)
        return {k: v.copy() if isinstance(v, (dict, list)) else v for k, v in DEFAULT_ECONOMY_STRUCTURE.items()}

def save_economy_data(data: dict):
    path_to_file = config.ECONOMY_FILE
    temp_path_to_file = path_to_file + ".tmp"
    try:
        with open(temp_path_to_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        os.replace(temp_path_to_file, path_to_file)
    except Exception as e:
        logger.error(f"Lỗi khi lưu dữ liệu vào {path_to_file}:", exc_info=True)
        if os.path.exists(temp_path_to_file):
            try:
                os.remove(temp_path_to_file)
            except Exception as e_remove:
                logger.error(f"Không thể xóa file tạm {temp_path_to_file}: {e_remove}")

def get_or_create_global_user_profile(data: dict, user_id: int) -> dict:
    user_id_str = str(user_id)
    users_data = data.setdefault("users", {})
    
    if user_id_str not in users_data or not isinstance(users_data[user_id_str], dict):
        users_data[user_id_str] = {k: v.copy() if isinstance(v, (dict, list)) else v for k, v in DEFAULT_GLOBAL_USER_PROFILE.items()}
        logger.info(f"User mới {user_id_str} đã được khởi tạo với dữ liệu toàn cục mặc định.")
    else:
        user_profile = users_data[user_id_str]
        changed = False
        for key, default_val in DEFAULT_GLOBAL_USER_PROFILE.items():
            if key not in user_profile:
                user_profile[key] = default_val.copy() if isinstance(default_val, (dict, list)) else default_val
                changed = True
        if "server_data" not in user_profile or not isinstance(user_profile["server_data"], dict):
            user_profile["server_data"] = {}
            changed = True
        if changed:
            logger.debug(f"Đã cập nhật các key toàn cục còn thiếu cho user {user_id_str}.")
            
    return users_data[user_id_str]

def get_or_create_user_server_data(global_user_profile: dict, guild_id: int) -> dict:
    guild_id_str = str(guild_id)
    server_data_pool = global_user_profile.setdefault("server_data", {})
    
    if guild_id_str not in server_data_pool or not isinstance(server_data_pool.get(guild_id_str), dict):
        server_data_pool[guild_id_str] = {k: v.copy() if isinstance(v, (dict, list)) else v for k, v in DEFAULT_USER_SERVER_DATA.items()}
        logger.info(f"Đã khởi tạo server_data cho user tại guild {guild_id_str}.")
    else:
        server_data = server_data_pool[guild_id_str]
        changed = False
        for key, default_val in DEFAULT_USER_SERVER_DATA.items():
            if key not in server_data:
                server_data[key] = default_val.copy() if isinstance(default_val, (dict, list)) else default_val
                changed = True
        if "local_balance" not in server_data or not isinstance(server_data["local_balance"], dict):
            server_data["local_balance"] = DEFAULT_LOCAL_BALANCE.copy()
            changed = True
        server_data.setdefault("local_balance", {}).setdefault("earned", 0)
        server_data.setdefault("local_balance", {}).setdefault("admin_added", 0)
        if changed:
             logger.debug(f"Đã cập nhật các key local còn thiếu cho user tại guild {guild_id_str}.")
             
    return server_data_pool[guild_id_str]

def get_or_create_guild_config(data: dict, guild_id: int) -> dict:
    guild_id_str = str(guild_id)
    guild_configs_pool = data.setdefault("guild_configs", {})
    
    if guild_id_str not in guild_configs_pool or not isinstance(guild_configs_pool[guild_id_str], dict):
        guild_configs_pool[guild_id_str] = {k: (v.copy() if isinstance(v, (dict, list)) else v) for k, v in DEFAULT_GUILD_CONFIG.items()}
        logger.info(f"Config mặc định đã được tạo cho guild mới: {guild_id_str}")
    else:
        guild_cfg = guild_configs_pool[guild_id_str]
        changed = False
        for key, default_val in DEFAULT_GUILD_CONFIG.items():
            if key not in guild_cfg:
                guild_cfg[key] = default_val.copy() if isinstance(default_val, (dict, list)) else default_val
                changed = True
        if changed:
            logger.debug(f"Đã cập nhật các key config còn thiếu cho guild {guild_id_str}.")
    return guild_configs_pool[guild_id_str]

def load_moderator_ids() -> list:
    path_to_file = config.MODERATORS_FILE
    try:
        if not os.path.exists(path_to_file):
            with open(path_to_file, 'w', encoding='utf-8') as f: json.dump({"moderator_ids": []}, f, indent=4)
            return []
        with open(path_to_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                return []
            data = json.loads(content)
            return data.get("moderator_ids", [])
    except Exception as e:
        logger.error(f"Lỗi khi tải moderator_ids:", exc_info=True)
        return []

def save_moderator_ids(ids: list) -> bool:
    path_to_file = config.MODERATORS_FILE 
    try:
        cleaned_ids = list(set(int(mod_id) for mod_id in ids if str(mod_id).strip().isdigit()))
        with open(path_to_file, 'w', encoding='utf-8') as f:
            json.dump({"moderator_ids": cleaned_ids}, f, indent=4)
        logger.info(f"Danh sách moderator đã được lưu vào {path_to_file}.")
        return True
    except Exception as e:
        logger.error(f"Lỗi khi lưu moderator_ids:", exc_info=True)
        return False

def add_moderator_id(user_id: int) -> bool:
    current_ids = load_moderator_ids()
    if int(user_id) not in current_ids:
        current_ids.append(int(user_id))
        return save_moderator_ids(current_ids)
    return True 

def remove_moderator_id(user_id: int) -> bool:
    current_ids = load_moderator_ids()
    id_to_remove = int(user_id)
    if id_to_remove in current_ids:
        current_ids.remove(id_to_remove)
        return save_moderator_ids(current_ids)
    return False
