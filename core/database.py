# bot/core/database.py
import json
import os
import logging

from . import config # Sử dụng config.ECONOMY_FILE, config.MODERATORS_FILE

logger = logging.getLogger(__name__)

# Cấu trúc dữ liệu mặc định cho một user hoàn toàn mới (phần toàn cục)
DEFAULT_GLOBAL_USER_DATA = {
    "global_balance": 100,  # Số dư ví toàn cục ban đầu
    "inventory_global": [],
    "bank_accounts": {},    # Sẽ có dạng {"GUILD_ID": balance}
    "last_work_global": 0,
    "last_daily_global": 0,
    "last_beg_global": 0,
    "last_rob_global": 0,
    "last_crime_global": 0,
    "last_fish_global": 0,
    "last_slots_global": 0,
    "last_cf_global": 0,
    "last_dice_global": 0
    # Thêm các trường toàn cục khác ở đây nếu cần
}

# Cấu trúc dữ liệu mặc định cho một guild config mới
DEFAULT_GUILD_CONFIG = {
    "bare_command_active_channels": [],
    "muted_channels": []
    # Thêm các trường config guild khác ở đây nếu cần
}

# Cấu trúc dữ liệu mặc định cho file economy.json nếu file rỗng hoặc mới
DEFAULT_ECONOMY_STRUCTURE = {
    "users": {},
    "guild_configs": {},
    "bot_metadata": {} # Có thể thêm các metadata cho bot ở đây
}

