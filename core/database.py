# bot/core/database.py
import json
import os
import logging

# Import các thành phần cần thiết từ các file khác trong 'core'
from . import config # Giả sử bạn import config theo cách này

logger = logging.getLogger(__name__) # Logger cho module database

# --- load_data() và save_data() giữ nguyên như trước ---
def load_data():
    # ... (code của hàm load_data không thay đổi) ...
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
    # ... (code của hàm save_data không thay đổi) ...
    path_to_file = config.ECONOMY_FILE 
    logger.debug(f"Đang lưu dữ liệu vào: {path_to_file}")
    try:
        with open(path_to_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.debug(f"Dữ liệu đã được lưu thành công vào {path_to_file}.")
    except Exception as e:
        logger.error(f"Lỗi khi lưu dữ liệu vào {path_to_file}: {e}", exc_info=True)

# --- HÀM get_guild_config ĐƯỢC CẬP NHẬT ---
def get_guild_config(guild_id):
    data = load_data()
    guild_id_str = str(guild_id)
    
    # Trường hợp guild chưa có trong dữ liệu
    if guild_id_str not in data:
        logger.info(f"Khởi tạo config mặc định cho guild ID mới: {guild_id_str}")
        data[guild_id_str] = {
            "config": {
                "bare_command_active_channels": [],
                "muted_channels": [],
                "active_events": {}  # << Đảm bảo active_events được khởi tạo
            }
            # Không cần khởi tạo user data ở đây, check_user sẽ làm việc đó
        }
        # Lưu ý: get_guild_config thường chỉ đọc và chuẩn bị dữ liệu.
        # Việc lưu thực sự (save_data) thường do các hàm khác gọi sau khi có thay đổi.
        
    # Trường hợp guild đã có nhưng thiếu mục "config" hoặc "config" không phải là dictionary
    elif "config" not in data[guild_id_str] or not isinstance(data[guild_id_str]["config"], dict):
        logger.warning(f"Config cho guild ID {guild_id_str} không hợp lệ hoặc thiếu. Khởi tạo lại.")
        data[guild_id_str]["config"] = {
            "bare_command_active_channels": [],
            "muted_channels": [],
            "active_events": {}  # << Đảm bảo active_events được khởi tạo lại
        }
    # Trường hợp guild đã có "config" hợp lệ
    else:
        # Sử dụng setdefault để đảm bảo các key cơ bản tồn tại mà không ghi đè nếu đã có
        data[guild_id_str]["config"].setdefault("bare_command_active_channels", [])
        data[guild_id_str]["config"].setdefault("muted_channels", [])
        data[guild_id_str]["config"].setdefault("active_events", {})  # << ĐẢM BẢO active_events LUÔN TỒN TẠI

    return data[guild_id_str]["config"].copy() # Trả về bản copy của config

# --- Các hàm còn lại (save_guild_config, check_user, get_user_data, load_moderator_ids, etc.) ---
# --- giữ nguyên như phiên bản bạn đã cung cấp trước đó, không cần thay đổi cho Bước 1 này. ---
