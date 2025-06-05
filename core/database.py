# bot/core/database.py
import json
import os
import logging

from . import config # Sử dụng config.ECONOMY_FILE, config.MODERATORS_FILE

logger = logging.getLogger(__name__)

# --- Cấu trúc dữ liệu mặc định ---
DEFAULT_GLOBAL_USER_PROFILE = {
    "global_balance": 100,
    "inventory_global": [],
    "bank_accounts": {},    # Sẽ có dạng {"GUILD_ID_STR": balance}
    "level_global": 1,
    "xp_global": 0,
    "rebirths": 0,
    "server_specific_data": {}, # Sẽ có dạng {"GUILD_ID_STR": {"level_local": 1, "xp_local": 0, "inventory_local": []}}
    "last_work_global": 0,
    "last_daily_global": 0,
    "last_beg_global": 0,
    "last_rob_global": 0,
    "last_crime_global": 0,
    "last_fish_global": 0,
    "last_slots_global": 0,
    "last_cf_global": 0,
    "last_dice_global": 0,
    "preferred_language": "vi" # Ngôn ngữ mặc định
}

DEFAULT_USER_SERVER_SPECIFIC_DATA = {
    "level_local": 1,
    "xp_local": 0,
    "inventory_local": []
    # Thêm các trường dữ liệu local khác của user tại server ở đây
}

DEFAULT_GUILD_CONFIG = {
    "bare_command_active_channels": [],
    "muted_channels": []
    # "min_local_level_for_global_item_tier1": 5 # Ví dụ
}

DEFAULT_GLOBAL_SHOP_STOCK_ITEM = { # Cấu trúc cho một item trong global_shop_stock
    "current_stock": 0,
    "max_stock": 10,
    "base_price": 100, # Giá này có thể được lấy từ SHOP_ITEMS trong config.py
    "can_restock": True,
    "last_restock_time": 0
}

DEFAULT_ECONOMY_STRUCTURE = {
    "users": {},
    "guild_configs": {},
    "global_shop_stock": {}, # Thêm mục này
    "bot_metadata": {
        "data_structure_version": "hybrid_v2_level_shop", # Cập nhật phiên bản
        "notes": "Ecoworld initial data structure with global shop and levels."
    }
}

