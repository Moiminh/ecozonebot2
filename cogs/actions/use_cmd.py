# bot/cogs/actions/use_cmd.py
import nextcord
from nextcord.ext import commands
import logging
from core.utils import try_send
from core.icons import ICON_SUCCESS, ICON_ERROR, ICON_INFO, ICON_SURVIVAL

logger = logging.getLogger(__name__)

class UseCommandCog(commands.Cog, name="Use Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("UseCommandCog (SQLite Ready) initialized.")

    @commands.command(name='use')
    @commands.guild_only()
    async def use(self, ctx: commands.Context, item_id: str):
        author_id = ctx.author.id
        guild_id = ctx.guild.id
        item_id_to_use = item_id.lower().strip()

        try:
            # Tìm vật phẩm trong túi đồ của người dùng
            item_to_remove = self.bot.db.find_item_in_inventory(author_id, item_id_to_use, guild_id)
            
            if not item_to_remove:
                await try_send(ctx, content=f"{ICON_ERROR} Bạn không có vật phẩm `{item_id_to_use}`.")
                return

            item_details = self.bot.item_definitions.get(item_id_to_use, {})
            if "effect" not in item_details:
                await try_send(ctx, content=f"{ICON_ERROR} Bạn không thể 'dùng' vật phẩm này.")
                return
            
            # Lấy dữ liệu local để biết chỉ số hiện tại
            local_data = self.bot.db.get_or_create_user_local_data(author_id, guild_id)
            
            # Áp dụng hiệu ứng
            effect = item_details["effect"]
            stat_to_change = effect["stat"] # 'health', 'hunger', hoặc 'energy'
            value_to_add = effect["value"]
            
            original_value = local_data[stat_to_change]
            new_value = original_value + value_to_add
            
            # Gọi hàm cập nhật chỉ số
            args = {'user_id': author_id, 'guild_id': guild_id, stat_to_change: new_value}
            self.bot.db.update_user_stats(**args)
            
            # Xóa vật phẩm đã dùng
            self.bot.db.remove_item_from_inventory(item_to_remove['inventory_id'])
            
            stat_name_vn = {"health": "Máu", "hunger": "Độ no", "energy": "Năng lượng"}
            stat_name = stat_name_vn.get(stat_to_change, stat_to_change)
            
            await try_send(ctx, content=f"{ICON_SUCCESS} Bạn đã dùng **{item_details['description']}** và hồi phục **{value_to_add} {stat_name}** {ICON_SURVIVAL}.")
            logger.info(f"User {author_id} used {item_id_to_use}, restored {value_to_add} {stat_to_change}.")

        except Exception as e:
            logger.error(f"Error in 'use' command for user {author_id}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi khi bạn sử dụng vật phẩm.")

def setup(bot: commands.Bot):
    bot.add_cog(UseCommandCog(bot))
