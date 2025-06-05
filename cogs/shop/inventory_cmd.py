# bot/cogs/shop/inventory_cmd.py
import nextcord
from nextcord.ext import commands
import logging

from core.database import (
    load_economy_data,
    get_or_create_global_user_profile,
    save_economy_data # Cần để lưu user mới nếu được tạo
)
from core.utils import try_send
from core.config import CURRENCY_SYMBOL, SHOP_ITEMS # Cần SHOP_ITEMS để lấy tên hiển thị
from core.icons import ICON_INVENTORY, ICON_ERROR, ICON_INFO

logger = logging.getLogger(__name__)

class InventoryCommandCog(commands.Cog, name="Inventory Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"InventoryCommandCog initialized.")

    @commands.command(name='inventory', aliases=['inv', 'items', 'i'])
    async def inventory(self, ctx: commands.Context, user: nextcord.Member = None):
        target_user = user or ctx.author
        guild_name_for_log = ctx.guild.name if ctx.guild else "DM"
        guild_id_for_log = ctx.guild.id if ctx.guild else "N/A"

        logger.debug(f"Lệnh 'inventory' được gọi bởi {ctx.author.name} cho target {target_user.name} (ID: {target_user.id}) tại context guild '{guild_name_for_log}' ({guild_id_for_log}).")
        
        try:
            economy_data = load_economy_data()
            target_user_profile = get_or_create_global_user_profile(economy_data, target_user.id)
            
            # Lấy túi đồ toàn cục
            inv_global_list = target_user_profile.get("inventory_global", [])
            if not isinstance(inv_global_list, list):
                logger.warning(f"Inventory global của user {target_user.id} không phải là list: {inv_global_list}. Reset thành list rỗng.")
                inv_global_list = []
                target_user_profile["inventory_global"] = inv_global_list # Sửa trực tiếp vào profile
                # Không cần save_economy_data ngay ở đây, sẽ save ở cuối nếu có thay đổi từ get_or_create...

            # (Trong tương lai, nếu có inventory_local, bạn sẽ lấy ở đây)
            # user_server_data = get_or_create_user_server_data(target_user_profile, guild_id_for_log)
            # inv_local_list = user_server_data.get("inventory_local", [])

            embed = nextcord.Embed(title=f"{ICON_INVENTORY} Túi Đồ Toàn Cục của {target_user.display_name}", color=nextcord.Color.green())

            item_summary_for_log = "trống"
            if not inv_global_list: # Hiện tại chỉ hiển thị inv_global
                embed.description = "Túi đồ toàn cục trống trơn."
                logger.debug(f"Túi đồ toàn cục của {target_user.name} trống.")
            else:
                item_counts = {}
                for item_id_in_inv in inv_global_list:
                    item_counts[item_id_in_inv] = item_counts.get(item_id_in_inv, 0) + 1
                
                description_parts = []
                log_summary_parts = [] 
                if item_counts:
                    for item_id, count in item_counts.items():
                        item_details_from_master = config.SHOP_ITEMS.get(item_id, {}) # Lấy thông tin từ SHOP_ITEMS gốc trong config
                        item_display_name = item_details_from_master.get("description", item_id.replace("_", " ").capitalize()) # Ưu tiên description làm tên hiển thị
                        
                        # Lấy thông tin giá từ SHOP_ITEMS (master list)
                        buy_price = item_details_from_master.get("price")
                        sell_price = item_details_from_master.get("sell_price")
                        
                        price_info_parts = []
                        if buy_price is not None: price_info_parts.append(f"Mua gốc: {buy_price:,}") # Giá mua gốc
                        if sell_price is not None: price_info_parts.append(f"Bán: {sell_price:,}")
                        
                        price_str = ""
                        if price_info_parts: price_str = f" ({' | '.join(price_info_parts)} {CURRENCY_SYMBOL})"
                        
                        description_parts.append(f"- {item_display_name} (x{count}) {price_str}")
                        log_summary_parts.append(f"{item_display_name}(x{count})")
                    
                    embed.description = "\n".join(description_parts) if description_parts else "Túi đồ toàn cục trống trơn hoặc có lỗi."
                    if log_summary_parts: item_summary_for_log = ", ".join(log_summary_parts)
                else: 
                     embed.description = f"{ICON_INFO} Túi đồ toàn cục có vẻ trống hoặc có lỗi khi đọc vật phẩm."
                     logger.debug(f"Túi đồ toàn cục của {target_user.name} có item_counts rỗng dù inv_global_list không rỗng. inv_list: {inv_global_list}")
            
            await try_send(ctx, embed=embed)
            
            # Log hành động xem inventory
            log_message_action = f"User {ctx.author.display_name} ({ctx.author.id}) đã xem túi đồ toàn cục của "
            if ctx.author.id == target_user.id:
                log_message_action += "chính mình."
            else:
                log_message_action += f"{target_user.display_name} ({target_user.id})."
            log_message_action += f" Nội dung tóm tắt: {item_summary_for_log}. (Lệnh gọi từ guild '{guild_name_for_log}')"
            logger.info(log_message_action) # Ghi vào player_actions.log

            # Lưu lại economy_data nếu get_or_create_global_user_profile có thể đã tạo mới user
            # hoặc sửa lỗi inventory_global không phải list
            save_economy_data(economy_data)

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'inventory' cho user {target_user.name} ({target_user.id}) tại guild '{guild_name_for_log}': {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi không xác định khi xem túi đồ của {target_user.mention}.")

def setup(bot: commands.Bot):
    bot.add_cog(InventoryCommandCog(bot))
