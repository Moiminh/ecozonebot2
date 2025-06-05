# bot/core/database.py
import json
import os
import logging 

# Import toàn bộ module config để truy cập các hằng số qua tiền tố 'config.'
from . import config 

logger = logging.getLogger(__name__) # Logger cho module database

# --- JSON Data System (cho economy.json) ---
def load_data():
    """Tải dữ liệu kinh tế từ file ECONOMY_FILE."""
    path_to_file = config.ECONOMY_FILE 
    logger.debug(f"Đang tải dữ liệu từ: {path_to_file}")
    if not os.path.exists(path_to_file):
        logger.warning(f"File {path_to_file} không tồn tại. Tạo file mới với dữ liệu rỗng.")
        with open(path_to_file, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=4, ensure_ascii=False)
        return {}
    try:
        with open(path_to_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                logger.warning(f"File {path_to_file} trống. Trả về dữ liệu rỗng.")
                return {} 
            data = json.loads(content)
            logger.debug(f"Dữ liệu từ {path_to_file} đã tải thành công.")
            return data
    except json.JSONDecodeError:
        logger.error(f"LỖI JSONDecodeError: File {path_to_file} bị lỗi JSON. Tạo lại file rỗng.", exc_info=True)
        try:
            with open(path_to_file, 'w', encoding='utf-8') as f:
                json.dump({}, f, indent=4, ensure_ascii=False)
        except Exception as e_write:
            logger.error(f"Không thể tạo lại file {path_to_file} sau lỗi JSONDecodeError: {e_write}", exc_info=True)
        return {}
    except Exception as e:
        logger.error(f"Lỗi không xác định khi tải dữ liệu từ {path_to_file}: {e}", exc_info=True)
        return {}

def save_data(data):
    """Lưu dữ liệu kinh tế vào file ECONOMY_FILE."""
    path_to_file = config.ECONOMY_FILE 
    logger.debug(f"Đang lưu dữ liệu vào: {path_to_file}")
    try:
        with open(path_to_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.debug(f"Dữ liệu đã được lưu thành công vào {path_to_file}.")
    except Exception as e:
        logger.error(f"Lỗi khi lưu dữ liệu vào {path_to_file}: {e}", exc_info=True)

def get_guild_config(guild_id):
    data = load_data()
    guild_id_str = str(guild_id)
    if guild_id_str not in data:
        logger.info(f"Khởi tạo config mặc định cho guild ID mới: {guild_id_str}")
        data[guild_id_str] = {"config": {"bare_command_active_channels": [], "muted_channels": []}}
    elif "config" not in data[guild_id_str] or not isinstance(data[guild_id_str]["config"], dict):
        logger.warning(f"Config cho guild ID {guild_id_str} không hợp lệ hoặc thiếu. Khởi tạo lại.")
        data[guild_id_str]["config"] = {"bare_command_active_channels": [], "muted_channels": []}
    else:
        data[guild_id_str]["config"].setdefault("bare_command_active_channels", [])
        data[guild_id_str]["config"].setdefault("muted_channels", [])
    return data[guild_id_str]["config"].copy()


def save_guild_config(guild_id, config_data_to_save):
    data = load_data()
    guild_id_str = str(guild_id)
    logger.info(f"Đang lưu guild config cho guild ID {guild_id_str}. Dữ liệu mới: {config_data_to_save}")
    if guild_id_str not in data: 
        data[guild_id_str] = {}
    data[guild_id_str]["config"] = config_data_to_save 
    save_data(data)
    logger.info(f"Đã lưu guild config cho guild ID {guild_id_str}.")


def check_user(data, guild_id, user_id):
    guild_id_str, user_id_str = str(guild_id), str(user_id)
    if guild_id_str not in data:
        data[guild_id_str] = {"config": {"bare_command_active_channels": [], "muted_channels": []}}
        logger.debug(f"check_user: Đã tạo mục guild mới cho {guild_id_str} vì chưa tồn tại.")
    elif "config" not in data[guild_id_str] or not isinstance(data[guild_id_str]["config"], dict):
        data[guild_id_str]["config"] = {"bare_command_active_channels": [], "muted_channels": []}
        logger.debug(f"check_user: Đã reset config cho {guild_id_str} do không hợp lệ.")
    else:
        data[guild_id_str]["config"].setdefault("bare_command_active_channels", [])
        data[guild_id_str]["config"].setdefault("muted_channels", [])

    defaults_user = {
        "balance": 100, "bank_balance": 0, "inventory": [],
        "last_work": 0, "last_daily": 0, "last_beg": 0, "last_rob": 0,
        "last_crime": 0, "last_fish": 0, "last_slots": 0, "last_cf": 0, "last_dice": 0
    }
    if user_id_str != "config":
        if user_id_str not in data[guild_id_str]:
            data[guild_id_str][user_id_str] = defaults_user.copy()
            logger.info(f"check_user: User mới {user_id_str} trong guild {guild_id_str} đã được khởi tạo với dữ liệu mặc định.")
        elif not isinstance(data[guild_id_str][user_id_str], dict):
             data[guild_id_str][user_id_str] = defaults_user.copy()
             logger.warning(f"check_user: Dữ liệu của user {user_id_str} trong guild {guild_id_str} không phải dict, đã reset về mặc định.")
        else: 
            updated_keys = False # Sử dụng biến khác để tránh nhầm lẫn với hàm updated() của Python 3.12
            for key, default_value in defaults_user.items():
                if key not in data[guild_id_str][user_id_str]: # Chỉ setdefault nếu key thực sự thiếu
                    data[guild_id_str][user_id_str].setdefault(key, default_value)
                    updated_keys = True
            if updated_keys:
                 logger.debug(f"check_user: Đã cập nhật các key còn thiếu cho user {user_id_str} trong guild {guild_id_str}.")
    return data

def get_user_data(guild_id, user_id):
    data = load_data()
    data = check_user(data, guild_id, user_id)
    return data

# ========== CÁC HÀM CHO QUẢN LÝ MODERATOR ==========

def load_moderator_ids() -> list: # <<< ĐẢM BẢO HÀM NÀY ĐƯỢC ĐỊNH NGHĨA ĐÚNG
    """Tải danh sách User ID của moderator từ file MODERATORS_FILE."""
    path_to_file = config.MODERATORS_FILE 
    logger.debug(f"Đang tải danh sách moderator từ: {path_to_file}")
    try:
        if not os.path.exists(path_to_file):
            logger.warning(f"File moderator {path_to_file} không tồn tại. Tạo file mới với danh sách rỗng.")
            with open(path_to_file, 'w', encoding='utf-8') as f:
                json.dump({"moderator_ids": []}, f, indent=4)
            return []
        
        with open(path_to_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                logger.warning(f"File moderator {path_to_file} trống. Ghi lại cấu trúc mặc định.")
                with open(path_to_file, 'w', encoding='utf-8') as wf:
                    json.dump({"moderator_ids": []}, wf, indent=4)
                return []
            data = json.loads(content)
            ids = data.get("moderator_ids", [])
            # Đảm bảo tất cả ID trong danh sách là số nguyên
            valid_ids = []
            for mod_id in ids:
                try:
                    valid_ids.append(int(mod_id))
                except ValueError:
                    logger.warning(f"ID moderator không hợp lệ trong file {path_to_file}: '{mod_id}'. Bỏ qua.")
            logger.debug(f"Danh sách moderator đã tải thành công từ {path_to_file}. Số lượng hợp lệ: {len(valid_ids)}")
            return valid_ids
    except json.JSONDecodeError:
        logger.error(f"LỖI JSONDecodeError: File {path_to_file} bị lỗi JSON. Trả về danh sách moderator rỗng.", exc_info=True)
        try:
            with open(path_to_file, 'w', encoding='utf-8') as f: # Đảm bảo path_to_file được dùng ở đây
                json.dump({"moderator_ids": []}, f, indent=4)
        except Exception as e_write:
            logger.error(f"Không thể tạo lại file {path_to_file} sau lỗi JSONDecodeError: {e_write}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"Lỗi không xác định khi tải moderator_ids từ {path_to_file}: {e}", exc_info=True)
        return []

def save_moderator_ids(ids: list) -> bool:
    """Lưu danh sách User ID của moderator vào file MODERATORS_FILE."""
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
    """Thêm một User ID vào danh sách moderator và lưu lại."""
    try:
        mod_id_to_add = int(user_id)
    except ValueError:
        logger.error(f"Lỗi: User ID '{user_id}' cung cấp cho add_moderator_id không phải là số.")
        return False

    current_ids = load_moderator_ids()
    if mod_id_to_add not in current_ids:
        logger.info(f"Thêm moderator ID: {mod_id_to_add} vào danh sách.")
        current_ids.append(mod_id_to_add)
        return save_moderator_ids(current_ids)
    else:
        logger.info(f"User ID {mod_id_to_add} đã có trong danh sách moderator. Không thêm.")
        return True 

def remove_moderator_id(user_id: int) -> bool:
    """Xóa một User ID khỏi danh sách moderator và lưu lại."""
    try:
        mod_id_to_remove = int(user_id)
    except ValueError:
        logger.error(f"Lỗi: User ID '{user_id}' cung cấp cho remove_moderator_id không phải là số.")
        return False
        
    current_ids = load_moderator_ids()
    if mod_id_to_remove in current_ids:
        logger.info(f"Xóa moderator ID: {mod_id_to_remove} khỏi danh sách.")
        current_ids.remove(mod_id_to_remove)
        return save_moderator_ids(current_ids)
    else:
        logger.warning(f"User ID {mod_id_to_remove} không tìm thấy trong danh sách moderator để xóa.")
        return False
