# bot/cogs/admin/bare_command_toggle.py
from discord.ext import commands
import json # Ví dụ để lưu trạng thái vào file

# --- Quản lý trạng thái ---
# Bạn có thể chọn cách lưu trạng thái này:
# 1. Biến global trong bộ nhớ (đơn giản, mất khi bot restart):
#    bare_command_enabled_guilds = set()
# 2. File JSON (khá đơn giản, persistent):
#    Sẽ dùng cách này cho ví dụ.
# 3. Cơ sở dữ liệu (mạnh mẽ hơn cho nhiều dữ liệu):
#    Cần setup DB riêng.

CONFIG_FILE = "bot_config/bare_command_status.json" # Đặt file config ở một nơi hợp lý

def load_bare_command_status():
    """Tải trạng thái bật/tắt lệnh không prefix từ file JSON."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            # Lưu dưới dạng danh sách các ID của server đã bật
            return set(json.load(f))
    except FileNotFoundError:
        return set() # Trả về set rỗng nếu file không tồn tại
    except json.JSONDecodeError:
        print(f"LỖI: Không thể đọc file {CONFIG_FILE}. File có thể bị hỏng.")
        return set()


def save_bare_command_status(status_set):
    """Lưu trạng thái bật/tắt lệnh không prefix vào file JSON."""
    try:
        # Đảm bảo thư mục tồn tại
        import os
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(list(status_set), f, indent=4)
    except Exception as e:
        print(f"LỖI: Không thể lưu trạng thái bare command: {e}")

class BareCommandToggle(commands.Cog, name="Bật/Tắt Lệnh Không Prefix"):
    """
    Cog cho phép admin bật/tắt chế độ lệnh không cần prefix cho server.
    LƯU Ý: Việc XỬ LÝ các lệnh không prefix cần được thực hiện
    trong một listener on_message riêng. Cog này chỉ quản lý việc bật/tắt.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Tải trạng thái khi cog được nạp
        # self.bare_command_enabled_guilds sẽ là một set chứa ID các guild đã bật bare commands
        self.bare_command_enabled_guilds = load_bare_command_status()
        # Bạn cũng cần một cách để bot (ví dụ: listener on_message) truy cập trạng thái này.
        # Có thể gán nó vào bot instance nếu listener on_message của bạn có thể truy cập.
        # Ví dụ: self.bot.bare_command_enabled_guilds = self.bare_command_enabled_guilds
        # Hoặc listener on_message sẽ gọi một hàm từ cog này để kiểm tra.

    @commands.command(name="togglebarecommands", aliases=["toggleprefixless", "barecommands"])
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def toggle_bare_commands(self, ctx: commands.Context):
        """
        Bật hoặc tắt chế độ nhận lệnh không cần prefix cho server này.
        Việc xử lý lệnh không prefix cần được implement trong listener on_message.
        """
        guild_id = ctx.guild.id
        if guild_id in self.bare_command_enabled_guilds:
            # Nếu đang bật -> tắt nó đi
            self.bare_command_enabled_guilds.remove(guild_id)
            current_status_message = "TẮT"
        else:
            # Nếu đang tắt -> bật nó lên
            self.bare_command_enabled_guilds.add(guild_id)
            current_status_message = "BẬT"

        save_bare_command_status(self.bare_command_enabled_guilds) # Lưu thay đổi
        await ctx.send(f"Chế độ lệnh không cần prefix đã được **{current_status_message}** cho server này.")
        print(f"Admin {ctx.author} ({ctx.author.id}) đã {current_status_message} chế độ bare commands cho guild {guild_id}")

    @commands.command(name="checkbarestatus", aliases=["barestatus"])
    @commands.has_permissions(administrator=True) # Hoặc cho phép mọi người dùng nếu muốn
    @commands.guild_only()
    async def check_bare_status(self, ctx: commands.Context):
        """Kiểm tra trạng thái của chế độ lệnh không cần prefix cho server này."""
        guild_id = ctx.guild.id
        if guild_id in self.bare_command_enabled_guilds:
            await ctx.send("Chế độ lệnh không cần prefix hiện đang **BẬT** cho server này.")
        else:
            await ctx.send("Chế độ lệnh không cần prefix hiện đang **TẮT** cho server này.")

    # Quan trọng: Cần có một listener on_message để thực sự xử lý các lệnh không prefix.
    # Listener này có thể nằm ở đây, trong main bot file, hoặc một cog chung.
    # Ví dụ (nếu đặt listener ở đây, nhưng thường sẽ tách ra):
    #
    # @commands.Cog.listener()
    # async def on_message(self, message: discord.Message):
    #     if message.author.bot or not message.guild:
    #         return # Bỏ qua bot và DM
    #
    #     if message.guild.id in self.bare_command_enabled_guilds:
    #         # Kiểm tra xem nội dung message có phải là một lệnh không
    #         # Đây là phần phức tạp: bạn cần logic để phân biệt lệnh và tin nhắn thường
    #         # Ví dụ rất đơn giản:
    #         # command_name = message.content.split(" ")[0].lower()
    #         # if self.bot.get_command(command_name):
    #         #     # Tạo một Context giả hoặc điều chỉnh message để process_commands có thể xử lý
    #         #     # Cẩn thận: điều này có thể cần tùy chỉnh sâu vào cách bot xử lý lệnh
    #         #     # Hoặc bạn tự gọi callback của lệnh nếu tìm thấy
    #         #     print(f"Bare command '{command_name}' detected in guild {message.guild.id}")
    #         #     # await self.bot.process_commands(message) # Gọi lại process_commands có thể không an toàn nếu không có prefix
    #         pass # Để trống phần xử lý này, vì nó phức tạp và tùy thuộc vào thiết kế bot

    @toggle_bare_commands.error
    @check_bare_status.error
    async def bare_command_toggle_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Bạn không có quyền sử dụng lệnh này.")
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send("Lệnh này chỉ có thể sử dụng trong server.")
        else:
            await ctx.send("Có lỗi xảy ra khi thực thi lệnh.")
            print(f"Lỗi trong BareCommandToggle cog: {error} (Lệnh: {ctx.command.name})")

async def setup(bot: commands.Bot):
    cog_instance = BareCommandToggle(bot)
    await bot.add_cog(cog_instance)
    # Gán instance vào bot để các module khác (ví dụ on_message listener) có thể truy cập
    # nếu bạn không muốn truyền bot và gọi hàm từ cog.
    # Hoặc, bạn có thể tạo một hàm trong cog này để kiểm tra trạng thái:
    # Ví dụ: bot.is_bare_command_enabled = cog_instance.is_enabled_for_guild
    print("Cog BareCommandToggle đã được nạp.")

# Nếu bạn muốn có một hàm tiện ích trong cog để kiểm tra từ bên ngoài:
# def is_enabled_for_guild(self, guild_id: int) -> bool:
# return guild_id in self.bare_command_enabled_guilds
