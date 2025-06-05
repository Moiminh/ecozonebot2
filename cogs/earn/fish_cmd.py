# bot/cogs/earn/fish_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime
import logging # Đã có từ trước

from core.database import get_user_data, save_data
from core.utils import try_send, get_time_left_str
from core.config import CURRENCY_SYMBOL, FISH_COOLDOWN, FISH_CATCHES
from core.icons import ICON_LOADING, ICON_FISH, ICON_INFO # Đảm bảo ICON_INFO có trong icons.py

logger = logging.getLogger(__name__) # Đã có từ trước

class FishCommandCog(commands.Cog, name="Fish Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info(f"{ICON_INFO} FishCommandCog initialized.") 

    @commands.command(name='fish')
    async def fish(self, ctx: commands.Context):
        """Đi câu cá để kiếm tiền từ việc bán cá (hoặc rác)."""
        # Sử dụng logger.critical để chắc chắn thấy trên console khi debug lỗi gửi 2 tin nhắn
        logger.critical(f"FISH_CMD_DEBUG: === BẮT ĐẦU LỆNH FISH bởi {ctx.author.name} (ID: {ctx.author.id}) ===")
        
        data = get_user_data(ctx.guild.id, ctx.author.id)
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]

        time_left = get_time_left_str(user_data.get("last_fish"), FISH_COOLDOWN)
        if time_left:
            logger.critical(f"FISH_CMD_DEBUG: User {ctx.author.id} đang cooldown. Còn lại: {time_left}. Chuẩn bị gửi tin nhắn cooldown.")
            await try_send(ctx, content=f"{ICON_LOADING} Cá cần thời gian để cắn câu! Lệnh `fish` chờ: **{time_left}**.")
            logger.critical(f"FISH_CMD_DEBUG: Đã GỬI XONG tin nhắn cooldown cho {ctx.author.id}.")
            logger.critical(f"FISH_CMD_DEBUG: === KẾT THÚC LỆNH FISH (do cooldown) cho {ctx.author.name} ===")
            return
            
        user_data["last_fish"] = datetime.now().timestamp()
        catch_emoji, price = random.choice(list(FISH_CATCHES.items())) 
        
        original_balance = user_data.get("balance", 0) # Lấy số dư cũ để log
        user_data["balance"] = original_balance + price
        save_data(data)
        logger.debug(f"FISH_CMD_DEBUG: Dữ liệu đã được lưu cho user {ctx.author.id} sau khi câu cá.")

        # Ghi log hành động (INFO level, sẽ vào player_actions.log và general_log)
        logger.info(f"User {ctx.author.display_name} ({ctx.author.id}) câu được '{catch_emoji}' trị giá {price} {CURRENCY_SYMBOL}. Số dư: {original_balance:,} -> {user_data['balance']:,}.")
        
        message_to_send = ""
        if price >= 50: 
            message_to_send = f"{ICON_FISH} Chúc mừng! Bạn câu được một con {catch_emoji} và bán nó được **{price:,}** {CURRENCY_SYMBOL}!"
        elif price > 5: 
            message_to_send = f"{ICON_FISH} Bạn câu được {catch_emoji}, bán được **{price:,}** {CURRENCY_SYMBOL}. Cũng không tệ!"
        else: 
            message_to_send = f"{ICON_FISH} Ôi không! Bạn câu được rác {catch_emoji}... nhưng may là vẫn bán được **{price:,}** {CURRENCY_SYMBOL}."

        logger.critical(f"FISH_CMD_DEBUG: Chuẩn bị gửi tin nhắn kết quả: '{message_to_send}' cho {ctx.author.name}")
        await try_send(ctx, content=message_to_send)
        logger.critical(f"FISH_CMD_DEBUG: ĐÃ GỬI XONG tin nhắn kết quả cho {ctx.author.name}.")
        logger.critical(f"FISH_CMD_DEBUG: === KẾT THÚC LỆNH FISH (thành công) cho {ctx.author.name} ===")


def setup(bot: commands.Bot):
    bot.add_cog(FishCommandCog(bot))
