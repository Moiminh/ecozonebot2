# bot/core/database.py
import json
import os
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# --- CÁC CẤU TRÚC DỮ LIỆU MẶC ĐỊNH ---

DEFAULT_USER_LOCAL_DATA = {
    "local_balance": {"earned": 0, "adadd": 0},
    "inventory_local": [],
    "tickets": [],
    "level_local": 1,
    "xp_local": 0,
    "survival_stats": {
        "health": 100,
        "hunger": 100,
        "energy": 100
    },
    "is_mafia": False,
    "is_police": False,
    "is_doctor": False,
    "role_stats": {
        "arrests_made": 0,
        "patients_healed": 0
    },
    "daily_accusations": { "date": "1970-01-01", "count": 0 }
}

DEFAULT_GLOBAL_USER_PROFILE = {
    "bank_balance": 0,
    "inventory_global": [],
    "wanted_level": 0.0,
    "level_global": 1,
    "xp_global": 0,
    "last_active_guild_id": None,
    "preferred_language": "vi",
    "cooldowns": {
        "work": 0, "daily": 0, "beg": 0, "rob": 0, "crime": 0, "fish": 0,
        "slots": 0, "coinflip": 0, "dice": 0, "launder": 0,
        "last_tainted_sell_date": "1970-01-01",
        "tainted_sells_today": 0
    },
    "server_data": {}
}

