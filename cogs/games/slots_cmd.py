import nextcord
from nextcord.ext import commands
import random
from datetime import datetime
import logging

from core.database import (
    load_economy_data,
    get_or_create_global_user_profile,
    get_or_create_user_server_data,
    save_economy_data
)
from core.utils import try_send, get_time_left_str
from core.config import CURRENCY_SYMBOL, SLOTS_COOLDOWN, SLOTS_EMOJIS
from core.icons import ICON_LOADING, ICON_ERROR, ICON_SLOTS, ICON_MONEY_BAG, ICON_INFO

logger = logging.getLogger(__name__)

class SlotsCommandCog(commands.Cog, name="Slots Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"SlotsCommandCog initialized for Ecoworld Economy.")

    @commands.command(name='slots', aliases=['sl'])
    async def slots(self, ctx: commands.Context, bet: int):
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server.")
            return

        author_id = ctx.author.id
        guild_id = ctx.guild.id
        
        logger.debug(f"Lệnh 'slots' được gọi bởi {ctx.author.name} ({author_id}) với số tiền cược {bet} tại guild '{ctx.guild.name}' ({guild_id}).")
        
        economy_data = load_economy_data()
        global_profile = get_or_create_global_user_profile(economy_data, author_id)
        
        time_left = get_time_left_str(global_profile.get("last_slots_global"), SLOTS_COOLDOWN)
        if time_left:
            await try_send(ctx, content=f"{ICON_LOADING} Chơi chậm thôi! Lệnh `slots` (toàn cục) chờ: **{time_left}**.")
            return
        
        if bet <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Tiền cược phải lớn hơn 0!")
            return
        
        server_data = get_or_create_user_server_data(global_profile, guild_id)
        local_balance_dict = server_data.get("local_balance", {"earned": 0, "admin_added": 0})
        original_earned_amount = local_balance_dict.get("earned", 0)
        original_admin_added_amount = local_balance_dict.get("admin_added", 0)
        total_local_balance = original_earned_amount + original_admin_added_amount

        if total_local_balance < bet:
            await try_send(ctx, content=f"{ICON_ERROR} Không đủ tiền trong Ví Local! Ví của bạn: **{total_local_balance:,}** {CURRENCY_SYMBOL}.")
            return

        admin_money_spent = min(original_admin_added_amount, bet)
        earned_money_spent = bet - admin_money_spent
        
        local_balance_dict["admin_added"] -= admin_money_spent
        local_balance_dict["earned"] -= earned_money_spent
        
        rolls = [random.choice(SLOTS_EMOJIS) for _ in range(3)]
        logger.debug(f"User {author_id} chơi 'slots'. Kết quả quay: {' | '.join(rolls)}")
        
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
            local_balance_dict["earned"] += winnings_payout
        
        global_profile["last_slots_global"] = datetime.now().timestamp()
        save_economy_data(economy_data)

        logger.info(f"Guild: {ctx.guild.name} ({guild_id}) - User: {ctx.author.display_name} ({author_id}) chơi 'slots' với cược {bet:,}. "
                    f"Kết quả: {' '.join(rolls)}. {result_text_for_log}. "
                    f"Ví Local: {total_local_balance:,} -> {local_balance_dict['earned'] + local_balance_dict['admin_added']:,}.")
        
        new_total_local_balance = local_balance_dict['earned'] + local_balance_dict['admin_added']
        final_message_to_user = header_msg + result_msg_for_user + f"\n{ICON_MONEY_BAG} Ví Local của bạn giờ là: **{new_total_local_balance:,}** {CURRENCY_SYMBOL}."
        await try_send(ctx, content=final_message_to_user)

def setup(bot: commands.Bot):
    bot.add_cog(SlotsCommandCog(bot))