def load_economy_data() -> dict:
    """
    Tải dữ liệu từ file config.ECONOMY_FILE.
    Nếu file không tồn tại, rỗng, hoặc lỗi JSON, sẽ tạo/khởi tạo cấu trúc mặc định.
    """
    path_to_file = config.ECONOMY_FILE
    logger.debug(f"Đang tải dữ liệu kinh tế từ: {path_to_file}")
    
    if not os.path.exists(path_to_file):
        logger.warning(f"File {path_to_file} không tồn tại. Tạo file mới với cấu trúc mặc định.")
        data = DEFAULT_ECONOMY_STRUCTURE.copy() # Dùng copy để tránh thay đổi hằng số
        save_economy_data(data) # Lưu lại file mới được tạo
        return data
    
    try:
        with open(path_to_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                logger.warning(f"File {path_to_file} trống. Khởi tạo với cấu trúc mặc định.")
                data = DEFAULT_ECONOMY_STRUCTURE.copy()
                save_economy_data(data) # Lưu lại file mới được tạo
                return data
            
            loaded_data = json.loads(content)
            
            # Đảm bảo các key chính tồn tại
            data_changed = False
            for key, default_value in DEFAULT_ECONOMY_STRUCTURE.items():
                if key not in loaded_data:
                    loaded_data[key] = default_value
                    data_changed = True
            
            if data_changed:
                logger.info(f"Đã thêm các key chính còn thiếu vào {path_to_file}. Tiến hành lưu.")
                save_economy_data(loaded_data) # Lưu lại nếu có thay đổi cấu trúc chính

            logger.debug(f"Dữ liệu từ {path_to_file} đã tải thành công.")
            return loaded_data
            
    except json.JSONDecodeError:
        logger.error(f"LỖI JSONDecodeError: File {path_to_file} bị lỗi JSON. Khởi tạo file mới với cấu trúc mặc định.", exc_info=True)
        data = DEFAULT_ECONOMY_STRUCTURE.copy()
        save_economy_data(data)
        return data
    except Exception as e:
        logger.error(f"Lỗi không xác định khi tải dữ liệu từ {path_to_file}: {e}", exc_info=True)
        # Trong trường hợp lỗi nghiêm trọng không rõ, trả về cấu trúc mặc định để bot có thể tiếp tục (cẩn thận)
        return DEFAULT_ECONOMY_STRUCTURE.copy()

def save_economy_data(data: dict):
    """Lưu toàn bộ dữ liệu kinh tế vào file config.ECONOMY_FILE."""
    path_to_file = config.ECONOMY_FILE
    logger.debug(f"Đang lưu dữ liệu kinh tế vào: {path_to_file}")
    try:
        # Ghi vào file tạm trước
        temp_path_to_file = path_to_file + ".tmp"
        with open(temp_path_to_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        # Nếu ghi file tạm thành công, đổi tên thành file chính
        os.replace(temp_path_to_file, path_to_file) # os.replace là atomic trên nhiều hệ thống
        logger.debug(f"Dữ liệu đã được lưu thành công vào {path_to_file} (qua file tạm).")
    except Exception as e:
        logger.error(f"Lỗi khi lưu dữ liệu vào {path_to_file}: {e}", exc_info=True)

# --- Các hàm xử lý dữ liệu người dùng TOÀN CỤC ---
def get_or_create_global_user_profile(data: dict, user_id: int) -> dict:
    """
    Lấy (hoặc tạo nếu chưa có) profile toàn cục của người dùng từ dictionary `data` đã load.
    Trả về dictionary con của user đó trong `data['users']`.
    Hàm này sẽ chỉnh sửa `data` trực tiếp nếu user mới.
    """
    user_id_str = str(user_id)
    if "users" not in data or not isinstance(data["users"], dict): # Đảm bảo key 'users' tồn tại và là dict
        data["users"] = {}
        logger.warning("'users' key không tồn tại hoặc không phải dict trong data. Đã khởi tạo.")

    if user_id_str not in data["users"]:
        data["users"][user_id_str] = DEFAULT_GLOBAL_USER_DATA.copy()
        logger.info(f"User mới {user_id_str} đã được khởi tạo với dữ liệu toàn cục mặc định.")
    else:
        # Đảm bảo user hiện tại có đủ các key mặc định toàn cục
        user_profile = data["users"][user_id_str]
        if not isinstance(user_profile, dict): # Nếu dữ liệu user bị lỗi, không phải dict
            logger.warning(f"Dữ liệu của user {user_id_str} không phải dict, reset về mặc định. Dữ liệu cũ: {user_profile}")
            data["users"][user_id_str] = DEFAULT_GLOBAL_USER_DATA.copy()
        else:
            changed = False
            for key, default_val in DEFAULT_GLOBAL_USER_DATA.items():
                if key not in user_profile:
                    user_profile[key] = default_val
                    changed = True
            if changed:
                logger.debug(f"Đã cập nhật các key toàn cục còn thiếu cho user {user_id_str}.")
    
    # Đảm bảo bank_accounts là một dictionary
    if "bank_accounts" not in data["users"][user_id_str] or not isinstance(data["users"][user_id_str]["bank_accounts"], dict):
        data["users"][user_id_str]["bank_accounts"] = {}
        logger.debug(f"Đã khởi tạo 'bank_accounts' rỗng cho user {user_id_str}.")

    return data["users"][user_id_str]


# --- Các hàm xử lý NGÂN HÀNG THEO SERVER của người dùng ---
def get_server_bank_balance(user_profile: dict, guild_id: int) -> int:
    """Lấy số dư ngân hàng của user tại guild_id. Trả về 0 nếu chưa có."""
    guild_id_str = str(guild_id)
    # user_profile ở đây là data['users'][user_id_str]
    return user_profile.get("bank_accounts", {}).get(guild_id_str, 0)

def update_server_bank_balance(user_profile: dict, guild_id: int, amount_change: int, is_deposit: bool = True):
    """
    Cập nhật số dư ngân hàng của user tại guild_id.
    Nếu is_deposit=True, amount_change là số dương.
    Nếu is_deposit=False (withdraw), amount_change cũng là số dương (số tiền rút).
    Hàm này sẽ tự trừ/cộng.
    """
    guild_id_str = str(guild_id)
    # Đảm bảo bank_accounts là một dictionary
    if "bank_accounts" not in user_profile or not isinstance(user_profile["bank_accounts"], dict):
        user_profile["bank_accounts"] = {}
        logger.debug(f"Khởi tạo 'bank_accounts' cho user khi update_server_bank_balance.")
        
    current_bank_balance = user_profile.get("bank_accounts", {}).get(guild_id_str, 0)
    
    if is_deposit:
        user_profile["bank_accounts"][guild_id_str] = current_bank_balance + amount_change
    else: # Withdraw
        user_profile["bank_accounts"][guild_id_str] = current_bank_balance - amount_change
    logger.debug(f"Đã cập nhật bank balance cho guild {guild_id_str} của user. Is_deposit: {is_deposit}, Amount_change: {amount_change}, New_bank_balance: {user_profile['bank_accounts'][guild_id_str]}")


# --- Các hàm xử lý GUILD CONFIG (tương tự như cũ nhưng truy cập vào data["guild_configs"]) ---
def get_or_create_guild_config(data: dict, guild_id: int) -> dict:
    """Lấy (hoặc tạo nếu chưa có) config của guild từ dictionary `data` đã load."""
    guild_id_str = str(guild_id)
    if "guild_configs" not in data or not isinstance(data["guild_configs"], dict):
        data["guild_configs"] = {}
        logger.warning("'guild_configs' key không tồn tại hoặc không phải dict trong data. Đã khởi tạo.")

    if guild_id_str not in data["guild_configs"]:
        data["guild_configs"][guild_id_str] = DEFAULT_GUILD_CONFIG.copy()
        logger.info(f"Config mặc định đã được tạo cho guild mới: {guild_id_str}")
    else:
        # Đảm bảo guild hiện tại có đủ các key config mặc định
        guild_cfg = data["guild_configs"][guild_id_str]
        if not isinstance(guild_cfg, dict):
            logger.warning(f"Config của guild {guild_id_str} không phải dict, reset về mặc định. Dữ liệu cũ: {guild_cfg}")
            data["guild_configs"][guild_id_str] = DEFAULT_GUILD_CONFIG.copy()
        else:
            changed = False
            for key, default_val in DEFAULT_GUILD_CONFIG.items():
                if key not in guild_cfg:
                    guild_cfg[key] = default_val
                    changed = True
            if changed:
                logger.debug(f"Đã cập nhật các key config còn thiếu cho guild {guild_id_str}.")
                
    return data["guild_configs"][guild_id_str]
# --- Các hàm quản lý MODERATOR (sử dụng file moderators.json riêng, giữ nguyên như trước) ---
def load_moderator_ids() -> list:
    path_to_file = config.MODERATORS_FILE 
    # ... (logic hàm này giữ nguyên như phiên bản bạn đã có và test thành công) ...
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
    # ... (hàm này giữ nguyên như phiên bản bạn đã có và test thành công) ...
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
    # ... (hàm này giữ nguyên như phiên bản bạn đã có và test thành công) ...
    try: mod_id_to_add = int(user_id)
    except ValueError: logger.error(f"Lỗi: User ID '{user_id}' cung cấp cho add_moderator_id không phải là số."); return False
    current_ids = load_moderator_ids()
    if mod_id_to_add not in current_ids:
        logger.info(f"Thêm moderator ID: {mod_id_to_add} vào danh sách.")
        current_ids.append(mod_id_to_add)
        return save_moderator_ids(current_ids)
    else: logger.info(f"User ID {mod_id_to_add} đã có trong danh sách moderator. Không thêm."); return True 


def remove_moderator_id(user_id: int) -> bool:
    # ... (hàm này giữ nguyên như phiên bản bạn đã có và test thành công) ...
    try: mod_id_to_remove = int(user_id)
    except ValueError: logger.error(f"Lỗi: User ID '{user_id}' cung cấp cho remove_moderator_id không phải là số."); return False
    current_ids = load_moderator_ids()
    if mod_id_to_remove in current_ids:
        logger.info(f"Xóa moderator ID: {mod_id_to_remove} khỏi danh sách.")
        current_ids.remove(mod_id_to_remove)
        return save_moderator_ids(current_ids)
    else: logger.warning(f"User ID {mod_id_to_remove} không tìm thấy trong danh sách moderator để xóa."); return False
