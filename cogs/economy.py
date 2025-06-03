# bot/cogs/economy.py
import nextcord
from nextcord.ext import commands

# Import các thành phần cần thiết từ package 'core'
from core.database import get_user_data, save_data, check_user # check_user có thể cần cho transfer
from core.utils import try_send
from core.config import CURRENCY_SYMBOL, COMMAND_PREFIX # COMMAND_PREFIX có thể dùng cho docstring hoặc tin nhắn

class EconomyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='balance', aliases=['bal', 'cash', 'money', '$'])
    async def balance(self, ctx: commands.Context, user: nextcord.Member = None):
        """Hiển thị số dư tiền trong ví của bạn hoặc của một người dùng khác.

        Công dụng:
        Kiểm tra tài sản hiện có trong ví. Tiền trong ví có thể dùng để mua sắm, cờ bạc, hoặc chuyển cho người khác.
        Tiền trong ví có thể bị cướp.

        Sử dụng:
        `!balance` - Xem số dư của chính bạn.
        `!balance @tên_người_dùng` - Xem số dư của người khác.

        Ví dụ:
        `!balance`
        `!bal @User123`

        Lệnh tắt (nếu admin đã bật cho kênh): `bal`, `cash`, `money`, `$`
        """
        target_user = user or ctx.author
        guild_id_str = str(ctx.guild.id)
        user_id_str = str(target_user.id)
        
        try:
            # get_user_data đã bao gồm check_user để đảm bảo dữ liệu tồn tại
            full_data = get_user_data(ctx.guild.id, target_user.id)
            # Truy cập dữ liệu người dùng cụ thể từ full_data
            user_account_data = full_data.get(guild_id_str, {}).get(user_id_str)

            if user_id_str == "config" or not isinstance(user_account_data, dict):
                await try_send(ctx, content=f"Lỗi: Dữ liệu tài khoản của {target_user.mention} không đúng định dạng hoặc không tìm thấy.")
                return
            
            bal = user_account_data.get("balance") # Mặc định là 0 nếu key không tồn tại (do check_user)
            
            # Dòng code kiểm tra bal is None có thể không cần thiết nếu check_user luôn đảm bảo key 'balance' tồn tại với giá trị mặc định.
            # Tuy nhiên, để an toàn, có thể giữ lại hoặc đơn giản hóa.
            # Hiện tại, check_user đã đảm bảo key 'balance' sẽ có giá trị (mặc định là 0 hoặc 100 cho user mới).
            await try_send(ctx, content=f"Ví của {target_user.mention}: **{bal:,}** {CURRENCY_SYMBOL}.")

        except Exception as e:
            await try_send(ctx, content=f"Đã xảy ra lỗi không xác định khi xem số dư của {target_user.mention}.")
            print(f"ERROR in balance command (cog): {type(e).__name__} - {e}")

    @commands.command(name='bank')
    async def bank(self, ctx: commands.Context, user: nextcord.Member = None):
        """Hiển thị số dư tiền trong ngân hàng của bạn hoặc của người dùng được chỉ định."""
        target_user = user or ctx.author
        guild_id_str = str(ctx.guild.id)
        user_id_str = str(target_user.id)

        full_data = get_user_data(ctx.guild.id, target_user.id)
        user_specific_data = full_data.get(guild_id_str, {}).get(user_id_str, {})

        if user_id_str == "config" or not isinstance(user_specific_data, dict):
            await try_send(ctx, content=f"Lỗi: Không tìm thấy dữ liệu ngân hàng cho {target_user.mention}.")
            return
        
        bank_bal = user_specific_data.get("bank_balance", 0)
        await try_send(ctx, content=f"Ngân hàng của {target_user.mention}: **{bank_bal:,}** {CURRENCY_SYMBOL}.")

    @commands.command(name='deposit', aliases=['dep'])
    async def deposit(self, ctx: commands.Context, amount_str: str):
        """Gửi tiền từ ví vào tài khoản ngân hàng của bạn."""
        # get_user_data tải và kiểm tra dữ liệu cho người dùng hiện tại
        data = get_user_data(ctx.guild.id, ctx.author.id)
        # Truy cập trực tiếp vào dữ liệu người dùng sau khi đã được get_user_data xử lý
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]
        
        try:
            if amount_str.lower() == 'all':
                amount = user_data.get("balance", 0)
            else:
                amount = int(amount_str)
        except ValueError:
            await try_send(ctx, content="Vui lòng nhập một số tiền hợp lệ hoặc 'all'.")
            return
            
        if amount <= 0:
            await try_send(ctx, content="Số tiền gửi phải lớn hơn 0.")
            return
        if user_data.get("balance", 0) < amount:
            await try_send(ctx, content="Bạn không có đủ tiền trong ví.")
            return
        
        user_data["balance"] -= amount
        user_data["bank_balance"] = user_data.get("bank_balance", 0) + amount
        save_data(data) # Lưu lại toàn bộ cấu trúc data sau khi thay đổi
        await try_send(ctx, content=f"Bạn đã gửi **{amount:,}** {CURRENCY_SYMBOL} vào ngân hàng. Ví: **{user_data['balance']:,}** | Ngân hàng: **{user_data['bank_balance']:,}**")

    @commands.command(name='withdraw', aliases=['wd'])
    async def withdraw(self, ctx: commands.Context, amount_str: str):
        """Rút tiền từ tài khoản ngân hàng về ví của bạn."""
        data = get_user_data(ctx.guild.id, ctx.author.id)
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]
        
        try:
            if amount_str.lower() == 'all':
                amount = user_data.get("bank_balance", 0)
            else:
                amount = int(amount_str)
        except ValueError:
            await try_send(ctx, content="Vui lòng nhập một số tiền hợp lệ hoặc 'all'.")
            return
            
        if amount <= 0:
            await try_send(ctx, content="Số tiền rút phải lớn hơn 0.")
            return
        if user_data.get("bank_balance", 0) < amount:
            await try_send(ctx, content="Bạn không có đủ tiền trong ngân hàng.")
            return

        user_data["balance"] = user_data.get("balance", 0) + amount
        user_data["bank_balance"] -= amount
        save_data(data)
        await try_send(ctx, content=f"Bạn đã rút **{amount:,}** {CURRENCY_SYMBOL} từ ngân hàng. Ví: **{user_data['balance']:,}** | Ngân hàng: **{user_data['bank_balance']:,}**")

    @commands.command(name='transfer', aliases=['give', 'pay'])
    async def transfer(self, ctx: commands.Context, recipient: nextcord.Member, amount: int):
        """Chuyển một số tiền từ ví của bạn cho người dùng khác."""
        if amount <= 0:
            await try_send(ctx, content="Số tiền phải lớn hơn 0!")
            return
        if recipient.id == ctx.author.id:
            await try_send(ctx, content="Bạn không thể tự chuyển tiền cho mình!")
            return
        if recipient.bot: # Không cho chuyển tiền cho bot
            await try_send(ctx, content="Không thể chuyển tiền cho bot!")
            return

        # get_user_data sẽ load toàn bộ data và đảm bảo sender có dữ liệu
        full_data = get_user_data(ctx.guild.id, ctx.author.id)
        # Sau đó, đảm bảo recipient cũng có dữ liệu trong full_data mà không cần load lại file
        # check_user sẽ sửa đổi full_data nếu recipient chưa có
        full_data = check_user(full_data, ctx.guild.id, recipient.id)

        sender_data = full_data[str(ctx.guild.id)][str(ctx.author.id)]
        recipient_data = full_data[str(ctx.guild.id)][str(recipient.id)] # Dữ liệu này đã được đảm bảo bởi check_user

        if sender_data.get("balance", 0) < amount:
            await try_send(ctx, content=f"Bạn không có đủ tiền! Bạn chỉ có **{sender_data.get('balance',0):,}** {CURRENCY_SYMBOL}.")
            return
        
        sender_data["balance"] -= amount
        recipient_data["balance"] = recipient_data.get("balance", 0) + amount # Đảm bảo key tồn tại
        save_data(full_data) # Lưu lại toàn bộ cấu trúc full_data
        await try_send(ctx, content=f"{ctx.author.mention} đã chuyển **{amount:,}** {CURRENCY_SYMBOL} cho {recipient.mention}!")

# Hàm này bắt buộc phải có ở cuối mỗi file cog
# Nó cho phép bot load cog này
def setup(bot: commands.Bot):
    bot.add_cog(EconomyCog(bot))
