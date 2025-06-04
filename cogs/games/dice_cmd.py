# bot/cogs/games/dice_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime

from core.database import get_user_data, save_data
from core.utils import try_send, get_time_left_str
from core.config import CURRENCY_SYMBOL, DICE_COOLDOWN
from core.icons import ICON_LOADING, ICON_ERROR, ICON_MONEY_BAG, ICON_DICE

class DiceCommandCog(commands.Cog, name="Dice Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='dice', aliases=['roll'])
    async def dice(self, ctx: commands.Context, bet: int):
        """Đổ một cặp xúc xắc. Nếu tổng điểm lớn hơn 7, bạn thắng và nhận lại 1.5 lần tiền cược (lời 0.5 lần)."""
        data = get_user_data(ctx.guild.id, ctx.author.id)
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]

        time_left = get_time_left_str(user_data.get("last_dice"), DICE_COOLDOWN)
        if time_left:
            await try_send(ctx, content=f"{ICON_LOADING} Chơi chậm thôi! Lệnh `dice` chờ: **{time_left}**.")
            return
            
        if bet <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Tiền cược phải lớn hơn 0!")
            return
        if user_data.get("balance", 0) < bet:
            await try_send(ctx, content=f"{ICON_ERROR} Không đủ tiền! Ví của bạn: **{user_data.get('balance',0):,}** {CURRENCY_SYMBOL}.")
            return

        user_data["balance"] -= bet # Trừ tiền cược trước
        d1 = random.randint(1, 6)
        d2 = random.randint(1, 6)
        total = d1 + d2
        
        # Tạo emoji cho từng mặt xúc xắc (ví dụ)
        dice_emojis = ["<:dice_1:ID_EMOJI_1>", "<:dice_2:ID_EMOJI_2>", ... ] # Nếu có emoji custom
        # Hoặc dùng unicode
        dice_unicode_map = {
            1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"
        }
        d1_emoji = dice_unicode_map.get(d1, str(d1))
        d2_emoji = dice_unicode_map.get(d2, str(d2))

        msg = f"{ICON_DICE} Bạn đổ ra: {d1_emoji} + {d2_emoji} = **{total}**.\n"
        
        if total > 7:
            profit = int(bet * 0.5) 
            total_received = bet + profit 
            user_data["balance"] += total_received
            msg += f"🎉 Chúc mừng! Bạn thắng cược, nhận lại tổng cộng **{total_received:,}** {CURRENCY_SYMBOL} (lời **{profit:,}** {CURRENCY_SYMBOL})!"
        else:
            msg += f"😭 Tiếc quá! Bạn thua và mất **{bet:,}** {CURRENCY_SYMBOL}."
            
        user_data["last_dice"] = datetime.now().timestamp()
        save_data(data)
        await try_send(ctx, content=msg + f"\n{ICON_MONEY_BAG} Ví của bạn giờ là: **{user_data['balance']:,}** {CURRENCY_SYMBOL}.")

def setup(bot: commands.Bot):
    bot.add_cog(DiceCommandCog(bot))
