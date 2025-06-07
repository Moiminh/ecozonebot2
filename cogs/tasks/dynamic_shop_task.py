# bot/cogs/tasks/dynamic_shop_task.py
import nextcord
from nextcord.ext import commands, tasks
import random
import logging

from core.database import load_economy_data, save_economy_data
from core.config import SHOP_ITEMS

logger = logging.getLogger(__name__)

class DynamicShopTaskCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.restock_and_update_prices.start()
        logger.info("DynamicShopTaskCog (v2) initialized and task started.")

    def cog_unload(self):
        self.restock_and_update_prices.cancel()
        logger.info("DynamicShopTaskCog unloaded and task cancelled.")

    @tasks.loop(minutes=30)
    async def restock_and_update_prices(self):
        """
        Tác vụ chạy nền để tự động restock và cập nhật giá của shop toàn cục.
        """
        logger.info("Dynamic Shop Task: Running...")
        
        try:
            economy_data = load_economy_data()
            global_shop_stock = economy_data.setdefault("global_shop_stock", {})

            # Lặp qua tất cả các vật phẩm được định nghĩa trong config
            for item_id, item_details in SHOP_ITEMS.items():
                
                # --- Xử lý Restock ---
                item_stock = global_shop_stock.setdefault(item_id, {
                    "current_stock": 0,
                    "max_stock": item_details.get("max_stock", 20), # Lấy max_stock từ config hoặc mặc định 20
                    "base_price": item_details.get("price", 0)
                })
                
                current_stock = item_stock.get("current_stock", 0)
                max_stock = item_stock.get("max_stock", 20)
                
                if current_stock < max_stock:
                    # Thêm một lượng ngẫu nhiên (ví dụ: 1 đến 5)
                    amount_to_add = random.randint(1, 5)
                    new_stock = min(current_stock + amount_to_add, max_stock)
                    item_stock["current_stock"] = new_stock
                    logger.debug(f"Restocked {item_id}: {current_stock} -> {new_stock} (Max: {max_stock})")

                # --- Xử lý Biến động giá ---
                base_price = item_stock.get("base_price", item_details.get("price", 0))
                # Thay đổi giá trong khoảng -5% đến +5%
                price_fluctuation = random.uniform(-0.05, 0.05)
                new_price = round(base_price * (1 + price_fluctuation))
                
                # Đảm bảo giá không bị giảm quá 20% hoặc tăng quá 20% so với giá gốc trong config
                original_price = item_details.get("price", 0)
                min_allowed_price = round(original_price * 0.8)
                max_allowed_price = round(original_price * 1.2)
                
                final_price = max(min_allowed_price, min(new_price, max_allowed_price))
                
                # Cập nhật lại giá trong SHOP_ITEMS của config để lệnh !shop hiển thị đúng
                # Lưu ý: Việc này chỉ thay đổi giá trị trong bộ nhớ, không ghi lại vào file config.py
                SHOP_ITEMS[item_id]["price"] = final_price 
                logger.debug(f"Price updated for {item_id}: {base_price} -> {final_price}")

            save_economy_data(economy_data)
            logger.info("Dynamic Shop Task: Finished and data saved.")

        except Exception as e:
            logger.error(f"Error in Dynamic Shop Task: {e}", exc_info=True)

    @restock_and_update_prices.before_loop
    async def before_restock_task(self):
        await self.bot.wait_until_ready() # Đợi bot sẵn sàng rồi mới chạy task

def setup(bot: commands.Bot):
    bot.add_cog(DynamicShopTaskCog(bot))
