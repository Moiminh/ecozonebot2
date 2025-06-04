# bot/core/config.py
# from datetime import timedelta # Hiện tại không dùng timedelta trực tiếp ở đây

# --- Bot Configuration ---
# BOT_TOKEN hiện được quản lý thông qua file .env và được load trong main.py.
# Chúng ta không cần định nghĩa BOT_TOKEN ở đây nữa.
# Nếu muốn, bạn có thể xóa hoàn toàn dòng BOT_TOKEN = None đã có trước đó.

COMMAND_PREFIX = '!'
ECONOMY_FILE = 'economy.json' # Đường dẫn tương đối tới file economy.json
CURRENCY_SYMBOL = "💰" # Giữ lại đây vì nó là cấu hình cốt lõi của hệ thống kinh tế

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
BARE_COMMAND_MAP = {
    "slots": "slots", "sl": "slots",
    "dep": "deposit",
    "cf": "coinflip",
    "bal": "balance", "$": "balance", "cash": "balance", "money": "balance",
    "work": "work", "w": "work",
    "daily": "daily", "d": "daily",
    "inv": "inventory", "items": "inventory", "i": "inventory",
    "lb": "leaderboard", "top": "leaderboard",
    "richest": "richest",
    "beg": "beg", "b": "beg",
    "wd": "withdraw",
    "rob": "rob", "steal": "rob",
    "crime": "crime",
    "fish": "fish",
    "shop": "shop", "store": "shop",
    "bank": "bank",
    "buy": "buy",         # Đã thêm ở các bước trước
    "sell": "sell",       # Đã thêm ở các bước trước
    "give": "transfer",   # Đã thêm ở các bước trước
    "pay": "transfer"     # Đã thêm ở các bước trước
}
