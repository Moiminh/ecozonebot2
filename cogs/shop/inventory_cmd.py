# bot/cogs/shop/inventory_cmd.py
import nextcord
from nextcord.ext import commands
import logging
from collections import Counter
from core.utils import try_send
from core.icons import ICON_INVENTORY, ICON_ERROR, ICON_INFO, ICON_GLOBAL, ICON_LOCAL, ICON_TIEN_LAU

logger = logging.getLogger(__name__)

def format_inventory_list(inventory_data: list, item_definitions: dict) -> str:
    if not inventory_data:
        return "*Trống*"

    item_counts = Counter()
    # inventory_data giờ là list của sqlite3.Row
    for item in inventory_data:
        item_id = item["item_id"]
        is_tainted = item["is_tainted"]
        item_counts[(item_id, is_tainted)] += 1
            
    description_parts = []
    for (item_id, is_tainted), count in item_counts.items():
        item_details = item_definitions.get(item_id, {})
        item_name = item_details.get("description", item_id.replace("_", " ").capitalize())
        
        taint_icon = f"{ICON_TIEN_LAU} " if is_tainted else ""
        
        description_parts.append(f"- {taint_icon}{item_name} (x{count})")
        
    return "\n".join(description_parts)


class InventoryCommandCog(commands.Cog, name="Inventory Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("InventoryCommandCog (SQLite Ready) initialized.")

    @commands.command(name='inventory', aliases=['inv', 'items', 'i'])
    async def inventory(self, ctx: commands.Context, user: nextcord.Member = None):
        target_user = user or ctx.author

        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Vui lòng sử dụng lệnh này trong một server.")
            return
            
        try:
            inv_global = self.bot.db.get_inventory(target_user.id, location='global')
            inv_local = self.bot.db.get_inventory(target_user.id, guild_id=ctx.guild.id, location='local')
            
            embed = nextcord.Embed(title=f"{ICON_INVENTORY} Túi Đồ của {target_user.display_name}", color=nextcord.Color.dark_green())
            embed.set_thumbnail(url=target_user.display_avatar.url)

            global_inv_display = format_inventory_list(inv_global, self.bot.item_definitions)
            local_inv_display = format_inventory_list(inv_local, self.bot.item_definitions)
            
            embed.add_field(name=f"{ICON_GLOBAL} Túi Đồ Toàn Cục (Global)", value=global_inv_display, inline=False)
            embed.add_field(name=f"{ICON_LOCAL} Túi Đồ Tại Server (Local)", value=local_inv_display, inline=False)
            
            await try_send(ctx, embed=embed)
        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'inventory' cho user {target_user.name}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi khi xem túi đồ.")

def setup(bot: commands.Bot):
    bot.add_cog(InventoryCommandCog(bot))
