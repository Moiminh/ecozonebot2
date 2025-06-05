# bot/core/config.py

# --- Bot Configuration ---
COMMAND_PREFIX = '!'               # <<< ĐẢM BẢO DÒNG NÀY TỒN TẠI VÀ ĐÚNG
ECONOMY_FILE = 'economy.json' 
MODERATORS_FILE = 'moderators.json'
CURRENCY_SYMBOL = "💰" 

# --- Cooldowns (seconds) ---
WORK_COOLDOWN = 3600
BEG_COOLDOWN = 300
DAILY_COOLDOWN = 86400
ROB_COOLDOWN = 7200
CRIME_COOLDOWN = 1800
FISH_COOLDOWN = 600
SLOTS_COOLDOWN = 5
CF_COOLDOWN = 5
DICE_COOLDOWN = 5

# --- Other Configurations ---
ROB_SUCCESS_RATE = 0.50
ROB_FINE_RATE = 0.25
CRIME_SUCCESS_RATE = 0.60
SLOTS_EMOJIS = ["🍒", "🍊", "🍋", "🔔", "⭐", "💎"]
FISH_CATCHES = {
    "🐠": 50, "🐟": 75, "🐡": 100, "🦑": 150, "🦐": 30, "🦀": 60,
    "👢": 5, "🔩": 1, "🪵": 10
}

# --- Shop ---
SHOP_ITEMS = {
    "laptop": {"price": 1000, "description": "Một chiếc laptop đa năng.", "type": "item", "sell_price": 500},
    "gold_watch": {"price": 5000, "description": "Thể hiện đẳng cấp và sự giàu có!", "type": "item", "sell_price": 2500},
    "fishing_rod": {"price": 500, "description": "Cần câu tốt để tăng cơ hội bắt được cá xịn.", "type": "item", "sell_price": 200},
}

# --- Bare Command Mapping ---
# Ánh xạ các lệnh không cần prefix (lệnh tắt) tới tên lệnh gốc
BARE_COMMAND_MAP = { # <<< ĐẢM BẢO BIẾN NÀY CŨNG ĐƯỢC ĐỊNH NGHĨA ĐÚNG
    # Tài Khoản & Tổng Quan
    "balance": "balance",
    "bal": "balance",
    "bank": "bank",
    "deposit": "deposit",
    "dep": "deposit",
    "withdraw": "withdraw",
    "wd": "withdraw",
    "transfer": "transfer",
    "tf": "transfer",
    "leaderboard": "leaderboard",
    "lb": "leaderboard",
    "richest": "richest",
    "rich": "richest",
    "inventory": "inventory",
    "inv": "inventory",

    # Kiếm Tiền & Cơ Hội
    "work": "work",
    "w": "work",
    "daily": "daily",
    "beg": "beg",
    "crime": "crime",
    "fish": "fish",
    "rob": "rob",

    # Giải Trí & Cờ Bạc
    "slots": "slots",
    "sl": "slots",
    "coinflip": "coinflip",
    "cf": "coinflip",
    "dice": "dice",
    "roll": "dice", # Giữ lại "roll" nếu bạn muốn nó cũng là lệnh tắt cho dice

    # Cửa Hàng Vật Phẩm
    "shop": "shop",
    "store": "shop", # Giữ lại "store" nếu bạn muốn nó cũng là lệnh tắt cho shop
    "buy": "buy",
    "sell": "sell",
}
