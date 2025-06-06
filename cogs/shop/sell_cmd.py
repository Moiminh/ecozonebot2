import nextcord
from nextcord.ext import commands
import logging

from core.database import (
    load_economy_data,
    get_or_create_global_user_profile,
    get_or_create_user_server_data,
    save_economy_data
)
from core.utils import try_send
from core.config import CURRENCY_SYMBOL, SHOP_ITEMS as MASTER_ITEM_LIST, COMMAND_PREFIX
from core.icons import ICON_SUCCESS, ICON_ERROR, ICON_WARNING, ICON_INFO, ICON_MONEY_BAG

logger = logging.getLogger(__name__)

class SellCommandCog(commands.Cog, name="Sell Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"SellCommandCog initialized for Ecoworld Economy.")

    @commands.command(name='sell')
    async def sell(self, ctx: commands.Context, item_name: str, quantity: int = 1):
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server.")
            return

        author_id = ctx.author.id
        guild_id = ctx.guild.id

        logger.debug(f"Lệnh 'sell' được gọi bởi {ctx.author.name} ({author_id}) với item_name='{item_name}', quantity={quantity} tại guild '{ctx.guild.name}' ({guild_id}).")

        if quantity <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Số lượng bán phải lớn hơn 0.")
            return

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
             await try_send(ctx, content=f"{ICON_WARNING} Vui lòng nhập tên vật phẩm bạn muốn bán.")
             return

        if parsed_quantity <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Số lượng bán phải lớn hơn 0.")
            return

        if item_id_to_sell not in MASTER_ITEM_LIST:
            await try_send(ctx, content=f"{ICON_ERROR} Vật phẩm `{item_name_display}` không nằm trong danh mục có thể bán của cửa hàng.")
            return

        item_master_details = MASTER_ITEM_LIST[item_id_to_sell]
        sell_price_per_item = item_master_details.get("sell_price")

        if sell_price_per_item is None:
            await try_send(ctx, content=f"{ICON_INFO} Vật phẩm `{item_name_display}` này không thể bán lại.")
            return
            
        economy_data = load_economy_data()
        global_profile = get_or_create_global_user_profile(economy_data, author_id)
        server_data = get_or_create_user_server_data(global_profile, guild_id)

        inv_global_list = global_profile.get("inventory_global", [])
        inv_local_list = server_data.get("inventory_local", [])

        count_in_global = sum(1 for item in inv_global_list if isinstance(item, dict) and item.get("item_id") == item_id_to_sell)
        count_in_local = sum(1 for item in inv_local_list if isinstance(item, dict) and item.get("item_id") == item_id_to_sell)
        total_item_count = count_in_global + count_in_local

        if total_item_count < parsed_quantity:
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ **{parsed_quantity} {item_name_display}** để bán. Bạn chỉ có tổng cộng {total_item_count} cái (ở cả Kho Local và Global).")
            return
        
        items_removed_from_local = 0
        items_to_remove = parsed_quantity
        
        temp_inv_local = list(inv_local_list)
        for item_data in reversed(temp_inv_local):
            if items_to_remove == 0: break
            if isinstance(item_data, dict) and item_data.get("item_id") == item_id_to_sell:
                inv_local_list.remove(item_data)
                items_to_remove -= 1
                items_removed_from_local += 1

        items_removed_from_global = 0
        if items_to_remove > 0:
            temp_inv_global = list(inv_global_list)
            for item_data in reversed(temp_inv_global):
                if items_to_remove == 0: break
                if isinstance(item_data, dict) and item_data.get("item_id") == item_id_to_sell:
                    inv_global_list.remove(item_data)
                    items_to_remove -= 1
                    items_removed_from_global += 1
        
        total_sell_price = sell_price_per_item * parsed_quantity
        
        original_local_earned = server_data["local_balance"].get("earned", 0)
        server_data["local_balance"]["earned"] = original_local_earned + total_sell_price
        
        save_economy_data(economy_data)

        logger.info(f"Guild: {ctx.guild.name} ({guild_id}) - User: {ctx.author.display_name} ({author_id}) đã bán {parsed_quantity} x '{item_name_display}'. "
                    f"Nguồn: {items_removed_from_local} từ local, {items_removed_from_global} từ global. "
                    f"Thu về: {total_sell_price:,} {CURRENCY_SYMBOL} vào Ví Local (Earned).")
        
        await try_send(ctx, content=f"{ICON_SUCCESS} Bạn đã bán thành công **{parsed_quantity} {item_name_display}** và nhận được **{total_sell_price:,}** {CURRENCY_SYMBOL} vào Ví Local (Earned)!")

def setup(bot: commands.Bot):
    bot.add_cog(SellCommandCog(bot))