DEFAULT_GUILD_CONFIG = {
    "server_level": 1,
    "server_xp": 0,
# bot/core/database.py
import json
import os
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# --- CÁC CẤU TRÚC DỮ LIỆU MẶC ĐỊNH ---

# [SỬA LỖI] Thêm biến còn thiếu dựa trên cấu trúc economy.json
DEFAULT_ECONOMY_STRUCTURE = {
    "users": {},
    "guild_configs": {},
    "global_shop_stock": {},
    "global_item_definitions": {},
    "bot_metadata": {
        "data_structure_version": "Ecoworld_LoGlo_v1.0",
        "notes": "Hệ thống kinh tế Ecoworld với Ví Local (earned/adadd) và Ví Global (BANK)."
    }
}

DEFAULT_USER_LOCAL_DATA = {
    "local_balance": {"earned": 0, "adadd": 0},
    "inventory_local": [],
    "tickets": [],
    "level_local": 1,
    "xp_local": 0,
    "survival_stats": {
        "health": 100,
        "hunger": 100,
        "energy": 100
    },
    "is_mafia": False,
    "is_police": False,
    "is_doctor": False,
    "role_stats": {
        "arrests_made": 0,
        "patients_healed": 0
    },
    "daily_accusations": { "date": "1970-01-01", "count": 0 }
}

DEFAULT_GLOBAL_USER_PROFILE = {
    "bank_balance": 0,
    "inventory_global": [],
    "wanted_level": 0.0,
    "level_global": 1,
    "xp_global": 0,
    "last_active_guild_id": None,
    "preferred_language": "vi",
    "cooldowns": {
        "work": 0, "daily": 0, "beg": 0, "rob": 0, "crime": 0, "fish": 0,
        "slots": 0, "coinflip": 0, "dice": 0, "launder": 0,
        "last_tainted_sell_date": "1970-01-01",
        "tainted_sells_today": 0
    },
    "server_data": {}
}

DEFAULT_GUILD_CONFIG = {
    "server_level": 1,
    "server_xp": 0,
    "admin_vault": {
        "balance": 1000000000, # Khởi đầu với 1 tỷ
        "capacity": 1000000000,
        "last_refill_date": "1970-01-01"
    },
    "faction_info": {
        "mafia_betrayal_count": 0,
        "police_betrayal_count": 0,
        "mafia_traitors_log": [],
        "police_traitors_log": []
    },
    "mafia_role_id": None,
    "police_role_id": None,
    "doctor_role_id": None,
    "bare_command_active_channels": [],
    "muted_channels": [],
    "active_events": {}
}
# --- CÁC HÀM QUẢN LÝ DỮ LIỆU ---

def _save_data(data: Dict[str, Any], file_path: str):
    """Hàm nội bộ để lưu dữ liệu một cách an toàn."""
    temp_path = file_path + ".tmp"
    try:
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        os.replace(temp_path, file_path)
    except Exception as e:
        logger.error(f"Lỗi nghiêm trọng khi lưu dữ liệu vào {file_path}:", exc_info=True)
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e_remove:
                logger.error(f"Không thể xóa file tạm {temp_path}: {e_remove}")


def load_economy_data(file_path: str = 'economy.json') -> Dict[str, Any]:
    """
    Tải dữ liệu kinh tế từ file JSON.
    Tự động tạo file nếu không tồn tại và cập nhật cấu trúc nếu thiếu key.
    """
    if not os.path.exists(file_path):
        logger.warning(f"File '{file_path}' không tồn tại. Đang tạo file mới với cấu trúc mặc định.")
        _save_data(DEFAULT_ECONOMY_STRUCTURE, file_path)
        return DEFAULT_ECONOMY_STRUCTURE.copy()

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                logger.warning(f"File '{file_path}' trống. Đang ghi lại cấu trúc mặc định.")
                _save_data(DEFAULT_ECONOMY_STRUCTURE, file_path)
                return DEFAULT_ECONOMY_STRUCTURE.copy()
            
            data = json.loads(content)
            
            data_changed = False
            for key, default_value in DEFAULT_ECONOMY_STRUCTURE.items():
                if key not in data:
                    data[key] = default_value.copy() if isinstance(default_value, (dict, list)) else default_value
                    data_changed = True
            
            if data_changed:
                logger.info("Phát hiện thiếu key ở cấp cao nhất. Đã cập nhật và lưu lại file.")
                _save_data(data, file_path)

            return data
    except json.JSONDecodeError:
        logger.error(f"LỖI JSONDecodeError: File {file_path} bị lỗi. Đang tạo file backup và sử dụng dữ liệu mặc định.")
        backup_path = f"{file_path}.corrupted.{os.path.getmtime(file_path)}.bak"
        os.rename(file_path, backup_path)
        _save_data(DEFAULT_ECONOMY_STRUCTURE, file_path)
        return DEFAULT_ECONOMY_STRUCTURE.copy()
    except Exception:
        logger.critical(f"Lỗi không xác định khi tải dữ liệu từ {file_path}. Trả về cấu trúc mặc định để bot không bị crash.", exc_info=True)
        return DEFAULT_ECONOMY_STRUCTURE.copy()

def save_economy_data(data: Dict[str, Any], file_path: str = 'economy.json'):
    """Lưu dữ liệu kinh tế vào file JSON một cách an toàn."""
    _save_data(data, file_path)

# --- CÁC HÀM TRUY XUẤT VÀ CHUẨN HÓA DỮ LIỆU ---

def get_or_create_global_user_profile(data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
    """
    Lấy profile toàn cục của người dùng. Tự động tạo và cập nhật nếu cần.
    """
    user_id_str = str(user_id)
    users_data = data.setdefault("users", {})
    
    if user_id_str not in users_data:
        users_data[user_id_str] = DEFAULT_GLOBAL_USER_PROFILE.copy()
        users_data[user_id_str]["cooldowns"] = DEFAULT_GLOBAL_USER_PROFILE["cooldowns"].copy()
        users_data[user_id_str]["server_data"] = {}
        logger.info(f"User mới {user_id_str} đã được khởi tạo profile toàn cục.")
        return users_data[user_id_str]

    user_profile = users_data[user_id_str]
    profile_changed = False
    for key, default_value in DEFAULT_GLOBAL_USER_PROFILE.items():
        if key not in user_profile:
            user_profile[key] = default_value.copy() if isinstance(default_value, (dict, list)) else default_value
            profile_changed = True
    
    # Kiểm tra sâu hơn cho dict cooldowns
    if "cooldowns" not in user_profile or not isinstance(user_profile["cooldowns"], dict):
        user_profile["cooldowns"] = DEFAULT_GLOBAL_USER_PROFILE["cooldowns"].copy()
        profile_changed = True
    else:
        for cd_key, cd_default in DEFAULT_GLOBAL_USER_PROFILE["cooldowns"].items():
            if cd_key not in user_profile["cooldowns"]:
                user_profile["cooldowns"][cd_key] = cd_default
                profile_changed = True
    
    if profile_changed:
        logger.debug(f"Đã cập nhật các key toàn cục còn thiếu cho user {user_id_str}.")

    return user_profile

def get_or_create_user_local_data(global_user_profile: Dict[str, Any], guild_id: int) -> Dict[str, Any]:
    """
    Lấy dữ liệu local (theo server) của người dùng từ global_profile của họ.
    Tự động tạo và cập nhật nếu cần.
    """
    guild_id_str = str(guild_id)
    server_data_pool = global_user_profile.setdefault("server_data", {})

    if guild_id_str not in server_data_pool:
        server_data_pool[guild_id_str] = DEFAULT_USER_LOCAL_DATA.copy()
        server_data_pool[guild_id_str]["local_balance"] = DEFAULT_USER_LOCAL_DATA["local_balance"].copy()
        server_data_pool[guild_id_str]["inventory_local"] = []
        server_data_pool[guild_id_str]["tickets"] = []
        logger.info(f"Đã khởi tạo dữ liệu local cho user tại guild {guild_id_str}.")
        return server_data_pool[guild_id_str]
    
    local_data = server_data_pool[guild_id_str]
    data_changed = False
    for key, default_value in DEFAULT_USER_LOCAL_DATA.items():
        if key not in local_data:
            local_data[key] = default_value.copy() if isinstance(default_value, (dict, list)) else default_value
            data_changed = True
            
    balance = local_data.setdefault("local_balance", {})
    if "earned" not in balance:
        balance["earned"] = 0
        data_changed = True
    if "adadd" not in balance:
        balance["adadd"] = 0
        data_changed = True

    if data_changed:
        logger.debug(f"Đã cập nhật các key local còn thiếu cho user tại guild {guild_id_str}.")
        
    return local_data

def get_or_create_guild_config(data: Dict[str, Any], guild_id: int) -> Dict[str, Any]:
    """
    Lấy cấu hình của một server. Tự động tạo và cập nhật nếu cần.
    """
    guild_id_str = str(guild_id)
    guild_configs_pool = data.setdefault("guild_configs", {})

    if guild_id_str not in guild_configs_pool:
        guild_configs_pool[guild_id_str] = DEFAULT_GUILD_CONFIG.copy()
        logger.info(f"Config mặc định đã được tạo cho guild mới: {guild_id_str}")
        return guild_configs_pool[guild_id_str]

    guild_cfg = guild_configs_pool[guild_id_str]
    cfg_changed = False
    for key, default_value in DEFAULT_GUILD_CONFIG.items():
        if key not in guild_cfg:
            guild_cfg[key] = default_value.copy() if isinstance(default_value, (dict, list)) else default_value
            cfg_changed = True
    
    if cfg_changed:
        logger.debug(f"Đã cập nhật các key config còn thiếu cho guild {guild_id_str}.")
        
    return guild_cfg

def load_moderator_ids(file_path: str = 'moderators.json') -> List[int]:
    """Tải danh sách ID của moderator."""
    try:
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({"moderator_ids": []}, f, indent=4)
            return []
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("moderator_ids", [])
    except (json.JSONDecodeError, FileNotFoundError):
        logger.error(f"Lỗi khi tải moderator_ids từ {file_path}. Trả về danh sách rỗng.")
        return []

def save_moderator_ids(ids: List[int], file_path: str = 'moderators.json'):
    """Lưu danh sách ID của moderator."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({"moderator_ids": ids}, f, indent=4)
    except Exception:
        logger.error(f"Lỗi khi lưu moderator_ids vào {file_path}", exc_info=True)
    "admin_vault": {
        "balance": 1000000000, # Khởi đầu với 1 tỷ
        "capacity": 1000000000,
        "last_refill_date": "1970-01-01"
    },
    "faction_info": {
        "mafia_betrayal_count": 0,
        "police_betrayal_count": 0,
        "mafia_traitors_log": [],
        "police_traitors_log": []
    },
    "mafia_role_id": None,
    "police_role_id": None,
    "doctor_role_id": None,
    "bare_command_active_channels": [],
    "muted_channels": [],
    "active_events": {}
}

def _save_data(data: Dict[str, Any], file_path: str):
    """Hàm nội bộ để lưu dữ liệu một cách an toàn."""
    temp_path = file_path + ".tmp"
    try:
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        os.replace(temp_path, file_path)
    except Exception as e:
        logger.error(f"Lỗi nghiêm trọng khi lưu dữ liệu vào {file_path}:", exc_info=True)
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e_remove:
                logger.error(f"Không thể xóa file tạm {temp_path}: {e_remove}")


def load_economy_data(file_path: str = 'economy.json') -> Dict[str, Any]:
    """
    Tải dữ liệu kinh tế từ file JSON.
    Tự động tạo file nếu không tồn tại và cập nhật cấu trúc nếu thiếu key.
    """
    if not os.path.exists(file_path):
        logger.warning(f"File '{file_path}' không tồn tại. Đang tạo file mới với cấu trúc mặc định.")
        _save_data(DEFAULT_ECONOMY_STRUCTURE, file_path)
        return DEFAULT_ECONOMY_STRUCTURE.copy()

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                logger.warning(f"File '{file_path}' trống. Đang ghi lại cấu trúc mặc định.")
                _save_data(DEFAULT_ECONOMY_STRUCTURE, file_path)
                return DEFAULT_ECONOMY_STRUCTURE.copy()
            
            data = json.loads(content)
            
            data_changed = False
            for key, default_value in DEFAULT_ECONOMY_STRUCTURE.items():
                if key not in data:
                    data[key] = default_value.copy() if isinstance(default_value, (dict, list)) else default_value
                    data_changed = True
            
            if data_changed:
                logger.info("Phát hiện thiếu key ở cấp cao nhất. Đã cập nhật và lưu lại file.")
                _save_data(data, file_path)

            return data
    except json.JSONDecodeError:
        logger.error(f"LỖI JSONDecodeError: File {file_path} bị lỗi. Đang tạo file backup và sử dụng dữ liệu mặc định.")
        backup_path = f"{file_path}.corrupted.{os.path.getmtime(file_path)}.bak"
        os.rename(file_path, backup_path)
        _save_data(DEFAULT_ECONOMY_STRUCTURE, file_path)
        return DEFAULT_ECONOMY_STRUCTURE.copy()
    except Exception:
        logger.critical(f"Lỗi không xác định khi tải dữ liệu từ {file_path}. Trả về cấu trúc mặc định để bot không bị crash.", exc_info=True)
        return DEFAULT_ECONOMY_STRUCTURE.copy()

def save_economy_data(data: Dict[str, Any], file_path: str = 'economy.json'):
    """Lưu dữ liệu kinh tế vào file JSON một cách an toàn."""
    _save_data(data, file_path)


def get_or_create_global_user_profile(data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
    """
    Lấy profile toàn cục của người dùng. Tự động tạo và cập nhật nếu cần.
    """
    user_id_str = str(user_id)
    users_data = data.setdefault("users", {})
    
    if user_id_str not in users_data:
        users_data[user_id_str] = DEFAULT_GLOBAL_USER_PROFILE.copy()
        users_data[user_id_str]["cooldowns"] = DEFAULT_GLOBAL_USER_PROFILE["cooldowns"].copy()
        users_data[user_id_str]["server_data"] = {}
        logger.info(f"User mới {user_id_str} đã được khởi tạo profile toàn cục.")
        return users_data[user_id_str]

    user_profile = users_data[user_id_str]
ue.copy() if isinstance(default_value, (dict, list)) else default_value
            cfg_changed = True
    
    if cfg_changed:
        logger.debug(f"Đã cập nhật các key config còn thiếu cho guild {guild_id_str}.")
        
    return guild_cfg

def load_moderator_ids(file_path: str = 'moderators.json') -> List[int]:
    """Tải danh sách ID của moderator."""
    try:
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({"moderator_ids": []}, f, indent=4)
            return []
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("moderator_ids", [])
    except (json.JSONDecodeError, FileNotFoundError):
        logger.error(f"Lỗi khi tải moderator_ids từ {file_path}. Trả về danh sách rỗng.")
        return []

def save_moderator_ids(ids: List[int], file_path: str = 'moderators.json'):
    """Lưu danh sách ID của moderator."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({"moderator_ids": ids}, f, indent=4)
    except Exception:
        logger.error(f"Lỗi khi lưu moderator_ids vào {file_path}", exc_info=True)

def load_item_definitions(file_path: str = 'items.json') -> Dict[str, Any]:
    """Tải định nghĩa của tất cả vật phẩm từ file JSON."""
    try:
        if not os.path.exists(file_path):
            logger.error(f"File định nghĩa vật phẩm '{file_path}' không tồn tại. Cửa hàng và các vật phẩm sẽ không hoạt động.")
            return {}
        with open(file_path, 'r', encoding='utf-8') as f:
            item_data = json.load(f)
            # Hợp nhất shop_items và utility_items vào một dictionary để dễ truy cập
            all_items = {}
            all_items.update(item_data.get("shop_items", {}))
            all_items.update(item_data.get("utility_items", {}))
            return all_items
    except Exception as e:
        logger.error(f"Lỗi nghiêm trọng khi tải file định nghĩa vật phẩm '{file_path}': {e}", exc_info=True)
        return {}
