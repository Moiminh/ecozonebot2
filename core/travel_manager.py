# bot/core/travel_manager.py
import nextcord
import logging
from typing import List, Dict, Any

from .database import (
    load_economy_data,
    save_economy_data,
    get_or_create_global_user_profile,
    get_or_create_user_local_data
)
from .utils import try_send
from .config import UTILITY_ITEMS
from .icons import ICON_INFO, ICON_ECOVISA, ICON_BACKPACK # Giả sử đã thêm ICON_BACKPACK = "🎒"

logger = logging.getLogger(__name__)

# --- View cho việc chọn vật phẩm từ Balo ---
class BackpackItemSelectView(nextcord.ui.View):
    def __init__(self, ctx, travel_manager_instance, items_to_choose_from: List[Dict[str, Any]], capacity: int):
        super().__init__(timeout=300) # 5 phút để chọn
        self.ctx = ctx
        self.travel_manager = travel_manager_instance
        self.interaction_user = ctx.author
        self.message = None
        self.chosen_items = []

        # Tạo các lựa chọn cho Select menu
        options = [
            nextcord.SelectOption(label=item.get("item_id"), description=f"Vật phẩm trong túi đồ cũ của bạn.")
            for item in items_to_choose_from
        ]
        
        item_select = nextcord.ui.Select(
            placeholder="Chọn vật phẩm để mang theo...",
            min_values=0,
            max_values=min(capacity, len(options)), # Không thể chọn nhiều hơn sức chứa của balo
            options=options
        )
        item_select.callback = self.on_select_items
        self.add_item(item_select)

    async def on_select_items(self, interaction: nextcord.Interaction):
        await interaction.response.defer()
        self.chosen_items = interaction.data.get("values", [])
        self.stop() # Dừng View sau khi người dùng đã chọn

    async def interaction_check(self, interaction: nextcord.Interaction) -> bool:
        return interaction.user.id == self.interaction_user.id
        
# --- Hàm chính xử lý sự kiện Du lịch ---
async def handle_travel_event(ctx: nextcord.Message, bot: nextcord.Client):
    """
    Hàm chính để xử lý toàn bộ logic khi người chơi "du lịch" đến server mới.
    """
    author_id = ctx.author.id
    guild_id = ctx.guild.id
    
    await try_send(ctx.channel, f"🌍 Chào mừng {ctx.author.mention} đã 'du lịch' đến **{ctx.guild.name}**! Đang kiểm tra hành lý của bạn...")

    economy_data = load_economy_data()
    global_profile = get_or_create_global_user_profile(economy_data, author_id)
    
    travel_results = []

    # --- 1. Xử lý Visa ---
    # (Logic tìm Visa tốt nhất và áp dụng hiệu ứng sẽ ở đây)
    # Ví dụ đơn giản:
    # ...
    # travel_results.append(f"{ICON_ECOVISA} Nhờ có Visa, bạn đã mang theo X Ecoin.")

    # --- 2. Xử lý Balo Du Lịch ---
    last_guild_id = global_profile.get("last_active_guild_id")
    if last_guild_id:
        backpack_to_use = next((item for item in global_profile.get("inventory_global", []) 
                                if item.get("type") == "backpack" and 
                                not item.get("used", False) and
                                item.get("source_guild_id") == last_guild_id), None)
        
        if backpack_to_use:
            old_local_data = get_or_create_user_local_data(global_profile, last_guild_id)
            old_inventory = old_local_data.get("inventory_local", [])

            if old_inventory:
                capacity = UTILITY_ITEMS.get(backpack_to_use["item_id"], {}).get("capacity", 0)
                
                view = BackpackItemSelectView(ctx, None, old_inventory, capacity)
                msg = await try_send(ctx.channel, f"{ICON_BACKPACK} Bạn có một Balo từ server cũ! Hãy chọn tối đa **{capacity}** vật phẩm để mang theo:", view=view)
                view.message = msg
                
                await view.wait() # Đợi người dùng chọn xong

                if view.chosen_items:
                    new_local_data = get_or_create_user_local_data(global_profile, guild_id)
                    items_moved_names = []
                    
                    for item_id_to_move in view.chosen_items:
                        # Tìm và di chuyển vật phẩm
                        item_found = next((item for item in old_inventory if item.get("item_id") == item_id_to_move), None)
                        if item_found:
                            old_inventory.remove(item_found)
                            item_found["is_foreign"] = True # Gắn cờ "ngoại lai"
                            new_local_data.setdefault("inventory_local", []).append(item_found)
                            items_moved_names.append(item_id_to_move)

                    travel_results.append(f"{ICON_BACKPACK} Bạn đã mang theo các vật phẩm: `{', '.join(items_moved_names)}`.")
                
                # Đánh dấu balo đã sử dụng
                backpack_to_use["used"] = True

    # --- Tổng kết và Lưu ---
    if not travel_results:
        travel_results.append("😅 Nhưng có vẻ như bạn đã đến đây tay không. Chúc may mắn ở vùng đất mới!")
    
    summary_embed = nextcord.Embed(title=f"Kết quả chuyến du lịch của {ctx.author.name}", description="\n".join(travel_results), color=nextcord.Color.blue())
    await try_send(ctx.channel, embed=summary_embed)

    save_economy_data(economy_data)
