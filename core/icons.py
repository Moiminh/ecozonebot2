# bot/core/icons.py

# Icon cho các thông báo chung
ICON_SUCCESS = "✅"
ICON_ERROR = "❌"
ICON_WARNING = "⚠️"
ICON_INFO = "ℹ️"
ICON_QUESTION = "❓"
ICON_LOADING = "⏳" # Hoặc một emoji loading động nếu bạn biết ID

# Icon cho các lệnh hoặc mục cụ thể
ICON_MONEY_BAG = "💰" # Có thể dùng thay thế hoặc cùng với CURRENCY_SYMBOL
ICON_BANK = "🏦"
ICON_SHOP = "🏪"
ICON_INVENTORY = "🎒"
ICON_LEADERBOARD = "🏆"
ICON_PROFILE = "👤"
ICON_SETTINGS = "⚙️"

# Icon cho các hành động
ICON_WORK = "🔨"
ICON_FISH = "🐟"
ICON_CRIME = "🔫" # Cẩn thận khi dùng các icon nhạy cảm
ICON_ROB = "🥷"
ICON_SLOTS = "🎰"
ICON_COINFLIP_HEADS = "🪙" # Mặt ngửa của đồng xu
ICON_COINFLIP_TAILS = "🔘" # Mặt sấp (ví dụ)
ICON_DICE = "🎲"
ICON_GIFT = "🎁" # Cho daily, transfer

# Icon cho các vật phẩm (ví dụ)
ICON_LAPTOP = "💻"
ICON_GOLD_WATCH = "⌚"
ICON_FISHING_ROD = "🎣" # Trùng với ICON_FISH, có thể tạo sự khác biệt nếu muốn

# Bạn có thể thêm bất kỳ icon nào bạn muốn ở đây
# Nếu bạn muốn dùng custom emoji của server, cú pháp sẽ là:
# ICON_CUSTOM_HAPPY = "<:tên_emoji_custom:ID_của_emoji>"
# Ví dụ: ICON_MY_SERVER_LOGO = "<:myserverlogo:123456789012345678>"
# Để lấy ID, trong Discord gõ \:tên_emoji_custom: nó sẽ hiện ra dạng trên.
# Lưu ý: Bot phải ở trong server có emoji đó thì mới hiển thị được.
