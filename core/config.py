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
ICON_SURVIVAL = "❤️‍🩹"
# --- Economy & Game Balance ---
DEPOSIT_FEE_PERCENTAGE = 0.05  # 5% phí khi gửi Ecoin vào Bank trung tâm
UPGRADE_VISA_COST = 20000      # Phí nâng cấp từ Ecobank lên Ecovisa, trả bằng tiền Bank

# --- Cooldowns (seconds) ---
WORK_COOLDOWN = 3600
DAILY_COOLDOWN = 86400
CRIME_COOLDOWN = 1800
BEG_COOLDOWN = 300
FISH_COOLDOWN = 600
# bot/core/config.py

# --- Bot Configuration ---
COMMAND_PREFIX = '!'
ECONOMY_FILE = 'economy.json' 
MODERATORS_FILE = 'moderators.json'
# [CẢI TIẾN] Thêm đường dẫn file item
ITEMS_FILE = 'items.json'

# --- Currency & Item Icons (NEW) ---
# Sẽ được dùng trong các file cogs/ sau này để hiển thị cho người dùng
ICON_ECOIN = "🪙"      # Tiền Sạch (earned)
ICON_ECOBIT = "🧪"      # Tiền Lậu (adadd)
ICON_BANK_MAIN = "🏦" # Bank trung tâm
ICON_ECOBANK = "🏦"     # Visa Nội địa
ICON_ECOVISA = "💳"     # Visa Quốc tế
ICON_TICKET = "🎟️"
ICON_SURVIVAL = "❤️‍🩹"
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
FOREIGN_ITEM_SELL_PENALTY = 0.5 # Vật phẩm ngoại lai bán lại bị giảm 50% 
# --- Game Specifics ---
CRIME_SUCCESS_RATE = 0.60
ROB_SUCCESS_RATE = 0.50
ROB_FINE_RATE = 0.25
SLOTS_EMOJIS = ["🍒", "🍊", "🍋", "🔔", "⭐", "💎"]
FISH_CATCHES = {
    "🐠": 50, "🐟": 75, "🐡": 100, "🦑": 150, "🦐": 30, "🦀": 60,
    "👢": 5, "🔩": 1, "🪵": 10
}

# [CẢI TIẾN] Xóa bỏ định nghĩa SHOP_ITEMS và UTILITY_ITEMS ở đây
# Chúng đã được chuyển vào items.json

# --- Survival Stats Costs (NEW) ---
WORK_ENERGY_COST = 10
WORK_HUNGER_COST = 5

CRIME_ENERGY_COST = 8
CRIME_HUNGER_COST = 4

ROB_ENERGY_COST = 12
ROB_HUNGER_COST = 6

FISH_ENERGY_COST = 5
FISH_HUNGER_COST = 3


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
