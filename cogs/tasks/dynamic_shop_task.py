# bot/cogs/tasks/dynamic_shop_task.py
import nextcord
from nextcord.ext import commands, tasks
import random
import logging
import os

logger = logging.getLogger(__name__)

class DynamicShopTaskCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_type = os.getenv("DATABASE_TYPE", "json").lower()
        if self.db_type == 'sqlite':
            self.restock_and_update_prices_sqlite.start()
            logger.info("DynamicShopTaskCog initialized and task started (SQLite mode).")
        else:
            # Có thể giữ lại logic JSON cũ ở đây nếu muốn
            logger.info("DynamicShopTaskCog initialized, task is INACTIVE (JSON mode).")


    def cog_unload(self):
        if self.db_type == 'sqlite' and self.restock_and_update_prices_sqlite.is_running():
            self.restock_and_update_prices_sqlite.cancel()
            logger.info("DynamicShopTaskCog unloaded and task cancelled.")

    @tasks.loop(minutes=30)
    async def restock_and_update_prices_sqlite(self):
        """Tác vụ chạy nền để restock và cập nhật giá shop, dùng CSDL SQLite."""
        logger.info("Dynamic Shop Task (SQLite): Running...")
        
        try:
            conn = self.bot.db.get_db_connection()
            # Lấy tất cả vật phẩm từ CSDL để xử lý
            items = conn.execute("SELECT * FROM items WHERE price > 0").fetchall()

            for item in items:
                item_id = item['item_id']
                current_stock = item['current_stock']
                max_stock = item['max_stock']
                
                # --- Xử lý Restock ---
                if current_stock < max_stock:
                    amount_to_add = random.randint(1, 5)
                    new_stock = min(current_stock + amount_to_add, max_stock)
                    conn.execute("UPDATE items SET current_stock = ? WHERE item_id = ?", (new_stock, item_id))
                    logger.debug(f"Restocked {item_id}: {current_stock} -> {new_stock} (Max: {max_stock})")

                # --- Xử lý Biến động giá ---
                # Lấy giá gốc từ item_definitions để làm giá tham chiếu
                base_price_from_def = self.bot.item_definitions.get(item_id, {}).get("price", item['price'])
                price_fluctuation = random.uniform(-0.05, 0.05)
                new_price = round(item['price'] * (1 + price_fluctuation))
                
                min_allowed_price = round(base_price_from_def * 0.8)
                max_allowed_price = round(base_price_from_def * 1.2)
                
                final_price = max(min_allowed_price, min(new_price, max_allowed_price))
                
                conn.execute("UPDATE items SET price = ? WHERE item_id = ?", (final_price, item_id))
                
                # Cập nhật lại cache trong bot để các lệnh khác dùng ngay
                if item_id in self.bot.item_definitions:
                    self.bot.item_definitions[item_id]["price"] = final_price

            conn.commit()
            conn.close()
            logger.info("Dynamic Shop Task (SQLite): Finished.")

        except Exception as e:
            logger.error(f"Error in Dynamic Shop Task (SQLite): {e}", exc_info=True)

    @restock_and_update_prices_sqlite.before_loop
    async def before_restock_task(self):
        await self.bot.wait_until_ready()

def setup(bot: commands.Bot):
    bot.add_cog(DynamicShopTaskCog(bot))
