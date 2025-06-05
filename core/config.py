# Trong file bot/core/config.py
BARE_COMMAND_MAP = {
    # Tài Khoản & Tổng Quan
    "balance": "balance", "bal": "balance",
    "bank": "bank",
    "deposit": "deposit", "dep": "deposit",
    "withdraw": "withdraw", "wd": "withdraw",
    "transfer": "transfer", "tf": "transfer",
    "leaderboard": "leaderboard", "lb": "leaderboard",
    "richest": "richest", "rich": "richest",
    "inventory": "inventory", "inv": "inventory",

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
    "dice": "dice", # Bạn đã thêm "roll": "dice" và "dice": "dice" ở bước trước, bạn có thể giữ cả hai nếu muốn "roll" cũng là lệnh tắt

    # Cửa Hàng Vật Phẩm
    "shop": "shop", 
    "buy": "buy",
    "sell": "sell",
}
