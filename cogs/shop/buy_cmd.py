# bot/cogs/shop/buy_cmd.py
import nextcord
from nextcord.ext import commands
import logging

from core.database import (
    load_economy_data,
    save_economy_data,
    get_or_create_global_user_profile,
    get_or_create_user_local_data
)
from core.utils import try_send
from core.config import SHOP_ITEMS
from core.icons import (
    ICON_SUCCESS, ICON_ERROR, ICON_WARNING, ICON_MONEY_BAG,
    ICON_TIEN_LAU, ICON_GLOBAL, ICON_LOCAL
)

logger = logging.getLogger(__name__)

class BuyCommandCog(commands.Cog, name="Buy Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("BuyCommandCog (v2) initialized.")

    @commands.command(name='buy')
    async def buy(self, ctx: commands.Context, item_id: str, quantity: int = 1):
        """Mua một vật phẩm từ cửa hàng."""
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server.")
            return

        author_id = ctx.author.id
        guild_id = ctx.guild.id
        item_id_to_buy = item_id.lower().strip().replace(" ", "_")

        # --- Kiểm tra đầu vào ---
        if quantity <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Số lượng mua phải lớn hơn 0.")
            return
        
        if item_id_to_buy not in SHOP_ITEMS:
            await try_send(ctx, content=f"{ICON_ERROR} Vật phẩm `{item_id}` không tồn tại trong cửa hàng.")
            return

        try:
            economy_data = load_economy_data()
            global_profile = get_or_create_global_user_profile(economy_data, author_id)
            local_data = get_or_create_user_local_data(global_profile, guild_id)

            item_details = SHOP_ITEMS[item_id_to_buy]
            price_per_item = item_details.get("price", 0)
            total_price = price_per_item * quantity

            # --- Kiểm tra số dư ---
            adadd_balance = local_data["local_balance"]["adadd"]
            earned_balance = local_data["local_balance"]["earned"]
            total_local_balance = adadd_balance + earned_balance

            if total_local_balance < total_price:
                await try_send(ctx, content=f"{ICON_ERROR} Bạn không đủ tiền trong Ví Local! Bạn cần **{total_price:,}** nhưng chỉ có **{total_local_balance:,}**.")
                return
            
            # --- Logic trừ tiền thông minh & Gắn cờ vật phẩm bẩn ---
            adadd_spent = min(adadd_balance, total_price)
            earned_spent = total_price - adadd_spent
            
            local_data["local_balance"]["adadd"] -= adadd_spent
            local_data["local_balance"]["earned"] -= earned_spent
            
            is_tainted = adadd_spent > 0
            
            # --- Tạo vật phẩm và thêm vào túi đồ ---
            new_item_data = {"item_id": item_id_to_buy, "is_tainted": is_tainted}
            
            # Vật phẩm "sạch" vào túi global, "bẩn" vào túi local
            destination_inventory_name = ""
            if is_tainted:
                local_data.setdefault("inventory_local", []).extend([new_item_data] * quantity)
                destination_inventory_name = f"{ICON_LOCAL} Túi Đồ Tại Server"
            else:
                global_profile.setdefault("inventory_global", []).extend([new_item_data] * quantity)
                destination_inventory_name = f"{ICON_GLOBAL} Túi Đồ Toàn Cục"

            save_economy_data(economy_data)

            item_name_display = item_details.get("description", item_id_to_buy)
            logger.info(f"User {author_id} đã mua {quantity}x {item_id_to_buy} (tainted={is_tainted}).")

            # --- Gửi thông báo ---
            msg = (
                f"{ICON_SUCCESS} Bạn đã mua thành công **{quantity}x {item_name_display}** với giá **{total_price:,}** {ICON_MONEY_BAG}.\n"
                f"Vật phẩm đã được thêm vào **{destination_inventory_name}** của bạn."
            )
            
            # Gửi cảnh báo nếu mua phải đồ bẩn
            if is_tainted:
                msg += f"\n\n> {ICON_WARNING} *Mua bằng tiền không rõ nguồn gốc, giá trị bán lại có thể bị giảm.*"

            await try_send(ctx, content=msg)

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'buy' (v2) cho user {author_id}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi khi bạn mua hàng.")

def setup(bot: commands.Bot):
    bot.add_cog(BuyCommandCog(bot))
