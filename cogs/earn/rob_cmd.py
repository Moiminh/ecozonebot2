# bot/cogs/earn/rob_cmd.py
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
from core.config import CURRENCY_SYMBOL, ROB_COOLDOWN, ROB_SUCCESS_RATE, ROB_FINE_RATE
from core.icons import ICON_LOADING, ICON_ERROR, ICON_INFO, ICON_ROB, ICON_MONEY_BAG

logger = logging.getLogger(__name__)

class RobCommandCog(commands.Cog, name="Rob Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"RobCommandCog initialized.")

    @commands.command(name='rob', aliases=['steal'])
    async def rob(self, ctx: commands.Context, target: nextcord.User):
        author = ctx.author
        guild_name_for_log = ctx.guild.name if ctx.guild else "DM"
        guild_id_for_log = ctx.guild.id if ctx.guild else "N/A"

        logger.debug(f"Lệnh 'rob' được gọi bởi {author.name} ({author.id}) nhắm vào {target.name} ({target.id}) tại context guild '{guild_name_for_log}' ({guild_id_for_log}).")

        if target.id == author.id:
            logger.warning(f"User {author.id} cố gắng tự cướp mình.")
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không thể tự cướp mình!")
            return
        if target.bot:
            logger.warning(f"User {author.id} cố gắng cướp bot {target.name}.")
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không thể cướp bot!")
            return

        economy_data = load_economy_data()
        author_profile = get_or_create_global_user_profile(economy_data, author.id)
        original_author_balance = author_profile.get("global_balance", 0)

        time_left = get_time_left_str(author_profile.get("last_rob_global"), ROB_COOLDOWN)
        if time_left:
            logger.debug(f"User {author.id} dùng lệnh 'rob' khi đang cooldown. Còn lại: {time_left}")
            await try_send(ctx, content=f"{ICON_LOADING} Bạn vừa mới đi cướp xong! Lệnh `rob` (toàn cục) chờ: **{time_left}**.")
            return

        target_profile = get_or_create_global_user_profile(economy_data, target.id)
        original_target_balance = target_profile.get("global_balance", 0)

        author_profile["last_rob_global"] = datetime.now().timestamp()

        if original_target_balance < 100:
            logger.info(f"User {author.display_name} ({author.id}) thử 'rob' {target.display_name} ({target.id}) nhưng mục tiêu quá nghèo (dưới 100). Số dư mục tiêu: {original_target_balance}")
            await try_send(ctx, content=f"{ICON_INFO} {target.mention} quá nghèo để cướp.")
            save_economy_data(economy_data)
            return
        
        if random.random() < ROB_SUCCESS_RATE:
            min_rob_amount = int(original_target_balance * 0.10)
            max_rob_amount = int(original_target_balance * 0.40)
            max_rob_amount = max(min_rob_amount, max_rob_amount)
            
            robbed_amount = 0
            if max_rob_amount > 0:
                 robbed_amount = random.randint(min_rob_amount, max_rob_amount)
            
            if robbed_amount <= 0:
                 logger.info(f"User {author.display_name} ({author.id}) thử 'rob' {target.display_name} ({target.id}) nhưng số tiền cướp được quá nhỏ ({robbed_amount}). Mục tiêu có: {original_target_balance}")
                 await try_send(ctx,content=f"{ICON_INFO} {target.mention} có quá ít tiền để cướp có ý nghĩa.")
                 save_economy_data(economy_data)
                 return

            author_profile["global_balance"] = original_author_balance + robbed_amount
            target_profile["global_balance"] = original_target_balance - robbed_amount
            
            logger.info(f"ROB SUCCESS: {author.display_name} ({author.id}) đã cướp {robbed_amount:,} {CURRENCY_SYMBOL} từ {target.display_name} ({target.id}) tại context guild '{guild_name_for_log}'. "
                        f"Author global_balance: {original_author_balance:,} -> {author_profile['global_balance']:,}. "
                        f"Target global_balance: {original_target_balance:,} -> {target_profile['global_balance']:,}.")
            
            await try_send(ctx, content=f"{ICON_ROB} Bạn đã cướp thành công **{robbed_amount:,}** {CURRENCY_SYMBOL} từ Ví Toàn Cục của {target.mention}! {ICON_MONEY_BAG} Ví bạn: {author_profile['global_balance']:,}")
        else:
            fine_amount = min(int(original_author_balance * ROB_FINE_RATE), original_author_balance) 
            author_profile["global_balance"] = original_author_balance - fine_amount
            
            logger.info(f"ROB FAILED: {author.display_name} ({author.id}) cướp thất bại {target.display_name} ({target.id}) và bị phạt {fine_amount:,} {CURRENCY_SYMBOL} tại context guild '{guild_name_for_log}'. "
                        f"Author global_balance: {original_author_balance:,} -> {author_profile['global_balance']:,}.")

            await try_send(ctx, content=f"👮 {ICON_ERROR} Bạn đã bị bắt khi cố cướp {target.mention} và bị phạt **{fine_amount:,}** {CURRENCY_SYMBOL}. {ICON_MONEY_BAG} Ví bạn còn: {author_profile['global_balance']:,}")
        
        save_economy_data(economy_data)
        logger.debug(f"Lệnh 'rob' từ {author.name} nhắm vào {target.name} đã xử lý xong.")

def setup(bot: commands.Bot):
    bot.add_cog(RobCommandCog(bot))
