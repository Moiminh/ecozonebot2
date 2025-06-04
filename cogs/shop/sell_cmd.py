# bot/cogs/shop/sell_cmd.py
import nextcord
from nextcord.ext import commands

# Import các thành phần cần thiết từ package 'core'
from core.database import get_user_data, save_data
from core.utils import try_send
from core.config import CURRENCY_SYMBOL, SHOP_ITEMS, COMMAND_PREFIX
from core.icons import ICON_SUCCESS, ICON_ERROR, ICON_WARNING, ICON_INFO, ICON_MONEY_BAG # Đảm bảo các icon này có trong core/icons.py

class SellCommandCog(commands.Cog, name="Sell Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='sell')
    async def sell(self, ctx: commands.Context, item_name: str, quantity: int = 1):
        """Bán một hoặc nhiều vật phẩm từ túi đồ của bạn. Nếu không nhập số lượng, mặc định là 1.
        Ví dụ: !sell laptop
               !sell laptop 2
               !sell "gold watch"
        """
        if quantity <= 0:
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
            except ValueError:
                processed_item_name = item_name 
        
        item_id_to_sell = processed_item_name.lower().strip().replace(" ", "_")
        item_name_display = item_id_to_sell.replace("_", " ").capitalize()

        if not item_id_to_sell:
             await try_send(ctx, content=f"{ICON_WARNING} Vui lòng nhập tên vật phẩm bạn muốn bán. Cú pháp: `{COMMAND_PREFIX}sell <tên_vật_phẩm> [số_lượng]`")
             return
        
        if parsed_quantity <= 0: 
            await try_send(ctx, content=f"{ICON_ERROR} Số lượng bán phải lớn hơn 0.")
            return

        if item_id_to_sell not in SHOP_ITEMS:
            await try_send(ctx, content=f"{ICON_ERROR} Vật phẩm `{item_name_display}` không nằm trong danh mục có thể bán của cửa hàng.")
            return

        item_details = SHOP_ITEMS[item_id_to_sell]
        sell_price_per_item = item_details.get("sell_price")

        if sell_price_per_item is None:
            await try_send(ctx, content=f"{ICON_INFO} Vật phẩm `{item_name_display}` này không thể bán lại.")
            return
            
        data = get_user_data(ctx.guild.id, ctx.author.id)
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]
        
        inventory_list = user_data.get("inventory", [])
        if not isinstance(inventory_list, list): # Đảm bảo inventory là list
            inventory_list = []
            user_data["inventory"] = inventory_list

        current_item_count = inventory_list.count(item_id_to_sell)

        if current_item_count < parsed_quantity:
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ **{parsed_quantity} {item_name_display}** để bán. Bạn chỉ có {current_item_count}.")
            return
        
        total_sell_price = sell_price_per_item * parsed_quantity
        user_data["balance"] = user_data.get("balance", 0) + total_sell_price
        
        items_removed_successfully = 0
        for _ in range(parsed_quantity):
            try:
                inventory_list.remove(item_id_to_sell)
                items_removed_successfully += 1
            except ValueError:
                # Lỗi này không nên xảy ra nếu logic đếm ở trên đúng và không có thay đổi đồng thời
                print(f"Lỗi logic khi xóa {item_id_to_sell} cho user {ctx.author.id}. Đã đếm {current_item_count}, muốn xóa {parsed_quantity}, đã xóa {items_removed_successfully}.")
                # Hoàn lại tiền nếu không xóa đủ số lượng như dự kiến
                user_data["balance"] -= (sell_price_per_item * (parsed_quantity - items_removed_successfully))
                save_data(data) 
                await try_send(ctx, content=f"{ICON_ERROR} Có lỗi xảy ra khi xóa vật phẩm khỏi túi đồ. Giao dịch có thể không hoàn tất đúng. Vui lòng kiểm tra lại.")
                return
        
        save_data(data)
        await try_send(ctx, content=f"{ICON_SUCCESS} Bạn đã bán thành công **{parsed_quantity} {item_name_display}** và nhận được **{total_sell_price:,}** {CURRENCY_SYMBOL}! {ICON_MONEY_BAG} Ví: {user_data['balance']:,}")

def setup(bot: commands.Bot):
    bot.add_cog(SellCommandCog(bot))
