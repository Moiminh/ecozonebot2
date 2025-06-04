# bot/cogs/shop.py
import nextcord
from nextcord.ext import commands
from typing import Optional # Để dùng cho quantity nếu muốn có giá trị mặc định

# Import các thành phần cần thiết từ package 'core'
from core.database import get_user_data, save_data
from core.utils import try_send
from core.config import CURRENCY_SYMBOL, SHOP_ITEMS, COMMAND_PREFIX

class ShopCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='shop', aliases=['store'])
    async def shop(self, ctx: commands.Context):
        """Hiển thị các vật phẩm đang được bán trong cửa hàng.
        Sử dụng lệnh `buy <số_lượng> <tên_vật_phẩm>` để mua.
        Sử dụng lệnh `sell <số_lượng> <tên_vật_phẩm>` để bán.
        """
        embed = nextcord.Embed(
            title="🏪 Cửa Hàng 🏪",
            description=f"Mua: `{COMMAND_PREFIX}buy <số_lượng> <tên_vật_phẩm>`\nBán: `{COMMAND_PREFIX}sell <số_lượng> <tên_vật_phẩm>`",
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
    async def buy(self, ctx: commands.Context, quantity: int, *, item_name: str):
        """Mua một hoặc nhiều vật phẩm từ cửa hàng.
        Ví dụ: !buy 2 laptop
        """
        if quantity <= 0:
            await try_send(ctx, content="Số lượng mua phải lớn hơn 0.")
            return

        item_id_to_buy = item_name.lower().strip().replace(" ", "_")

        if item_id_to_buy not in SHOP_ITEMS:
            await try_send(ctx, content=f"Vật phẩm `{item_name}` không tồn tại trong cửa hàng.")
            return
        
        item_details = SHOP_ITEMS[item_id_to_buy]
        price_per_item = item_details["price"]
        total_price = price_per_item * quantity
        
        data = get_user_data(ctx.guild.id, ctx.author.id)
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]
        item_name_display = item_id_to_buy.replace("_", " ").capitalize()

        if user_data.get("balance", 0) < total_price:
            await try_send(ctx, content=f"Bạn không đủ tiền! Bạn cần **{total_price:,}** {CURRENCY_SYMBOL} để mua {quantity} {item_name_display}. (Ví bạn có: {user_data.get('balance', 0):,} {CURRENCY_SYMBOL})")
            return
            
        user_data["balance"] -= total_price
        if "inventory" not in user_data or not isinstance(user_data["inventory"], list):
            user_data["inventory"] = []
        
        for _ in range(quantity): # Thêm vật phẩm vào túi đồ quantity lần
            user_data["inventory"].append(item_id_to_buy)
        
        save_data(data)
        await try_send(ctx, content=f"🛍️ Bạn đã mua thành công **{quantity} {item_name_display}** với tổng giá **{total_price:,}** {CURRENCY_SYMBOL}! Chúng đã được thêm vào túi đồ (`{COMMAND_PREFIX}inv`).")

    @commands.command(name='sell')
    async def sell(self, ctx: commands.Context, quantity: int, *, item_name: str):
        """Bán một hoặc nhiều vật phẩm từ túi đồ của bạn.
        Ví dụ: !sell 2 laptop
        """
        if quantity <= 0:
            await try_send(ctx, content="Số lượng bán phải lớn hơn 0.")
            return

        item_id_to_sell = item_name.lower().strip().replace(" ", "_")
        item_name_display = item_id_to_sell.replace("_", " ").capitalize()

        if item_id_to_sell not in SHOP_ITEMS:
            await try_send(ctx, content=f"Vật phẩm `{item_name_display}` không nằm trong danh mục có thể bán của cửa hàng.")
            return

        item_details = SHOP_ITEMS[item_id_to_sell]
        sell_price_per_item = item_details.get("sell_price")

        if sell_price_per_item is None:
            await try_send(ctx, content=f"Vật phẩm `{item_name_display}` này không thể bán lại.")
            return
            
        data = get_user_data(ctx.guild.id, ctx.author.id)
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]
        
        inventory_list = user_data.get("inventory", [])
        if not isinstance(inventory_list, list):
            inventory_list = []
            user_data["inventory"] = inventory_list

        # Đếm số lượng vật phẩm người dùng có
        current_item_count = inventory_list.count(item_id_to_sell)

        if current_item_count < quantity:
            await try_send(ctx, content=f"Bạn không có đủ **{quantity} {item_name_display}** để bán. Bạn chỉ có {current_item_count}.")
            return
        
        total_sell_price = sell_price_per_item * quantity
        user_data["balance"] = user_data.get("balance", 0) + total_sell_price
        
        for _ in range(quantity): # Xóa vật phẩm khỏi túi đồ quantity lần
            try:
                inventory_list.remove(item_id_to_sell)
            except ValueError:
                # Lỗi này không nên xảy ra nếu logic đếm ở trên đúng
                # nhưng thêm vào để phòng trường hợp bất thường
                await try_send(ctx, content=f"Lỗi khi cố gắng xóa {item_name_display} khỏi túi đồ. Vui lòng thử lại.")
                # Có thể cần hoàn lại tiền nếu đã cộng ở trên mà xóa lỗi
                user_data["balance"] -= total_sell_price # Hoàn tiền nếu xóa lỗi
                save_data(data) # Lưu trạng thái đã hoàn tiền
                return
        
        # user_data["inventory"] đã được cập nhật vì inventory_list là một tham chiếu đến list trong user_data
        save_data(data)
        await try_send(ctx, content=f"💰 Bạn đã bán thành công **{quantity} {item_name_display}** và nhận được **{total_sell_price:,}** {CURRENCY_SYMBOL}!")

    @commands.command(name='inventory', aliases=['inv', 'items', 'i'])
    async def inventory(self, ctx: commands.Context, user: nextcord.Member = None):
        """Hiển thị túi đồ (các vật phẩm đang sở hữu) của bạn hoặc người dùng khác."""
        target_user = user or ctx.author
        data = get_user_data(ctx.guild.id, target_user.id)
        guild_id_str = str(ctx.guild.id)
        user_id_str = str(target_user.id)
        user_specific_data = data.get(guild_id_str, {}).get(user_id_str, {})

        if user_id_str == "config" or not isinstance(user_specific_data, dict):
            await try_send(ctx, content=f"Lỗi: Không tìm thấy dữ liệu túi đồ cho {target_user.mention}.")
            return

        inv_list = user_specific_data.get("inventory", [])
        if not isinstance(inv_list, list):
            inv_list = []

        embed = nextcord.Embed(title=f"🎒 Túi Đồ - {target_user.name} 🎒", color=nextcord.Color.green())

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
            else: # Trường hợp inv_list không rỗng nhưng item_counts lại rỗng (ít khả năng)
                 embed.description = "Túi đồ có vẻ trống hoặc có lỗi khi đọc vật phẩm."
            
        await try_send(ctx, embed=embed)

# Hàm setup để bot có thể load cog này
def setup(bot: commands.Bot):
    bot.add_cog(ShopCog(bot))
