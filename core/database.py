# bot/core/database.py
import json
import os
import logging

# Sử dụng config.ECONOMY_FILE và config.MODERATORS_FILE
from . import config 

logger = logging.getLogger(__name__)

# --- Cấu trúc dữ liệu mặc định ---
DEFAULT_GLOBAL_USER_DATA = {
    "global_balance": 100,
    "inventory_global": [],
    "bank_accounts": {}, # Sẽ có dạng {"GUILD_ID_STR": balance}
    "last_work_global": 0,
    "last_daily_global": 0,
    "last_beg_global": 0,
    "last_rob_global": 0,
    "last_crime_global": 0,
    "last_fish_global": 0,
    "last_slots_global": 0,
    "last_cf_global": 0,
    "last_dice_global": 0
    # "preferred_language": "vi" # Cho tương lai
}

DEFAULT_GUILD_CONFIG = {
    "bare_command_active_channels": [],
    "muted_channels": []
    # Thêm các config server khác ở đây
}

DEFAULT_ECONOMY_STRUCTURE = {
    "users": {},
    "guild_configs": {},
    "bot_metadata": {
        "version": "1.0_hybrid_global" # Ví dụ metadata
    }
}

# --- Hàm xử lý file dữ liệu kinh tế chính (economy.json) ---
def load_economy_data() -> dict:
    """
    Tải dữ liệu từ config.ECONOMY_FILE.
    Nếu file không tồn tại, rỗng, hoặc lỗi JSON, sẽ tạo/khởi tạo cấu trúc mặc định.
    """
    path_to_file = config.ECONOMY_FILE
    logger.debug(f"Đang tải dữ liệu kinh tế từ: {path_to_file}")
    
    if not os.path.exists(path_to_file):
        logger.warning(f"File {path_to_file} không tồn tại. Tạo file mới với cấu trúc mặc định.")
        data = DEFAULT_ECONOMY_STRUCTURE.copy()
        save_economy_data(data)
        return data
    
    try:
        with open(path_to_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                logger.warning(f"File {path_to_file} trống. Khởi tạo với cấu trúc mặc định.")
                data = DEFAULT_ECONOMY_STRUCTURE.copy()
                save_economy_data(data)
                return data
            
            loaded_data = json.loads(content)
            
            data_changed = False
            for key, default_value in DEFAULT_ECONOMY_STRUCTURE.items():
                if key not in loaded_data:
                    logger.info(f"Key chính '{key}' không tồn tại trong {path_to_file}. Đang thêm key mặc định.")
                    loaded_data[key] = default_value.copy() # Dùng copy cho dict/list
                    data_changed = True
            
            if data_changed:
                logger.info(f"Đã thêm các key chính còn thiếu vào {path_to_file}. Tiến hành lưu.")
                save_economy_data(loaded_data)

            logger.debug(f"Dữ liệu từ {path_to_file} đã tải thành công.")
            return loaded_data
            
    except json.JSONDecodeError:
        logger.error(f"LỖI JSONDecodeError: File {path_to_file} bị lỗi JSON. Khởi tạo file mới.", exc_info=True)
        data = DEFAULT_ECONOMY_STRUCTURE.copy()
        save_economy_data(data)
        return data
    except Exception as e:
        logger.error(f"Lỗi không xác định khi tải dữ liệu từ {path_to_file}: {e}", exc_info=True)
        return DEFAULT_ECONOMY_STRUCTURE.copy()

def save_economy_data(data: dict):
    """Lưu toàn bộ dữ liệu kinh tế vào file config.ECONOMY_FILE (an toàn hơn)."""
    path_to_file = config.ECONOMY_FILE
    temp_path_to_file = path_to_file + ".tmp"
    logger.debug(f"Chuẩn bị lưu dữ liệu kinh tế vào: {path_to_file} (qua file tạm: {temp_path_to_file})")
    try:
        with open(temp_path_to_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        os.replace(temp_path_to_file, path_to_file)
        logger.debug(f"Dữ liệu đã được lưu thành công vào {path_to_file}.")
    except Exception as e:
        logger.error(f"Lỗi khi lưu dữ liệu kinh tế vào {path_to_file}: {e}", exc_info=True)
        # Cân nhắc việc thử xóa file tạm nếu có lỗi os.replace
        if os.path.exists(temp_path_to_file):
            try:
                os.remove(temp_path_to_file)
                logger.debug(f"Đã xóa file tạm {temp_path_to_file} sau lỗi lưu.")
            except Exception as e_remove:
                logger.error(f"Không thể xóa file tạm {temp_path_to_file}: {e_remove}")

# --- Các hàm lấy và tạo dữ liệu người dùng TOÀN CỤC ---
def get_or_create_global_user_profile(data: dict, user_id: int) -> dict:
    """
    Lấy (hoặc tạo nếu chưa có) profile toàn cục của người dùng từ `data['users']`.
    Trả về dictionary profile của user đó. Chỉnh sửa `data` trực tiếp nếu user mới.
    """
    user_id_str = str(user_id)
    # Đảm bảo data['users'] là một dictionary
    if not isinstance(data.get("users"), dict):
        data["users"] = {}
        logger.warning("Mục 'users' không phải dict hoặc không tồn tại. Đã khởi tạo lại.")

    if user_id_str not in data["users"] or not isinstance(data["users"][user_id_str], dict):
        data["users"][user_id_str] = DEFAULT_GLOBAL_USER_DATA.copy()
        logger.info(f"User mới {user_id_str} đã được khởi tạo với dữ liệu toàn cục mặc định.")
    else:
        # Đảm bảo user hiện tại có đủ các key mặc định toàn cục
        user_profile = data["users"][user_id_str]
        changed = False
        for key, default_val in DEFAULT_GLOBAL_USER_DATA.items():
            if key not in user_profile: # Chỉ thêm nếu key thực sự thiếu
                user_profile[key] = default_val.copy() if isinstance(default_val, (dict, list)) else default_val
                changed = True
        if "bank_accounts" not in user_profile or not isinstance(user_profile["bank_accounts"], dict):
            user_profile["bank_accounts"] = {} # Đảm bảo bank_accounts là dict
            changed = True
        if changed:
            logger.debug(f"Đã cập nhật các key toàn cục còn thiếu cho user {user_id_str}.")
            
    return data["users"][user_id_str]

# --- Các hàm xử lý NGÂN HÀNG THEO SERVER của người dùng ---
def get_server_bank_balance(user_profile: dict, guild_id: int) -> int:
    """Lấy số dư ngân hàng của user tại guild_id từ user_profile đã có. Trả về 0 nếu chưa có."""
    guild_id_str = str(guild_id)
    # user_profile['bank_accounts'] đã được đảm bảo là dict bởi get_or_create_global_user_profile
    return user_profile.get("bank_accounts", {}).get(guild_id_str, 0)

def set_server_bank_balance(user_profile: dict, guild_id: int, new_balance: int):
    """Đặt số dư ngân hàng của user tại guild_id. Sẽ tạo nếu chưa có."""
    guild_id_str = str(guild_id)
    # user_profile['bank_accounts'] đã được đảm bảo là dict
    user_profile["bank_accounts"][guild_id_str] = int(new_balance) # Đảm bảo là int
    logger.debug(f"Đã đặt bank balance cho guild {guild_id_str} của user thành {new_balance}.")

# --- Các hàm xử lý GUILD CONFIG (tương tự như cũ nhưng truy cập vào data["guild_configs"]) ---
def get_or_create_guild_config(data: dict, guild_id: int) -> dict:
    """Lấy (hoặc tạo nếu chưa có) config của guild từ `data['guild_configs']`."""
    guild_id_str = str(guild_id)
    if not isinstance(data.get("guild_configs"), dict):
        data["guild_configs"] = {}
        logger.warning("'guild_configs' key không tồn tại hoặc không phải dict. Đã khởi tạo lại.")

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

# Hàm save_guild_config riêng không cần thiết nữa, các lệnh sẽ gọi save_economy_data(data) sau khi sửa guild_config lấy từ get_or_create_guild_config.

# --- Các hàm quản lý MODERATOR (sử dụng file moderators.json riêng, giữ nguyên như trước) ---
def load_moderator_ids() -> list:
    # ... (Nội dung hàm này giữ nguyên như phiên bản đã có logger và test thành công) ...
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
    # ... (Nội dung hàm này giữ nguyên như phiên bản đã có logger và test thành công) ...
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
    # ... (Nội dung hàm này giữ nguyên như phiên bản đã có logger và test thành công) ...
    try: mod_id_to_add = int(user_id)
    except ValueError: logger.error(f"Lỗi: User ID '{user_id}' cung cấp cho add_moderator_id không phải là số."); return False
    current_ids = load_moderator_ids()
    if mod_id_to_add not in current_ids:
        logger.info(f"Thêm moderator ID: {mod_id_to_add} vào danh sách.")
        current_ids.append(mod_id_to_add)
        return save_moderator_ids(current_ids)
    else: logger.info(f"User ID {mod_id_to_add} đã có trong danh sách moderator. Không thêm."); return True 

def remove_moderator_id(user_id: int) -> bool:
    # ... (Nội dung hàm này giữ nguyên như phiên bản đã có logger và test thành công) ...
    try: mod_id_to_remove = int(user_id)
    except ValueError: logger.error(f"Lỗi: User ID '{user_id}' cung cấp cho remove_moderator_id không phải là số."); return False
    current_ids = load_moderator_ids()
    if mod_id_to_remove in current_ids:
        logger.info(f"Xóa moderator ID: {mod_id_to_remove} khỏi danh sách.")
        current_ids.remove(mod_id_to_remove)
        return save_moderator_ids(current_ids)
    else: logger.warning(f"User ID {mod_id_to_remove} không tìm thấy trong danh sách moderator để xóa."); return False
