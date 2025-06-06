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
import nextcord
from nextcord.ext import commands
import logging

from core.database import (
    load_economy_data,
    get_or_create_global_user_profile,
    get_or_create_user_server_data,
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
        logger.debug(f"BuyCommandCog initialized for Ecoworld Economy.")

    @commands.command(name='buy')
    async def buy(self, ctx: commands.Context, item_name: str, quantity: int = 1):
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server.")
            return

        author_id = ctx.author.id
        guild_id = ctx.guild.id
        
        logger.debug(f"Lệnh 'buy' được gọi bởi {ctx.author.name} ({author_id}) với item_name='{item_name}', quantity={quantity} tại guild '{ctx.guild.name}' ({guild_id}).")

        if quantity <= 0:
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
             await try_send(ctx, content=f"{ICON_WARNING} Vui lòng nhập tên vật phẩm bạn muốn mua.")
             return

        if parsed_quantity <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Số lượng mua phải lớn hơn 0.")
            return

        if item_id_to_buy not in MASTER_ITEM_LIST:
            await try_send(ctx, content=f"{ICON_ERROR} Vật phẩm `{item_name_display}` không tồn tại trong danh mục cửa hàng.")
            return
        
        economy_data = load_economy_data()
        user_profile = get_or_create_global_user_profile(economy_data, author_id)
        user_server_data = get_or_create_user_server_data(user_profile, guild_id)
        shop_stock = get_or_create_global_shop_stock(economy_data)
        item_stock_details = get_shop_item_details_from_stock(shop_stock, item_id_to_buy)

        item_master_details = MASTER_ITEM_LIST[item_id_to_buy]
        price_per_item = item_master_details["price"]
        total_price = price_per_item * parsed_quantity

        if item_stock_details is None:
            await try_send(ctx, content=f"{ICON_INFO} Rất tiếc, vật phẩm `{item_name_display}` hiện không có bán trong cửa hàng toàn cục.")
            return

        current_stock = item_stock_details.get("current_stock", 0)
        if current_stock < parsed_quantity:
             await try_send(ctx, content=f"{ICON_ERROR} Rất tiếc, cửa hàng toàn cục chỉ còn **{current_stock}** {item_name_display}. Bạn không thể mua {parsed_quantity} cái.")
             return
        
        local_balance = user_server_data.get("local_balance", {})
        earned_amount = local_balance.get("earned", 0)
        admin_added_amount = local_balance.get("admin_added", 0)
        total_local_balance = earned_amount + admin_added_amount

        if total_local_balance < total_price:
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không đủ tiền trong Ví Local! Bạn cần **{total_price:,}** {CURRENCY_SYMBOL} nhưng chỉ có **{total_local_balance:,}** {CURRENCY_SYMBOL}.")
            return
            
        admin_money_spent = min(admin_added_amount, total_price)
        earned_money_spent = total_price - admin_money_spent
        
        user_server_data["local_balance"]["admin_added"] -= admin_money_spent
        user_server_data["local_balance"]["earned"] -= earned_money_spent
        
        item_source = "admin_added" if admin_money_spent > 0 else "earned"
        
        if item_source == "admin_added":
            inventory_to_add = user_server_data.setdefault("inventory_local", [])
            destination_inventory_name = "Túi Đồ Local"
        else: # item_source == "earned"
            inventory_to_add = user_profile.setdefault("inventory_global", [])
            destination_inventory_name = "Túi Đồ Toàn Cục (GOL)"

        for _ in range(parsed_quantity):
            inventory_to_add.append({"item_id": item_id_to_buy, "source": item_source})
        
        update_shop_item_stock(shop_stock, item_id_to_buy, -parsed_quantity)
        
        save_economy_data(economy_data)

        logger.info(f"Guild: {ctx.guild.name} ({guild_id}) - User: {ctx.author.display_name} ({author_id}) đã mua {parsed_quantity} x '{item_name_display}'. "
                    f"Giá: {total_price:,}. Tiêu từ 'admin_added': {admin_money_spent:,}, từ 'earned': {earned_money_spent:,}. "
                    f"Vật phẩm được thêm vào: {destination_inventory_name}.")
        
        await try_send(ctx, content=f"{ICON_SUCCESS} Bạn đã mua thành công **{parsed_quantity} {item_name_display}** với tổng giá **{total_price:,}** {CURRENCY_SYMBOL}! "
                                    f"Vật phẩm đã được thêm vào **{destination_inventory_name}** của bạn.")

def setup(bot: commands.Bot):
    bot.add_cog(BuyCommandCog(bot))
với tổng giá {total_price:,} {CURRENCY_SYMBOL}. "
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
