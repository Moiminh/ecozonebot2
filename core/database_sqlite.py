# bot/core/database_sqlite.py
import sqlite3
import logging
import os

logger = logging.getLogger(__name__)
DB_PATH = "data/econzone.sqlite"

def get_db_connection():
    """Tạo và trả về một kết nối tới CSDL.
    Sử dụng sqlite3.Row để có thể truy cập các cột bằng tên."""
    # Đảm bảo thư mục 'data' tồn tại
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database():
    """
    Tạo tất cả các bảng cần thiết nếu chúng chưa tồn tại.
    Hàm này nên được gọi một lần khi bot khởi động ở chế độ SQLite.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Dán toàn bộ mã SQL CREATE TABLE từ Bước 1 vào đây
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
    
    conn.commit()
    conn.close()
    logger.info("CSDL SQLite đã được kiểm tra và khởi tạo (nếu cần).")

def get_or_create_global_user_profile(user_id: int) -> sqlite3.Row:
    """
    Lấy profile global của người dùng từ CSDL.
    Nếu không tồn tại, tự động tạo một profile mới với giá trị mặc định.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Dùng INSERT OR IGNORE để tránh lỗi nếu user_id đã tồn tại.
    # Lệnh này sẽ không làm gì nếu user_id đã có trong bảng.
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    
    # Sau đó, chắc chắn lấy dữ liệu của người dùng
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user_profile = cursor.fetchone()
    
    conn.commit()
    conn.close()
    
    return user_profile

def get_or_create_user_local_data(user_id: int, guild_id: int) -> sqlite3.Row:
    """
    Lấy dữ liệu local của người dùng tại một server.
    Nếu không tồn tại, tự động tạo mới.
    """
    # Đầu tiên, đảm bảo profile global tồn tại
    get_or_create_global_user_profile(user_id)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tương tự, dùng INSERT OR IGNORE cho dữ liệu local
    cursor.execute("INSERT OR IGNORE INTO user_guild_data (user_id, guild_id) VALUES (?, ?)", (user_id, guild_id))
    
    # Lấy dữ liệu local
    cursor.execute("SELECT * FROM user_guild_data WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))
    local_data = cursor.fetchone()
    
    conn.commit()
    conn.close()
    
    return local_data

def update_balance(user_id: int, guild_id: int, balance_type: str, new_value: int):
    """
    Cập nhật số dư cho người dùng.
    balance_type có thể là: 'bank_balance', 'local_balance_earned', 'local_balance_adadd'
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if balance_type == 'bank_balance':
        cursor.execute("UPDATE users SET bank_balance = ? WHERE user_id = ?", (new_value, user_id))
    elif balance_type in ['local_balance_earned', 'local_balance_adadd']:
        # Cần tên cột trong CSDL, không phải key trong JSON
        column_name = balance_type 
        cursor.execute(f"UPDATE user_guild_data SET {column_name} = ? WHERE user_id = ? AND guild_id = ?", (new_value, user_id, guild_id))
    else:
        logger.error(f"Loại balance không hợp lệ: {balance_type}")
        
    conn.commit()
    conn.close()

# ... Chúng ta sẽ thêm các hàm khác như quản lý inventory, cooldowns ở các bước sau ...
