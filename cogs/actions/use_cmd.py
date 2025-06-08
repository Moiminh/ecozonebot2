# bot/cogs/actions/use_cmd.py
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
from core.icons import ICON_SUCCESS, ICON_ERROR, ICON_INFO, ICON_SURVIVAL

logger = logging.getLogger(__name__)

class UseCommandCog(commands.Cog, name="Use Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("UseCommandCog initialized.")

    @commands.command(name='use')
    async def use(self, ctx: commands.Context, item_id: str):
        """Sử dụng một vật phẩm tiêu thụ từ túi đồ của bạn."""
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server.")
            return
            
        author_id = ctx.author.id
        guild_id = ctx.guild.id
        item_id_to_use = item_id.lower().strip()

        try:
            economy_data = load_economy_data()
            global_profile = get_or_create_global_user_profile(economy_data, author_id)
            local_data = get_or_create_user_local_data(global_profile, guild_id)

            # Tìm vật phẩm trong cả hai túi đồ
            inventory_local = local_data.get("inventory_local", [])
            inventory_global = global_profile.get("inventory_global", [])
            
            item_to_remove = None
            source_inventory = None

            # Ưu tiên tìm trong túi local trước
            for item in inventory_local:
                if isinstance(item, dict) and item.get("item_id") == item_id_to_use:
                    item_to_remove = item
                    source_inventory = inventory_local
                    break
            
            if not item_to_remove:
                for item in inventory_global:
                    if isinstance(item, dict) and item.get("item_id") == item_id_to_use:
                        item_to_remove = item
                        source_inventory = inventory_global
                        break
            
            if not item_to_remove:
                await try_send(ctx, content=f"{ICON_ERROR} Bạn không có vật phẩm `{item_id_to_use}` trong túi đồ.")
                return

            # Kiểm tra xem vật phẩm có thể sử dụng được không
            item_details = SHOP_ITEMS.get(item_id_to_use, {})
            if not item_details or "effect" not in item_details:
                await try_send(ctx, content=f"{ICON_ERROR} Bạn không thể 'dùng' vật phẩm này.")
                return
            
            # Áp dụng hiệu ứng
            effect = item_details["effect"]
            stat_to_change = effect["stat"]
            value_to_add = effect["value"]
            
            stats = local_data.get("survival_stats")
            original_value = stats[stat_to_change]
            stats[stat_to_change] = min(100, original_value + value_to_add) # Không cho vượt quá 100

            # Xóa vật phẩm đã dùng
            source_inventory.remove(item_to_remove)
            
            save_economy_data(economy_data)
            
            stat_name_vn = {"health": "Máu", "hunger": "Độ no", "energy": "Năng lượng"}
            stat_name = stat_name_vn.get(stat_to_change, stat_to_change)
            
            await try_send(ctx, content=f"{ICON_SUCCESS} Bạn đã dùng **{item_details['description']}** và hồi phục **{value_to_add} {stat_name}** {ICON_SURVIVAL}.")
            logger.info(f"User {author_id} đã dùng {item_id_to_use}, hồi {value_to_add} {stat_to_change}.")

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'use' cho user {author_id}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi khi bạn sử dụng vật phẩm.")


def setup(bot: commands.Bot):
    bot.add_cog(UseCommandCog(bot))
