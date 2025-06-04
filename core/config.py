# bot/cogs/games/coinflip_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime
import logging # <<< THÊM IMPORT NÀY

from core.database import get_user_data, save_data
from core.utils import try_send, get_time_left_str
from core.config import CURRENCY_SYMBOL, CF_COOLDOWN
from core.icons import ( # Đảm bảo các icon này có trong core/icons.py
    ICON_LOADING, ICON_ERROR, ICON_WARNING, ICON_MONEY_BAG, 
    ICON_COINFLIP_HEADS, ICON_COINFLIP_TAILS, ICON_INFO
)

logger = logging.getLogger(__name__) # <<< LẤY LOGGER CHO MODULE NÀY

class CoinflipCommandCog(commands.Cog, name="Coinflip Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"CoinflipCommandCog initialized.")

    @commands.command(name='coinflip', aliases=['cf'])
    async def coinflip(self, ctx: commands.Context, bet: int, choice: str):
        """Tung đồng xu và cược vào mặt Sấp (tails/s) hoặc Ngửa (heads/h/n)."""
        logger.debug(f"Lệnh 'coinflip' được gọi bởi {ctx.author.name} (ID: {ctx.author.id}) với cược {bet}, lựa chọn '{choice}' tại guild {ctx.guild.id}.")
        
        data = get_user_data(ctx.guild.id, ctx.author.id)
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]
        original_balance = user_data.get("balance", 0)

        time_left = get_time_left_str(user_data.get("last_cf"), CF_COOLDOWN)
        if time_left:
            logger.debug(f"User {ctx.author.id} dùng lệnh 'coinflip' khi đang cooldown. Còn lại: {time_left}")
            await try_send(ctx, content=f"{ICON_LOADING} Chơi chậm thôi! Lệnh `coinflip` chờ: **{time_left}**.")
            return
            
        choice_lower = choice.lower()
        valid_choices_heads = {'heads', 'ngửa', 'h', 'n'}
        valid_choices_tails = {'tails', 'sấp', 't', 's'}
        
        player_choice_internal = None
        if choice_lower in valid_choices_heads:
            player_choice_internal = "heads"
        elif choice_lower in valid_choices_tails:
            player_choice_internal = "tails"
        else:
            logger.warning(f"User {ctx.author.id} nhập lựa chọn không hợp lệ cho 'coinflip': '{choice}'")
            await try_send(ctx, content=f"{ICON_WARNING} Lựa chọn không hợp lệ. Hãy chọn: heads/ngửa (h/n) hoặc tails/sấp (t/s).")
            return

        if bet <= 0:
            logger.warning(f"User {ctx.author.id} đặt cược không hợp lệ (<=0) cho 'coinflip': {bet}")
            await try_send(ctx, content=f"{ICON_ERROR} Tiền cược phải lớn hơn 0!")
            return
        
        if original_balance < bet:
            logger.warning(f"User {ctx.author.id} không đủ tiền cược {bet} cho 'coinflip'. Số dư: {original_balance}")
            await try_send(ctx, content=f"{ICON_ERROR} Không đủ tiền! Ví của bạn: **{original_balance:,}** {CURRENCY_SYMBOL}.")
            return

        user_data["balance"] -= bet 
        result_internal = random.choice(['heads', 'tails'])
        logger.debug(f"User {ctx.author.id} chơi 'coinflip'. Lựa chọn: {player_choice_internal}, Kết quả tung: {result_internal}")
        
        result_display_icon = ICON_COINFLIP_HEADS if result_internal == "heads" else ICON_COINFLIP_TAILS
        result_vn_text = "Ngửa" if result_internal == "heads" else "Sấp"
        
        msg_to_user = f"Đồng xu được tung... Kết quả là: {result_display_icon} **{result_vn_text}**!\n"
        log_outcome_message = ""
        
        if player_choice_internal == result_internal:
            winnings_payout = bet * 2 
            user_data["balance"] += winnings_payout
            msg_to_user += f"🎉 Chúc mừng! Bạn đoán đúng và thắng cược, nhận lại tổng cộng **{winnings_payout:,}** {CURRENCY_SYMBOL} (lời **{bet:,}** {CURRENCY_SYMBOL})!"
            log_outcome_message = f"Thắng. Lời {bet:,} {CURRENCY_SYMBOL}."
        else:
            msg_to_user += f"😭 Tiếc quá! Bạn đoán sai và mất **{bet:,}** {CURRENCY_SYMBOL}."
            log_outcome_message = f"Thua. Mất {bet:,} {CURRENCY_SYMBOL}."
        
        user_data["last_cf"] = datetime.now().timestamp()
        save_data(data)

        # Ghi log hành động của người chơi
        logger.info(f"User {ctx.author.display_name} ({ctx.author.id}) chơi 'coinflip'. Cược: {bet:,} {CURRENCY_SYMBOL} vào '{player_choice_internal}'. "
                    f"Kết quả: {result_internal}. {log_outcome_message} "
                    f"Số dư: {original_balance:,} -> {user_data['balance']:,}.")
        
        await try_send(ctx, content=msg_to_user + f"\n{ICON_MONEY_BAG} Ví của bạn giờ là: **{user_data['balance']:,}** {CURRENCY_SYMBOL}.")
        logger.debug(f"Lệnh 'coinflip' cho {ctx.author.name} đã xử lý xong.")

def setup(bot: commands.Bot):
    bot.add_cog(CoinflipCommandCog(bot))
