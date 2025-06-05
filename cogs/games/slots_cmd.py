# bot/cogs/games/slots_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime
import logging

from core.database import (
    load_economy_data,
    get_or_create_global_user_profile,
    save_economy_data
)
from core.utils import try_send, get_time_left_str
from core.config import CURRENCY_SYMBOL, SLOTS_COOLDOWN, SLOTS_EMOJIS
from core.icons import ICON_LOADING, ICON_ERROR, ICON_SLOTS, ICON_MONEY_BAG, ICON_INFO

logger = logging.getLogger(__name__)

class SlotsCommandCog(commands.Cog, name="Slots Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"SlotsCommandCog initialized.")

    @commands.command(name='slots', aliases=['sl'])
    async def slots(self, ctx: commands.Context, bet: int):
        author_id = ctx.author.id
        guild_id = ctx.guild.id if ctx.guild else None
        guild_name_for_log = ctx.guild.name if ctx.guild else "DM"

        logger.debug(f"Lệnh 'slots' được gọi bởi {ctx.author.name} ({author_id}) với số tiền cược {bet} tại guild '{guild_name_for_log}' ({guild_id}).")
        
        economy_data = load_economy_data()
        user_profile = get_or_create_global_user_profile(economy_data, author_id)
        original_global_balance = user_profile.get("global_balance", 0)

        time_left = get_time_left_str(user_profile.get("last_slots_global"), SLOTS_COOLDOWN)
        if time_left:
            logger.debug(f"User {author_id} dùng lệnh 'slots' khi đang cooldown. Còn lại: {time_left}")
            await try_send(ctx, content=f"{ICON_LOADING} Chơi chậm thôi! Lệnh `slots` (toàn cục) chờ: **{time_left}**.")
            return
        
        if bet <= 0:
            logger.warning(f"User {author_id} đặt cược không hợp lệ (<=0) cho 'slots': {bet}")
            await try_send(ctx, content=f"{ICON_ERROR} Tiền cược phải lớn hơn 0!")
            return
        if original_global_balance < bet:
            logger.warning(f"User {author_id} không đủ tiền cược {bet} cho 'slots'. Số dư Ví Toàn Cục: {original_global_balance}")
            await try_send(ctx, content=f"{ICON_ERROR} Không đủ tiền trong Ví Toàn Cục! {ICON_MONEY_BAG} Ví của bạn: **{original_global_balance:,}** {CURRENCY_SYMBOL}.")
            return

        # Trừ tiền cược từ Ví Toàn Cục
        user_profile["global_balance"] = original_global_balance - bet
        
        rolls = [random.choice(SLOTS_EMOJIS) for _ in range(3)]
        logger.debug(f"User {author_id} chơi 'slots', kết quả quay: {' | '.join(rolls)}")
        
        header_msg = f"{ICON_SLOTS} Máy xèng quay: **[{' | '.join(rolls)}]** {ICON_SLOTS}\n"
        result_text_for_log = "" 
        result_msg_for_user = "" 
        winnings_payout = 0 

        if rolls[0] == rolls[1] == rolls[2]: 
            winnings_payout = bet * 10 
            result_text_for_log = f"JACKPOT! Thắng {winnings_payout - bet}" 
            result_msg_for_user = f"🎉 **JACKPOT!** Bạn thắng lớn, nhận lại tổng cộng **{winnings_payout:,}** {CURRENCY_SYMBOL}! (Lời **{winnings_payout - bet:,}** {CURRENCY_SYMBOL})"
        elif rolls[0] == rolls[1] or rolls[1] == rolls[2] or rolls[0] == rolls[2]: 
            winnings_payout = bet * 2 
            result_text_for_log = f"Thắng thường. Thắng {winnings_payout - bet}"
            result_msg_for_user = f"✨ Chúc mừng! Bạn thắng, nhận lại tổng cộng **{winnings_payout:,}** {CURRENCY_SYMBOL}! (Lời **{winnings_payout - bet:,}** {CURRENCY_SYMBOL})"
        else: 
            result_text_for_log = f"Thua cược {bet}"
            result_msg_for_user = f"😭 Tiếc quá, bạn thua rồi và mất **{bet:,}** {CURRENCY_SYMBOL}."
            
        if winnings_payout > 0:
            user_profile["global_balance"] += winnings_payout # Tiền thắng được cộng vào Ví Toàn Cục
        
        user_profile["last_slots_global"] = datetime.now().timestamp() # Cập nhật cooldown toàn cục
        save_economy_data(economy_data)

        logger.info(f"Guild: {guild_name_for_log} ({guild_id}) - User: {ctx.author.display_name} ({author_id}) chơi 'slots' với cược {bet:,} {CURRENCY_SYMBOL}. "
                    f"Kết quả: {' '.join(rolls)}. {result_text_for_log}. "
                    f"Ví Toàn Cục: {original_global_balance:,} -> {user_profile['global_balance']:,}.")
        
        final_message_to_user = header_msg + result_msg_for_user + f"\n{ICON_MONEY_BAG} Ví Toàn Cục của bạn giờ là: **{user_profile['global_balance']:,}** {CURRENCY_SYMBOL}."
        await try_send(ctx, content=final_message_to_user)
        logger.debug(f"Lệnh 'slots' cho {ctx.author.name} tại guild '{guild_name_for_log}' ({guild_id}) đã xử lý xong.")

def setup(bot: commands.Bot):
    bot.add_cog(SlotsCommandCog(bot))
