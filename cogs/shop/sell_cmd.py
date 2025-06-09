# bot/cogs/shop/sell_cmd.py
import nextcord
from nextcord.ext import commands
import logging
from datetime import date
from core.utils import try_send
from core.config import TAINTED_ITEM_SELL_LIMIT, TAINTED_ITEM_SELL_RATE, TAINTED_ITEM_TAX_RATE, FOREIGN_ITEM_SELL_PENALTY
from core.icons import ICON_SUCCESS, ICON_ERROR, ICON_WARNING, ICON_INFO, ICON_ECOIN

logger = logging.getLogger(__name__)

class SellCommandCog(commands.Cog, name="Sell Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("SellCommandCog (SQLite Ready) initialized.")

    @commands.command(name='sell')
    async def sell(self, ctx: commands.Context, item_id: str, quantity: int = 1, item_type: str = "bẩn"):
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server.")
            return

        author_id = ctx.author.id
        item_id_to_sell = item_id.lower().strip()

        if quantity <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Số lượng bán phải lớn hơn 0.")
            return

        if item_id_to_sell not in self.bot.item_definitions:
            await try_send(ctx, content=f"{ICON_ERROR} Vật phẩm `{item_id}` không tồn tại.")
            return

        try:
            full_inventory = self.bot.db.get_inventory(author_id)
            items_of_id = [item for item in full_inventory if item['item_id'] == item_id_to_sell]

            tainted_items = [item for item in items_of_id if item['is_tainted']]
            clean_items = [item for item in items_of_id if not item['is_tainted']]

            sellable_items = []
            if item_type.lower() in ['bẩn', 'ban', 'tainted', 'dirty']:
                sellable_items = tainted_items + clean_items
            elif item_type.lower() in ['sạch', 'sach', 'clean']:
                sellable_items = clean_items + tainted_items
            else:
                 await try_send(ctx, content=f"{ICON_ERROR} Loại vật phẩm không hợp lệ. Vui lòng chọn 'sạch' hoặc 'bẩn'.")
                 return

            if len(sellable_items) < quantity:
                await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ **{quantity}x {item_id_to_sell}** để bán.")
                return

            total_earnings = 0
            items_sold_count = 0
            warnings = []

            # Lấy profile và balance một lần
            global_profile = self.bot.db.get_or_create_global_user_profile(author_id)
            local_data = self.bot.db.get_or_create_user_local_data(author_id, ctx.guild.id)
            current_earned_balance = local_data['local_balance_earned']
            current_wanted_level = global_profile['wanted_level']

            items_to_sell_list = sellable_items[:quantity]

            for item_to_sell in items_to_sell_list:
                is_tainted = item_to_sell['is_tainted']
                is_foreign = item_to_sell['is_foreign']
                base_details = self.bot.item_definitions[item_id_to_sell]
                
                final_proceeds = 0
                if is_tainted:
                    # Logic giới hạn bán đồ bẩn (cần CSDL cho cooldown)
                    # Giả sử tạm thời không có giới hạn để đơn giản hóa
                    proceeds = base_details.get("price", 0) * TAINTED_ITEM_SELL_RATE
                    tax = proceeds * TAINTED_ITEM_TAX_RATE
                    final_proceeds = round(proceeds - tax)
                    current_wanted_level += 0.25
                elif is_foreign:
                    sell_price = base_details.get("sell_price", 0)
                    final_proceeds = round(sell_price * (1 - FOREIGN_ITEM_SELL_PENALTY))
                else:
                    final_proceeds = base_details.get("sell_price", 0)

                total_earnings += final_proceeds
                self.bot.db.remove_item_from_inventory(item_to_sell['inventory_id'])
                items_sold_count += 1

            # Cập nhật balance và wanted level một lần sau vòng lặp
            self.bot.db.update_balance(author_id, ctx.guild.id, 'local_balance_earned', current_earned_balance + total_earnings)
            self.bot.db.update_wanted_level(author_id, current_wanted_level)

            msg = f"{ICON_SUCCESS} Bạn đã bán thành công **{items_sold_count}x {item_id_to_sell}** và nhận được tổng cộng **{total_earnings:,}** {ICON_ECOIN}."
            if warnings:
                msg += "\n" + "\n".join(warnings)
                
            await try_send(ctx, content=msg)

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'sell' cho user {author_id}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi bạn bán hàng.")

def setup(bot: commands.Bot):
    bot.add_cog(SellCommandCog(bot))
