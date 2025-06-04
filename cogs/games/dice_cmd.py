# bot/cogs/games/dice_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime
import logging # <<< THÊM IMPORT NÀY

from core.database import get_user_data, save_data
from core.utils import try_send, get_time_left_str
from core.config import CURRENCY_SYMBOL, DICE_COOLDOWN
from core.icons import ICON_LOADING, ICON_ERROR, ICON_MONEY_BAG, ICON_DICE, ICON_INFO # Đảm bảo có ICON_INFO

logger = logging.getLogger(__name__) # <<< LẤY LOGGER CHO MODULE NÀY

class DiceCommandCog(commands.Cog, name="Dice Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"DiceCommandCog initialized.")

    @commands.command(name='dice', aliases=['roll'])
    async def dice(self, ctx: commands.Context, bet: int):
        """Đổ một cặp xúc xắc. Nếu tổng điểm lớn hơn 7, bạn thắng và nhận lại 1.5 lần tiền cược (lời 0.5 lần)."""
        logger.debug(f"Lệnh 'dice' được gọi bởi {ctx.author.name} (ID: {ctx.author.id}) với số tiền cược {bet} tại guild {ctx.guild.id}.")
        
        data = get_user_data(ctx.guild.id, ctx.author.id)
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]
        original_balance = user_data.get("balance", 0)

        time_left = get_time_left_str(user_data.get("last_dice"), DICE_COOLDOWN)
        if time_left:
            logger.debug(f"User {ctx.author.id} dùng lệnh 'dice' khi đang cooldown. Còn lại: {time_left}")
            await try_send(ctx, content=f"{ICON_LOADING} Chơi chậm thôi! Lệnh `dice` chờ: **{time_left}**.")
            return
            
        if bet <= 0:
            logger.warning(f"User {ctx.author.id} đặt cược không hợp lệ (<=0) cho 'dice': {bet}")
            await try_send(ctx, content=f"{ICON_ERROR} Tiền cược phải lớn hơn 0!")
            return
        if original_balance < bet:
            logger.warning(f"User {ctx.author.id} không đủ tiền cược {bet} cho 'dice'. Số dư: {original_balance}")
            await try_send(ctx, content=f"{ICON_ERROR} Không đủ tiền! Ví của bạn: **{original_balance:,}** {CURRENCY_SYMBOL}.")
            return

        user_data["balance"] -= bet 
        d1 = random.randint(1, 6)
        d2 = random.randint(1, 6)
        total_roll = d1 + d2 # Đổi tên biến từ 'total' để tránh nhầm lẫn
        logger.debug(f"User {ctx.author.id} chơi 'dice'. Kết quả đổ xúc xắc: {d1} + {d2} = {total_roll}")
        
        dice_unicode_map = {
            1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"
        }
        d1_emoji = dice_unicode_map.get(d1, str(d1))
        d2_emoji = dice_unicode_map.get(d2, str(d2))

        msg_to_user = f"{ICON_DICE} Bạn đổ ra: {d1_emoji} + {d2_emoji} = **{total_roll}**.\n"
        log_outcome_message = ""
        
        if total_roll > 7:
            profit = int(bet * 0.5) 
            total_received = bet + profit 
            user_data["balance"] += total_received
            msg_to_user += f"🎉 Chúc mừng! Bạn thắng cược, nhận lại tổng cộng **{total_received:,}** {CURRENCY_SYMBOL} (lời **{profit:,}** {CURRENCY_SYMBOL})!"
            log_outcome_message = f"Thắng. Lời {profit:,} {CURRENCY_SYMBOL}."
        else:
            msg_to_user += f"😭 Tiếc quá! Bạn thua và mất **{bet:,}** {CURRENCY_SYMBOL}."
            log_outcome_message = f"Thua. Mất {bet:,} {CURRENCY_SYMBOL}."
            
        user_data["last_dice"] = datetime.now().timestamp()
        save_data(data)

        # Ghi log hành động của người chơi
        logger.info(f"User {ctx.author.display_name} ({ctx.author.id}) chơi 'dice' với cược {bet:,} {CURRENCY_SYMBOL}. "
                    f"Kết quả xúc xắc: {d1}+{d2}={total_roll}. {log_outcome_message} "
                    f"Số dư: {original_balance:,} -> {user_data['balance']:,}.")
        
        await try_send(ctx, content=msg_to_user + f"\n{ICON_MONEY_BAG} Ví của bạn giờ là: **{user_data['balance']:,}** {CURRENCY_SYMBOL}.")
        logger.debug(f"Lệnh 'dice' cho {ctx.author.name} đã xử lý xong.")

def setup(bot: commands.Bot):
    bot.add_cog(DiceCommandCog(bot))
