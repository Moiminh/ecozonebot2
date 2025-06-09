# bot/core/config.py

# --- Bot Configuration ---
COMMAND_PREFIX = '!'
ECONOMY_FILE = 'economy.json'
MODERATORS_FILE = 'moderators.json'
ITEMS_FILE = 'items.json'

# --- Cooldowns (seconds) ---
WORK_COOLDOWN = 3600
DAILY_COOLDOWN = 86400
CRIME_COOLDOWN = 1800
BEG_COOLDOWN = 300
FISH_COOLDOWN = 600
ROB_COOLDOWN = 7200
SLOTS_COOLDOWN = 5
CF_COOLDOWN = 5
DICE_COOLDOWN = 5

# --- Economy & Game Balance ---
DEPOSIT_FEE_PERCENTAGE = 0.05
UPGRADE_VISA_COST = 20000
TAINTED_ITEM_SELL_LIMIT = 2
TAINTED_ITEM_SELL_RATE = 0.2
TAINTED_ITEM_TAX_RATE = 0.4
LAUNDER_EXCHANGE_rate = 100_000_000
FOREIGN_ITEM_SELL_PENALTY = 0.5
CRIME_SUCCESS_RATE = 0.60
ROB_SUCCESS_RATE = 0.50
ROB_FINE_RATE = 0.25
BASE_CATCH_CHANCE = 0.1
WANTED_LEVEL_CATCH_MULTIPLIER = 0.05

# [THÊM] Các biến còn thiếu cho hệ thống Wanted Level và Danh hiệu
MODERATOR_USER_IDS = [] # Thêm ID của các super-moderator vào đây nếu cần
WANTED_LEVEL_CRIMINAL_THRESHOLD = 5.0 # Mức wanted_level để bị coi là Tội phạm

# Danh hiệu cho người chơi thường (key là level yêu cầu)
CITIZEN_TITLES = {
    0: "Công Dân",
    10: "Người Có Tiếng Tăm",
    25: "Nhân Vật Ưu Tú",
    50: "Huyền Thoại Server"
}

# Danh hiệu cho tội phạm (key là level yêu cầu)
CRIMINAL_TITLES = {
    0: "Tội Phạm Vặt",
    10: "Kẻ Ngoài Vòng Pháp Luật",
    25: "Trùm Tội Phạm",
    50: "Bố Già"
}


# --- Survival Stats Costs ---
WORK_ENERGY_COST = 10
WORK_HUNGER_COST = 5
CRIME_ENERGY_COST = 8
CRIME_HUNGER_COST = 4
ROB_ENERGY_COST = 12
ROB_HUNGER_COST = 6
FISH_ENERGY_COST = 5
FISH_HUNGER_COST = 3

# --- Game Specifics ---
SLOTS_EMOJIS = ["🍒", "🍊", "🍋", "🔔", "⭐", "💎"]
FISH_CATCHES = {
    "🐠": 50, "🐟": 75, "🐡": 100, "🦑": 150, "🦐": 30, "🦀": 60,
    "👢": 5, "🔩": 1, "🪵": 10
}

# --- Bare Command Mapping ---
BARE_COMMAND_MAP = {
    # Tài Khoản & Tổng Quan
    "balance": "balance", "bal": "balance",
    "bank": "bank",
    "deposit": "deposit", "dep": "deposit",
    "withdraw": "withdraw", "wd": "withdraw",
    "transfer": "transfer", "tf": "transfer",
    "leaderboard": "leaderboard", "lb": "leaderboard",
    "inventory": "inventory", "inv": "inventory",
    "visa": "visa",

    # Kiếm Tiền & Cơ Hội
    "work": "work", "w": "work",
    "daily": "daily",

    "beg": "beg",
    "crime": "crime",
    "fish": "fish",
    "rob": "rob",

    # Giải Trí & Cờ Bạc
    "slots": "slots", "sl": "slots",
    "coinflip": "coinflip", "cf": "coinflip",
    "dice": "dice", "roll": "dice",

    # Cửa Hàng Vật Phẩm
    "shop": "shop", "store": "shop",
    "buy": "buy",
    "sell": "sell",
    "use": "use"
}
