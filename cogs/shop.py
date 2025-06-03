# bot/cogs/shop.py
import nextcord
from nextcord.ext import commands

# Import các thành phần cần thiết từ package 'core'
from core.database import get_user_data, save_data
from core.utils import try_send
from core.config import CURRENCY_SYMBOL, SHOP_ITEMS, COMMAND_PREFIX

class ShopCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='shop', aliases=['store'])
    async def shop(self, ctx: commands.Context):
        """Hiển thị các vật phẩm đang được bán trong cửa hàng."""
        embed = nextcord.Embed(
            title="🏪 Cửa Hàng 🏪",
            description=f"Sử dụng `{COMMAND_PREFIX}buy <tên_vật_phẩm>` để mua hoặc `{COMMAND_PREFIX}sell <tên_vật_phẩm>` để bán.",
            color=nextcord.Color.orange()
        )
        if not SHOP_ITEMS: # Kiểm tra nếu SHOP_ITEMS rỗng
            embed.description = "Cửa hàng hiện đang trống hoặc đang được cập nhật."
        else:
            for item_id, details in SHOP_ITEMS.items():
                # item_id là key (ví dụ "laptop"), details là dictionary chứa thông tin
                item_name_display = item_id.replace("_", " ").capitalize() # Thay "_" bằng " " và viết hoa chữ đầu
                buy_price_str = f"{details['price']:,}"
                
                sell_price_val = details.get('sell_price') # Dùng .get() để tránh lỗi nếu không có 'sell_price'
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
    async def buy(self, ctx: commands.Context, *, item_name: str): # Dùng * để nhận tất cả các từ sau là item_name
        """Mua một vật phẩm từ cửa hàng."""
        item_id_to_buy = item_name.lower().strip().replace(" ", "_") # Chuẩn hóa tên vật phẩm về dạng key trong SHOP_ITEMS

        if item_id_to_buy not in SHOP_ITEMS:
            await try_send(ctx, content=f"Vật phẩm `{item_name}` không tồn tại trong cửa hàng.")
            return
        
        item_details = SHOP_ITEMS[item_id_to_buy]
        price = item_details["price"]
        
        data = get_user_data(ctx.guild.id, ctx.author.id)
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]

        if user_data.get("balance", 0) < price:
            await try_send(ctx, content=f"Bạn không đủ tiền! Bạn cần **{price:,}** {CURRENCY_SYMBOL} để mua {item_details.get('name', item_id_to_buy.capitalize())}.")
            return
            
        user_data["balance"] -= price
        # Đảm bảo 'inventory' là một list trước khi append
        if "inventory" not in user_data or not isinstance(user_data["inventory"], list):
            user_data["inventory"] = []
        user_data["inventory"].append(item_id_to_buy) # Lưu item_id (key) vào inventory
        
        save_data(data)
        item_name_display = item_id_to_buy.replace("_", " ").capitalize()
        await try_send(ctx, content=f"Bạn đã mua thành công **{item_name_display}** với giá **{price:,}** {CURRENCY_SYMBOL}! Nó đã được thêm vào túi đồ của bạn (`{COMMAND_PREFIX}inv`).")

    @commands.command(name='sell')
    async def sell(self, ctx: commands.Context, *, item_name: str):
        """Bán một vật phẩm từ túi đồ của bạn để lấy tiền."""
        item_id_to_sell = item_name.lower().strip().replace(" ", "_")

        # Kiểm tra xem vật phẩm này có trong SHOP_ITEMS không (để biết giá bán)
        if item_id_to_sell not in SHOP_ITEMS:
            await try_send(ctx, content=f"Không thể bán vật phẩm `{item_name}` này hoặc nó không có trong danh mục cửa hàng.")
            return

        item_details = SHOP_ITEMS[item_id_to_sell]
        sell_price = item_details.get("sell_price") # Dùng .get() để an toàn

        if sell_price is None: # Nếu vật phẩm không có giá bán
            await try_send(ctx, content=f"Vật phẩm `{item_id_to_sell.replace('_', ' ').capitalize()}` này không thể bán lại.")
            return
            
        data = get_user_data(ctx.guild.id, ctx.author.id)
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]
        
        # Đảm bảo inventory tồn tại và là list
        inventory_list = user_data.get("inventory", [])
        if not isinstance(inventory_list, list): # Nếu inventory không phải list (dữ liệu cũ có thể bị lỗi)
            inventory_list = [] # Reset thành list rỗng
            user_data["inventory"] = inventory_list


        if item_id_to_sell not in inventory_list:
            await try_send(ctx, content=f"Bạn không có vật phẩm `{item_id_to_sell.replace('_', ' ').capitalize()}` trong túi đồ.")
            return
            
        user_data["balance"] = user_data.get("balance", 0) + sell_price
        try:
            inventory_list.remove(item_id_to_sell) # Xóa một instance của vật phẩm
        except ValueError:
            # Trường hợp này không nên xảy ra nếu check ở trên đã đúng
            await try_send(ctx, content=f"Lỗi: Không tìm thấy vật phẩm `{item_id_to_sell.replace('_', ' ').capitalize()}` để xóa khỏi túi đồ, dù đã kiểm tra có.")
            return

        # user_data["inventory"] đã được cập nhật vì inventory_list là một tham chiếu
        save_data(data)
        item_name_display = item_id_to_sell.replace("_", " ").capitalize()
        await try_send(ctx, content=f"Bạn đã bán thành công **{item_name_display}** và nhận được **{sell_price:,}** {CURRENCY_SYMBOL}!")

    @commands.command(name='inventory', aliases=['inv', 'items', 'i'])
    async def inventory(self, ctx: commands.Context, user: nextcord.Member = None):
        """Hiển thị túi đồ (các vật phẩm đang sở hữu) của bạn hoặc người dùng khác."""
        target_user = user or ctx.author
        data = get_user_data(ctx.guild.id, target_user.id)
        # Truy cập dữ liệu user cụ thể từ full_data
        guild_id_str = str(ctx.guild.id)
        user_id_str = str(target_user.id)
        user_specific_data = data.get(guild_id_str, {}).get(user_id_str, {})


        if user_id_str == "config" or not isinstance(user_specific_data, dict):
            await try_send(ctx, content=f"Lỗi: Không tìm thấy dữ liệu túi đồ cho {target_user.mention}.")
            return

        inv_list = user_specific_data.get("inventory", []) # Lấy danh sách inventory
        if not isinstance(inv_list, list): # Đảm bảo inv_list là list
            inv_list = []


        embed = nextcord.Embed(title=f"🎒 Túi Đồ - {target_user.name} 🎒", color=nextcord.Color.green())

        if not inv_list:
            embed.description = "Túi đồ trống trơn."
        else:
            # Đếm số lượng mỗi loại vật phẩm
            item_counts = {}
            for item_id_in_inv in inv_list:
                item_counts[item_id_in_inv] = item_counts.get(item_id_in_inv, 0) + 1
            
            description_parts = []
            for item_id, count in item_counts.items():
                # Lấy tên hiển thị từ SHOP_ITEMS nếu có, nếu không thì dùng item_id đã chuẩn hóa
                item_display_name = SHOP_ITEMS.get(item_id, {}).get("name", item_id.replace("_", " ").capitalize())
                description_parts.append(f"- {item_display_name} (x{count})")
            
            embed.description = "\n".join(description_parts) if description_parts else "Túi đồ trống trơn."
            
        await try_send(ctx, embed=embed)

# Hàm setup để bot có thể load cog này
def setup(bot: commands.Bot):
    bot.add_cog(ShopCog(bot))
