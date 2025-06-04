# bot/cogs/shop/buy_cmd.py
import nextcord
from nextcord.ext import commands

# Import các thành phần cần thiết từ package 'core'
from core.database import get_user_data, save_data
from core.utils import try_send
from core.config import CURRENCY_SYMBOL, SHOP_ITEMS, COMMAND_PREFIX
from core.icons import ICON_SUCCESS, ICON_ERROR, ICON_WARNING, ICON_MONEY_BAG # Đảm bảo các icon này có trong core/icons.py

class BuyCommandCog(commands.Cog, name="Buy Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='buy')
    async def buy(self, ctx: commands.Context, item_name: str, quantity: int = 1):
        """Mua một hoặc nhiều vật phẩm từ cửa hàng. Nếu không nhập số lượng, mặc định là 1.
        Ví dụ: !buy laptop
               !buy laptop 2
               !buy "gold watch"
        """
        if quantity <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Số lượng mua phải lớn hơn 0.")
            return

        # Xử lý trường hợp người dùng có thể nhập sai thứ tự (ví dụ `buy 2 laptop`)
        # khi họ đang dùng lệnh prefix và quantity lại là giá trị mặc định.
        # Nếu lệnh tắt, on_message đã chuẩn hóa thành `!buy <arg1> <arg2...>`
        # nên `item_name` sẽ chứa toàn bộ phần sau `!buy`.
        
        # Chúng ta sẽ thử tách item_name và quantity nếu người dùng nhập theo kiểu "tên_item số_lượng"
        # hoặc "số_lượng tên_item" (chỉ khi quantity gốc là 1).
