# bot/cogs/games.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime # Cần cho cooldown

# Import các thành phần cần thiết từ package 'core'
from core.database import get_user_data, save_data
from core.utils import try_send, get_time_left_str
from core.config import (
    CURRENCY_SYMBOL, SLOTS_COOLDOWN, SLOTS_EMOJIS,
    CF_COOLDOWN, DICE_COOLDOWN
)

class GamesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='slots', aliases=['sl'])
    async def slots(self, ctx: commands.Context, bet: int):
        """Chơi máy xèng may mắn! Đặt cược và thử vận may quay ra các biểu tượng giống nhau."""
        data = get_user_data(ctx.guild.id, ctx.author.id)
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]

        time_left = get_time_left_str(user_data.get("last_slots"), SLOTS_COOLDOWN)
        if time_left:
            await try_send(ctx, content=f"Chơi chậm thôi! Lệnh `slots` chờ: **{time_left}**.")
            return
        
        if bet <= 0:
            await try_send(ctx, content="Tiền cược phải lớn hơn 0!")
            return
        if user_data.get("balance", 0) < bet:
            await try_send(ctx, content=f"Không đủ tiền! Ví của bạn: **{user_data.get('balance',0):,}** {CURRENCY_SYMBOL}.")
            return

        user_data["balance"] -= bet
        rolls = [random.choice(SLOTS_EMOJIS) for _ in range(3)]
        result_msg = f"**[{' | '.join(rolls)}]**\n"
        winnings = 0

        if rolls[0] == rolls[1] == rolls[2]: # Ba biểu tượng giống nhau
            winnings = bet * 10 # Thưởng gấp 10 lần tiền cược
            result_msg += f"🎉 **JACKPOT!** Bạn thắng **{winnings:,}** {CURRENCY_SYMBOL}! 🎉"
        elif rolls[0] == rolls[1] or rolls[1] == rolls[2] or rolls[0] == rolls[2]: # Hai biểu tượng giống nhau
            winnings = bet * 2 # Thưởng gấp 2 lần tiền cược
            result_msg += f"✨ Bạn thắng **{winnings:,}** {CURRENCY_SYMBOL}! ✨"
        else: # Không có biểu tượng nào giống nhau
            result_msg += f"😭 Bạn thua rồi và mất **{bet:,}** {CURRENCY_SYMBOL}. 😭" # Thông báo thua cược
            # Tiền cược đã bị trừ, không cần trừ thêm. Winnings là 0.

        # Nếu thắng, user_data["balance"] sẽ được cộng winnings (tiền thắng + tiền cược ban đầu)
        # Nếu thua, winnings là 0, user_data["balance"] không đổi (tiền cược đã bị trừ ở trên)
        if winnings > 0: # Chỉ cộng lại nếu thắng
             user_data["balance"] += winnings # Thắng thì nhận lại tiền cược + tiền thưởng (winnings đã bao gồm cả tiền cược gốc)
                                            # Ví dụ: cược 10, thắng x2 -> winnings = 20. Trừ 10, rồi cộng 20 -> lời 10.
        
        user_data["last_slots"] = datetime.now().timestamp()
        save_data(data)
        await try_send(ctx, content=result_msg + f"\nVí của bạn giờ là: **{user_data['balance']:,}** {CURRENCY_SYMBOL}.")

    @commands.command(name='coinflip', aliases=['cf'])
    async def coinflip(self, ctx: commands.Context, bet: int, choice: str):
        """Tung đồng xu và cược vào mặt Sấp (tails) hoặc Ngửa (heads)."""
        data = get_user_data(ctx.guild.id, ctx.author.id)
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]

        time_left = get_time_left_str(user_data.get("last_cf"), CF_COOLDOWN)
        if time_left:
            await try_send(ctx, content=f"Chơi chậm thôi! Lệnh `coinflip` chờ: **{time_left}**.")
            return
            
        choice_lower = choice.lower()
        valid_choices = {'heads', 'tails', 'ngửa', 'sấp', 'n', 's', 'h', 't'} # Thêm các lựa chọn viết tắt
        if choice_lower not in valid_choices:
            await try_send(ctx, content=f"Lựa chọn không hợp lệ. Hãy chọn: heads/ngửa (h/n) hoặc tails/sấp (t/s).")
            return
        if bet <= 0:
            await try_send(ctx, content="Tiền cược phải lớn hơn 0!")
            return
        
        player_choice_internal = "heads" if choice_lower in ["heads", "ngửa", "h", "n"] else "tails"

        if user_data.get("balance", 0) < bet:
            await try_send(ctx, content=f"Không đủ tiền! Ví của bạn: **{user_data.get('balance',0):,}** {CURRENCY_SYMBOL}.")
            return

        user_data["balance"] -= bet # Trừ tiền cược trước
        result_internal = random.choice(['heads', 'tails'])
        result_vn = "Ngửa" if result_internal == "heads" else "Sấp"
        
        msg = f"Đồng xu lật ra: **{result_vn}**! "
        if player_choice_internal == result_internal:
            winnings = bet * 2 # Tổng nhận lại (tiền cược ban đầu + tiền thắng bằng tiền cược)
            user_data["balance"] += winnings
            msg += f"Bạn đoán đúng và thắng cược, nhận lại tổng cộng **{winnings:,}** {CURRENCY_SYMBOL} (lời **{bet:,}** {CURRENCY_SYMBOL})!"
        else:
            msg += f"Bạn đoán sai và mất **{bet:,}** {CURRENCY_SYMBOL}."
        
        user_data["last_cf"] = datetime.now().timestamp()
        save_data(data)
        await try_send(ctx, content=msg + f"\nVí của bạn giờ là: **{user_data['balance']:,}** {CURRENCY_SYMBOL}.")

    @commands.command(name='dice', aliases=['roll'])
    async def dice(self, ctx: commands.Context, bet: int):
        """Đổ một cặp xúc xắc. Nếu tổng điểm lớn hơn 7, bạn thắng và nhận lại 1.5 lần tiền cược của mình (tức là lời 0.5 lần)."""
        data = get_user_data(ctx.guild.id, ctx.author.id)
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]

        time_left = get_time_left_str(user_data.get("last_dice"), DICE_COOLDOWN)
        if time_left:
            await try_send(ctx, content=f"Chơi chậm thôi! Lệnh `dice` chờ: **{time_left}**.")
            return
            
        if bet <= 0:
            await try_send(ctx, content="Tiền cược phải lớn hơn 0!")
            return
        if user_data.get("balance", 0) < bet:
            await try_send(ctx, content=f"Không đủ tiền! Ví của bạn: **{user_data.get('balance',0):,}** {CURRENCY_SYMBOL}.")
            return

        user_data["balance"] -= bet # Trừ tiền cược trước
        d1, d2 = random.randint(1, 6), random.randint(1, 6)
        total = d1 + d2
        
        msg = f"Bạn đổ ra: 🎲 **{d1}** + **{d2}** = **{total}** 🎲. "
        if total > 7:
            # Thắng: nhận lại tiền cược + 0.5 lần tiền cược
            profit = int(bet * 0.5) # Tiền lời
            total_received = bet + profit # Tổng nhận lại
            user_data["balance"] += total_received
            msg += f"Bạn thắng! Nhận lại tổng cộng **{total_received:,}** {CURRENCY_SYMBOL} (lời **{profit:,}** {CURRENCY_SYMBOL})!"
        else:
            # Thua: mất tiền cược (đã trừ ở trên)
            msg += f"Bạn thua và mất **{bet:,}** {CURRENCY_SYMBOL}."
            
        user_data["last_dice"] = datetime.now().timestamp()
        save_data(data)
        await try_send(ctx, content=msg + f"\nVí của bạn giờ là: **{user_data['balance']:,}** {CURRENCY_SYMBOL}.")

# Hàm setup để bot có thể load cog này
def setup(bot: commands.Bot):
    bot.add_cog(GamesCog(bot))

