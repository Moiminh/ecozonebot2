# bot/cogs/misc/richest_cmd.py
import nextcord
from nextcord.ext import commands
import logging 

from core.database import load_data
from core.utils import try_send
from core.config import CURRENCY_SYMBOL
from core.icons import ICON_CROWN, ICON_INFO, ICON_ERROR

logger = logging.getLogger(__name__) 

class RichestCommandCog(commands.Cog, name="Richest Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug("RichestCommandCog initialized.") # Giữ debug cho init Cog

    @commands.command(name='richest')
    async def richest(self, ctx: commands.Context):
        logger.debug(f"Lệnh 'richest' được gọi bởi {ctx.author.name} (ID: {ctx.author.id}) tại guild {ctx.guild.id}.")
        
        data = load_data()
        guild_id = str(ctx.guild.id)

        if guild_id not in data or not data[guild_id] or all(key == "config" for key in data[guild_id]):
            logger.info(f"Không có dữ liệu để tìm người giàu nhất cho guild {ctx.guild.name} ({guild_id}). Yêu cầu từ {ctx.author.name}.") # INFO này vẫn có thể hữu ích
            await try_send(ctx, content=f"{ICON_INFO} Chưa có ai để xếp hạng trên server này!")
            return
        
        # ... (phần lấy guild_user_data và sorted_users giữ nguyên) ...
        guild_user_data = {uid: udata for uid, udata in data[guild_id].items() if uid != "config" and isinstance(udata, dict) and ("balance" in udata or "bank_balance" in udata)}
        if not guild_user_data:
            logger.info(f"Không có user data hợp lệ để tìm người giàu nhất cho guild {ctx.guild.name} ({guild_id}). Yêu cầu từ {ctx.author.name}.")
            await try_send(ctx, content=f"{ICON_INFO} Chưa có ai để xếp hạng trên server này!")
            return
        sorted_users = sorted(guild_user_data.items(), key=lambda item: item[1].get('balance', 0) + item[1].get('bank_balance', 0), reverse=True)
        if not sorted_users: 
            logger.info(f"Không có user nào sau khi sắp xếp để tìm người giàu nhất cho guild {ctx.guild.name} ({guild_id}). Yêu cầu từ {ctx.author.name}.")
            await try_send(ctx, content=f"{ICON_INFO} Chưa có ai để xếp hạng trên server này!")
            return

        top_user_id, top_user_data_dict = sorted_users[0] 
        logger.debug(f"Người dùng tiềm năng giàu nhất: ID {top_user_id} với data {top_user_data_dict}")
        try:
            user_obj = await self.bot.fetch_user(int(top_user_id))
            total_wealth = top_user_data_dict.get('balance', 0) + top_user_data_dict.get('bank_balance', 0)
            
            # --- THAY ĐỔI Ở ĐÂY: Chuyển từ info sang debug ---
            logger.debug(f"Người giàu nhất server {ctx.guild.name} (ID: {ctx.guild.id}) là {user_obj.name} (ID: {top_user_id}) với {total_wealth:,} {CURRENCY_SYMBOL}.")
            # ---------------------------------------------
            
            await try_send(ctx, content=f"{ICON_CROWN} Người giàu nhất server là **{user_obj.name}** với tổng tài sản **{total_wealth:,}** {CURRENCY_SYMBOL}!")
            logger.debug(f"Lệnh 'richest' cho {ctx.author.name} đã hiển thị người giàu nhất là {user_obj.name}.")

        except (nextcord.NotFound, ValueError, KeyError) as e:
            logger.error(f"Lỗi khi fetch/xử lý user ID {top_user_id} cho lệnh 'richest': {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Không thể tìm thấy thông tin người giàu nhất (có thể do lỗi fetch user hoặc dữ liệu không hợp lệ).")
        except Exception as e:
            logger.error(f"Lỗi không xác định trong lệnh 'richest' khi xử lý user ID {top_user_id}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi tìm người giàu nhất.")

def setup(bot: commands.Bot):
    bot.add_cog(RichestCommandCog(bot))
