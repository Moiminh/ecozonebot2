# bot/cogs/earn/fish_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime
import logging 

from core.database import get_user_data, save_data
from core.utils import try_send, get_time_left_str
from core.config import CURRENCY_SYMBOL, FISH_COOLDOWN, FISH_CATCHES
from core.icons import ICON_LOADING, ICON_FISH, ICON_INFO, ICON_ERROR # Đảm bảo ICON_ERROR đã được import nếu dùng trong try_send

logger = logging.getLogger(__name__) 

class FishCommandCog(commands.Cog, name="Fish Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info(f"{ICON_INFO} FishCommandCog initialized.") 

    @commands.command(name='fish')
    async def fish(self, ctx: commands.Context):
        """Đi câu cá để kiếm tiền từ việc bán cá (hoặc rác)."""
        # Đổi từ critical sang debug
        logger.debug(f"FISH_CMD_DEBUG: === BẮT ĐẦU LỆNH FISH bởi {ctx.author.name} (ID: {ctx.author.id}) ===")
        
        data = get_user_data(ctx.guild.id, ctx.author.id)
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]

        time_left = get_time_left_str(user_data.get("last_fish"), FISH_COOLDOWN)
        if time_left:
            # Đổi từ critical sang debug
            logger.debug(f"FISH_CMD_DEBUG: User {ctx.author.id} đang cooldown. Còn lại: {time_left}. Chuẩn bị gửi tin nhắn cooldown.")
            cooldown_message_content = f"{ICON_LOADING} Cá cần thời gian để cắn câu! Lệnh `fish` chờ: **{time_left}**."
            
            try:
                # Đổi từ critical sang debug
                logger.debug(f"FISH_CMD_DEBUG: Chuẩn bị gọi ctx.send TRỰC TIẾP cho tin nhắn cooldown: '{cooldown_message_content}'")
                await ctx.send(content=cooldown_message_content) 
                # Đổi từ critical sang debug
                logger.debug(f"FISH_CMD_DEBUG: Đã KẾT THÚC gọi ctx.send TRỰC TIẾP cho tin nhắn cooldown.")
            except Exception as e:
                logger.error(f"FISH_CMD_DEBUG: Lỗi khi gọi ctx.send trực tiếp cho cooldown: {e}", exc_info=True)
            
            # Đổi từ critical sang debug
            logger.debug(f"FISH_CMD_DEBUG: === KẾT THÚC LỆNH FISH (do cooldown) cho {ctx.author.name} ===")
            return
            
        user_data["last_fish"] = datetime.now().timestamp()
        catch_emoji, price = random.choice(list(FISH_CATCHES.items())) 
        
        original_balance = user_data.get("balance", 0)
        user_data["balance"] = original_balance + price
        save_data(data)
        logger.debug(f"FISH_CMD_DEBUG: Dữ liệu đã được lưu cho user {ctx.author.id} sau khi câu cá.")

        # Dòng logger.info này giữ nguyên để ghi vào player_actions.log
        logger.info(f"User {ctx.author.display_name} ({ctx.author.id}) câu được '{catch_emoji}' trị giá {price} {CURRENCY_SYMBOL}. Số dư mới: {user_data['balance']:,}.")
        
        message_to_send = ""
        if price >= 50: 
            message_to_send = f"{ICON_FISH} Chúc mừng! Bạn câu được một con {catch_emoji} và bán nó được **{price:,}** {CURRENCY_SYMBOL}!"
        elif price > 5: 
            message_to_send = f"{ICON_FISH} Bạn câu được {catch_emoji}, bán được **{price:,}** {CURRENCY_SYMBOL}. Cũng không tệ!"
        else: 
            message_to_send = f"{ICON_FISH} Ôi không! Bạn câu được rác {catch_emoji}... nhưng may là vẫn bán được **{price:,}** {CURRENCY_SYMBOL}."

        # Đổi từ critical sang debug
        logger.debug(f"FISH_CMD_DEBUG: Chuẩn bị gửi tin nhắn kết quả (dùng try_send): '{message_to_send}' cho {ctx.author.name}")
        await try_send(ctx, content=message_to_send) 
        # Đổi từ critical sang debug
        logger.debug(f"FISH_CMD_DEBUG: ĐÃ GỬI XONG tin nhắn kết quả (dùng try_send) cho {ctx.author.name}.")
        # Đổi từ critical sang debug
        logger.debug(f"FISH_CMD_DEBUG: === KẾT THÚC LỆNH FISH (thành công) cho {ctx.author.name} ===")

def setup(bot: commands.Bot):
    bot.add_cog(FishCommandCog(bot))