# --- Hàm xử lý file dữ liệu kinh tế chính (economy.json) ---
def load_economy_data() -> dict:
    path_to_file = config.ECONOMY_FILE
    logger.debug(f"Đang tải dữ liệu kinh tế từ: {path_to_file}")
    if not os.path.exists(path_to_file):
        logger.warning(f"File {path_to_file} không tồn tại. Tạo file mới với cấu trúc mặc định.")
        data = DEFAULT_ECONOMY_STRUCTURE.copy()
        # Tạo bản sao sâu cho các dictionary lồng nhau để tránh tham chiếu dùng chung
        for key in ["users", "guild_configs", "global_shop_stock", "bot_metadata"]:
            if isinstance(DEFAULT_ECONOMY_STRUCTURE[key], dict):
                data[key] = DEFAULT_ECONOMY_STRUCTURE[key].copy()
        save_economy_data(data)
        return data
    try:
        with open(path_to_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                logger.warning(f"File {path_to_file} trống. Khởi tạo với cấu trúc mặc định.")
                data = DEFAULT_ECONOMY_STRUCTURE.copy()
                for key in ["users", "guild_configs", "global_shop_stock", "bot_metadata"]:
                     if isinstance(DEFAULT_ECONOMY_STRUCTURE[key], dict):
                        data[key] = DEFAULT_ECONOMY_STRUCTURE[key].copy()
                save_economy_data(data)
                return data
            loaded_data = json.loads(content)
            data_changed_structure = False
            for key, default_value in DEFAULT_ECONOMY_STRUCTURE.items():
                if key not in loaded_data:
                    logger.info(f"Key chính '{key}' không tồn tại trong {path_to_file}. Đang thêm key mặc định.")
                    loaded_data[key] = default_value.copy() if isinstance(default_value, (dict, list)) else default_value
                    data_changed_structure = True
            if data_changed_structure:
                logger.info(f"Đã thêm các key chính còn thiếu vào {path_to_file}. Tiến hành lưu.")
                save_economy_data(loaded_data)
            logger.debug(f"Dữ liệu từ {path_to_file} đã tải thành công.")
            return loaded_data
    except json.JSONDecodeError:
        logger.error(f"LỖI JSONDecodeError: File {path_to_file} bị lỗi JSON. Khởi tạo file mới.", exc_info=True)
        data = DEFAULT_ECONOMY_STRUCTURE.copy()
        for key in ["users", "guild_configs", "global_shop_stock", "bot_metadata"]:
            if isinstance(DEFAULT_ECONOMY_STRUCTURE[key], dict):
                data[key] = DEFAULT_ECONOMY_STRUCTURE[key].copy()
        save_economy_data(data)
        return data
    except Exception as e:
        logger.error(f"Lỗi không xác định khi tải dữ liệu từ {path_to_file}: {e}", exc_info=True)
        data = DEFAULT_ECONOMY_STRUCTURE.copy()
        for key in ["users", "guild_configs", "global_shop_stock", "bot_metadata"]:
             if isinstance(DEFAULT_ECONOMY_STRUCTURE[key], dict):
                data[key] = DEFAULT_ECONOMY_STRUCTURE[key].copy()
        return data

def save_economy_data(data: dict):
    path_to_file = config.ECONOMY_FILE
    temp_path_to_file = path_to_file + ".tmp"
    logger.debug(f"Chuẩn bị lưu dữ liệu kinh tế vào: {path_to_file}")
    try:
        with open(temp_path_to_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        os.replace(temp_path_to_file, path_to_file)
        logger.debug(f"Dữ liệu đã được lưu thành công vào {path_to_file}.")
    except Exception as e:
        logger.error(f"Lỗi khi lưu dữ liệu kinh tế vào {path_to_file}: {e}", exc_info=True)
        if os.path.exists(temp_path_to_file):
            try:
                os.remove(temp_path_to_file)
                logger.debug(f"Đã xóa file tạm {temp_path_to_file} sau lỗi lưu.")
            except Exception as e_remove:
                logger.error(f"Không thể xóa file tạm {temp_path_to_file}: {e_remove}")

# --- Quản lý User Profile Toàn Cục ---
def get_or_create_global_user_profile(data: dict, user_id: int) -> dict:
    user_id_str = str(user_id)
    if not isinstance(data.get("users"), dict): data["users"] = {}
    
    if user_id_str not in data["users"] or not isinstance(data["users"][user_id_str], dict):
        data["users"][user_id_str] = {k: (v.copy() if isinstance(v, (dict, list)) else v) for k, v in DEFAULT_GLOBAL_USER_DATA.items()}
        logger.info(f"User mới {user_id_str} đã được khởi tạo với dữ liệu toàn cục mặc định.")
    else:
        user_profile = data["users"][user_id_str]
        changed = False
        for key, default_val in DEFAULT_GLOBAL_USER_DATA.items():
            if key not in user_profile:
                user_profile[key] = default_val.copy() if isinstance(default_val, (dict, list)) else default_val
                changed = True
        if "bank_accounts" not in user_profile or not isinstance(user_profile["bank_accounts"], dict):
            user_profile["bank_accounts"] = {}
            changed = True
        if "server_specific_data" not in user_profile or not isinstance(user_profile["server_specific_data"], dict):
            user_profile["server_specific_data"] = {}
            changed = True
        if changed:
            logger.debug(f"Đã cập nhật các key toàn cục/cấu trúc còn thiếu cho user {user_id_str}.")
            
    return data["users"][user_id_str]

# --- Quản lý Dữ liệu Riêng của User tại Server ---
def get_or_create_user_server_data(global_user_profile: dict, guild_id: int) -> dict:
    """Lấy hoặc tạo mục server_specific_data cho user tại guild."""
    guild_id_str = str(guild_id)
    # global_user_profile['server_specific_data'] đã được đảm bảo là dict bởi hàm trên
    if guild_id_str not in global_user_profile["server_specific_data"] or \
       not isinstance(global_user_profile["server_specific_data"][guild_id_str], dict):
        global_user_profile["server_specific_data"][guild_id_str] = {
            k: (v.copy() if isinstance(v, (dict, list)) else v) for k, v in DEFAULT_USER_SERVER_SPECIFIC_DATA.items()
        }
        logger.debug(f"Đã khởi tạo server_specific_data cho user tại guild {guild_id_str}.")
    else: # Đảm bảo các key mặc định trong server_specific_data[guild_id_str]
        server_data = global_user_profile["server_specific_data"][guild_id_str]
        changed = False
        for key, default_val in DEFAULT_USER_SERVER_SPECIFIC_DATA.items():
            if key not in server_data:
                server_data[key] = default_val.copy() if isinstance(default_val, (dict, list)) else default_val
                changed = True
        if changed:
             logger.debug(f"Đã cập nhật các key local còn thiếu cho user tại guild {guild_id_str}.")
             
    return global_user_profile["server_specific_data"][guild_id_str]

# --- Ngân Hàng Server ---
def get_server_bank_balance(global_user_profile: dict, guild_id: int) -> int:
    guild_id_str = str(guild_id)
    return global_user_profile.get("bank_accounts", {}).get(guild_id_str, 0)

def set_server_bank_balance(global_user_profile: dict, guild_id: int, new_balance: int):
    guild_id_str = str(guild_id)
    # Đảm bảo bank_accounts là dict đã được thực hiện trong get_or_create_global_user_profile
    global_user_profile["bank_accounts"][guild_id_str] = int(new_balance)
    logger.debug(f"Đã đặt bank balance cho guild {guild_id_str} của user thành {new_balance}.")

# --- Guild Config ---
def get_or_create_guild_config(data: dict, guild_id: int) -> dict:
    guild_id_str = str(guild_id)
    if not isinstance(data.get("guild_configs"), dict): data["guild_configs"] = {}
    
    if guild_id_str not in data["guild_configs"] or not isinstance(data["guild_configs"][guild_id_str], dict):
        data["guild_configs"][guild_id_str] = DEFAULT_GUILD_CONFIG.copy()
        logger.info(f"Config mặc định đã được tạo cho guild mới: {guild_id_str}")
    else:
        guild_cfg = data["guild_configs"][guild_id_str]
        changed = False
        for key, default_val in DEFAULT_GUILD_CONFIG.items():
            if key not in guild_cfg:
                guild_cfg[key] = default_val.copy() if isinstance(default_val, (dict, list)) else default_val
                changed = True
        if changed:
            logger.debug(f"Đã cập nhật các key config còn thiếu cho guild {guild_id_str}.")
    return data["guild_configs"][guild_id_str]

# --- Global Shop Stock ---
def get_or_create_global_shop_stock(data: dict) -> dict:
    if not isinstance(data.get("global_shop_stock"), dict):
        data["global_shop_stock"] = {}
        logger.warning("'global_shop_stock' key không tồn tại hoặc không phải dict. Đã khởi tạo lại.")
    return data["global_shop_stock"]

def get_shop_item_info(shop_stock: dict, item_id: str) -> Optional[dict]:
    return shop_stock.get(item_id)

def update_shop_item_stock(shop_stock: dict, item_id: str, quantity_change: int):
    """quantity_change > 0 để tăng stock (restock), < 0 để giảm stock (mua)."""
    if item_id not in shop_stock: # Nếu item chưa từng có trong shop stock động
        # Lấy thông tin từ SHOP_ITEMS trong config để tạo mục mới
        if item_id in config.SHOP_ITEMS: # Kiểm tra xem item_id có trong danh sách item gốc không
            shop_stock[item_id] = {
                "current_stock": 0, # Khởi tạo stock là 0
                "max_stock": config.SHOP_ITEMS[item_id].get("default_max_stock", 10), # Lấy max_stock từ config hoặc mặc định
                "base_price": config.SHOP_ITEMS[item_id].get("price"),
                "can_restock": config.SHOP_ITEMS[item_id].get("default_can_restock", True),
                "last_restock_time": 0
            }
            logger.info(f"Vật phẩm '{item_id}' được thêm vào global_shop_stock lần đầu.")
        else:
            logger.error(f"Cố gắng cập nhật stock cho vật phẩm '{item_id}' không có trong SHOP_ITEMS gốc.")
            return False # Không thể cập nhật stock cho item không xác định

    item_data = shop_stock[item_id]
    item_data["current_stock"] = max(0, item_data["current_stock"] + quantity_change) # Đảm bảo stock không âm
    if quantity_change > 0 : # Restock
        item_data["last_restock_time"] = datetime.now().timestamp()
    logger.debug(f"Stock của vật phẩm '{item_id}' đã cập nhật: {quantity_change}. Stock mới: {item_data['current_stock']}")
    return True


# --- Các hàm quản lý MODERATOR (sử dụng file moderators.json riêng, giữ nguyên) ---
def load_moderator_ids() -> list:
    # ... (Nội dung hàm này giữ nguyên như phiên bản trước) ...
    path_to_file = config.MODERATORS_FILE 
    logger.debug(f"Đang tải danh sách moderator từ: {path_to_file}")
    try:
        if not os.path.exists(path_to_file):
            logger.warning(f"File moderator {path_to_file} không tồn tại. Tạo file mới với danh sách rỗng.")
            with open(path_to_file, 'w', encoding='utf-8') as f: json.dump({"moderator_ids": []}, f, indent=4)
            return []
        with open(path_to_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                logger.warning(f"File moderator {path_to_file} trống. Ghi lại cấu trúc mặc định.")
                with open(path_to_file, 'w', encoding='utf-8') as wf: json.dump({"moderator_ids": []}, wf, indent=4)
                return []
            data = json.loads(content)
            ids = data.get("moderator_ids", []); valid_ids = []
            for mod_id in ids:
                try: valid_ids.append(int(mod_id))
                except ValueError: logger.warning(f"ID moderator không hợp lệ trong file {path_to_file}: '{mod_id}'. Bỏ qua.")
            logger.debug(f"Danh sách moderator đã tải thành công từ {path_to_file}. Số lượng hợp lệ: {len(valid_ids)}")
            return valid_ids
    except json.JSONDecodeError:
        logger.error(f"LỖI JSONDecodeError: File {path_to_file} bị lỗi JSON. Trả về danh sách moderator rỗng.", exc_info=True)
        try:
            with open(path_to_file, 'w', encoding='utf-8') as f: json.dump({"moderator_ids": []}, f, indent=4)
        except Exception as e_write: logger.error(f"Không thể tạo lại file {path_to_file} sau lỗi JSONDecodeError: {e_write}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"Lỗi không xác định khi tải moderator_ids từ {path_to_file}: {e}", exc_info=True)
        return []

def save_moderator_ids(ids: list) -> bool:
    # ... (Nội dung hàm này giữ nguyên như phiên bản trước) ...
    path_to_file = config.MODERATORS_FILE 
    logger.debug(f"Đang lưu danh sách moderator vào: {path_to_file}. Dữ liệu: {ids}")
    try:
        cleaned_ids = list(set(int(mod_id) for mod_id in ids if str(mod_id).strip().isdigit()))
        with open(path_to_file, 'w', encoding='utf-8') as f:
            json.dump({"moderator_ids": cleaned_ids}, f, indent=4)
        logger.info(f"Danh sách moderator đã được lưu thành công vào {path_to_file}. Số lượng: {len(cleaned_ids)}")
        return True
    except Exception as e:
        logger.error(f"Lỗi khi lưu moderator_ids vào {path_to_file}: {e}", exc_info=True)
        return False

def add_moderator_id(user_id: int) -> bool:
    # ... (Nội dung hàm này giữ nguyên như phiên bản trước) ...
    try: mod_id_to_add = int(user_id)
    except ValueError: logger.error(f"Lỗi: User ID '{user_id}' cung cấp cho add_moderator_id không phải là số."); return False
    current_ids = load_moderator_ids()
    if mod_id_to_add not in current_ids:
        logger.info(f"Thêm moderator ID: {mod_id_to_add} vào danh sách.")
        current_ids.append(mod_id_to_add)
        return save_moderator_ids(current_ids)
    else: logger.info(f"User ID {mod_id_to_add} đã có trong danh sách moderator. Không thêm."); return True 

def remove_moderator_id(user_id: int) -> bool:
    # ... (Nội dung hàm này giữ nguyên như phiên bản trước) ...
    try: mod_id_to_remove = int(user_id)
    except ValueError: logger.error(f"Lỗi: User ID '{user_id}' cung cấp cho remove_moderator_id không phải là số."); return False
    current_ids = load_moderator_ids()
    if mod_id_to_remove in current_ids:
        logger.info(f"Xóa moderator ID: {mod_id_to_remove} khỏi danh sách.")
        current_ids.remove(mod_id_to_remove)
        return save_moderator_ids(current_ids)
    else: logger.warning(f"User ID {mod_id_to_remove} không tìm thấy trong danh sách moderator để xóa."); return False
