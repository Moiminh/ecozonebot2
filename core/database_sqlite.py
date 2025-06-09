# bot/core/database_sqlite.py
import sqlite3
import logging
import os
import json # Cần để load item definitions

logger = logging.getLogger(__name__)
DB_PATH = "data/econzone.sqlite"

# --- KẾT NỐI VÀ KHỞI TẠO ---

def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, bank_balance INTEGER DEFAULT 0, wanted_level REAL DEFAULT 0.0,
            level_global INTEGER DEFAULT 1, xp_global INTEGER DEFAULT 0, last_active_guild_id INTEGER
        );
        CREATE TABLE IF NOT EXISTS user_guild_data (
            user_id INTEGER NOT NULL, guild_id INTEGER NOT NULL, local_balance_earned INTEGER DEFAULT 0,
            local_balance_adadd INTEGER DEFAULT 0, level_local INTEGER DEFAULT 1, xp_local INTEGER DEFAULT 0,
            health INTEGER DEFAULT 100, hunger INTEGER DEFAULT 100, energy INTEGER DEFAULT 100,
            PRIMARY KEY (user_id, guild_id), FOREIGN KEY (user_id) REFERENCES users (user_id)
        );
        CREATE TABLE IF NOT EXISTS items (
            item_id TEXT PRIMARY KEY, name TEXT, description TEXT, price INTEGER, sell_price INTEGER, type TEXT,
            effect_stat TEXT, effect_value INTEGER, capacity INTEGER
        );
        CREATE TABLE IF NOT EXISTS inventories (
            inventory_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, item_id TEXT NOT NULL,
            location TEXT NOT NULL, guild_id INTEGER, is_tainted BOOLEAN DEFAULT 0, is_foreign BOOLEAN DEFAULT 0,
            quantity INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (user_id), FOREIGN KEY (item_id) REFERENCES items (item_id)
        );
        CREATE TABLE IF NOT EXISTS cooldowns (key TEXT PRIMARY KEY, value REAL);
        CREATE TABLE IF NOT EXISTS guild_configs (
            guild_id INTEGER PRIMARY KEY, bare_command_active_channels TEXT DEFAULT '[]', muted_channels TEXT DEFAULT '[]'
        );
    """)
    conn.commit()
    conn.close()
    logger.info("CSDL SQLite đã được kiểm tra và khởi tạo (nếu cần).")

# --- HÀM TẢI DỮ LIỆU ---

def load_item_definitions(file_path: str = 'items.json') -> Dict[str, Any]:
    # Hàm này không đổi, vẫn đọc từ file JSON
    try:
        if not os.path.exists(file_path): return {}
        with open(file_path, 'r', encoding='utf-8') as f:
            item_data = json.load(f)
        all_items = {}
        all_items.update(item_data.get("shop_items", {}))
        all_items.update(item_data.get("utility_items", {}))
        return all_items
    except Exception as e:
        logger.error(f"Lỗi khi tải file định nghĩa vật phẩm '{file_path}': {e}", exc_info=True)
        return {}

# --- QUẢN LÝ USER & GUILD ---

def get_or_create_global_user_profile(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user_profile = cursor.fetchone()
    conn.commit()
    conn.close()
    return user_profile

def get_or_create_user_local_data(user_id: int, guild_id: int):
    get_or_create_global_user_profile(user_id)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO user_guild_data (user_id, guild_id) VALUES (?, ?)", (user_id, guild_id))
    cursor.execute("SELECT * FROM user_guild_data WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))
    local_data = cursor.fetchone()
    conn.commit()
    conn.close()
    return local_data

def get_or_create_guild_config(guild_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO guild_configs (guild_id) VALUES (?)", (guild_id,))
    cursor.execute("SELECT * FROM guild_configs WHERE guild_id = ?", (guild_id,))
    config = cursor.fetchone()
    conn.commit()
    conn.close()
    return config

# --- CẬP NHẬT DỮ LIỆU ---

def update_balance(user_id: int, guild_id: int, balance_type: str, new_value: int):
    conn = get_db_connection()
    if balance_type == 'bank_balance':
        conn.execute("UPDATE users SET bank_balance = ? WHERE user_id = ?", (new_value, user_id))
    elif balance_type in ['local_balance_earned', 'local_balance_adadd']:
        conn.execute(f"UPDATE user_guild_data SET {balance_type} = ? WHERE user_id = ? AND guild_id = ?", (new_value, user_id, guild_id))
    conn.commit()
    conn.close()

def update_user_stats(user_id: int, guild_id: int, health: int = None, hunger: int = None, energy: int = None):
    conn = get_db_connection()
    if health is not None:
        conn.execute("UPDATE user_guild_data SET health = ? WHERE user_id = ? AND guild_id = ?", (health, user_id, guild_id))
    if hunger is not None:
        conn.execute("UPDATE user_guild_data SET hunger = ? WHERE user_id = ? AND guild_id = ?", (hunger, user_id, guild_id))
    if energy is not None:
        conn.execute("UPDATE user_guild_data SET energy = ? WHERE user_id = ? AND guild_id = ?", (energy, user_id, guild_id))
    conn.commit()
    conn.close()

def update_xp(user_id: int, guild_id: int, xp_local: int, xp_global: int):
    conn = get_db_connection()
    conn.execute("UPDATE users SET xp_global = xp_global + ? WHERE user_id = ?", (xp_global, user_id))
    conn.execute("UPDATE user_guild_data SET xp_local = xp_local + ? WHERE user_id = ? AND guild_id = ?", (xp_local, user_id, guild_id))
    conn.commit()
    conn.close()

# --- QUẢN LÝ COOLDOWN ---

def get_cooldown(user_id: int, command: str) -> float:
    conn = get_db_connection()
    key = f"{user_id}_{command}"
    result = conn.execute("SELECT value FROM cooldowns WHERE key = ?", (key,)).fetchone()
    conn.close()
    return result['value'] if result else 0

def set_cooldown(user_id: int, command: str, timestamp: float):
    conn = get_db_connection()
    key = f"{user_id}_{command}"
    conn.execute("INSERT OR REPLACE INTO cooldowns (key, value) VALUES (?, ?)", (key, timestamp))
    conn.commit()
    conn.close()

# --- QUẢN LÝ INVENTORY ---

def get_inventory(user_id: int, guild_id: int = None, location: str = None):
    """Lấy túi đồ của user. Nếu location là 'local' cần guild_id."""
    conn = get_db_connection()
    if location:
        if location == 'local':
            return conn.execute("SELECT * FROM inventories WHERE user_id = ? AND location = 'local' AND guild_id = ?", (user_id, guild_id)).fetchall()
        else: # global
            return conn.execute("SELECT * FROM inventories WHERE user_id = ? AND location = 'global'", (user_id,)).fetchall()
    else: # Lấy tất cả
        return conn.execute("SELECT * FROM inventories WHERE user_id = ?", (user_id,)).fetchall()


def add_item_to_inventory(user_id: int, item_id: str, quantity: int, location: str, guild_id: int = None, is_tainted: bool = False):
    conn = get_db_connection()
    for _ in range(quantity):
        conn.execute("""
            INSERT INTO inventories (user_id, item_id, location, guild_id, is_tainted)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, item_id, location, guild_id, is_tainted))
    conn.commit()
    conn.close()

def remove_item_from_inventory(user_id: int, item_id: str, quantity: int, location: str, guild_id: int = None, is_tainted: bool = None):
    """Xóa vật phẩm. Ưu tiên xóa theo is_tainted nếu được cung cấp."""
    conn = get_db_connection()
    query = "DELETE FROM inventories WHERE inventory_id IN (SELECT inventory_id FROM inventories WHERE user_id = ? AND item_id = ? AND location = ?"
    params = [user_id, item_id, location]
    
    if location == 'local':
        query += " AND guild_id = ?"
        params.append(guild_id)
    if is_tainted is not None:
        query += " AND is_tainted = ?"
        params.append(is_tainted)
        
    query += " LIMIT ?)"
    params.append(quantity)
    
    conn.execute(query, tuple(params))
    conn.commit()
    conn.close()
