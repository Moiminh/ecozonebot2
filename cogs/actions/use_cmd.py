# bot/cogs/actions/use_cmd.py
import nextcord
from nextcord.ext import commands
import logging

from core.database import get_or_create_global_user_profile, get_or_create_user_local_data
from core.utils import try_send
from core.icons import ICON_SUCCESS, ICON_ERROR, ICON_INFO, ICON_SURVIVAL

logger = logging.getLogger(__name__)

class UseCommandCog(commands.Cog, name="Use Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("UseCommandCog (v2 - Refactored) initialized.")

    @commands.command(name='use')
    @commands.guild_only()
    async def use(self, ctx: commands.Context, item_id: str):
        """Sử dụng một vật phẩm tiêu thụ từ túi đồ của bạn."""
        author_id = ctx.author.id
        guild_id = ctx.guild.id
        item_id_to_use = item_id.lower().strip()

        try:
            # Use the bot's data cache instead of loading from file
            economy_data = self.bot.economy_data
            global_profile = get_or_create_global_user_profile(economy_data, author_id)
            local_data = get_or_create_user_local_data(global_profile, guild_id)

            # Find item in both inventories
            inventory_local = local_data.get("inventory_local", [])
            inventory_global = global_profile.get("inventory_global", [])
            
            item_to_remove = None
            source_inventory = None

            # Prioritize local inventory
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

            # Check if the item is usable, using the bot's item definition cache
            item_details = self.bot.item_definitions.get(item_id_to_use, {})
            if not item_details or "effect" not in item_details:
                await try_send(ctx, content=f"{ICON_ERROR} Bạn không thể 'dùng' vật phẩm này.")
                return
            
            # Apply effect
            effect = item_details["effect"]
            stat_to_change = effect["stat"]
            value_to_add = effect["value"]
            
            stats = local_data.get("survival_stats")
            original_value = stats[stat_to_change]
            stats[stat_to_change] = min(100, original_value + value_to_add) # Cap at 100

            # Remove used item
            source_inventory.remove(item_to_remove)
            
            # No need to save data, autosave task will handle it
            
            stat_name_vn = {"health": "Máu", "hunger": "Độ no", "energy": "Năng lượng"}
            stat_name = stat_name_vn.get(stat_to_change, stat_to_change)
            
            await try_send(ctx, content=f"{ICON_SUCCESS} Bạn đã dùng **{item_details['description']}** và hồi phục **{value_to_add} {stat_name}** {ICON_SURVIVAL}.")
            logger.info(f"User {author_id} used {item_id_to_use}, restored {value_to_add} {stat_to_change}.")

        except Exception as e:
            logger.error(f"Error in 'use' command for user {author_id}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi khi bạn sử dụng vật phẩm.")


def setup(bot: commands.Bot):
    bot.add_cog(UseCommandCog(bot))
