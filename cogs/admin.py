# bot/cogs/admin.py
import nextcord
from nextcord.ext import commands

# Import các thành phần cần thiết từ package 'core'
from core.database import get_user_data, save_data, get_guild_config, save_guild_config
from core.utils import try_send, is_guild_owner_check
from core.config import CURRENCY_SYMBOL, COMMAND_PREFIX
# --- Thêm import này ---
from core.icons import ICON_SUCCESS, ICON_ERROR, ICON_WARNING, ICON_INFO
# -----------------------

class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='addmoney', aliases=['am', 'ecoadd'])
    @commands.check(is_guild_owner_check)
    async def add_money(self, ctx: commands.Context, member: nextcord.Member, amount: int):
        """(Chỉ Chủ Server) Cộng tiền vào tài khoản của một thành viên."""
        if amount <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Số tiền cộng thêm phải là số dương.")
            return
        
        data = get_user_data(ctx.guild.id, member.id)
        user_data = data[str(ctx.guild.id)][str(member.id)]
        
        user_data["balance"] = user_data.get("balance", 0) + amount
        save_data(data)
        await try_send(ctx, content=f"{ICON_SUCCESS} Đã cộng **{amount:,}** {CURRENCY_SYMBOL} cho {member.mention}. Số dư mới của họ: **{user_data['balance']:,}**")

    @add_money.error
    async def add_money_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CheckFailure):
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ dành cho Chủ Server (người tạo ra server).")
        elif isinstance(error, commands.MissingRequiredArgument):
            await try_send(ctx, content=f"{ICON_WARNING} Sử dụng đúng: `{COMMAND_PREFIX}{ctx.command.name} <@người_dùng> <số_tiền>`")
        elif isinstance(error, commands.BadArgument):
            await try_send(ctx, content=f"{ICON_ERROR} Đối số không hợp lệ. Hãy tag một người dùng và nhập một số tiền là số nguyên.")
        else:
            print(f"Lỗi không xác định trong lệnh {ctx.command.name}: {error}")
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi thực hiện lệnh cộng tiền.")

    @commands.command(name='removemoney', aliases=['rm', 'ecotake', 'submoney'])
    @commands.check(is_guild_owner_check)
    async def remove_money(self, ctx: commands.Context, member: nextcord.Member, amount: int):
        """(Chỉ Chủ Server) Trừ tiền từ tài khoản của một thành viên."""
        if amount <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Số tiền trừ đi phải là số dương.")
            return

        data = get_user_data(ctx.guild.id, member.id)
        user_data = data[str(ctx.guild.id)][str(member.id)]
        original_balance = user_data.get("balance", 0)
        
        amount_removed = min(amount, original_balance)
        user_data["balance"] -= amount_removed
        save_data(data)
        
        msg_content = f"{ICON_SUCCESS} Đã trừ **{amount_removed:,}** {CURRENCY_SYMBOL} từ {member.mention}. Số dư mới của họ: **{user_data['balance']:,}**"
        if amount > original_balance and original_balance > 0:
            msg_content = f"{ICON_WARNING} {member.mention} không đủ tiền như yêu cầu ({amount:,}). " + msg_content
        elif original_balance == 0 and amount > 0:
            msg_content = f"{ICON_INFO} {member.mention} không có tiền để trừ."
        await try_send(ctx, content=msg_content)
        
    @remove_money.error
    async def remove_money_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CheckFailure):
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ dành cho Chủ Server (người tạo ra server).")
        elif isinstance(error, commands.MissingRequiredArgument):
            await try_send(ctx, content=f"{ICON_WARNING} Sử dụng đúng: `{COMMAND_PREFIX}{ctx.command.name} <@người_dùng> <số_tiền>`")
        elif isinstance(error, commands.BadArgument):
            await try_send(ctx, content=f"{ICON_ERROR} Đối số không hợp lệ. Hãy tag một người dùng và nhập một số tiền là số nguyên.")
        else:
            print(f"Lỗi không xác định trong lệnh {ctx.command.name}: {error}")
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi thực hiện lệnh trừ tiền.")

    @commands.command(name="auto")
    @commands.has_guild_permissions(administrator=True)
    async def auto_toggle_bare_commands(self, ctx: commands.Context):
        """(Admin) Bật/Tắt nhận diện lệnh không cần prefix cho kênh này."""
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server.")
            return
            
        current_guild_config = get_guild_config(ctx.guild.id)
        active_channels = current_guild_config.get("bare_command_active_channels", [])
        channel_id = ctx.channel.id
        
        msg_content = ""
        if channel_id in active_channels:
            active_channels.remove(channel_id)
            msg_content = f"{ICON_ERROR} Đã **TẮT** tính năng lệnh tắt (không cần prefix) cho kênh {ctx.channel.mention} này."
        else:
            active_channels.append(channel_id)
            msg_content = f"{ICON_SUCCESS} Đã **BẬT** tính năng lệnh tắt (không cần prefix) cho kênh {ctx.channel.mention} này."
            
        current_guild_config["bare_command_active_channels"] = active_channels
        save_guild_config(ctx.guild.id, current_guild_config)
        await try_send(ctx, content=msg_content)

    @auto_toggle_bare_commands.error
    async def auto_toggle_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await try_send(ctx, content=f"{ICON_ERROR} Bạn cần quyền `Administrator` để sử dụng lệnh này.")
        else:
            print(f"Lỗi không xác định trong lệnh auto: {error}")
            await try_send(ctx, content=f"{ICON_ERROR} Có lỗi xảy ra với lệnh `auto`.")

    @commands.command(name="mutebot")
    @commands.has_guild_permissions(administrator=True)
    async def mute_bot_channel(self, ctx: commands.Context, channel: nextcord.TextChannel = None):
        """(Admin) Tắt tiếng bot (không gửi tin nhắn công khai) trong kênh này hoặc kênh được chỉ định."""
        target_channel = channel or ctx.channel
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server.")
            return
            
        current_guild_config = get_guild_config(ctx.guild.id)
        muted_channels_list = current_guild_config.get("muted_channels", [])
        
        if target_channel.id in muted_channels_list:
            await try_send(ctx, content=f"{ICON_INFO} Bot đã bị tắt tiếng (công khai) trong kênh {target_channel.mention} rồi.")
        else:
            muted_channels_list.append(target_channel.id)
            current_guild_config["muted_channels"] = muted_channels_list
            save_guild_config(ctx.guild.id, current_guild_config)
            await try_send(ctx, content=f"🔇 Bot đã bị **TẮT TIẾNG** (công khai) trong kênh {target_channel.mention}. Các tin nhắn ephemeral (nếu có) vẫn hoạt động.") # Giữ emoji gốc nếu muốn

    @mute_bot_channel.error
    async def mute_bot_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await try_send(ctx, content=f"{ICON_ERROR} Bạn cần quyền `Administrator` để dùng lệnh này.")
        elif isinstance(error, commands.BadArgument):
            await try_send(ctx, content=f"{ICON_ERROR} Không tìm thấy kênh được chỉ định hoặc bạn nhập sai.")
        else:
            print(f"Lỗi không xác định trong lệnh mutebot: {error}")
            await try_send(ctx, content=f"{ICON_ERROR} Có lỗi xảy ra khi thực hiện lệnh tắt tiếng bot.")

    @commands.command(name="unmutebot")
    @commands.has_guild_permissions(administrator=True)
    async def unmute_bot_channel(self, ctx: commands.Context, channel: nextcord.TextChannel = None):
        """(Admin) Bật lại tiếng bot (cho phép gửi tin nhắn công khai) trong kênh này hoặc kênh được chỉ định."""
        target_channel = channel or ctx.channel
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server.")
            return
            
        current_guild_config = get_guild_config(ctx.guild.id)
        muted_channels_list = current_guild_config.get("muted_channels", [])
        
        if target_channel.id not in muted_channels_list:
            await try_send(ctx, content=f"{ICON_INFO} Bot không bị tắt tiếng (công khai) trong kênh {target_channel.mention}.")
        else:
            muted_channels_list.remove(target_channel.id)
            current_guild_config["muted_channels"] = muted_channels_list
            save_guild_config(ctx.guild.id, current_guild_config)
            await try_send(ctx, content=f"🔊 Bot đã được **BẬT TIẾNG** (công khai) trở lại trong kênh {target_channel.mention}.") # Giữ emoji gốc nếu muốn

    @unmute_bot_channel.error
    async def unmute_bot_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await try_send(ctx, content=f"{ICON_ERROR} Bạn cần quyền `Administrator` để dùng lệnh này.")
        elif isinstance(error, commands.BadArgument):
            await try_send(ctx, content=f"{ICON_ERROR} Không tìm thấy kênh được chỉ định hoặc bạn nhập sai.")
        else:
            print(f"Lỗi không xác định trong lệnh unmutebot: {error}")
            await try_send(ctx, content=f"{ICON_ERROR} Có lỗi xảy ra khi thực hiện lệnh bật tiếng bot.")

def setup(bot: commands.Bot):
    bot.add_cog(AdminCog(bot))
