# bot/cogs/games/dice_cmd.py
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
from core.config import CURRENCY_SYMBOL, DICE_COOLDOWN # DICE_COOLDOWN giờ là global
from core.icons import ICON_LOADING, ICON_ERROR, ICON_MONEY_BAG, ICON_DICE, ICON_INFO

logger = logging.getLogger(__name__)

class DiceCommandCog(commands.Cog, name="Dice Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"DiceCommandCog initialized.")

    @commands.command(name='dice', aliases=['roll'])
    async def dice(self, ctx: commands.Context, bet: int):
        """Đổ một cặp xúc xắc. Nếu tổng điểm lớn hơn 7, bạn thắng và nhận lại 1.5 lần tiền cược (lời 0.5 lần)."""
        author_id = ctx.author.id
        guild_id = ctx.guild.id if ctx.guild else None
        guild_name_for_log = ctx.guild.name if ctx.guild else "DM"

        logger.debug(f"Lệnh 'dice' được gọi bởi {ctx.author.name} ({author_id}) với số tiền cược {bet} tại guild '{guild_name_for_log}' ({guild_id}).")
        
        economy_data = load_economy_data()
        user_profile = get_or_create_global_user_profile(economy_data, author_id)
        original_global_balance = user_profile.get("global_balance", 0)

        # Sử dụng cooldown toàn cục
        time_left = get_time_left_str(user_profile.get("last_dice_global"), DICE_COOLDOWN)
        if time_left:
            logger.debug(f"User {author_id} dùng lệnh 'dice' khi đang cooldown. Còn lại: {time_left}")
            await try_send(ctx, content=f"{ICON_LOADING} Chơi chậm thôi! Lệnh `dice` (toàn cục) chờ: **{time_left}**.")
            return
            
        if bet <= 0:
            logger.warning(f"User {author_id} đặt cược không hợp lệ (<=0) cho 'dice': {bet} tại guild '{guild_name_for_log}' ({guild_id}).")
            await try_send(ctx, content=f"{ICON_ERROR} Tiền cược phải lớn hơn 0!")
            return
        if original_global_balance < bet:
            logger.warning(f"User {author_id} không đủ tiền cược {bet} cho 'dice'. Số dư Ví Toàn Cục: {original_global_balance} tại guild '{guild_name_for_log}' ({guild_id}).")
            await try_send(ctx, content=f"{ICON_ERROR} Không đủ tiền trong Ví Toàn Cục! {ICON_MONEY_BAG} Ví của bạn: **{original_global_balance:,}** {CURRENCY_SYMBOL}.")
            return

        # Trừ tiền cược từ Ví Toàn Cục
        user_profile["global_balance"] = original_global_balance - bet
        
        d1 = random.randint(1, 6)
        d2 = random.randint(1, 6)
        total_roll = d1 + d2
        logger.debug(f"User {author_id} chơi 'dice'. Kết quả đổ xúc xắc: {d1} + {d2} = {total_roll}")
        
        dice_unicode_map = {
            1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"
        }
        d1_emoji = dice_unicode_map.get(d1, str(d1))
        d2_emoji = dice_unicode_map.get(d2, str(d2))

        msg_to_user = f"{ICON_DICE} Bạn đổ ra: {d1_emoji} + {d2_emoji} = **{total_roll}**.\n"
        log_outcome_message = ""
        
        if total_roll > 7: # Thắng
            profit = int(bet * 0.5) 
            total_received = bet + profit # Bao gồm cả tiền cược gốc trả lại
            user_profile["global_balance"] += total_received # Tiền thắng được cộng vào Ví Toàn Cục
            msg_to_user += f"🎉 Chúc mừng! Bạn thắng cược, nhận lại tổng cộng **{total_received:,}** {CURRENCY_SYMBOL} (lời **{profit:,}** {CURRENCY_SYMBOL})!"
            log_outcome_message = f"Thắng. Lời {profit:,} {CURRENCY_SYMBOL}."
        else: # Thua
            msg_to_user += f"😭 Tiếc quá! Bạn thua và mất **{bet:,}** {CURRENCY_SYMBOL}."
            log_outcome_message = f"Thua. Mất {bet:,} {CURRENCY_SYMBOL}."
            
        user_profile["last_dice_global"] = datetime.now().timestamp() # Cập nhật cooldown toàn cục
        save_economy_data(economy_data)

        logger.info(f"Guild: {guild_name_for_log} ({guild_id}) - User: {ctx.author.display_name} ({author_id}) chơi 'dice' với cược {bet:,} {CURRENCY_SYMBOL}. "
                    f"Kết quả xúc xắc: {d1}+{d2}={total_roll}. {log_outcome_message} "
                    f"Ví Toàn Cục: {original_global_balance:,} -> {user_profile['global_balance']:,}.")
        
        await try_send(ctx, content=msg_to_user + f"\n{ICON_MONEY_BAG} Ví Toàn Cục của bạn giờ là: **{user_profile['global_balance']:,}** {CURRENCY_SYMBOL}.")
        logger.debug(f"Lệnh 'dice' cho {ctx.author.name} tại guild '{guild_name_for_log}' ({guild_id}) đã xử lý xong.")

def setup(bot: commands.Bot):
    bot.add_cog(DiceCommandCog(bot))
