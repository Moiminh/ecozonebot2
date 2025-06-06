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
from core.config import CURRENCY_SYMBOL, CF_COOLDOWN
from core.icons import ICON_LOADING, ICON_ERROR, ICON_WARNING, ICON_MONEY_BAG, ICON_COINFLIP_HEADS, ICON_COINFLIP_TAILS

logger = logging.getLogger(__name__)

class CoinflipCommandCog(commands.Cog, name="Coinflip Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"CoinflipCommandCog initialized for Ecoworld Economy.")

    @commands.command(name='coinflip', aliases=['cf'])
    async def coinflip(self, ctx: commands.Context, bet: int, choice: str):
        author_id = ctx.author.id
        guild_name_for_log = ctx.guild.name if ctx.guild else "DM"

        logger.debug(f"Lệnh 'coinflip' được gọi bởi {ctx.author.name} ({author_id}) với cược {bet}, lựa chọn '{choice}' tại guild '{guild_name_for_log}'.")
        
        economy_data = load_economy_data()
        user_profile = get_or_create_global_user_profile(economy_data, author_id)
        original_global_balance = user_profile.get("global_balance", 0)

        time_left = get_time_left_str(user_profile.get("last_cf_global"), CF_COOLDOWN)
        if time_left:
            await try_send(ctx, content=f"{ICON_LOADING} Chơi chậm thôi! Lệnh `coinflip` (toàn cục) chờ: **{time_left}**.")
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
            await try_send(ctx, content=f"{ICON_WARNING} Lựa chọn không hợp lệ. Hãy chọn: heads/ngửa (h/n) hoặc tails/sấp (t/s).")
            return

        if bet <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Tiền cược phải lớn hơn 0!")
            return
        
        if original_global_balance < bet:
            await try_send(ctx, content=f"{ICON_ERROR} Không đủ tiền trong Ví Toàn Cục! {ICON_MONEY_BAG} Ví của bạn: **{original_global_balance:,}** {CURRENCY_SYMBOL}.")
            return

        user_profile["global_balance"] = original_global_balance - bet
        
        result_internal = random.choice(['heads', 'tails'])
        logger.debug(f"User {author_id} chơi 'coinflip'. Lựa chọn: {player_choice_internal}, Kết quả tung: {result_internal}")
        
        result_display_icon = ICON_COINFLIP_HEADS if result_internal == "heads" else ICON_COINFLIP_TAILS
        result_vn_text = "Ngửa" if result_internal == "heads" else "Sấp"
        
        msg_to_user = f"Đồng xu được tung... Kết quả là: {result_display_icon} **{result_vn_text}**!\n"
        log_outcome_message = ""
        
        if player_choice_internal == result_internal:
            winnings_payout = bet * 2
            user_profile["global_balance"] += winnings_payout
            msg_to_user += f"🎉 Chúc mừng! Bạn đoán đúng và thắng cược, nhận lại tổng cộng **{winnings_payout:,}** {CURRENCY_SYMBOL} (lời **{bet:,}** {CURRENCY_SYMBOL})!"
            log_outcome_message = f"Thắng. Lời {bet:,} {CURRENCY_SYMBOL}."
        else:
            msg_to_user += f"😭 Tiếc quá! Bạn đoán sai và mất **{bet:,}** {CURRENCY_SYMBOL}."
            log_outcome_message = f"Thua. Mất {bet:,} {CURRENCY_SYMBOL}."
        
        user_profile["last_cf_global"] = datetime.now().timestamp()
        save_economy_data(economy_data)

        logger.info(f"Guild Context: '{guild_name_for_log}' - User: {ctx.author.display_name} ({author_id}) chơi 'coinflip'. Cược: {bet:,} {CURRENCY_SYMBOL} vào '{player_choice_internal}'. "
                    f"Kết quả: {result_internal}. {log_outcome_message} "
                    f"Ví Toàn Cục: {original_global_balance:,} -> {user_profile['global_balance']:,}.")
        
        await try_send(ctx, content=msg_to_user + f"\n{ICON_MONEY_BAG} Ví Toàn Cục của bạn giờ là: **{user_profile['global_balance']:,}** {CURRENCY_SYMBOL}.")

def setup(bot: commands.Bot):
    bot.add_cog(CoinflipCommandCog(bot))
