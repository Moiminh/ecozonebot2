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
        logging.error(f"Lỗi: Không tìm thấy file {JSON_ECONOMY_FILE} hoặc {JSON_ITEMS_FILE}.")
        return

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Sử dụng schema đầy đủ nhất
        cursor.executescript("""
            DROP TABLE IF EXISTS inventories;
            DROP TABLE IF EXISTS items;
            DROP TABLE IF EXISTS user_guild_data;
            DROP TABLE IF EXISTS users;
            DROP TABLE IF EXISTS cooldowns;
            DROP TABLE IF EXISTS guild_configs;

            CREATE TABLE users (
                user_id INTEGER PRIMARY KEY, bank_balance INTEGER DEFAULT 0, wanted_level REAL DEFAULT 0.0,
                level_global INTEGER DEFAULT 1, xp_global INTEGER DEFAULT 0, last_active_guild_id INTEGER
            );
            CREATE TABLE user_guild_data (
                user_id INTEGER NOT NULL, guild_id INTEGER NOT NULL, local_balance_earned INTEGER DEFAULT 0,
                local_balance_adadd INTEGER DEFAULT 0, level_local INTEGER DEFAULT 1, xp_local INTEGER DEFAULT 0,
                health INTEGER DEFAULT 100, hunger INTEGER DEFAULT 100, energy INTEGER DEFAULT 100,
                PRIMARY KEY (user_id, guild_id), FOREIGN KEY (user_id) REFERENCES users (user_id)
            );
            CREATE TABLE items (
                item_id TEXT PRIMARY KEY, name TEXT, description TEXT, price INTEGER, sell_price INTEGER, type TEXT,
                effect_stat TEXT, effect_value INTEGER, capacity INTEGER, current_stock INTEGER DEFAULT 20, max_stock INTEGER DEFAULT 50
            );
            CREATE TABLE inventories (
                inventory_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, item_id TEXT NOT NULL,
                location TEXT NOT NULL, guild_id INTEGER, is_tainted BOOLEAN DEFAULT 0, is_foreign BOOLEAN DEFAULT 0,
                quantity INTEGER DEFAULT 1, custom_data TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id), FOREIGN KEY (item_id) REFERENCES items (item_id)
            );
            CREATE TABLE cooldowns (key TEXT PRIMARY KEY, value REAL);
            CREATE TABLE guild_configs (
                guild_id INTEGER PRIMARY KEY, bare_command_active_channels TEXT DEFAULT '[]', muted_channels TEXT DEFAULT '[]'
            );
        """)
        logging.info("Đã xóa bảng cũ và tạo lại schema mới nhất trong SQLite.")
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
            cursor.execute("""
                INSERT OR REPLACE INTO items 
                (item_id, name, description, price, sell_price, type, effect_stat, effect_value, capacity, max_stock)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item_id, details.get('name'), details.get('description'), details.get('price'), details.get('sell_price'),
                details.get('type'), effect.get('stat'), effect.get('value'), details.get('capacity'), details.get('max_stock')
            ))
        conn.commit()
        logging.info(f"Hoàn tất di chuyển {len(all_items)} vật phẩm từ {JSON_ITEMS_FILE}.")
    except Exception as e:
        logging.error(f"Lỗi khi di chuyển {JSON_ITEMS_FILE}: {e}", exc_info=True)
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
                (user_id, profile.get('global_balance', 0), 0.0, profile.get('level_global', 1), profile.get('xp_global', 0), None))

            for guild_id_str, local_data in profile.get('server_data', {}).items():
                if not guild_id_str.isdigit(): continue
                guild_id = int(guild_id_str)
                balance = local_data.get('local_balance', {})
                cursor.execute("INSERT OR REPLACE INTO user_guild_data (user_id, guild_id, local_balance_earned, local_balance_adadd, level_local, xp_local) VALUES (?, ?, ?, ?, ?, ?)",
                    (user_id, guild_id, balance.get('earned', 0), balance.get('admin_added', 0), local_data.get('level_local', 1), local_data.get('xp_local', 0)))

        conn.commit()
        logging.info(f"Hoàn tất di chuyển dữ liệu cho {len(users)} người dùng từ {JSON_ECONOMY_FILE}.")
    except Exception as e:
        logging.error(f"Lỗi khi di chuyển {JSON_ECONOMY_FILE}: {e}", exc_info=True)
    finally:
        conn.close()

    logging.info("====== QUÁ TRÌNH DI CHUYỂN HOÀN TẤT ======")

if __name__ == "__main__":
    migrate()
