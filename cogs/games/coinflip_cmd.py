# bot/cogs/games/coinflip_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime

from core.database import get_user_data, save_data
from core.utils import try_send, get_time_left_str
from core.config import CURRENCY_SYMBOL, CF_COOLDOWN
from core.icons import ICON_LOADING, ICON_ERROR, ICON_WARNING, ICON_MONEY_BAG, ICON_COINFLIP_HEADS, ICON_COINFLIP_TAILS

class CoinflipCommandCog(commands.Cog, name="Coinflip Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='coinflip', aliases=['cf'])
    async def coinflip(self, ctx: commands.Context, bet: int, choice: str):
        """Tung đồng xu và cược vào mặt Sấp (tails/s) hoặc Ngửa (heads/h/n)."""
        data = get_user_data(ctx.guild.id, ctx.author.id)
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]

        time_left = get_time_left_str(user_data.get("last_cf"), CF_COOLDOWN)
        if time_left:
            await try_send(ctx, content=f"{ICON_LOADING} Chơi chậm thôi! Lệnh `coinflip` chờ: **{time_left}**.")
            return
            
        choice_lower = choice.lower()
        # Mở rộng các lựa chọn hợp lệ
        valid_choices_heads = {'heads', 'ngửa', 'h', 'n'}
        valid_choices_tails = {'tails', 'sấp', 't', 's'}
        
        player_choice_internal = None
        if choice_lower in valid_choices_heads:
            player_choice_internal = "heads"
        elif choice_lower in valid_choices_tails:
            player_choice_internal = "tails"
        else:
            await try_send(ctx, content=f"{ICON_WARNING} Lựa chọn không hợp lệ. Hãy chọn: heads/ngửa (h/n) hoặc tails/sấp (t/s).")
            return

        if bet <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Tiền cược phải lớn hơn 0!")
            return
        
        if user_data.get("balance", 0) < bet:
            await try_send(ctx, content=f"{ICON_ERROR} Không đủ tiền! Ví của bạn: **{user_data.get('balance',0):,}** {CURRENCY_SYMBOL}.")
            return

        user_data["balance"] -= bet # Trừ tiền cược trước
        result_internal = random.choice(['heads', 'tails'])
        
        result_display_icon = ICON_COINFLIP_HEADS if result_internal == "heads" else ICON_COINFLIP_TAILS
        result_vn_text = "Ngửa" if result_internal == "heads" else "Sấp"
        
        msg = f"Đồng xu được tung... Kết quả là: {result_display_icon} **{result_vn_text}**!\n"
        
        if player_choice_internal == result_internal:
            winnings_payout = bet * 2 # Tổng nhận lại (cược gốc + lời bằng cược gốc)
            user_data["balance"] += winnings_payout
            msg += f"🎉 Chúc mừng! Bạn đoán đúng và thắng cược, nhận lại tổng cộng **{winnings_payout:,}** {CURRENCY_SYMBOL} (lời **{bet:,}** {CURRENCY_SYMBOL})!"
        else:
            msg += f"😭 Tiếc quá! Bạn đoán sai và mất **{bet:,}** {CURRENCY_SYMBOL}."
        
        user_data["last_cf"] = datetime.now().timestamp()
        save_data(data)
        await try_send(ctx, content=msg + f"\n{ICON_MONEY_BAG} Ví của bạn giờ là: **{user_data['balance']:,}** {CURRENCY_SYMBOL}.")

def setup(bot: commands.Bot):
    bot.add_cog(CoinflipCommandCog(bot))
