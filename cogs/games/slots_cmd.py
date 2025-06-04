# bot/cogs/games/slots_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime
import logging # <<< THÊM IMPORT NÀY

from core.database import get_user_data, save_data
from core.utils import try_send, get_time_left_str
from core.config import CURRENCY_SYMBOL, SLOTS_COOLDOWN, SLOTS_EMOJIS
from core.icons import ICON_LOADING, ICON_ERROR, ICON_SLOTS, ICON_MONEY_BAG, ICON_INFO # Đảm bảo có ICON_INFO

logger = logging.getLogger(__name__) # <<< LẤY LOGGER CHO MODULE NÀY

class SlotsCommandCog(commands.Cog, name="Slots Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"SlotsCommandCog initialized.")

    @commands.command(name='slots', aliases=['sl'])
    async def slots(self, ctx: commands.Context, bet: int):
        """Chơi máy xèng may mắn! Đặt cược và thử vận may."""
        logger.debug(f"Lệnh 'slots' được gọi bởi {ctx.author.name} (ID: {ctx.author.id}) với số tiền cược {bet} tại guild {ctx.guild.id}.")
        
        data = get_user_data(ctx.guild.id, ctx.author.id)
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]

        original_balance = user_data.get("balance", 0) # Lấy số dư ban đầu để log

        time_left = get_time_left_str(user_data.get("last_slots"), SLOTS_COOLDOWN)
        if time_left:
            logger.debug(f"User {ctx.author.id} dùng lệnh 'slots' khi đang cooldown. Còn lại: {time_left}")
            await try_send(ctx, content=f"{ICON_LOADING} Chơi chậm thôi! Lệnh `slots` chờ: **{time_left}**.")
            return
        
        if bet <= 0:
            logger.warning(f"User {ctx.author.id} đặt cược không hợp lệ (<=0) cho 'slots': {bet}")
            await try_send(ctx, content=f"{ICON_ERROR} Tiền cược phải lớn hơn 0!")
            return
        if original_balance < bet:
            logger.warning(f"User {ctx.author.id} không đủ tiền cược {bet} cho 'slots'. Số dư: {original_balance}")
            await try_send(ctx, content=f"{ICON_ERROR} Không đủ tiền! Ví của bạn: **{original_balance:,}** {CURRENCY_SYMBOL}.")
            return

        user_data["balance"] -= bet 
        rolls = [random.choice(SLOTS_EMOJIS) for _ in range(3)]
        logger.debug(f"User {ctx.author.id} chơi 'slots', kết quả quay: {' | '.join(rolls)}")
        
        header_msg = f"{ICON_SLOTS} Máy xèng quay: **[{' | '.join(rolls)}]** {ICON_SLOTS}\n"
        result_text_for_log = "" # Để ghi log kết quả
        result_msg_for_user = "" # Để gửi cho người dùng
        winnings_payout = 0 

        if rolls[0] == rolls[1] == rolls[2]: 
            winnings_payout = bet * 10 
            result_text_for_log = f"JACKPOT! Thắng {winnings_payout - bet}" # Lời
            result_msg_for_user = f"🎉 **JACKPOT!** Bạn thắng lớn, nhận lại tổng cộng **{winnings_payout:,}** {CURRENCY_SYMBOL}! (Lời **{winnings_payout - bet:,}** {CURRENCY_SYMBOL})"
        elif rolls[0] == rolls[1] or rolls[1] == rolls[2] or rolls[0] == rolls[2]: 
            winnings_payout = bet * 2 
            result_text_for_log = f"Thắng thường. Thắng {winnings_payout - bet}" # Lời
            result_msg_for_user = f"✨ Chúc mừng! Bạn thắng, nhận lại tổng cộng **{winnings_payout:,}** {CURRENCY_SYMBOL}! (Lời **{winnings_payout - bet:,}** {CURRENCY_SYMBOL})"
        else: 
            result_text_for_log = f"Thua cược {bet}"
            result_msg_for_user = f"😭 Tiếc quá, bạn thua rồi và mất **{bet:,}** {CURRENCY_SYMBOL}."
            
        if winnings_payout > 0:
            user_data["balance"] += winnings_payout
        
        user_data["last_slots"] = datetime.now().timestamp()
        save_data(data)

        # Ghi log hành động của người chơi
        logger.info(f"User {ctx.author.display_name} ({ctx.author.id}) chơi 'slots' với cược {bet:,} {CURRENCY_SYMBOL}. "
                    f"Kết quả: {' '.join(rolls)}. {result_text_for_log}. "
                    f"Số dư: {original_balance:,} -> {user_data['balance']:,}.")
        
        final_message_to_user = header_msg + result_msg_for_user + f"\n{ICON_MONEY_BAG} Ví của bạn giờ là: **{user_data['balance']:,}** {CURRENCY_SYMBOL}."
        await try_send(ctx, content=final_message_to_user)
        logger.debug(f"Lệnh 'slots' cho {ctx.author.name} đã xử lý xong.")

def setup(bot: commands.Bot):
    bot.add_cog(SlotsCommandCog(bot))
