# bot/cogs/games/slots_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime

from core.database import get_user_data, save_data
from core.utils import try_send, get_time_left_str
from core.config import CURRENCY_SYMBOL, SLOTS_COOLDOWN, SLOTS_EMOJIS
from core.icons import ICON_LOADING, ICON_ERROR, ICON_SLOTS, ICON_MONEY_BAG

class SlotsCommandCog(commands.Cog, name="Slots Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='slots', aliases=['sl'])
    async def slots(self, ctx: commands.Context, bet: int):
        """Chơi máy xèng may mắn! Đặt cược và thử vận may."""
        data = get_user_data(ctx.guild.id, ctx.author.id)
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]

        time_left = get_time_left_str(user_data.get("last_slots"), SLOTS_COOLDOWN)
        if time_left:
            await try_send(ctx, content=f"{ICON_LOADING} Chơi chậm thôi! Lệnh `slots` chờ: **{time_left}**.")
            return
        
        if bet <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Tiền cược phải lớn hơn 0!")
            return
        if user_data.get("balance", 0) < bet:
            await try_send(ctx, content=f"{ICON_ERROR} Không đủ tiền! Ví của bạn: **{user_data.get('balance',0):,}** {CURRENCY_SYMBOL}.")
            return

        user_data["balance"] -= bet # Trừ tiền cược trước
        rolls = [random.choice(SLOTS_EMOJIS) for _ in range(3)]
        
        header_msg = f"{ICON_SLOTS} Máy xèng quay: **[{' | '.join(rolls)}]** {ICON_SLOTS}\n"
        result_msg = ""
        winnings_payout = 0 # Tổng tiền trả lại (bao gồm cả cược gốc nếu thắng)

        if rolls[0] == rolls[1] == rolls[2]: # Jackpot
            winnings_payout = bet * 10 
            result_msg = f"🎉 **JACKPOT!** Bạn thắng lớn, nhận lại tổng cộng **{winnings_payout:,}** {CURRENCY_SYMBOL}! (Lời **{winnings_payout - bet:,}** {CURRENCY_SYMBOL})"
        elif rolls[0] == rolls[1] or rolls[1] == rolls[2] or rolls[0] == rolls[2]: # Thắng thường
            winnings_payout = bet * 2 
            result_msg = f"✨ Chúc mừng! Bạn thắng, nhận lại tổng cộng **{winnings_payout:,}** {CURRENCY_SYMBOL}! (Lời **{winnings_payout - bet:,}** {CURRENCY_SYMBOL})"
        else: # Thua
            result_msg = f"😭 Tiếc quá, bạn thua rồi và mất **{bet:,}** {CURRENCY_SYMBOL}."
            # winnings_payout vẫn là 0

        if winnings_payout > 0:
            user_data["balance"] += winnings_payout # Cộng lại tiền thắng (đã bao gồm cược gốc)
        
        user_data["last_slots"] = datetime.now().timestamp()
        save_data(data)
        
        final_message = header_msg + result_msg + f"\n{ICON_MONEY_BAG} Ví của bạn giờ là: **{user_data['balance']:,}** {CURRENCY_SYMBOL}."
        await try_send(ctx, content=final_message)

def setup(bot: commands.Bot):
    bot.add_cog(SlotsCommandCog(bot))
