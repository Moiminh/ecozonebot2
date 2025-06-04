# bot/cogs/shop/buy_cmd.py
import nextcord
from nextcord.ext import commands
import logging # <<< THÊM IMPORT NÀY

# Import các thành phần cần thiết từ package 'core'
from core.database import get_user_data, save_data
from core.utils import try_send
from core.config import CURRENCY_SYMBOL, SHOP_ITEMS, COMMAND_PREFIX
from core.icons import ICON_SUCCESS, ICON_ERROR, ICON_WARNING, ICON_MONEY_BAG, ICON_INFO # Đảm bảo có ICON_INFO

logger = logging.getLogger(__name__) # <<< LẤY LOGGER CHO MODULE NÀY

class BuyCommandCog(commands.Cog, name="Buy Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"BuyCommandCog initialized.")

    @commands.command(name='buy')
    async def buy(self, ctx: commands.Context, item_name: str, quantity: int = 1):
        """Mua một hoặc nhiều vật phẩm từ cửa hàng. Nếu không nhập số lượng, mặc định là 1."""
        logger.debug(f"Lệnh 'buy' được gọi bởi {ctx.author.name} (ID: {ctx.author.id}) với item_name='{item_name}', quantity={quantity} tại guild {ctx.guild.id}.")

        if quantity <= 0:
            logger.warning(f"User {ctx.author.id} cố gắng mua với quantity không hợp lệ (<=0): {quantity}")
            await try_send(ctx, content=f"{ICON_ERROR} Số lượng mua phải lớn hơn 0.")
            return

        # Xử lý item_name và quantity (logic này giữ nguyên từ phiên bản trước)
        parts = item_name.split()
        processed_item_name = item_name 
        parsed_quantity = quantity      

        if quantity == 1 and len(parts) > 1: 
            try:
                first_word_as_int = int(parts[0])
                parsed_quantity = first_word_as_int
                processed_item_name = " ".join(parts[1:])
                logger.debug(f"Đã phân tích lại input cho 'buy': quantity={parsed_quantity}, item_name='{processed_item_name}' từ input gốc item_name='{item_name}'")
            except ValueError:
                processed_item_name = item_name 
        
        item_id_to_buy = processed_item_name.lower().strip().replace(" ", "_")
        item_name_display = item_id_to_buy.replace("_", " ").capitalize() # Tên để hiển thị cho người dùng

        if not item_id_to_buy:
             logger.warning(f"User {ctx.author.id} không nhập tên vật phẩm cho lệnh 'buy'. Input item_name: '{item_name}'")
             await try_send(ctx, content=f"{ICON_WARNING} Vui lòng nhập tên vật phẩm bạn muốn mua. Cú pháp: `{COMMAND_PREFIX}buy <tên_vật_phẩm> [số_lượng]`")
             return

        if parsed_quantity <= 0: 
            logger.warning(f"User {ctx.author.id} cố gắng mua với parsed_quantity không hợp lệ (<=0): {parsed_quantity}")
            await try_send(ctx, content=f"{ICON_ERROR} Số lượng mua phải lớn hơn 0.")
            return

        if item_id_to_buy not in SHOP_ITEMS:
            logger.warning(f"User {ctx.author.id} cố gắng mua vật phẩm không tồn tại: '{item_id_to_buy}' (từ input: '{processed_item_name}')")
            await try_send(ctx, content=f"{ICON_ERROR} Vật phẩm `{item_name_display}` không tồn tại trong cửa hàng.")
            return
        
        item_details = SHOP_ITEMS[item_id_to_buy]
        price_per_item = item_details["price"]
        total_price = price_per_item * parsed_quantity
        
        data = get_user_data(ctx.guild.id, ctx.author.id)
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]
        original_balance = user_data.get("balance", 0)

        if original_balance < total_price:
            logger.warning(f"User {ctx.author.id} không đủ tiền mua {parsed_quantity} '{item_name_display}'. Cần: {total_price}, Có: {original_balance}")
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không đủ tiền! Bạn cần **{total_price:,}** {CURRENCY_SYMBOL} để mua {parsed_quantity} {item_name_display}. ({ICON_MONEY_BAG} Ví bạn có: {original_balance:,} {CURRENCY_SYMBOL})")
            return
            
        user_data["balance"] -= total_price
        if "inventory" not in user_data or not isinstance(user_data["inventory"], list):
            user_data["inventory"] = []
        
        for _ in range(parsed_quantity):
            user_data["inventory"].append(item_id_to_buy)
        
        save_data(data)

        # Ghi log hành động của người chơi
        logger.info(f"User {ctx.author.display_name} ({ctx.author.id}) đã mua {parsed_quantity} x '{item_name_display}' (ID: {item_id_to_buy}) "
                    f"với tổng giá {total_price:,} {CURRENCY_SYMBOL}. "
                    f"Số dư: {original_balance:,} -> {user_data['balance']:,}.")
        
        await try_send(ctx, content=f"{ICON_SUCCESS} Bạn đã mua thành công **{parsed_quantity} {item_name_display}** với tổng giá **{total_price:,}** {CURRENCY_SYMBOL}! Chúng đã được thêm vào túi đồ (`{COMMAND_PREFIX}inv`).")
        logger.debug(f"Lệnh 'buy' cho {ctx.author.name} (mua {parsed_quantity} {item_name_display}) đã xử lý xong.")

def setup(bot: commands.Bot):
    bot.add_cog(BuyCommandCog(bot))
