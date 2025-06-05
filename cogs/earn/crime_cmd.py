# bot/cogs/earn/crime_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime
import logging # <<< Đã có hoặc thêm vào

from core.database import get_user_data, save_data
from core.utils import try_send, get_time_left_str
from core.config import CURRENCY_SYMBOL, CRIME_COOLDOWN, CRIME_SUCCESS_RATE
from core.icons import ICON_LOADING, ICON_CRIME, ICON_ERROR, ICON_MONEY_BAG, ICON_INFO # Đảm bảo có ICON_INFO

logger = logging.getLogger(__name__) # <<< Đã có hoặc thêm vào

class CrimeCommandCog(commands.Cog, name="Crime Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info(f"{ICON_INFO} CrimeCommandCog initialized.") # Dùng INFO nếu muốn thấy trên console

    @commands.command(name='crime')
    async def crime(self, ctx: commands.Context):
        """Thực hiện một hành vi phạm tội ngẫu nhiên để kiếm tiền."""
        logger.debug(f"Lệnh 'crime' được gọi bởi {ctx.author.name} (ID: {ctx.author.id}) tại guild {ctx.guild.id}.")
        
        data = get_user_data(ctx.guild.id, ctx.author.id)
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]
        original_balance = user_data.get("balance", 0)

        time_left = get_time_left_str(user_data.get("last_crime"), CRIME_COOLDOWN)
        if time_left:
            logger.debug(f"User {ctx.author.id} dùng lệnh 'crime' khi đang cooldown. Còn lại: {time_left}")
            # logger.info(f"User {ctx.author.display_name} ({ctx.author.id}) thử 'crime' nhưng đang cooldown ({time_left}).") # Tùy chọn log INFO
            await try_send(ctx, content=f"{ICON_LOADING} Cảnh sát đang theo dõi! Lệnh `crime` chờ: **{time_left}**.")
            return
            
        user_data["last_crime"] = datetime.now().timestamp()
        crimes_list = ["trộm vặt", "buôn lậu", "hack tài khoản", "tổ chức đua xe đường phố", "giả danh quan chức", "lừa đảo qua mạng", "in tiền giả"]
        chosen_crime = random.choice(crimes_list)
        logger.debug(f"User {ctx.author.id} thực hiện tội '{chosen_crime}'.")

        if random.random() < CRIME_SUCCESS_RATE:
            earnings = random.randint(300, 1000)
            user_data["balance"] = original_balance + earnings
            save_data(data) 
            
            # Ghi log hành động thành công
            logger.info(f"CRIME SUCCESS: User {ctx.author.display_name} ({ctx.author.id}) thực hiện '{chosen_crime}' thành công, kiếm được {earnings:,} {CURRENCY_SYMBOL}. "
                        f"Số dư: {original_balance:,} -> {user_data['balance']:,}.")
            
            await try_send(ctx, content=f"{ICON_CRIME} Bạn đã thực hiện thành công phi vụ **'{chosen_crime}'** và kiếm được **{earnings:,}** {CURRENCY_SYMBOL}! {ICON_MONEY_BAG} Ví: {user_data['balance']:,}")
        else:
            # Tính toán tiền phạt cẩn thận hơn
            fine_percentage = random.uniform(0.05, 0.20) # Phạt từ 5% đến 20% số tiền đang có
            potential_fine_from_percentage = int(original_balance * fine_percentage)
            min_random_fine = random.randint(100, 500) # Phạt ngẫu nhiên tối thiểu nếu % quá nhỏ
            
            fine = max(potential_fine_from_percentage, min_random_fine)
            fine = min(fine, original_balance) # Đảm bảo không phạt quá số tiền đang có
            
            user_data["balance"] = original_balance - fine
            save_data(data) 

            # Ghi log hành động thất bại
            logger.info(f"CRIME FAILED: User {ctx.author.display_name} ({ctx.author.id}) thực hiện '{chosen_crime}' thất bại, bị phạt {fine:,} {CURRENCY_SYMBOL}. "
                        f"Số dư: {original_balance:,} -> {user_data['balance']:,}.")

            await try_send(ctx, content=f"{ICON_ERROR} Bạn đã thất bại thảm hại khi thực hiện **'{chosen_crime}'** và bị phạt **{fine:,}** {CURRENCY_SYMBOL}! {ICON_MONEY_BAG} Ví còn: {user_data['balance']:,}")
        
        logger.debug(f"Lệnh 'crime' cho {ctx.author.name} đã xử lý xong.")

def setup(bot: commands.Bot):
    bot.add_cog(CrimeCommandCog(bot))
