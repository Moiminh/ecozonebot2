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

        
        
        parts = item_name.split()
        processed_item_name = item_name # Giả định ban đầu
        parsed_quantity = quantity      # Giữ quantity được truyền vào hoặc mặc định


        if quantity == 1 and len(parts) > 1: # Nếu quantity là mặc định và item_name có nhiều hơn 1 từ
            try:
                # Thử xem từ đầu tiên của item_name có phải là số không
                first_word_as_int = int(parts[0])
                # Nếu thành công, có thể người dùng đã nhập `!buy <số> <tên còn lại>`
                parsed_quantity = first_word_as_int
                processed_item_name = " ".join(parts[1:])
            except ValueError:
                # Từ đầu tiên không phải là số, vậy toàn bộ là tên vật phẩm
                processed_item_name = item_name 
        
        item_id_to_buy = processed_item_name.lower().strip().replace(" ", "_")

        if not item_id_to_buy:
             await try_send(ctx, content=f"{ICON_WARNING} Vui lòng nhập tên vật phẩm bạn muốn mua. Cú pháp: `{COMMAND_PREFIX}buy <tên_vật_phẩm> [số_lượng]`")
             return

        if parsed_quantity <= 0: # Kiểm tra lại parsed_quantity sau khi có thể đã thay đổi
            await try_send(ctx, content=f"{ICON_ERROR} Số lượng mua phải lớn hơn 0.")
            return

        if item_id_to_buy not in SHOP_ITEMS:
            await try_send(ctx, content=f"{ICON_ERROR} Vật phẩm `{processed_item_name}` không tồn tại trong cửa hàng.")
            return
        
        item_details = SHOP_ITEMS[item_id_to_buy]
        price_per_item = item_details["price"]
        total_price = price_per_item * parsed_quantity
        
        data = get_user_data(ctx.guild.id, ctx.author.id)
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]
        item_name_display = item_id_to_buy.replace("_", " ").capitalize()

        if user_data.get("balance", 0) < total_price:
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không đủ tiền! Bạn cần **{total_price:,}** {CURRENCY_SYMBOL} để mua {parsed_quantity} {item_name_display}. ({ICON_MONEY_BAG} Ví bạn có: {user_data.get('balance', 0):,} {CURRENCY_SYMBOL})")
            return
            
        user_data["balance"] -= total_price
        if "inventory" not in user_data or not isinstance(user_data["inventory"], list):
            user_data["inventory"] = []
        
        for _ in range(parsed_quantity):
            user_data["inventory"].append(item_id_to_buy)
        
        save_data(data)
        await try_send(ctx, content=f"{ICON_SUCCESS} Bạn đã mua thành công **{parsed_quantity} {item_name_display}** với tổng giá **{total_price:,}** {CURRENCY_SYMBOL}! Chúng đã được thêm vào túi đồ (`{COMMAND_PREFIX}inv`).")

def setup(bot: commands.Bot):
    bot.add_cog(BuyCommandCog(bot))
