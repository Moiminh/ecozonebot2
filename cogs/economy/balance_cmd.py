# bot/cogs/economy/balance_cmd.py
import nextcord
from nextcord.ext import commands
import logging 

# Import các hàm mới từ database và các thành phần khác
from core.database import load_economy_data, get_or_create_global_user_profile, save_economy_data # Thêm save_economy_data nếu có thay đổi
from core.utils import try_send
from core.config import CURRENCY_SYMBOL
from core.icons import ICON_MONEY_BAG, ICON_ERROR, ICON_INFO

logger = logging.getLogger(__name__)

class BalanceCommandCog(commands.Cog, name="Balance Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug(f"BalanceCommandCog initialized.")

    @commands.command(name='balance', aliases=['bal', 'cash', 'money', '$'])
    async def balance(self, ctx: commands.Context, user: nextcord.Member = None):
        target_user = user or ctx.author
        logger.debug(f"Lệnh 'balance' được gọi bởi {ctx.author.name} cho target {target_user.name} (ID: {target_user.id}) tại guild '{ctx.guild.name}' ({ctx.guild.id}).")
        
        try:
            economy_data = load_economy_data() # Load toàn bộ dữ liệu
            # Lấy profile toàn cục của target_user, hàm này sẽ tạo nếu chưa có
            # và đảm bảo các key mặc định tồn tại.
            target_user_profile = get_or_create_global_user_profile(economy_data, target_user.id)
            
            # Truy cập ví toàn cục
            global_bal = target_user_profile.get("global_balance", 0) # Mặc định là 0 nếu key không có (dù get_or_create... đã xử lý)
            
            await try_send(ctx, content=f"{ICON_MONEY_BAG} Ví Toàn Cục của {target_user.mention}: **{global_bal:,}** {CURRENCY_SYMBOL}.")
            logger.debug(f"Hiển thị global_balance thành công cho {target_user.name}: {global_bal} {CURRENCY_SYMBOL}.")
            

            save_economy_data(economy_data) # Lưu lại để đảm bảo user mới (nếu có) được ghi nhận


        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'balance' cho user {target_user.name}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi không xác định khi xem số dư của {target_user.mention}.")

def setup(bot: commands.Bot):
    bot.add_cog(BalanceCommandCog(bot))
