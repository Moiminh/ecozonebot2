# bot/cogs/economy/transfer_cmd.py
import nextcord
from nextcord.ext import commands

# Import các thành phần cần thiết từ package 'core'
from core.database import get_user_data, save_data, check_user # Cần check_user để đảm bảo người nhận có dữ liệu
from core.utils import try_send
from core.config import CURRENCY_SYMBOL
from core.icons import ICON_GIFT, ICON_ERROR, ICON_MONEY_BAG # Đảm bảo các icon này có trong core/icons.py

class TransferCommandCog(commands.Cog, name="Transfer Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='transfer', aliases=['give', 'pay'])
    async def transfer(self, ctx: commands.Context, recipient: nextcord.Member, amount: int):
        """Chuyển một số tiền từ ví của bạn cho người dùng khác."""
        if amount <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Số tiền chuyển phải lớn hơn 0!")
            return
        if recipient.id == ctx.author.id:
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không thể tự chuyển tiền cho mình!")
            return
        if recipient.bot:
            await try_send(ctx, content=f"{ICON_ERROR} Không thể chuyển tiền cho bot!")
            return

        # Lấy dữ liệu, đảm bảo người gửi (author) có dữ liệu
        full_data = get_user_data(ctx.guild.id, ctx.author.id)
        # Sau đó, đảm bảo người nhận (recipient) cũng có dữ liệu trong full_data
        # check_user sẽ tạo mới nếu chưa có và sửa đổi trực tiếp full_data
        full_data = check_user(full_data, ctx.guild.id, recipient.id)

        sender_data = full_data[str(ctx.guild.id)][str(ctx.author.id)]
        # Dữ liệu người nhận đã được đảm bảo bởi check_user ở trên
        recipient_data = full_data[str(ctx.guild.id)][str(recipient.id)]

        if sender_data.get("balance", 0) < amount:
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ tiền! {ICON_MONEY_BAG} Ví của bạn: **{sender_data.get('balance',0):,}** {CURRENCY_SYMBOL}.")
            return
        
        sender_data["balance"] -= amount
        recipient_data["balance"] = recipient_data.get("balance", 0) + amount
        save_data(full_data) # Lưu lại toàn bộ cấu trúc full_data sau khi thay đổi
        await try_send(ctx, content=f"{ICON_GIFT} {ctx.author.mention} đã chuyển **{amount:,}** {CURRENCY_SYMBOL} cho {recipient.mention}!")

def setup(bot: commands.Bot):
    bot.add_cog(TransferCommandCog(bot))
