# bot/cogs/shop.py
import nextcord
from nextcord.ext import commands
from typing import Optional # Không thực sự cần nếu dùng giá trị mặc định trực tiếp

# Import các thành phần cần thiết từ package 'core'
from core.database import get_user_data, save_data
from core.utils import try_send
from core.config import CURRENCY_SYMBOL, SHOP_ITEMS, COMMAND_PREFIX
from core.icons import ICON_SHOP, ICON_INVENTORY, ICON_SUCCESS, ICON_ERROR, ICON_WARNING # Thêm các icon nếu cần

class ShopCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='shop', aliases=['store'])
    async def shop(self, ctx: commands.Context):
        """Hiển thị các vật phẩm đang được bán trong cửa hàng.
        Sử dụng lệnh `buy <tên_vật_phẩm> [số_lượng]` để mua (số lượng mặc định là 1).
        Sử dụng lệnh `sell <tên_vật_phẩm> [số_lượng]` để bán (số lượng mặc định là 1).
        """
        embed = nextcord.Embed(
            title=f"{ICON_SHOP} Cửa Hàng 🏪", # Thêm icon cho shop
            description=f"Mua: `{COMMAND_PREFIX}buy <tên_vật_phẩm> [số_lượng]` (mặc định số lượng là 1)\nBán: `{COMMAND_PREFIX}sell <tên_vật_phẩm> [số_lượng]` (mặc định số lượng là 1)",
            color=nextcord.Color.orange()
        )
        if not SHOP_ITEMS:
            embed.description = "Cửa hàng hiện đang trống hoặc đang được cập nhật."
        else:
            for item_id, details in SHOP_ITEMS.items():
                item_name_display = item_id.replace("_", " ").capitalize()
                buy_price_str = f"{details['price']:,}"
                
                sell_price_val = details.get('sell_price')
                if sell_price_val is not None:
                    sell_price_str = f"{sell_price_val:,} {CURRENCY_SYMBOL}"
                else:
                    sell_price_str = "Không thể bán"
                
                embed.add_field(
                    name=f"{item_name_display} - Mua: {buy_price_str} {CURRENCY_SYMBOL} | Bán: {sell_price_str}",
                    value=details['description'],
                    inline=False
                )
        await try_send(ctx, embed=embed)

    @commands.command(name='buy')
    async def buy(self, ctx: commands.Context, item_name: str, quantity: int = 1): # Thay đổi thứ tự và thêm giá trị mặc định cho quantity
        """Mua một hoặc nhiều vật phẩm từ cửa hàng. Nếu không nhập số lượng, mặc định là 1.
        Ví dụ: !buy laptop
               !buy laptop 2
        """
        if quantity <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Số lượng mua phải lớn hơn 0.")
            return

        # item_name giờ đứng trước, nên nó sẽ nhận phần chữ trước.
        # Nếu item_name có nhiều từ, người dùng lệnh prefix cần dùng dấu ngoặc kép: !buy "gold watch" 2
        # Lệnh tắt (bare command) ví dụ "buy gold watch 2" sẽ được xử lý:
        #   command_candidate = "buy"
        #   args_for_bare_command = "gold watch 2"
        #   message.content = "!buy gold watch 2"
        #   Nextcord sẽ cố gắng khớp "gold watch" với item_name và "2" với quantity.
        #   Nếu người dùng gõ "buy gold watch" (không có số lượng), quantity sẽ là 1 (mặc định).
        
        # Xử lý trường hợp người dùng gõ "buy 2 laptop" (sai thứ tự mới)
        # Đây là một cách đơn giản để thử đoán ý người dùng, có thể cần tinh chỉnh
        potential_quantity_in_item_name_str = item_name.split()
        actual_item_name_parts = []
        parsed_quantity = quantity # Giữ lại quantity gốc nếu có

        if len(potential_quantity_in_item_name_str) > 1:
            try:
                # Thử xem từ đầu tiên của item_name có phải là số không (trường hợp gõ `buy 2 laptop`)
                # và quantity gốc vẫn là giá trị mặc định (1)
                first_word_as_int = int(potential_quantity_in_item_name_str[0])
                if quantity == 1: # Chỉ ghi đè nếu quantity là mặc định
                    parsed_quantity = first_word_as_int
                    actual_item_name_parts = potential_quantity_in_item_name_str[1:]
                else: # Người dùng đã cung cấp quantity ở cuối, giữ nguyên item_name
                    actual_item_name_parts = potential_quantity_in_item_name_str
            except ValueError:
                # Từ đầu tiên không phải là số, coi như toàn bộ là item_name
                actual_item_name_parts = potential_quantity_in_item_name_str
        else:
            actual_item_name_parts = potential_quantity_in_item_name_str

        processed_item_name = " ".join(actual_item_name_parts)
        item_id_to_buy = processed_item_name.lower().strip().replace(" ", "_")

        if not item_id_to_buy: # Nếu sau khi xử lý item_name rỗng (ví dụ: chỉ nhập số)
             await try_send(ctx, content=f"{ICON_WARNING} Vui lòng nhập tên vật phẩm bạn muốn mua. Cú pháp: `{COMMAND_PREFIX}buy <tên_vật_phẩm> [số_lượng]`")
             return

        if parsed_quantity <= 0: # Kiểm tra lại parsed_quantity
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
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không đủ tiền! Bạn cần **{total_price:,}** {CURRENCY_SYMBOL} để mua {parsed_quantity} {item_name_display}. (Ví bạn có: {user_data.get('balance', 0):,} {CURRENCY_SYMBOL})")
            return
            
        user_data["balance"] -= total_price
        if "inventory" not in user_data or not isinstance(user_data["inventory"], list):
            user_data["inventory"] = []
        
        for _ in range(parsed_quantity):
            user_data["inventory"].append(item_id_to_buy)
        
        save_data(data)
        await try_send(ctx, content=f"{ICON_SUCCESS} Bạn đã mua thành công **{parsed_quantity} {item_name_display}** với tổng giá **{total_price:,}** {CURRENCY_SYMBOL}! Chúng đã được thêm vào túi đồ (`{COMMAND_PREFIX}inv`).")

    @commands.command(name='sell')
    async def sell(self, ctx: commands.Context, item_name: str, quantity: int = 1): # Thay đổi thứ tự và thêm giá trị mặc định
        """Bán một hoặc nhiều vật phẩm từ túi đồ của bạn. Nếu không nhập số lượng, mặc định là 1.
        Ví dụ: !sell laptop
               !sell laptop 2
        """
        if quantity <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Số lượng bán phải lớn hơn 0.")
            return

        # Tương tự như buy, xử lý trường hợp người dùng có thể nhập sai thứ tự (ví dụ `sell 2 laptop`)
        potential_quantity_in_item_name_str = item_name.split()
        actual_item_name_parts = []
        parsed_quantity = quantity

        if len(potential_quantity_in_item_name_str) > 1:
            try:
                first_word_as_int = int(potential_quantity_in_item_name_str[0])
                if quantity == 1: # Chỉ ghi đè nếu quantity là mặc định
                    parsed_quantity = first_word_as_int
                    actual_item_name_parts = potential_quantity_in_item_name_str[1:]
                else:
                    actual_item_name_parts = potential_quantity_in_item_name_str
            except ValueError:
                actual_item_name_parts = potential_quantity_in_item_name_str
        else:
            actual_item_name_parts = potential_quantity_in_item_name_str
        
        processed_item_name = " ".join(actual_item_name_parts)
        item_id_to_sell = processed_item_name.lower().strip().replace(" ", "_")
        item_name_display = item_id_to_sell.replace("_", " ").capitalize()

        if not item_id_to_sell:
             await try_send(ctx, content=f"{ICON_WARNING} Vui lòng nhập tên vật phẩm bạn muốn bán. Cú pháp: `{COMMAND_PREFIX}sell <tên_vật_phẩm> [số_lượng]`")
             return
        
        if parsed_quantity <= 0: # Kiểm tra lại parsed_quantity
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
        if not isinstance(inventory_list, list):
            inventory_list = []
            user_data["inventory"] = inventory_list

        current_item_count = inventory_list.count(item_id_to_sell)

        if current_item_count < parsed_quantity:
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ **{parsed_quantity} {item_name_display}** để bán. Bạn chỉ có {current_item_count}.")
            return
        
        total_sell_price = sell_price_per_item * parsed_quantity
        user_data["balance"] = user_data.get("balance", 0) + total_sell_price
        
        for _ in range(parsed_quantity):
            try:
                inventory_list.remove(item_id_to_sell)
            except ValueError:
                await try_send(ctx, content=f"{ICON_ERROR} Lỗi khi cố gắng xóa {item_name_display} khỏi túi đồ. Vui lòng thử lại.")
                user_data["balance"] -= total_sell_price 
                save_data(data) 
                return
        
        save_data(data)
        await try_send(ctx, content=f"{ICON_SUCCESS} Bạn đã bán thành công **{parsed_quantity} {item_name_display}** và nhận được **{total_sell_price:,}** {CURRENCY_SYMBOL}!")

    @commands.command(name='inventory', aliases=['inv', 'items', 'i'])
    async def inventory(self, ctx: commands.Context, user: nextcord.Member = None):
        """Hiển thị túi đồ (các vật phẩm đang sở hữu) của bạn hoặc người dùng khác."""
        target_user = user or ctx.author
        data = get_user_data(ctx.guild.id, target_user.id)
        guild_id_str = str(ctx.guild.id)
        user_id_str = str(target_user.id)
        user_specific_data = data.get(guild_id_str, {}).get(user_id_str, {})

        if user_id_str == "config" or not isinstance(user_specific_data, dict):
            await try_send(ctx, content=f"{ICON_ERROR} Lỗi: Không tìm thấy dữ liệu túi đồ cho {target_user.mention}.")
            return

        inv_list = user_specific_data.get("inventory", [])
        if not isinstance(inv_list, list):
            inv_list = []

        embed = nextcord.Embed(title=f"{ICON_INVENTORY} Túi Đồ - {target_user.name} 🎒", color=nextcord.Color.green()) # Thêm icon

        if not inv_list:
            embed.description = "Túi đồ trống trơn."
        else:
            item_counts = {}
            for item_id_in_inv in inv_list:
                item_counts[item_id_in_inv] = item_counts.get(item_id_in_inv, 0) + 1
            
            description_parts = []
            if item_counts:
                for item_id, count in item_counts.items():
                    item_display_name = SHOP_ITEMS.get(item_id, {}).get("name", item_id.replace("_", " ").capitalize())
                    item_price_info = SHOP_ITEMS.get(item_id, {})
                    buy_price = item_price_info.get("price", 0)
                    sell_price = item_price_info.get("sell_price")
                    
                    price_str = f"(Mua: {buy_price:,}"
                    if sell_price is not None:
                        price_str += f" | Bán: {sell_price:,}"
                    price_str += f" {CURRENCY_SYMBOL})"
                    
                    description_parts.append(f"- {item_display_name} (x{count}) {price_str}")
                embed.description = "\n".join(description_parts)
            else:
                 embed.description = "Túi đồ có vẻ trống hoặc có lỗi khi đọc vật phẩm."
            
        await try_send(ctx, embed=embed)

def setup(bot: commands.Bot):
    bot.add_cog(ShopCog(bot))

