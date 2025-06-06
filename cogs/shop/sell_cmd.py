# bot/cogs/shop/sell_cmd.py
import nextcord
from nextcord.ext import commands
import logging

from core.database import (
    load_economy_data,
    get_or_create_global_user_profile,
    save_economy_data
)
from core.utils import try_send
from core.config import CURRENCY_SYMBOL, SHOP_ITEMS as MASTER_ITEM_LIST, COMMAND_PREFIX
from core.icons import ICON_SUCCESS, ICON_ERROR, ICON_WARNING, ICON_INFO, ICON_MONEY_BAG

logger = logging.getLogger(__name__)

class SellCommandCog(commands.Cog, name="Sell Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"SellCommandCog initialized.")

    @commands.command(name='sell')
    async def sell(self, ctx: commands.Context, item_name: str, quantity: int = 1):
        """Bán một hoặc nhiều vật phẩm từ Túi Đồ Toàn Cục của bạn."""
        author_id = ctx.author.id
        guild_name_for_log = ctx.guild.name if ctx.guild else "DM"
        
        logger.debug(f"Lệnh 'sell' được gọi bởi {ctx.author.name} ({author_id}) với item_name='{item_name}', quantity={quantity} tại guild '{guild_name_for_log}'.")

        if quantity <= 0:
            logger.warning(f"User {author_id} cố gắng bán với quantity không hợp lệ (<=0): {quantity}")
            await try_send(ctx, content=f"{ICON_ERROR} Số lượng bán phải lớn hơn 0.")
            return

        # Xử lý input linh hoạt (tương tự lệnh buy)
        parts = item_name.split()
        processed_item_name = item_name 
        parsed_quantity = quantity      
        if quantity == 1 and len(parts) > 1:
            try:
                first_word_as_int = int(parts[0])
                parsed_quantity = first_word_as_int
                processed_item_name = " ".join(parts[1:])
                logger.debug(f"Đã phân tích lại input cho 'sell': quantity={parsed_quantity}, item_name='{processed_item_name}'")
            except ValueError:
                processed_item_name = item_name 
        
        item_id_to_sell = processed_item_name.lower().strip().replace(" ", "_")
        item_name_display = item_id_to_sell.replace("_", " ").capitalize()

        if not item_id_to_sell:
             logger.warning(f"User {author_id} không nhập tên vật phẩm cho lệnh 'sell'.")
             await try_send(ctx, content=f"{ICON_WARNING} Vui lòng nhập tên vật phẩm bạn muốn bán.")
             return
        
        if parsed_quantity <= 0:
            logger.warning(f"User {author_id} cố gắng bán với parsed_quantity không hợp lệ (<=0): {parsed_quantity}")
            await try_send(ctx, content=f"{ICON_ERROR} Số lượng bán phải lớn hơn 0.")
            return

        # Kiểm tra vật phẩm có trong danh sách master không để biết giá bán
        if item_id_to_sell not in MASTER_ITEM_LIST:
            logger.warning(f"User {author_id} cố gắng bán vật phẩm không có trong MASTER_ITEM_LIST: '{item_id_to_sell}'")
            await try_send(ctx, content=f"{ICON_ERROR} Vật phẩm `{item_name_display}` không nằm trong danh mục có thể bán của cửa hàng.")
            return

        item_master_details = MASTER_ITEM_LIST[item_id_to_sell]
        sell_price_per_item = item_master_details.get("sell_price")

        if sell_price_per_item is None:
            logger.warning(f"User {author_id} cố gắng bán vật phẩm không có giá bán: '{item_id_to_sell}'")
            await try_send(ctx, content=f"{ICON_INFO} Vật phẩm `{item_name_display}` này không thể bán lại.")
            return
            
        economy_data = load_economy_data()
        user_profile = get_or_create_global_user_profile(economy_data, author_id)
        original_global_balance = user_profile.get("global_balance", 0)
        
        # Lấy túi đồ toàn cục
        inventory_global_list = user_profile.get("inventory_global", [])
        if not isinstance(inventory_global_list, list):
            inventory_global_list = []
            user_profile["inventory_global"] = inventory_global_list

        current_item_count = inventory_global_list.count(item_id_to_sell)

        if current_item_count < parsed_quantity:
            logger.warning(f"User {author_id} không đủ {parsed_quantity} '{item_name_display}' để bán. Chỉ có {current_item_count}.")
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ **{parsed_quantity} {item_name_display}** trong Túi Đồ Toàn Cục để bán. Bạn chỉ có {current_item_count}.")
            return
        
        total_sell_price = sell_price_per_item * parsed_quantity
        
        # Thực hiện giao dịch
        user_profile["global_balance"] = original_global_balance + total_sell_price
        
        items_removed_successfully = 0
        for _ in range(parsed_quantity):
            try:
                inventory_global_list.remove(item_id_to_sell)
                items_removed_successfully += 1
            except ValueError:
                logger.error(f"Lỗi logic khi xóa '{item_id_to_sell}' khỏi inventory_global của user {author_id}. Hoàn tiền đã cộng.", exc_info=True)
                user_profile["global_balance"] = original_global_balance # Hoàn tác việc cộng tiền
                save_economy_data(economy_data) 
                await try_send(ctx, content=f"{ICON_ERROR} Có lỗi xảy ra khi xóa vật phẩm khỏi túi đồ. Giao dịch đã được hủy bỏ.")
                return
        
        save_economy_data(economy_data)

        logger.info(f"User {ctx.author.display_name} ({author_id}) đã bán {parsed_quantity} x '{item_name_display}' (ID: {item_id_to_sell}) "
                    f"thu về {total_sell_price:,} {CURRENCY_SYMBOL}. "
                    f"Ví Toàn Cục: {original_global_balance:,} -> {user_profile['global_balance']:,}.")
        
        await try_send(ctx, content=f"{ICON_SUCCESS} Bạn đã bán thành công **{parsed_quantity} {item_name_display}** và nhận được **{total_sell_price:,}** {CURRENCY_SYMBOL} vào Ví Toàn Cục! {ICON_MONEY_BAG} Ví Toàn Cục: {user_profile['global_balance']:,}")
        logger.debug(f"Lệnh 'sell' cho {ctx.author.name} (bán {parsed_quantity} {item_name_display}) đã xử lý xong.")

def setup(bot: commands.Bot):
    bot.add_cog(SellCommandCog(bot))
