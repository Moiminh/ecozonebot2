# bot/cogs/shop/inventory_cmd.py
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
from core.config import CURRENCY_SYMBOL, SHOP_ITEMS as MASTER_ITEM_LIST
from core.icons import ICON_INVENTORY, ICON_ERROR, ICON_INFO, ICON_GLOBAL, ICON_LOCAL # Thêm ICON_GLOBAL, ICON_LOCAL nếu muốn

logger = logging.getLogger(__name__)

def count_and_format_inventory(inventory_list: list) -> tuple[str, str]:
    if not inventory_list:
        return ("Trống", "trống")
    
    item_counts = {}
    for item_data in inventory_list:
        if isinstance(item_data, dict) and "item_id" in item_data:
            item_id = item_data["item_id"]
            item_counts[item_id] = item_counts.get(item_id, 0) + 1
        else: # Hỗ trợ cấu trúc cũ nếu cần (chỉ là chuỗi item_id)
            item_counts[item_data] = item_counts.get(item_data, 0) + 1

    description_parts = []
    log_summary_parts = []
    
    for item_id, count in item_counts.items():
        item_details_from_master = MASTER_ITEM_LIST.get(item_id, {})
        item_display_name = item_details_from_master.get("description", item_id.replace("_", " ").capitalize())
        description_parts.append(f"- {item_display_name} (x{count})")
        log_summary_parts.append(f"{item_display_name}(x{count})")
        
    return "\n".join(description_parts), ", ".join(log_summary_parts)

class InventoryCommandCog(commands.Cog, name="Inventory Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"InventoryCommandCog initialized for Ecoworld Economy.")

    @commands.command(name='inventory', aliases=['inv', 'items', 'i'])
    async def inventory(self, ctx: commands.Context, user: nextcord.Member = None):
        target_user = user or ctx.author

        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Vui lòng sử dụng lệnh này trong một server để xem cả Túi Đồ Local.")
            return
            
        author_id = target_user.id
        guild_id = ctx.guild.id
        
        logger.debug(f"Lệnh 'inventory' được gọi cho {target_user.name} ({author_id}) tại guild '{ctx.guild.name}' ({guild_id}).")

        try:
            economy_data = load_economy_data()
            global_profile = get_or_create_global_user_profile(economy_data, author_id)
            server_data = get_or_create_user_server_data(global_profile, guild_id)
            
            inv_global_list = global_profile.get("inventory_global", [])
            inv_local_list = server_data.get("inventory_local", [])
            
            embed = nextcord.Embed(
                title=f"{ICON_INVENTORY} Túi Đồ của {target_user.display_name}",
                color=nextcord.Color.dark_green()
            )
            embed.set_thumbnail(url=target_user.display_avatar.url)

            global_inv_display, global_inv_log = count_and_format_inventory(inv_global_list)
            local_inv_display, local_inv_log = count_and_format_inventory(inv_local_list)
            
            embed.add_field(
                name=f"💎 Túi Đồ Toàn Cục (GOL)",
                value=global_inv_display,
                inline=False
            )
            embed.add_field(
                name=f"📦 Túi Đồ Local (Server: {ctx.guild.name})",
                value=local_inv_display,
                inline=False
            )
            
            await try_send(ctx, embed=embed)
            
            logger.info(f"User {ctx.author.display_name} ({ctx.author.id}) đã xem túi đồ của {target_user.display_name} ({target_user.id}) tại guild '{ctx.guild.name}'. "
                        f"Global Inv: [{global_inv_log}]. Local Inv: [{local_inv_log}].")

            save_economy_data(economy_data)

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'inventory' cho user {target_user.name}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi không xác định khi xem túi đồ của {target_user.mention}.")

def setup(bot: commands.Bot):
    bot.add_cog(InventoryCommandCog(bot))
