# bot/cogs/economy.py
import nextcord
from nextcord.ext import commands

# Import các thành phần cần thiết từ package 'core'
from core.database import get_user_data, save_data, check_user
from core.utils import try_send
from core.config import CURRENCY_SYMBOL, COMMAND_PREFIX
# --- Thêm import này ---
from core.icons import ICON_MONEY_BAG, ICON_BANK, ICON_SUCCESS, ICON_ERROR, ICON_WARNING, ICON_GIFT, ICON_INFO
# -----------------------

class EconomyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='balance', aliases=['bal', 'cash', 'money', '$'])
    async def balance(self, ctx: commands.Context, user: nextcord.Member = None):
        """Hiển thị số dư tiền trong ví của bạn hoặc của một người dùng khác."""
        target_user = user or ctx.author
        guild_id_str = str(ctx.guild.id)
        user_id_str = str(target_user.id)
        
        try:
            full_data = get_user_data(ctx.guild.id, target_user.id)
            user_account_data = full_data.get(guild_id_str, {}).get(user_id_str)

            if user_id_str == "config" or not isinstance(user_account_data, dict):
                await try_send(ctx, content=f"{ICON_ERROR} Lỗi: Dữ liệu tài khoản của {target_user.mention} không đúng định dạng hoặc không tìm thấy.")
                return
            
            bal = user_account_data.get("balance", 0)
            await try_send(ctx, content=f"{ICON_MONEY_BAG} Ví của {target_user.mention}: **{bal:,}** {CURRENCY_SYMBOL}.")

        except Exception as e:
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi không xác định khi xem số dư của {target_user.mention}.")
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
            await try_send(ctx, content=f"{ICON_ERROR} Lỗi: Không tìm thấy dữ liệu ngân hàng cho {target_user.mention}.")
            return
        
        bank_bal = user_specific_data.get("bank_balance", 0)
        await try_send(ctx, content=f"{ICON_BANK} Ngân hàng của {target_user.mention}: **{bank_bal:,}** {CURRENCY_SYMBOL}.")

    @commands.command(name='deposit', aliases=['dep'])
    async def deposit(self, ctx: commands.Context, amount_str: str):
        """Gửi tiền từ ví vào tài khoản ngân hàng của bạn."""
        data = get_user_data(ctx.guild.id, ctx.author.id)
        user_data = data[str(ctx.guild.id)][str(ctx.author.id)]
        
        try:
            if amount_str.lower() == 'all':
                amount = user_data.get("balance", 0)
            else:
                amount = int(amount_str)
        except ValueError:
            await try_send(ctx, content=f"{ICON_WARNING} Vui lòng nhập một số tiền hợp lệ hoặc 'all'.")
            return
            
        if amount <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Số tiền gửi phải lớn hơn 0.")
            return
        if user_data.get("balance", 0) < amount:
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ tiền trong ví. Bạn có: {user_data.get('balance',0):,} {CURRENCY_SYMBOL}")
            return
        
        user_data["balance"] -= amount
        user_data["bank_balance"] = user_data.get("bank_balance", 0) + amount
        save_data(data)
        await try_send(ctx, content=f"{ICON_SUCCESS} Bạn đã gửi **{amount:,}** {CURRENCY_SYMBOL} vào ngân hàng.\n{ICON_MONEY_BAG} Ví: **{user_data['balance']:,}** | {ICON_BANK} Ngân hàng: **{user_data['bank_balance']:,}**")

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
            await try_send(ctx, content=f"{ICON_WARNING} Vui lòng nhập một số tiền hợp lệ hoặc 'all'.")
            return
            
        if amount <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Số tiền rút phải lớn hơn 0.")
            return
        if user_data.get("bank_balance", 0) < amount:
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ tiền trong ngân hàng. Ngân hàng có: {user_data.get('bank_balance',0):,} {CURRENCY_SYMBOL}")
            return

        user_data["balance"] = user_data.get("balance", 0) + amount
        user_data["bank_balance"] -= amount
        save_data(data)
        await try_send(ctx, content=f"{ICON_SUCCESS} Bạn đã rút **{amount:,}** {CURRENCY_SYMBOL} từ ngân hàng.\n{ICON_MONEY_BAG} Ví: **{user_data['balance']:,}** | {ICON_BANK} Ngân hàng: **{user_data['bank_balance']:,}**")

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

        full_data = get_user_data(ctx.guild.id, ctx.author.id)
        full_data = check_user(full_data, ctx.guild.id, recipient.id)

        sender_data = full_data[str(ctx.guild.id)][str(ctx.author.id)]
        recipient_data = full_data[str(ctx.guild.id)][str(recipient.id)]

        if sender_data.get("balance", 0) < amount:
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ tiền! Bạn chỉ có **{sender_data.get('balance',0):,}** {CURRENCY_SYMBOL}.")
            return
        
        sender_data["balance"] -= amount
        recipient_data["balance"] = recipient_data.get("balance", 0) + amount
        save_data(full_data)
        await try_send(ctx, content=f"{ICON_GIFT} {ctx.author.mention} đã chuyển **{amount:,}** {CURRENCY_SYMBOL} cho {recipient.mention}!")

def setup(bot: commands.Bot):
    bot.add_cog(EconomyCog(bot))
