# bot/cogs/shop/buy_cmd.py
import nextcord
from nextcord.ext import commands
import logging

from core.database import (
    load_economy_data,
    get_or_create_global_user_profile,
    get_or_create_global_shop_stock,
    update_shop_item_stock,
    save_economy_data
)
from core.utils import try_send
from core.config import CURRENCY_SYMBOL, SHOP_ITEMS, COMMAND_PREFIX
from core.icons import ICON_SUCCESS, ICON_ERROR, ICON_WARNING, ICON_MONEY_BAG, ICON_INFO
# bot/cogs/shop/buy_cmd.py
import nextcord
from nextcord.ext import commands
import logging

from core.database import (
    load_economy_data,
    get_or_create_global_user_profile,
    get_or_create_global_shop_stock,
    update_shop_item_stock,
    get_shop_item_details_from_stock,
    save_economy_data
)
from core.utils import try_send
from core.config import CURRENCY_SYMBOL, SHOP_ITEMS as MASTER_ITEM_LIST, COMMAND_PREFIX
from core.icons import ICON_SUCCESS, ICON_ERROR, ICON_WARNING, ICON_MONEY_BAG, ICON_INFO

logger = logging.getLogger(__name__)

class BuyCommandCog(commands.Cog, name="Buy Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"BuyCommandCog initialized.")

    @commands.command(name='buy')
    async def buy(self, ctx: commands.Context, item_name: str, quantity: int = 1):
        author_id = ctx.author.id
        guild_name_for_log = ctx.guild.name if ctx.guild else "DM"
        
        logger.debug(f"Lệnh 'buy' được gọi bởi {ctx.author.name} ({author_id}) với item_name='{item_name}', quantity={quantity} tại guild '{guild_name_for_log}'.")

        if quantity <= 0:
            logger.warning(f"User {author_id} cố gắng mua với quantity không hợp lệ (<=0): {quantity}")
            await try_send(ctx, content=f"{ICON_ERROR} Số lượng mua phải lớn hơn 0.")
            return

        parts = item_name.split()
        processed_item_name = item_name 
        parsed_quantity = quantity      
        if quantity == 1 and len(parts) > 1:
            try:
                first_word_as_int = int(parts[0])
                parsed_quantity = first_word_as_int
                processed_item_name = " ".join(parts[1:])
                logger.debug(f"Đã phân tích lại input cho 'buy': quantity={parsed_quantity}, item_name='{processed_item_name}'")
            except ValueError:
                processed_item_name = item_name 
        
        item_id_to_buy = processed_item_name.lower().strip().replace(" ", "_")
        item_name_display = item_id_to_buy.replace("_", " ").capitalize()

        if not item_id_to_buy:
             logger.warning(f"User {author_id} không nhập tên vật phẩm cho lệnh 'buy'.")
             await try_send(ctx, content=f"{ICON_WARNING} Vui lòng nhập tên vật phẩm bạn muốn mua.")
             return

        if parsed_quantity <= 0:
            logger.warning(f"User {author_id} cố gắng mua với parsed_quantity không hợp lệ (<=0): {parsed_quantity}")
            await try_send(ctx, content=f"{ICON_ERROR} Số lượng mua phải lớn hơn 0.")
            return

        if item_id_to_buy not in MASTER_ITEM_LIST:
            logger.warning(f"User {author_id} cố gắng mua vật phẩm không tồn tại trong master list: '{item_id_to_buy}'")
            await try_send(ctx, content=f"{ICON_ERROR} Vật phẩm `{item_name_display}` không tồn tại trong danh mục cửa hàng.")
            return
        
        item_master_details = MASTER_ITEM_LIST[item_id_to_buy]
        price_per_item = item_master_details["price"]
        total_price = price_per_item * parsed_quantity
        
        economy_data = load_economy_data()
        user_profile = get_or_create_global_user_profile(economy_data, author_id)
        original_global_balance = user_profile.get("global_balance", 0)
        shop_stock = get_or_create_global_shop_stock(economy_data)
        item_stock_details = get_shop_item_details_from_stock(shop_stock, item_id_to_buy)
        
        if item_stock_details is None:
            logger.warning(f"User {author_id} cố gắng mua vật phẩm '{item_id_to_buy}' chưa có trong global_shop_stock.")
            await try_send(ctx, content=f"{ICON_INFO} Rất tiếc, vật phẩm `{item_name_display}` hiện không có bán trong cửa hàng toàn cục.")
            return

        current_stock = item_stock_details.get("current_stock", 0)
        if current_stock < parsed_quantity:
             logger.warning(f"User {author_id} cố gắng mua {parsed_quantity} x '{item_id_to_buy}' nhưng shop chỉ còn {current_stock}.")
             await try_send(ctx, content=f"{ICON_ERROR} Rất tiếc, cửa hàng toàn cục chỉ còn **{current_stock}** {item_name_display}. Bạn không thể mua {parsed_quantity} cái.")
             return
        
        if original_global_balance < total_price:
            logger.warning(f"User {author_id} không đủ tiền mua {parsed_quantity} '{item_name_display}'. Cần: {total_price}, Có: {original_global_balance}")
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không đủ tiền trong Ví Toàn Cục! Bạn cần **{total_price:,}** {CURRENCY_SYMBOL} để mua {parsed_quantity} {item_name_display}. ({ICON_MONEY_BAG} Ví bạn có: {original_global_balance:,} {CURRENCY_SYMBOL})")
            return
            
        user_profile["global_balance"] = original_global_balance - total_price
        user_profile.setdefault("inventory_global", []).extend([item_id_to_buy] * parsed_quantity)
        
        update_shop_item_stock(shop_stock, item_id_to_buy, -parsed_quantity) 
        
        save_economy_data(economy_data)

        logger.info(f"User {ctx.author.display_name} ({author_id}) đã mua {parsed_quantity} x '{item_name_display}' (ID: {item_id_to_buy}) với tổng giá {total_price:,} {CURRENCY_SYMBOL}. "
                    f"Ví Toàn Cục: {original_global_balance:,} -> {user_profile['global_balance']:,}.")
        
        await try_send(ctx, content=f"{ICON_SUCCESS} Bạn đã mua thành công **{parsed_quantity} {item_name_display}** với tổng giá **{total_price:,}** {CURRENCY_SYMBOL}! Chúng đã được thêm vào Túi Đồ Toàn Cục của bạn (`{COMMAND_PREFIX}inv`).")
        logger.debug(f"Lệnh 'buy' cho {ctx.author.name} đã xử lý xong.")

def setup(bot: commands.Bot):
    bot.add_cog(BuyCommandCog(bot))
     f"Ví Toàn Cục: {original_global_balance:,} -> {user_profile['global_balance']:,}.")
        
        await try_send(ctx, content=f"{ICON_SUCCESS} Bạn đã mua thành công **{parsed_quantity} {item_name_display}** với tổng giá **{total_price:,}** {CURRENCY_SYMBOL}! Chúng đã được thêm vào Túi Đồ Toàn Cục của bạn (`{COMMAND_PREFIX}inv`).")
        logger.debug(f"Lệnh 'buy' cho {ctx.author.name} (mua {parsed_quantity} {item_name_display}) đã xử lý xong.")

def setup(bot: commands.Bot):
    bot.add_cog(BuyCommandCog(bot))
