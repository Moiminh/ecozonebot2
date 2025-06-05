# bot/cogs/shop/inventory_cmd.py
import nextcord
from nextcord.ext import commands
import logging 

from core.database import get_user_data
from core.utils import try_send
from core.config import CURRENCY_SYMBOL, SHOP_ITEMS 
from core.icons import ICON_INVENTORY, ICON_ERROR, ICON_INFO

logger = logging.getLogger(__name__)

class InventoryCommandCog(commands.Cog, name="Inventory Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"InventoryCommandCog initialized.") # Giữ debug cho init Cog

    @commands.command(name='inventory', aliases=['inv', 'items', 'i'])
    async def inventory(self, ctx: commands.Context, user: nextcord.Member = None):
        """Hiển thị túi đồ (các vật phẩm đang sở hữu) của bạn hoặc người dùng khác."""
        target_user = user or ctx.author
        logger.debug(f"Lệnh 'inventory' được gọi bởi {ctx.author.name} cho target {target_user.name} (ID: {target_user.id}) tại guild {ctx.guild.id}.")
        
        data = get_user_data(ctx.guild.id, target_user.id)
        
        guild_id_str = str(ctx.guild.id)
        user_id_str = str(target_user.id)
        user_specific_data = data.get(guild_id_str, {}).get(user_id_str, {})

        if user_id_str == "config" or not isinstance(user_specific_data, dict):
            logger.warning(f"Dữ liệu túi đồ không hợp lệ cho user {user_id_str} guild {guild_id_str} khi gọi lệnh 'inventory'. Data: {user_specific_data}")
            await try_send(ctx, content=f"{ICON_ERROR} Lỗi: Không tìm thấy dữ liệu túi đồ cho {target_user.mention}.")
            return

        inv_list = user_specific_data.get("inventory", [])
        if not isinstance(inv_list, list):
            logger.warning(f"Inventory của user {user_id_str} guild {guild_id_str} không phải là list: {inv_list}. Reset thành list rỗng.")
            inv_list = []

        embed = nextcord.Embed(title=f"{ICON_INVENTORY} Túi Đồ của {target_user.display_name}", color=nextcord.Color.green())

        item_summary_for_log = "trống" # Chuẩn bị tóm tắt cho log
        if not inv_list:
            embed.description = "Túi đồ trống trơn."
        else:
            item_counts = {}
            for item_id_in_inv in inv_list:
                item_counts[item_id_in_inv] = item_counts.get(item_id_in_inv, 0) + 1
            
            description_parts = []
            log_summary_parts = [] # Để tạo tóm tắt cho log
            if item_counts:
                for item_id, count in item_counts.items():
                    item_details = SHOP_ITEMS.get(item_id, {}) 
                    item_display_name = item_details.get("name", item_id.replace("_", " ").capitalize())
                    
                    buy_price = item_details.get("price")
                    sell_price = item_details.get("sell_price")
                    
                    price_info_parts = []
                    if buy_price is not None: price_info_parts.append(f"Mua: {buy_price:,}")
                    if sell_price is not None: price_info_parts.append(f"Bán: {sell_price:,}")
                    
                    price_str = ""
                    if price_info_parts: price_str = f" ({' | '.join(price_info_parts)} {CURRENCY_SYMBOL})"
                    
                    description_parts.append(f"- {item_display_name} (x{count}) {price_str}")
                    log_summary_parts.append(f"{item_display_name}(x{count})") # Tóm tắt cho log
                
                embed.description = "\n".join(description_parts) if description_parts else "Túi đồ trống trơn hoặc có lỗi khi đọc vật phẩm."
                if log_summary_parts: item_summary_for_log = ", ".join(log_summary_parts)

            else: 
                 embed.description = f"{ICON_INFO} Túi đồ có vẻ trống hoặc có lỗi khi đọc vật phẩm."
                 logger.debug(f"Túi đồ của {target_user.name} có item_counts rỗng dù inv_list không rỗng. inv_list: {inv_list}")
            
        await try_send(ctx, embed=embed)
        
        # --- THAY ĐỔI Ở ĐÂY: Chuyển từ debug sang info cho hành động xem inventory ---
        if ctx.author.id == target_user.id:
            logger.info(f"User {ctx.author.display_name} ({ctx.author.id}) đã xem túi đồ của chính mình. Nội dung: {item_summary_for_log}.")
        else:
            logger.info(f"User {ctx.author.display_name} ({ctx.author.id}) đã xem túi đồ của {target_user.display_name} ({target_user.id}). Nội dung: {item_summary_for_log}.")
        # --- KẾT THÚC THAY ĐỔI ---
        # logger.debug(f"Lệnh 'inventory' cho {target_user.name} đã hiển thị xong.") # Dòng debug cũ có thể giữ hoặc xóa

def setup(bot: commands.Bot):
    bot.add_cog(InventoryCommandCog(bot))
