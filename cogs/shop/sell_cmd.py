# bot/cogs/shop/sell_cmd.py
import nextcord
from nextcord.ext import commands
import logging
from datetime import date

from core.database import (
    load_economy_data,
    save_economy_data,
    get_or_create_global_user_profile,
    get_or_create_user_local_data
)
from core.utils import try_send
from core.config import (
    SHOP_ITEMS, TAINTED_ITEM_SELL_LIMIT, TAINTED_ITEM_SELL_RATE,
    TAINTED_ITEM_TAX_RATE, FOREIGN_ITEM_SELL_PENALTY
)
from core.icons import (
    ICON_SUCCESS, ICON_ERROR, ICON_WARNING, ICON_INFO,
    ICON_ECOIN, ICON_ECOBIT
)

logger = logging.getLogger(__name__)

class SellCommandCog(commands.Cog, name="Sell Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("SellCommandCog (v3 - Full) initialized.")

    @commands.command(name='sell')
    async def sell(self, ctx: commands.Context, item_id: str, quantity: int = 1):
# bot/cogs/shop/sell_cmd.py
import nextcord
from nextcord.ext import commands
import logging
from datetime import date

from core.database import (
    load_economy_data,
    save_economy_data,
    get_or_create_global_user_profile,
    get_or_create_user_local_data
)
from core.utils import try_send
from core.config import (
    SHOP_ITEMS, TAINTED_ITEM_SELL_LIMIT, TAINTED_ITEM_SELL_RATE,
    TAINTED_ITEM_TAX_RATE, FOREIGN_ITEM_SELL_PENALTY
)
from core.icons import (
    ICON_SUCCESS, ICON_ERROR, ICON_WARNING, ICON_INFO,
    ICON_ECOIN
)

logger = logging.getLogger(__name__)

class SellCommandCog(commands.Cog, name="Sell Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("SellCommandCog (v3 - Full) initialized.")

    @commands.command(name='sell')
    async def sell(self, ctx: commands.commanads.Context, item_id: str, quantity: int = 1):
        """Bán một vật phẩm từ túi đồ của bạn. Giá trị thu về phụ thuộc vào nguồn gốc vật phẩm."""
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server.")
            return

        author_id = ctx.author.id
        item_id_to_sell = item_id.lower().strip()

        if quantity <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Số lượng bán phải lớn hơn 0.")
            return

        if item_id_to_sell not in SHOP_ITEMS:
            await try_send(ctx, content=f"{ICON_ERROR} Vật phẩm `{item_id}` không tồn tại.")
            return

        try:
            economy_data = load_economy_data()
            global_profile = get_or_create_global_user_profile(economy_data, author_id)
            local_data = get_or_create_user_local_data(global_profile, ctx.guild.id)

            inv_local = local_data.get("inventory_local", [])
            inv_global = global_profile.get("inventory_global", [])
            full_inventory = inv_local + inv_global
            
            sellable_items = [item for item in full_inventory if isinstance(item, dict) and item.get("item_id") == item_id_to_sell]

            if len(sellable_items) < quantity:
                await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ **{quantity}x {item_id_to_sell}**. Bạn chỉ có tổng cộng {len(sellable_items)} cái.")
                return

            total_earnings = 0
            items_sold_count = 0
            warnings = []

            # Xử lý bán từng vật phẩm một
            for i in range(quantity):
                item_to_sell = sellable_items[i]
                
                is_tainted = item_to_sell.get("is_tainted", False)
                is_foreign = item_to_sell.get("is_foreign", False)
                base_details = SHOP_ITEMS[item_id_to_sell]
                final_proceeds = 0

                if is_tainted:
                    cooldowns = global_profile.get("cooldowns", {})
                    today_str = str(date.today())
                    
                    if cooldowns.get("last_tainted_sell_date") != today_str:
                        cooldowns["tainted_sells_today"] = 0
                        cooldowns["last_tainted_sell_date"] = today_str

                    if cooldowns.get("tainted_sells_today", 0) >= TAINTED_ITEM_SELL_LIMIT:
                        if not warnings:
                            warnings.append(f"{ICON_WARNING} Bạn đã đạt giới hạn bán 'vật phẩm bẩn' hôm nay, một số vật phẩm không được bán.")
                        continue

                    proceeds = base_details.get("price", 0) * TAINTED_ITEM_SELL_RATE
                    tax = proceeds * TAINTED_ITEM_TAX_RATE
                    final_proceeds = round(proceeds - tax)

                    global_profile["wanted_level"] = global_profile.get("wanted_level", 0.0) + 0.25
                    cooldowns["tainted_sells_today"] += 1
                
                elif is_foreign:
                    sell_price = base_details.get("sell_price", 0)
                    final_proceeds = round(sell_price * (1 - FOREIGN_ITEM_SELL_PENALTY))
                
                else: # Đồ sạch
                    final_proceeds = base_details.get("sell_price", 0)

                total_earnings += final_proceeds
                
                if item_to_sell in inv_local:
                    inv_local.remove(item_to_sell)
                elif item_to_sell in inv_global:
                    inv_global.remove(item_to_sell)
                
                items_sold_count += 1

            local_data["local_balance"]["earned"] += total_earnings
            
            save_economy_data(economy_data)

            logger.info(f"User {author_id} đã bán {items_sold_count}x {item_id_to_sell}, thu về {total_earnings} Ecoin.")

            msg = f"{ICON_SUCCESS} Bạn đã bán thành công **{items_sold_count}x {item_id_to_sell}** và nhận được tổng cộng **{total_earnings:,}** {ICON_ECOIN}."
            if warnings:
                msg += "\n" + "\n".join(warnings)
                
            await try_send(ctx, content=msg)

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'sell' (v3) cho user {author_id}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi bạn bán hàng.")

def setup(bot: commands.Bot):
    bot.add_cog(SellCommandCog(bot))
)
                
            await try_send(ctx, content=msg)

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'sell' (v3) cho user {author_id}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi bạn bán hàng.")

def setup(bot: commands.Bot):
    bot.add_cog(SellCommandCog(bot))
