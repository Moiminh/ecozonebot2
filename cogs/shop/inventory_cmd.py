# bot/cogs/shop/inventory_cmd.py
import nextcord
from nextcord.ext import commands

# Import các thành phần cần thiết từ package 'core'
from core.database import get_user_data
from core.utils import try_send
from core.config import CURRENCY_SYMBOL, SHOP_ITEMS # Cần SHOP_ITEMS để lấy tên và giá hiển thị
from core.icons import ICON_INVENTORY, ICON_ERROR # Đảm bảo các icon này có trong core/icons.py

class InventoryCommandCog(commands.Cog, name="Inventory Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='inventory', aliases=['inv', 'items', 'i'])
    async def inventory(self, ctx: commands.Context, user: nextcord.Member = None):
        """Hiển thị túi đồ (các vật phẩm đang sở hữu) của bạn hoặc người dùng khác."""
        target_user = user or ctx.author
        data = get_user_data(ctx.guild.id, target_user.id)
        
        guild_id_str = str(ctx.guild.id) # Không thực sự dùng guild_id_str ở đây nhưng giữ cho nhất quán
        user_id_str = str(target_user.id)
        user_specific_data = data.get(guild_id_str, {}).get(user_id_str, {})

        if user_id_str == "config" or not isinstance(user_specific_data, dict):
            await try_send(ctx, content=f"{ICON_ERROR} Lỗi: Không tìm thấy dữ liệu túi đồ cho {target_user.mention}.")
            return

        inv_list = user_specific_data.get("inventory", [])
        if not isinstance(inv_list, list): # Đảm bảo inv_list là list
            inv_list = []

        embed = nextcord.Embed(title=f"{ICON_INVENTORY} Túi Đồ của {target_user.display_name}", color=nextcord.Color.green())

        if not inv_list:
            embed.description = "Túi đồ trống trơn."
        else:
            item_counts = {}
            for item_id_in_inv in inv_list:
                item_counts[item_id_in_inv] = item_counts.get(item_id_in_inv, 0) + 1
            
            description_parts = []
            if item_counts:
                for item_id, count in item_counts.items():
                    # Lấy tên hiển thị từ SHOP_ITEMS nếu có, nếu không thì dùng item_id đã chuẩn hóa
                    item_details = SHOP_ITEMS.get(item_id, {}) # Lấy thông tin chi tiết của vật phẩm
                    item_display_name = item_details.get("name", item_id.replace("_", " ").capitalize()) # Ưu tiên tên 'name' nếu có trong SHOP_ITEMS
                    
                    # Lấy thông tin giá để hiển thị (tùy chọn)
                    buy_price = item_details.get("price")
                    sell_price = item_details.get("sell_price")
                    
                    price_info_parts = []
                    if buy_price is not None:
                        price_info_parts.append(f"Mua: {buy_price:,}")
                    if sell_price is not None:
                        price_info_parts.append(f"Bán: {sell_price:,}")
                    
                    price_str = ""
                    if price_info_parts:
                        price_str = f" ({' | '.join(price_info_parts)} {CURRENCY_SYMBOL})"
                    
                    description_parts.append(f"- {item_display_name} (x{count}) {price_str}")
                
                embed.description = "\n".join(description_parts) if description_parts else "Túi đồ trống trơn hoặc có lỗi khi đọc vật phẩm."
            else: 
                 embed.description = "Túi đồ có vẻ trống hoặc có lỗi khi đọc vật phẩm."
            
        await try_send(ctx, embed=embed)

def setup(bot: commands.Bot):
    bot.add_cog(InventoryCommandCog(bot))
