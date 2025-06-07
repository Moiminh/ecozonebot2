# bot/core/config.py

# --- Bot Configuration ---
COMMAND_PREFIX = '!'
ECONOMY_FILE = 'economy.json' 
MODERATORS_FILE = 'moderators.json'

# --- Currency & Item Icons (NEW) ---
# Sẽ được dùng trong các file cogs/ sau này
ICON_ECOIN = "🪙"
ICON_ECOBIT = "🧪"
ICON_ECOBANK = "🏦" # Visa nội địa
ICON_ECOVISA = "💳" # Visa quốc tế
ICON_TICKET = "🎟️"

# --- Economy & Game Balance ---
DEPOSIT_FEE_PERCENTAGE = 0.05  # 5% phí khi gửi Ecoin vào Bank
WORK_COOLDOWN = 3600
DAILY_COOLDOWN = 86400
# ... (các cooldown khác) ...

# --- Tainted Item & Laundering Rules ---
TAINTED_ITEM_SELL_LIMIT = 2     # Chỉ được bán 2 vật phẩm bẩn mỗi ngày
TAINTED_ITEM_SELL_RATE = 0.2    # Đồ bẩn bán lại chỉ được 20% giá gốc
TAINTED_ITEM_TAX_RATE = 0.4     # Chịu thêm 40% thuế trên giá đã giảm
LAUNDER_EXCHANGE_RATE = 100_000_000 # 100 triệu Ecobit = 1 Bank

# --- Định nghĩa Vật phẩm Shop ---
# Các vật phẩm thông thường, giá bằng Ecoin/Ecobit
SHOP_ITEMS = {
    "laptop": {"price": 1000, "description": "Một chiếc laptop đa năng.", "sell_price": 500},
    "fishing_rod": {"price": 500, "description": "Cần câu tốt hơn.", "sell_price": 200},
    # ... các vật phẩm khác ...
}

# Các vật phẩm đặc biệt (Visa, Balo), giá bằng tiền Bank
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
