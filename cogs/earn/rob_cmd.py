# bot/cogs/earn/rob_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime
import logging # <<< Đã có hoặc thêm vào

from core.database import get_user_data, save_data, check_user 
from core.utils import try_send, get_time_left_str
from core.config import CURRENCY_SYMBOL, ROB_COOLDOWN, ROB_SUCCESS_RATE, ROB_FINE_RATE
from core.icons import ICON_LOADING, ICON_ERROR, ICON_INFO, ICON_ROB, ICON_MONEY_BAG # Đảm bảo có ICON_MONEY_BAG

logger = logging.getLogger(__name__) # <<< Đã có hoặc thêm vào

class RobCommandCog(commands.Cog, name="Rob Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info(f"{ICON_INFO} RobCommandCog initialized.") # Đổi sang INFO nếu muốn thấy trên console

    @commands.command(name='rob', aliases=['steal'])
    async def rob(self, ctx: commands.Context, target: nextcord.Member):
        """Cố gắng cướp tiền từ ví của một người dùng khác."""
        author = ctx.author
        logger.debug(f"Lệnh 'rob' được gọi bởi {author.name} (ID: {author.id}) nhắm vào {target.name} (ID: {target.id}) tại guild {ctx.guild.id}.")

        if target.id == author.id:
            logger.warning(f"User {author.id} cố gắng tự cướp mình.")
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không thể tự cướp mình!")
            return
        if target.bot:
            logger.warning(f"User {author.id} cố gắng cướp bot {target.name}.")
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không thể cướp bot!")
            return

        full_data = get_user_data(ctx.guild.id, author.id)
        author_data = full_data[str(ctx.guild.id)][str(author.id)]
        original_author_balance = author_data.get("balance", 0)

        time_left = get_time_left_str(author_data.get("last_rob"), ROB_COOLDOWN)
        if time_left:
            logger.debug(f"User {author.id} dùng lệnh 'rob' khi đang cooldown. Còn lại: {time_left}")
            # logger.info(f"User {author.display_name} ({author.id}) thử 'rob' {target.display_name} nhưng đang cooldown ({time_left}).") # Tùy chọn log INFO
            await try_send(ctx, content=f"{ICON_LOADING} Bạn vừa mới đi cướp xong! Lệnh `rob` chờ: **{time_left}**.")
            return

        full_data = check_user(full_data, ctx.guild.id, target.id)
        target_data = full_data.get(str(ctx.guild.id), {}).get(str(target.id))
        original_target_balance = target_data.get("balance", 0) if target_data else 0


        author_data["last_rob"] = datetime.now().timestamp() 

        if not target_data or original_target_balance < 100: # Mục tiêu quá nghèo hoặc không có dữ liệu
            logger.info(f"User {author.display_name} ({author.id}) thử 'rob' {target.display_name} ({target.id}) nhưng mục tiêu quá nghèo (dưới 100 {CURRENCY_SYMBOL}) hoặc không có dữ liệu. Số dư mục tiêu: {original_target_balance}")
            await try_send(ctx, content=f"{ICON_INFO} {target.mention} quá nghèo để cướp hoặc không có dữ liệu.")
            save_data(full_data) 
            return
        
        if random.random() < ROB_SUCCESS_RATE:
            min_rob_amount = int(original_target_balance * 0.10)
            max_rob_amount = int(original_target_balance * 0.40)
            max_rob_amount = max(min_rob_amount, max_rob_amount)
            
            robbed_amount = 0 # Khởi tạo
            if max_rob_amount > 0 :
                 robbed_amount = random.randint(min_rob_amount, max_rob_amount)
            
            if robbed_amount <= 0: # Nếu tính ra số tiền cướp được là 0 hoặc âm (do làm tròn số nhỏ)
                 logger.info(f"User {author.display_name} ({author.id}) thử 'rob' {target.display_name} ({target.id}) nhưng số tiền cướp được quá nhỏ ({robbed_amount}). Mục tiêu có: {original_target_balance}")
                 await try_send(ctx,content=f"{ICON_INFO} {target.mention} có quá ít tiền để cướp có ý nghĩa.")
                 save_data(full_data) 
                 return

            author_data["balance"] = original_author_balance + robbed_amount
            target_data["balance"] = original_target_balance - robbed_amount
            
            logger.info(f"ROB SUCCESS: {author.display_name} ({author.id}) đã cướp {robbed_amount:,} {CURRENCY_SYMBOL} từ {target.display_name} ({target.id}). "
                        f"Author balance: {original_author_balance:,} -> {author_data['balance']:,}. "
                        f"Target balance: {original_target_balance:,} -> {target_data['balance']:,}.")
            
            await try_send(ctx, content=f"{ICON_ROB} Bạn đã cướp thành công **{robbed_amount:,}** {CURRENCY_SYMBOL} từ {target.mention}! Mwahaha! {ICON_MONEY_BAG} Ví bạn: {author_data['balance']:,}")
        else:
            fine_amount = min(int(original_author_balance * ROB_FINE_RATE), original_author_balance) 
            author_data["balance"] = original_author_balance - fine_amount
            
            logger.info(f"ROB FAILED: {author.display_name} ({author.id}) cướp thất bại {target.display_name} ({target.id}) và bị phạt {fine_amount:,} {CURRENCY_SYMBOL}. "
                        f"Author balance: {original_author_balance:,} -> {author_data['balance']:,}.")

            await try_send(ctx, content=f"👮 {ICON_ERROR} Bạn đã bị bắt khi cố cướp {target.mention} và bị phạt **{fine_amount:,}** {CURRENCY_SYMBOL}. {ICON_MONEY_BAG} Ví bạn còn: {author_data['balance']:,}")
        save_data(full_data)
        logger.debug(f"Lệnh 'rob' từ {author.name} nhắm vào {target.name} đã xử lý xong.")

def setup(bot: commands.Bot):
    bot.add_cog(RobCommandCog(bot))
