# migrate_to_sqlite.py
import json
import sqlite3
import logging
import os

JSON_ECONOMY_FILE = 'economy.json'
JSON_ITEMS_FILE = 'items.json'
DB_PATH = "data/econzone.sqlite"

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def migrate():
    logging.info("Bắt đầu quá trình di chuyển dữ liệu từ JSON sang SQLite...")
    if not os.path.exists(JSON_ECONOMY_FILE) or not os.path.exists(JSON_ITEMS_FILE):
        logging.error("Lỗi: Không tìm thấy file economy.json hoặc items.json.")
        return

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # (Dán toàn bộ mã SQL từ hàm initialize_database ở trên vào đây)
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS users ...;
            CREATE TABLE IF NOT EXISTS user_guild_data ...;
            ...
        """)
        logging.info("Đã kiểm tra/tạo các bảng trong SQLite.")
    except Exception as e:
        logging.error(f"Lỗi khi tạo bảng: {e}", exc_info=True)
        conn.close()
        return

    # Di chuyển items.json
    try:
        with open(JSON_ITEMS_FILE, 'r', encoding='utf-8') as f:
            items_data = json.load(f)
        all_items = {**items_data.get("shop_items", {}), **items_data.get("utility_items", {})}
        for item_id, details in all_items.items():
            effect = details.get('effect', {})
            cursor.execute("INSERT OR REPLACE INTO items (item_id, name, description, price, sell_price, type, effect_stat, effect_value, capacity) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (item_id, details.get('name'), details.get('description'), details.get('price'), details.get('sell_price'), details.get('type'), effect.get('stat'), effect.get('value'), details.get('capacity')))
        conn.commit()
        logging.info(f"Hoàn tất di chuyển {len(all_items)} vật phẩm.")
    except Exception as e:
        logging.error(f"Lỗi khi di chuyển items.json: {e}", exc_info=True)
        conn.close()
        return

    # Di chuyển economy.json
    try:
        with open(JSON_ECONOMY_FILE, 'r', encoding='utf-8') as f:
            eco_data = json.load(f)

        users = eco_data.get('users', {})
        for user_id_str, profile in users.items():
            if not user_id_str.isdigit(): continue
            user_id = int(user_id_str)
            
            cursor.execute("INSERT OR REPLACE INTO users (user_id, bank_balance, wanted_level, level_global, xp_global, last_active_guild_id) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, profile.get('bank_balance', 0), profile.get('wanted_level', 0.0), profile.get('level_global', 1), profile.get('xp_global', 0), profile.get('last_active_guild_id')))

            for item in profile.get('inventory_global', []):
                item_id = item if isinstance(item, str) else item.get('item_id')
                cursor.execute("INSERT INTO inventories (user_id, item_id, location, is_tainted, quantity) VALUES (?, ?, 'global', ?, 1)",
                    (user_id, item_id, item.get('is_tainted', 0) if isinstance(item, dict) else 0))

            for guild_id_str, local_data in profile.get('server_data', {}).items():
                if not guild_id_str.isdigit(): continue
                guild_id = int(guild_id_str)
                balance = local_data.get('local_balance', {})
                stats = local_data.get('survival_stats', {})
                cursor.execute("INSERT OR REPLACE INTO user_guild_data (user_id, guild_id, local_balance_earned, local_balance_adadd, level_local, xp_local, health, hunger, energy) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (user_id, guild_id, balance.get('earned', 0), balance.get('adadd', 0), local_data.get('level_local', 1), local_data.get('xp_local', 0), stats.get('health', 100), stats.get('hunger', 100), stats.get('energy', 100)))

                for item in local_data.get('inventory_local', []):
                    item_id = item if isinstance(item, str) else item.get('item_id')
                    cursor.execute("INSERT INTO inventories (user_id, item_id, location, guild_id, is_tainted, quantity) VALUES (?, ?, 'local', ?, ?, 1)",
                        (user_id, item_id, guild_id, item.get('is_tainted', 0) if isinstance(item, dict) else 0))
        conn.commit()
        logging.info(f"Hoàn tất di chuyển dữ liệu cho {len(users)} người dùng.")
    except Exception as e:
        logging.error(f"Lỗi khi di chuyển economy.json: {e}", exc_info=True)
    finally:
        conn.close()
    logging.info("====== QUÁ TRÌNH DI CHUYỂN HOÀN TẤT ======")

if __name__ == "__main__":
    migrate()
