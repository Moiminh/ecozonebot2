# bot/core/config.py

# --- Bot Configuration ---
COMMAND_PREFIX = '!'
ECONOMY_FILE = 'economy.json' 
MODERATORS_FILE = 'moderators.json'

# --- Currency & Item Icons (NEW) ---
# Sẽ được dùng trong các file cogs/ sau này để hiển thị cho người dùng
ICON_ECOIN = "🪙"      # Tiền Sạch (earned)
ICON_ECOBIT = "🧪"      # Tiền Lậu (adadd)
ICON_BANK_MAIN = "🏦" # Bank trung tâm
ICON_ECOBANK = "🏦"     # Visa Nội địa
ICON_ECOVISA = "💳"     # Visa Quốc tế
ICON_TICKET = "🎟️"

# --- Economy & Game Balance ---
DEPOSIT_FEE_PERCENTAGE = 0.05  # 5% phí khi gửi Ecoin vào Bank trung tâm
UPGRADE_VISA_COST = 20000      # Phí nâng cấp từ Ecobank lên Ecovisa, trả bằng tiền Bank

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

# --- Tainted Item & Laundering Rules ---
TAINTED_ITEM_SELL_LIMIT = 2     # Chỉ được bán 2 vật phẩm bẩn mỗi ngày
TAINTED_ITEM_SELL_RATE = 0.2    # Đồ bẩn bán lại chỉ được 20% giá trị gốc
TAINTED_ITEM_TAX_RATE = 0.4     # Chịu thêm 40% thuế trên giá đã giảm
LAUNDER_EXCHANGE_RATE = 100_000_000 # 100 triệu Ecobit = 1 Bank

# --- Game Specifics ---
CRIME_SUCCESS_RATE = 0.60
ROB_SUCCESS_RATE = 0.50
ROB_FINE_RATE = 0.25
SLOTS_EMOJIS = ["🍒", "🍊", "🍋", "🔔", "⭐", "💎"]
FISH_CATCHES = {
    "🐠": 50, "🐟": 75, "🐡": 100, "🦑": 150, "🦐": 30, "🦀": 60,
    "👢": 5, "🔩": 1, "🪵": 10
}

# --- Định nghĩa Vật phẩm Shop ---
# Các vật phẩm thông thường, giá bằng Ecoin/Ecobit
SHOP_ITEMS = {
    "laptop": {"price": 1000, "description": "Một chiếc laptop đa năng.", "sell_price": 500},
    "fishing_rod": {"price": 500, "description": "Cần câu tốt hơn.", "sell_price": 200},
}

# Các vật phẩm đặc biệt (Visa, Balo), giá bằng tiền Bank trung tâm
UTILITY_ITEMS = {
    "ecobank_small": {
        "price": 1000, "name": "Ecobank Card (Nhỏ)", "description": "Thẻ thanh toán nội địa cỡ nhỏ.", 
        "type": "visa", "visa_type": "local", "capacity": 10000
    },
    "ecobank_medium": {
        "price": 5000, "name": "Ecobank Card (Vừa)", "description": "Thẻ thanh toán nội địa cỡ vừa.",
        "type": "visa", "visa_type": "local", "capacity": 50000
    },
    "ecovisa_standard": {
        "price": 25000, "name": "Ecovisa Card (Tiêu chuẩn)", "description": "Thẻ thanh toán quốc tế tiêu chuẩn.",
        "type": "visa", "visa_type": "international", "capacity": 100000
    },
    "backpack_small": {
        "price": 50000, "name": "Balo Du lịch (Nhỏ)", "description": "Balo du lịch nhỏ, mang được 1 vật phẩm.",
        "type": "backpack", "capacity": 1
    }
}

# --- Bare Command Mapping ---
# Ánh xạ các lệnh không cần prefix (lệnh tắt) tới tên lệnh gốc
BARE_COMMAND_MAP = {
    # Tài Khoản & Tổng Quan
    "balance": "balance", "bal": "balance",
    "bank": "bank", # Sẽ cần được định nghĩa lại hoặc loại bỏ
    "deposit": "deposit", "dep": "deposit",
    "withdraw": "withdraw", "wd": "withdraw", # Sẽ được thay bằng !visa withdraw
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
}
