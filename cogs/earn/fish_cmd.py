# bot/cogs/earn/fish_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime

from core.database import get_user_data, save_data
from core.utils import try_send, get_time_left_str
from core.config import CURRENCY_SYMBOL, FISH_COOLDOWN, FISH_CATCHES
from core.icons import ICON_LOADING, ICON_FISH # Sử dụng ICON_FISH chung

class FishCommandCog(commands.Cog, name="Fish Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='fish')
    async def fish(self, ctx: commands.Context):
        """Đi câu cá để kiếm tiền từ việc bán cá (hoặc rác)."""
        data = get_user_data(ctx.guild.id, ctx.author.id)
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]

        time_left = get_time_left_str(user_data.get("last_fish"), FISH_COOLDOWN)
        if time_left:
            await try_send(ctx, content=f"{ICON_LOADING} Cá cần thời gian để cắn câu! Lệnh `fish` chờ: **{time_left}**.")
            return
            
        user_data["last_fish"] = datetime.now().timestamp()
        # FISH_CATCHES từ config.py là một dictionary: {"emoji_cá": giá_tiền}
        catch_emoji, price = random.choice(list(FISH_CATCHES.items())) 
        
        user_data["balance"] = user_data.get("balance", 0) + price
        save_data(data)

        # Phân loại thông báo dựa trên giá trị của vật phẩm câu được
        if price >= 50: # Ví dụ: cá xịn
            await try_send(ctx, content=f"{ICON_FISH} Chúc mừng! Bạn câu được một con {catch_emoji} và bán nó được **{price:,}** {CURRENCY_SYMBOL}!")
        elif price > 5: # Ví dụ: cá thường hoặc đồ có giá trị thấp
            await try_send(ctx, content=f"{ICON_FISH} Bạn câu được {catch_emoji}, bán được **{price:,}** {CURRENCY_SYMBOL}. Cũng không tệ!")
        else: # Ví dụ: rác
            await try_send(ctx, content=f"{ICON_FISH} Ôi không! Bạn câu được rác {catch_emoji}... nhưng may là vẫn bán được **{price:,}** {CURRENCY_SYMBOL}.")

def setup(bot: commands.Bot):
    bot.add_cog(FishCommandCog(bot))
