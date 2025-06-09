import json
import sqlite3
import logging
import os

# --- Cấu hình ---
JSON_ECONOMY_FILE = 'economy.json'
JSON_ITEMS_FILE = 'items.json'
DB_PATH = "data/econzone.sqlite"

# --- Thiết lập Logging ---
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def migrate():
    """
    Đọc dữ liệu từ các file JSON và ghi vào CSDL SQLite.
    Hàm này được thiết kế để chạy một lần.
    """
    logging.info("Bắt đầu quá trình di chuyển dữ liệu từ JSON sang SQLite...")

    if not os.path.exists(JSON_ECONOMY_FILE) or not os.path.exists(JSON_ITEMS_FILE):
        logging.error("Lỗi: Không tìm thấy file economy.json hoặc items.json. Vui lòng đặt các file này ở thư mục gốc.")
        return

    # Đảm bảo thư mục 'data' tồn tại
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Tạo các bảng trong CSDL (lấy từ Bước 1)
    try:
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                bank_balance INTEGER DEFAULT 0,
                wanted_level REAL DEFAULT 0.0,
                level_global INTEGER DEFAULT 1,
                xp_global INTEGER DEFAULT 0,
                last_active_guild_id INTEGER
            );
            CREATE TABLE IF NOT EXISTS user_guild_data (
                user_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                local_balance_earned INTEGER DEFAULT 0,
                local_balance_adadd INTEGER DEFAULT 0,
                level_local INTEGER DEFAULT 1,
                xp_local INTEGER DEFAULT 0,
                health INTEGER DEFAULT 100,
                hunger INTEGER DEFAULT 100,
                energy INTEGER DEFAULT 100,
                PRIMARY KEY (user_id, guild_id),
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            );
            CREATE TABLE IF NOT EXISTS items (
                item_id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                price INTEGER,
                sell_price INTEGER,
                type TEXT,
                effect_stat TEXT,
                effect_value INTEGER,
                capacity INTEGER
            );
            CREATE TABLE IF NOT EXISTS inventories (
                inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                item_id TEXT NOT NULL,
                location TEXT NOT NULL,
                guild_id INTEGER,
                is_tainted BOOLEAN DEFAULT 0,
                is_foreign BOOLEAN DEFAULT 0,
                quantity INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (item_id) REFERENCES items (item_id)
            );
        """)
        logging.info("Đã kiểm tra/tạo các bảng trong SQLite.")
    except Exception as e:
        logging.error(f"Lỗi khi tạo bảng: {e}", exc_info=True)
        conn.close()
        return

    # 2. Di chuyển dữ liệu từ items.json
    try:
        with open(JSON_ITEMS_FILE, 'r', encoding='utf-8') as f:
            items_data = json.load(f)
        
        all_items = {}
        all_items.update(items_data.get("shop_items", {}))
        all_items.update(items_data.get("utility_items", {}))
        
        for item_id, details in all_items.items():
            effect = details.get('effect', {})
            cursor.execute("""
                INSERT OR REPLACE INTO items 
                (item_id, name, description, price, sell_price, type, effect_stat, effect_value, capacity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item_id,
                details.get('name'), details.get('description'),
                details.get('price'), details.get('sell_price'),
                details.get('type'), effect.get('stat'), effect.get('value'),
                details.get('capacity')
            ))
        conn.commit()
        logging.info(f"Hoàn tất di chuyển {len(all_items)} vật phẩm từ {JSON_ITEMS_FILE}.")
    except Exception as e:
        logging.error(f"Lỗi khi di chuyển items.json: {e}", exc_info=True)
        conn.close()
        return

    # 3. Di chuyển dữ liệu từ economy.json
    try:
        with open(JSON_ECONOMY_FILE, 'r', encoding='utf-8') as f:
            eco_data = json.load(f)

        users = eco_data.get('users', {})
        for user_id_str, profile in users.items():
            if not user_id_str.isdigit(): continue # Bỏ qua các user mẫu
            user_id = int(user_id_str)
            
            # Chèn hoặc cập nhật profile global
            cursor.execute("""
                INSERT OR REPLACE INTO users (user_id, bank_balance, wanted_level, level_global, xp_global, last_active_guild_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                profile.get('global_balance', profile.get('bank_balance', 0)), # Hỗ trợ key cũ
                profile.get('wanted_level', 0.0),
                profile.get('level_global', 1),
                profile.get('xp_global', 0),
                profile.get('last_active_guild_id')
            ))

            # Xử lý túi đồ global
            for item in profile.get('inventory_global', []):
                item_id = item if isinstance(item, str) else item.get('item_id')
                cursor.execute("""
                    INSERT INTO inventories (user_id, item_id, location, is_tainted, is_foreign, quantity)
                    VALUES (?, ?, 'global', ?, ?, 1)
                """, (user_id, item_id, item.get('is_tainted', 0) if isinstance(item, dict) else 0, 0))

            # Xử lý dữ liệu local từng server
            for guild_id_str, local_data in profile.get('server_data', {}).items():
                if not guild_id_str.isdigit(): continue # Bỏ qua guild mẫu
                guild_id = int(guild_id_str)
                balance = local_data.get('local_balance', {})
                stats = local_data.get('survival_stats', {})
                
                cursor.execute("""
                    INSERT OR REPLACE INTO user_guild_data 
                    (user_id, guild_id, local_balance_earned, local_balance_adadd, level_local, xp_local, health, hunger, energy)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id, guild_id, 
                    balance.get('earned', 0), balance.get('adadd', 0),
                    local_data.get('level_local', 1), local_data.get('xp_local', 0),
                    stats.get('health', 100), stats.get('hunger', 100), stats.get('energy', 100)
                ))

                # Xử lý túi đồ local
                for item in local_data.get('inventory_local', []):
                    item_id = item if isinstance(item, str) else item.get('item_id')
                    cursor.execute("""
                        INSERT INTO inventories (user_id, item_id, location, guild_id, is_tainted, is_foreign, quantity)
                        VALUES (?, ?, 'local', ?, ?, ?, 1)
                    """, (user_id, item_id, guild_id, item.get('is_tainted', 0) if isinstance(item, dict) else 0, item.get('is_foreign', 0) if isinstance(item, dict) else 0))

        conn.commit()
        logging.info(f"Hoàn tất di chuyển dữ liệu cho {len(users)} người dùng từ {JSON_ECONOMY_FILE}.")
    except Exception as e:
        logging.error(f"Lỗi khi di chuyển economy.json: {e}", exc_info=True)
    
    finally:
        conn.close()

    logging.info("====== QUÁ TRÌNH DI CHUYỂN HOÀN TẤT ======")


if __name__ == "__main__":
    # Bạn có thể chạy file này trực tiếp từ terminal để bắt đầu di chuyển
    migrate()
