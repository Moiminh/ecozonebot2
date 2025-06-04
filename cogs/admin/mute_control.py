# bot/cogs/admin/mute_control.py
from discord.ext import commands
import discord
import json # Ví dụ để lưu trạng thái vào file

# --- Quản lý trạng thái kênh bị tắt tiếng ---
# Tương tự như bare_command_toggle, bạn có thể chọn cách lưu:
# 1. Biến global (set chứa channel_id)
# 2. File JSON (sử dụng cho ví dụ này)
# 3. Cơ sở dữ liệu

MUTE_CONFIG_FILE = "bot_config/muted_channels.json"

def load_muted_channels():
    """Tải danh sách ID các kênh bị tắt tiếng từ file JSON."""
    try:
        with open(MUTE_CONFIG_FILE, 'r') as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()
    except json.JSONDecodeError:
        print(f"LỖI: Không thể đọc file {MUTE_CONFIG_FILE}. File có thể bị hỏng.")
        return set()

def save_muted_channels(muted_set):
    """Lưu danh sách ID các kênh bị tắt tiếng vào file JSON."""
    try:
        import os
        os.makedirs(os.path.dirname(MUTE_CONFIG_FILE), exist_ok=True)
        with open(MUTE_CONFIG_FILE, 'w') as f:
            json.dump(list(muted_set), f, indent=4)
    except Exception as e:
        print(f"LỖI: Không thể lưu trạng thái kênh bị tắt tiếng: {e}")

class MuteControl(commands.Cog, name="Kiểm Soát Tắt Tiếng Bot"):
    """
    Cog cho phép admin tắt/bật tiếng bot trong các kênh cụ thể.
    Việc kiểm tra kênh có bị tắt tiếng hay không cần được thực hiện
    trước khi bot gửi bất kỳ tin nhắn nào.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.muted_channel_ids = load_muted_channels()
        # Gán vào bot instance để các phần khác của bot (ví dụ: global check) có thể truy cập
        # Hoặc cung cấp một phương thức kiểm tra trong cog này
        self.bot.muted_channel_ids = self.muted_channel_ids

    def is_channel_muted(self, channel_id: int) -> bool:
        """Kiểm tra xem một kênh có đang bị bot tắt tiếng không."""
        return channel_id in self.muted_channel_ids

    @commands.command(name="mutebotchannel", aliases=["mutechannel"])
    @commands.has_permissions(manage_channels=True) # Quyền quản lý kênh là hợp lý
    @commands.guild_only()
    async def mute_bot_in_channel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """
        Tắt tiếng bot trong kênh này hoặc một kênh được chỉ định.
        Bot sẽ không gửi tin nhắn trong kênh bị tắt tiếng.
        Ví dụ: !mutebotchannel #general
        """
        target_channel = channel or ctx.channel
        if target_channel.id in self.muted_channel_ids:
            await ctx.send(f"Bot đã bị tắt tiếng trong kênh {target_channel.mention} rồi.")
            return

        self.muted_channel_ids.add(target_channel.id)
        save_muted_channels(self.muted_channel_ids)
        await ctx.send(f"Bot đã được tắt tiếng trong kênh {target_channel.mention}. Bot sẽ không gửi tin nhắn ở đây nữa.")
        print(f"Admin {ctx.author} ({ctx.author.id}) đã tắt tiếng bot trong kênh {target_channel.name} ({target_channel.id})")

    @commands.command(name="unmutebotchannel", aliases=["unmutechannel"])
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def unmute_bot_in_channel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """
        Bật lại tiếng bot trong kênh này hoặc một kênh được chỉ định.
        Ví dụ: !unmutebotchannel #general
        """
        target_channel = channel or ctx.channel
        if target_channel.id not in self.muted_channel_ids:
            await ctx.send(f"Bot không bị tắt tiếng trong kênh {target_channel.mention}.")
            return

        self.muted_channel_ids.remove(target_channel.id)
        save_muted_channels(self.muted_channel_ids)
        await ctx.send(f"Bot đã được bật tiếng trở lại trong kênh {target_channel.mention}.")
        print(f"Admin {ctx.author} ({ctx.author.id}) đã bật tiếng bot trong kênh {target_channel.name} ({target_channel.id})")

    @commands.command(name="checkbotmute", aliases=["mutestatus"])
    @commands.guild_only() # Có thể cho phép mọi người dùng hoặc chỉ admin
    async def check_bot_mute_status(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Kiểm tra xem bot có bị tắt tiếng trong kênh hiện tại hoặc kênh chỉ định không."""
        target_channel = channel or ctx.channel
        if self.is_channel_muted(target_channel.id):
            await ctx.send(f"Bot hiện đang **BỊ TẮT TIẾNG** trong kênh {target_channel.mention}.")
        else:
            await ctx.send(f"Bot hiện đang **HOẠT ĐỘNG BÌNH THƯỜNG** (không bị tắt tiếng) trong kênh {target_channel.mention}.")

    # --- Cơ chế thực thi việc tắt tiếng ---
    # Cách tốt nhất để thực thi việc này là sử dụng một global check.
    # Bạn sẽ thêm check này vào bot instance trong file bot chính.
    # Cog này sẽ cung cấp logic kiểm tra.

    @mute_bot_in_channel.error
    @unmute_bot_in_channel.error
    @check_bot_mute_status.error
    async def mute_control_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Bạn không có quyền sử dụng lệnh này.")
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send("Lệnh này chỉ có thể sử dụng trong server.")
        elif isinstance(error, commands.ChannelNotFound):
            await ctx.send(f"Không tìm thấy kênh: `{error.argument}`.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Kênh được cung cấp không hợp lệ.")
        else:
            await ctx.send("Có lỗi xảy ra khi thực thi lệnh.")
            print(f"Lỗi trong MuteControl cog: {error} (Lệnh: {ctx.command.name})")

