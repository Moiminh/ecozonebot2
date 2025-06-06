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
from core.config import CURRENCY_SYMBOL, ROB_COOLDOWN, ROB_SUCCESS_RATE, ROB_FINE_RATE
from core.icons import ICON_LOADING, ICON_ERROR, ICON_INFO, ICON_ROB, ICON_MONEY_BAG

logger = logging.getLogger(__name__)

class RobCommandCog(commands.Cog, name="Rob Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"RobCommandCog initialized for Ecoworld Economy.")

    @commands.command(name='rob', aliases=['steal'])
    async def rob(self, ctx: commands.Context, target: nextcord.Member):
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Bạn chỉ có thể thực hiện hành vi phạm tội này trong một server!")
            return
            
        author = ctx.author
        guild_id = ctx.guild.id
        
        logger.debug(f"Lệnh 'rob' được gọi bởi {author.name} ({author.id}) nhắm vào {target.name} ({target.id}) tại guild '{ctx.guild.name}' ({guild_id}).")

        if target.id == author.id:
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không thể tự cướp mình!")
            return
        if target.bot:
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không thể cướp bot!")
            return

        economy_data = load_economy_data()
        author_global_profile = get_or_create_global_user_profile(economy_data, author.id)
        
        time_left = get_time_left_str(author_global_profile.get("last_rob_global"), ROB_COOLDOWN)
        if time_left:
            await try_send(ctx, content=f"{ICON_LOADING} Bạn vừa mới đi cướp xong! Lệnh `rob` (toàn cục) chờ: **{time_left}**.")
            return

        target_global_profile = get_or_create_global_user_profile(economy_data, target.id)
        target_server_data = get_or_create_user_server_data(target_global_profile, guild_id)
        target_local_balance_dict = target_server_data.get("local_balance", {})
        original_target_local_balance = target_local_balance_dict.get("earned", 0) + target_local_balance_dict.get("admin_added", 0)

        author_global_profile["last_rob_global"] = datetime.now().timestamp()

        if original_target_local_balance < 200: # Cần một lượng tiền tối thiểu trong ví local của mục tiêu
            logger.info(f"ROB FAILED (TARGET POOR): User {author.display_name} ({author.id}) thử 'rob' {target.display_name} ({target.id}) nhưng ví local của mục tiêu quá nghèo (dưới 200).")
            await try_send(ctx, content=f"{ICON_INFO} {target.mention} quá nghèo để cướp tại server này.")
            save_economy_data(economy_data)
            return
        
        if random.random() < ROB_SUCCESS_RATE:
            min_rob_amount = int(original_target_local_balance * 0.10)
            max_rob_amount = int(original_target_local_balance * 0.30) # Giảm % cướp được tối đa
            max_rob_amount = max(min_rob_amount, max_rob_amount)
            
            robbed_amount = 0
            if max_rob_amount > 0:
                 robbed_amount = random.randint(min_rob_amount, max_rob_amount)
            
            if robbed_amount <= 0:
                 await try_send(ctx,content=f"{ICON_INFO} {target.mention} có quá ít tiền trong Ví Local để cướp có ý nghĩa.")
                 save_economy_data(economy_data)
                 return

            author_server_data = get_or_create_user_server_data(author_global_profile, guild_id)
            author_server_data["local_balance"]["earned"] += robbed_amount
            
            target_earned_deducted = min(target_local_balance_dict.get("earned", 0), robbed_amount)
            target_admin_deducted = robbed_amount - target_earned_deducted
            target_local_balance_dict["earned"] -= target_earned_deducted
            target_local_balance_dict["admin_added"] -= target_admin_deducted

            logger.info(f"ROB SUCCESS: Guild: {ctx.guild.name} ({guild_id}) - User {author.display_name} ({author.id}) đã cướp {robbed_amount:,} {CURRENCY_SYMBOL} từ {target.display_name} ({target.id}). Số tiền được cộng vào Ví Local (Earned) của người cướp.")
            
            await try_send(ctx, content=f"{ICON_ROB} Bạn đã cướp thành công **{robbed_amount:,}** {CURRENCY_SYMBOL} từ Ví Local của {target.mention}!")
        else:
            author_server_data = get_or_create_user_server_data(author_global_profile, guild_id)
            author_local_balance_dict = author_server_data.get("local_balance", {})
            original_author_total_local_balance = author_local_balance_dict.get("earned", 0) + author_local_balance_dict.get("admin_added", 0)
            
            fine_amount = min(int(original_author_total_local_balance * ROB_FINE_RATE), original_author_total_local_balance) 

            admin_money_deducted = min(author_local_balance_dict.get("admin_added", 0), fine_amount)
            earned_money_deducted = fine_amount - admin_money_deducted
            author_local_balance_dict["admin_added"] -= admin_money_deducted
            author_local_balance_dict["earned"] -= earned_money_deducted

            logger.info(f"ROB FAILED (CAUGHT): Guild: {ctx.guild.name} ({guild_id}) - User {author.display_name} ({author.id}) cướp thất bại {target.display_name} ({target.id}) và bị phạt {fine_amount:,} {CURRENCY_SYMBOL} từ Ví Local.")

            await try_send(ctx, content=f"👮 {ICON_ERROR} Bạn đã bị bắt khi cố cướp {target.mention} và bị phạt **{fine_amount:,}** {CURRENCY_SYMBOL} từ Ví Local của bạn.")
        
        save_economy_data(economy_data)
        logger.debug(f"Lệnh 'rob' từ {author.name} nhắm vào {target.name} tại guild {ctx.guild.name} đã xử lý xong.")

def setup(bot: commands.Bot):
    bot.add_cog(RobCommandCog(bot))
