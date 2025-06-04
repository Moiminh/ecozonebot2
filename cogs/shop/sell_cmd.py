# bot/cogs/shop/sell_cmd.py
import nextcord
from nextcord.ext import commands
import logging # <<< THÊM IMPORT NÀY

# Import các thành phần cần thiết từ package 'core'
from core.database import get_user_data, save_data
from core.utils import try_send
from core.config import CURRENCY_SYMBOL, SHOP_ITEMS, COMMAND_PREFIX
from core.icons import ICON_SUCCESS, ICON_ERROR, ICON_WARNING, ICON_INFO, ICON_MONEY_BAG # Đảm bảo có ICON_INFO

logger = logging.getLogger(__name__) # <<< LẤY LOGGER CHO MODULE NÀY

class SellCommandCog(commands.Cog, name="Sell Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"SellCommandCog initialized.")

    @commands.command(name='sell')
    async def sell(self, ctx: commands.Context, item_name: str, quantity: int = 1):
        """Bán một hoặc nhiều vật phẩm từ túi đồ của bạn. Nếu không nhập số lượng, mặc định là 1."""
        logger.debug(f"Lệnh 'sell' được gọi bởi {ctx.author.name} (ID: {ctx.author.id}) với item_name='{item_name}', quantity={quantity} tại guild {ctx.guild.id}.")

        if quantity <= 0:
            logger.warning(f"User {ctx.author.id} cố gắng bán với quantity không hợp lệ (<=0): {quantity}")
            await try_send(ctx, content=f"{ICON_ERROR} Số lượng bán phải lớn hơn 0.")
            return

        # Xử lý item_name và quantity tương tự như lệnh buy
        parts = item_name.split()
        processed_item_name = item_name 
        parsed_quantity = quantity      

        if quantity == 1 and len(parts) > 1:
            try:
                first_word_as_int = int(parts[0])
                parsed_quantity = first_word_as_int
                processed_item_name = " ".join(parts[1:])
                logger.debug(f"Đã phân tích lại input cho 'sell': quantity={parsed_quantity}, item_name='{processed_item_name}' từ input gốc item_name='{item_name}'")
            except ValueError:
                processed_item_name = item_name 
        
        item_id_to_sell = processed_item_name.lower().strip().replace(" ", "_")
        item_name_display = item_id_to_sell.replace("_", " ").capitalize()

        if not item_id_to_sell:
             logger.warning(f"User {ctx.author.id} không nhập tên vật phẩm cho lệnh 'sell'. Input item_name: '{item_name}'")
             await try_send(ctx, content=f"{ICON_WARNING} Vui lòng nhập tên vật phẩm bạn muốn bán. Cú pháp: `{COMMAND_PREFIX}sell <tên_vật_phẩm> [số_lượng]`")
             return
        
        if parsed_quantity <= 0: 
            logger.warning(f"User {ctx.author.id} cố gắng bán với parsed_quantity không hợp lệ (<=0): {parsed_quantity}")
            await try_send(ctx, content=f"{ICON_ERROR} Số lượng bán phải lớn hơn 0.")
            return

        if item_id_to_sell not in SHOP_ITEMS:
            logger.warning(f"User {ctx.author.id} cố gắng bán vật phẩm không có trong SHOP_ITEMS: '{item_id_to_sell}' (từ input: '{processed_item_name}')")
            await try_send(ctx, content=f"{ICON_ERROR} Vật phẩm `{item_name_display}` không nằm trong danh mục có thể bán của cửa hàng.")
            return

        item_details = SHOP_ITEMS[item_id_to_sell]
        sell_price_per_item = item_details.get("sell_price")

        if sell_price_per_item is None:
            logger.warning(f"User {ctx.author.id} cố gắng bán vật phẩm không có giá bán: '{item_id_to_sell}'")
            await try_send(ctx, content=f"{ICON_INFO} Vật phẩm `{item_name_display}` này không thể bán lại.")
            return
            
        data = get_user_data(ctx.guild.id, ctx.author.id)
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]
        original_balance = user_data.get("balance", 0)
        
        inventory_list = user_data.get("inventory", [])
        if not isinstance(inventory_list, list):
            inventory_list = []
            user_data["inventory"] = inventory_list # Gán lại nếu nó không phải list

        current_item_count = inventory_list.count(item_id_to_sell)

        if current_item_count < parsed_quantity:
            logger.warning(f"User {ctx.author.id} không đủ {parsed_quantity} '{item_name_display}' để bán. Chỉ có {current_item_count}.")
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ **{parsed_quantity} {item_name_display}** để bán. Bạn chỉ có {current_item_count}.")
            return
        
        total_sell_price = sell_price_per_item * parsed_quantity
        user_data["balance"] = original_balance + total_sell_price # Cộng tiền bán được
        
        items_removed_count_for_log = 0
        for _ in range(parsed_quantity):
            try:
                inventory_list.remove(item_id_to_sell)
                items_removed_count_for_log += 1
            except ValueError:
                logger.error(f"Lỗi ValueError khi xóa '{item_id_to_sell}' cho user {ctx.author.id} lần thứ {items_removed_count_for_log + 1} (yêu cầu {parsed_quantity}, có {current_item_count}). Hoàn tiền đã cộng.", exc_info=True)
                user_data["balance"] = original_balance # Hoàn lại balance về trạng thái trước khi cộng tiền bán
                # Không cần save_data() ở đây vì giao dịch thất bại, nhưng nếu muốn log trạng thái cuối cùng thì có thể save
                await try_send(ctx, content=f"{ICON_ERROR} Có lỗi xảy ra khi xóa vật phẩm khỏi túi đồ. Giao dịch đã được hủy bỏ.")
                return
        
        save_data(data)

        # Ghi log hành động của người chơi
        logger.info(f"User {ctx.author.display_name} ({ctx.author.id}) đã bán {parsed_quantity} x '{item_name_display}' (ID: {item_id_to_sell}) "
                    f"thu về {total_sell_price:,} {CURRENCY_SYMBOL}. "
                    f"Số dư: {original_balance:,} -> {user_data['balance']:,}.")
        
        await try_send(ctx, content=f"{ICON_SUCCESS} Bạn đã bán thành công **{parsed_quantity} {item_name_display}** và nhận được **{total_sell_price:,}** {CURRENCY_SYMBOL}! {ICON_MONEY_BAG} Ví: {user_data['balance']:,}")
        logger.debug(f"Lệnh 'sell' cho {ctx.author.name} (bán {parsed_quantity} {item_name_display}) đã xử lý xong.")

def setup(bot: commands.Bot):
    bot.add_cog(SellCommandCog(bot))