async def setup(bot: commands.Bot):
    cog_instance = MuteControl(bot)
    await bot.add_cog(cog_instance)

    # QUAN TRỌNG: Đăng ký global check để ngăn bot gửi tin nhắn
    # Đây là một cách để làm điều đó.
    # Hàm check này sẽ được gọi trước mỗi lệnh.
    @bot.check # Đăng ký một global check
    async def globally_block_muted_channels(ctx: commands.Context):
        # Bỏ qua check này nếu lệnh được gọi bởi chủ bot (owner)
        # hoặc nếu lệnh không có kênh (ví dụ lệnh trong DM mà không phải là lệnh này)
        if await bot.is_owner(ctx.author) or not ctx.channel:
             return True # Owner có thể dùng lệnh ở mọi nơi, và không check nếu không có channel
        
        # Kiểm tra xem lệnh này có phải là một trong các lệnh của MuteControl không
        # Nếu là lệnh của MuteControl, cho phép chạy để admin có thể unmute
        if ctx.cog == cog_instance: # So sánh instance của cog
             return True

        # Nếu kênh nằm trong danh sách bị mute, không cho thực thi lệnh
        # (và bot sẽ không tự động gửi thông báo lỗi của check này)
        if isinstance(ctx.channel, discord.TextChannel) and cog_instance.is_channel_muted(ctx.channel.id):
            # Bạn có thể muốn log việc này hoặc gửi tin nhắn riêng cho người gọi lệnh (nếu không phải owner)
            print(f"Bot is muted in channel {ctx.channel.id}. Command '{ctx.command}' invoked by {ctx.author} was blocked.")
            # Raising commands.CheckFailure will silently stop the command.
            # If you want to send a message, you'd have to do it carefully,
            # e.g., DM the user, or have a specific error handler for this check.
            raise commands.CheckFailure(f"Bot is muted in channel {ctx.channel.name}.")
        return True # Nếu không bị mute, cho phép lệnh chạy

    print("Cog MuteControl đã được nạp và global check đã được thiết lập.")

