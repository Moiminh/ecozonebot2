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
from core.config import SHOP_ITEMS, TAINTED_ITEM_SELL_LIMIT
# Giả sử đã thêm các config mới vào config.py
# TAINTED_ITEM_SELL_LIMIT = 2
# TAINTED_ITEM_SELL_RATE = 0.2 # 20%
# TAINTED_ITEM_TAX_RATE = 0.4 # 40%
from core.icons import (
    ICON_SUCCESS, ICON_ERROR, ICON_WARNING, ICON_INFO,
    ICON_TIEN_SACH, ICON_TIEN_LAU
)

logger = logging.getLogger(__name__)

class SellCommandCog(commands.Cog, name="Sell Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("SellCommandCog (v2) initialized.")

    @commands.command(name='sell')
    async def sell(self, ctx: commands.Context, item_id: str, quantity: int = 1):
        """Bán một vật phẩm từ túi đồ của bạn."""
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server.")
            return

        author_id = ctx.author.id
        guild_id = ctx.guild.id
        item_id_to_sell = item_id.lower().strip().replace(" ", "_")

        if quantity <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Số lượng bán phải lớn hơn 0.")
            return

        if item_id_to_sell not in SHOP_ITEMS:
            await try_send(ctx, content=f"{ICON_ERROR} Vật phẩm `{item_id}` không tồn tại.")
            return

        try:
            economy_data = load_economy_data()
            global_profile = get_or_create_global_user_profile(economy_data, author_id)
            local_data = get_or_create_user_local_data(global_profile, guild_id)

            inv_local = local_data.get("inventory_local", [])
            inv_global = global_profile.get("inventory_global", [])
            
            # Đếm tổng số vật phẩm có thể bán
            total_item_count = sum(1 for item in inv_local + inv_global if isinstance(item, dict) and item.get("item_id") == item_id_to_sell)

            if total_item_count < quantity:
                await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ **{quantity}x {item_id_to_sell}**. Bạn chỉ có tổng cộng {total_item_count} cái.")
                return

            total_earnings = 0
            items_sold_info = {"clean": 0, "tainted": 0}
            warnings = []

            # Xử lý bán từng vật phẩm
            for _ in range(quantity):
                item_to_remove = None
                inventory_source = None
                
                # Ưu tiên tìm trong túi local trước
                for item in inv_local:
                    if isinstance(item, dict) and item.get("item_id") == item_id_to_sell:
                        item_to_remove = item
                        inventory_source = inv_local
                        break
                
                # Nếu không có, tìm trong túi global
                if not item_to_remove:
                    for item in inv_global:
                        if isinstance(item, dict) and item.get("item_id") == item_id_to_sell:
                            item_to_remove = item
                            inventory_source = inv_global
                            break
                
                # --- Áp dụng quy tắc bán hàng ---
                is_tainted = item_to_remove.get("is_tainted", False)
                base_details = SHOP_ITEMS[item_id_to_sell]
                
                if is_tainted:
                    # ---- XỬ LÝ ĐỒ BẨN ----
                    cooldowns = global_profile.get("cooldowns", {})
                    today_str = str(date.today())
                    
                    if cooldowns.get("last_tainted_sell_date") != today_str:
                        cooldowns["tainted_sells_today"] = 0
                        cooldowns["last_tainted_sell_date"] = today_str

                    if cooldowns.get("tainted_sells_today", 0) >= TAINTED_ITEM_SELL_LIMIT:
                        warnings.append(f"{ICON_WARNING} Bạn đã đạt giới hạn bán 'vật phẩm bẩn' hôm nay.")
                        continue # Bỏ qua việc bán vật phẩm này

                    # Tính giá trị thu hồi thấp
                    proceeds = base_details.get("price", 0) * 0.2 # Giả sử 20%
                    # Áp thuế cao
                    tax = proceeds * 0.4 # Giả sử thuế 40%
                    final_proceeds = round(proceeds - tax)

                    # Tăng điểm nghi ngờ
                    global_profile["wanted_level"] = global_profile.get("wanted_level", 0) + 0.25
                    cooldowns["tainted_sells_today"] += 1
                    items_sold_info["tainted"] += 1
                else:
                    # ---- XỬ LÝ ĐỒ SẠCH ----
                    final_proceeds = base_details.get("sell_price", 0)
                    items_sold_info["clean"] += 1

                total_earnings += final_proceeds
                inventory_source.remove(item_to_remove)

            # Cộng toàn bộ tiền bán được vào 'earned'
            local_data["local_balance"]["earned"] += total_earnings
            
            save_economy_data(economy_data)

            logger.info(f"User {author_id} đã bán {quantity}x {item_id_to_sell}, thu về {total_earnings} earned.")

            # --- Gửi thông báo ---
            msg_parts = [f"{ICON_SUCCESS} Giao dịch hoàn tất!"]
            if items_sold_info["clean"] > 0:
                msg_parts.append(f"- Đã bán **{items_sold_info['clean']}x vật phẩm sạch**.")
            if items_sold_info["tainted"] > 0:
                msg_parts.append(f"- Đã bán **{items_sold_info['tainted']}x vật phẩm bẩn** (đã trừ giá trị và thuế).")
            
            msg_parts.append(f"Bạn nhận được tổng cộng **{total_earnings:,}** {ICON_TIEN_SACH}.")
            
            if warnings:
                msg_parts.extend(warnings)
                
            await try_send(ctx, content="\n".join(msg_parts))

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'sell' (v2) cho user {author_id}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi khi bạn bán hàng.")

def setup(bot: commands.Bot):
    bot.add_cog(SellCommandCog(bot))
