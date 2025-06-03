# bot/core/bot.py
import nextcord
from nextcord.ext import commands
import os # Thư viện os để làm việc với hệ thống file (liệt kê file trong thư mục cogs)

# Import các thành phần cần thiết từ package 'core'
from .config import COMMAND_PREFIX, BARE_COMMAND_MAP # Lấy prefix và bản đồ lệnh tắt
from .database import get_guild_config # Để xử lý lệnh tắt và mute kênh
from .utils import try_send # Để gửi tin nhắn trong on_command_error

# --- Khởi tạo Bot ---
# Xác định các quyền (Intents) mà bot cần.
# message_content là quyền quan trọng để bot có thể đọc nội dung tin nhắn.
# members cũng cần thiết nếu bạn muốn truy cập thông tin thành viên (ví dụ khi họ tham gia server).
intents = nextcord.Intents.default()
intents.message_content = True # BẮT BUỘC phải bật trong Discord Developer Portal
intents.members = True       # BẮT BUỘC phải bật trong Discord Developer Portal nếu dùng

# Khởi tạo đối tượng bot với prefix và intents đã định nghĩa
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

# --- Các Sự Kiện (Events) của Bot ---

@bot.event
async def on_ready():
    """
    Sự kiện này được kích hoạt khi bot đã kết nối thành công với Discord
    và sẵn sàng nhận lệnh.
    """
    print(f'--------------------------------------------------')
    print(f'Bot đã đăng nhập với tên: {bot.user.name} (ID: {bot.user.id})')
    print(f'Prefix lệnh: {COMMAND_PREFIX}')
    print(f'Nextcord Version: {nextcord.__version__}')
    print(f'Bot đã sẵn sàng và đang chờ lệnh!')
    print(f'Để xem trợ giúp, hãy gõ /help trên Discord (nếu cog Misc đã được tải).')
    print(f'--------------------------------------------------')
    # Bạn có thể đặt trạng thái cho bot ở đây, ví dụ:
    # await bot.change_presence(activity=nextcord.Game(name=f"{COMMAND_PREFIX}help hoặc /help"))


@bot.event
async def on_message(message: nextcord.Message):
    """
    Sự kiện này được kích hoạt mỗi khi có một tin nhắn mới được gửi
    trong bất kỳ kênh nào mà bot có thể thấy.
    """
    # Bỏ qua tin nhắn từ chính bot để tránh vòng lặp vô hạn
    if message.author.bot:
        return

    # Nếu tin nhắn không phải từ một server (ví dụ: tin nhắn riêng),
    # chỉ xử lý lệnh bình thường và không áp dụng logic lệnh tắt.
    if not message.guild:
        await bot.process_commands(message) # Xử lý lệnh có prefix
        return

    # Lấy nội dung tin nhắn và loại bỏ khoảng trắng thừa
    content = message.content.strip()
    if not content: # Bỏ qua nếu tin nhắn rỗng sau khi strip
        return

    # Xử lý lệnh tắt (không cần prefix)
    # Lấy cấu hình của server từ database
    guild_config = get_guild_config(message.guild.id)
    active_bare_channels = guild_config.get("bare_command_active_channels", []) # Lấy danh sách kênh được bật lệnh tắt

    # Kiểm tra xem kênh hiện tại có nằm trong danh sách active_bare_channels không
    # và tin nhắn có bắt đầu bằng prefix không (nếu có prefix thì đó là lệnh thường)
    if message.channel.id in active_bare_channels and not content.startswith(COMMAND_PREFIX):
        parts = content.split(maxsplit=1) # Tách lệnh và các đối số (nếu có)
        command_candidate = parts[0].lower() # Lấy phần lệnh và chuyển thành chữ thường

        if command_candidate in BARE_COMMAND_MAP: # Kiểm tra xem có trong bản đồ lệnh tắt không
            actual_command_name = BARE_COMMAND_MAP[command_candidate] # Lấy tên lệnh gốc
            args_for_bare_command = parts[1] if len(parts) > 1 else "" # Lấy phần đối số
            
            # Tạo lại nội dung tin nhắn với prefix và tên lệnh gốc
            message.content = f"{COMMAND_PREFIX}{actual_command_name} {args_for_bare_command}".strip()
            # print(f"Bare command: '{content}' -> '{message.content}' in G:{message.guild.id} C:{message.channel.id}")
    
    # Sau khi đã xử lý (hoặc không) lệnh tắt, cho bot xử lý các lệnh (có prefix)
    await bot.process_commands(message)


@bot.event
async def on_command_error(ctx: commands.Context, error):
    """
    Sự kiện này được kích hoạt khi có lỗi xảy ra trong quá trình thực thi một lệnh.
    """
    # Bỏ qua lỗi CommandNotFound để tránh spam console hoặc chat
    if isinstance(error, commands.CommandNotFound):
        # await try_send(ctx, content=f"Lệnh `{ctx.invoked_with}` không tồn tại. Dùng `/help` để xem danh sách lệnh.", ephemeral=True, delete_after=10)
        return # Không làm gì cả

    # Lỗi thiếu tham số bắt buộc
    elif isinstance(error, commands.MissingRequiredArgument):
        cmd_name = ctx.command.name if ctx.command else "lệnh này"
        # Cố gắng cung cấp hướng dẫn sử dụng lệnh nếu có thể
        help_msg_for_cmd = f"Gõ `/help tên_lệnh {cmd_name}` để xem chi tiết." if bot.get_command(cmd_name) else ""
        await try_send(ctx, content=f"Bạn thiếu tham số `{error.param.name}` cho lệnh `{cmd_name}`. {help_msg_for_cmd}")

    # Lỗi sai kiểu dữ liệu của tham số
    elif isinstance(error, commands.BadArgument):
        await try_send(ctx, content=f"Đối số bạn cung cấp không hợp lệ. Vui lòng kiểm tra lại. Lỗi: {error}")

    # Lỗi lệnh đang trong thời gian chờ (cooldown)
    elif isinstance(error, commands.CommandOnCooldown):
        await try_send(ctx, content=f"Lệnh `{ctx.command.name}` đang trong thời gian chờ. Bạn cần đợi **{error.retry_after:.1f} giây** nữa.")

    # Lỗi thiếu quyền hạn (chung)
    elif isinstance(error, commands.MissingPermissions):
        # Lỗi này sẽ được xử lý cụ thể hơn ở error handler của từng lệnh nếu có
        # (ví dụ @auto_toggle_bare_commands.error)
        # Nếu không có error handler riêng, nó sẽ rơi vào đây.
        perms_list = ", ".join([f"`{perm.replace('_', ' ').title()}`" for perm in error.missing_permissions])
        await try_send(ctx, content=f"Bạn không có đủ quyền để dùng lệnh này. Thiếu quyền: {perms_list}.")

    # Lỗi chỉ chủ sở hữu bot mới được dùng
    elif isinstance(error, commands.NotOwner):
        await try_send(ctx, content="Lệnh này chỉ dành cho chủ sở hữu của Bot.")

    # Lỗi từ các hàm check (ví dụ: is_guild_owner_check, hoặc các check permission khác)
    # Các hàm error handler riêng của lệnh (ví dụ @add_money.error) nên xử lý CheckFailure của chính nó.
    # Đây là fallback nếu không có error handler riêng.
    elif isinstance(error, commands.CheckFailure):
        # Thông thường, các hàm check sẽ có thông báo lỗi riêng trong error handler của lệnh.
        # Ví dụ: Lệnh addmoney có @add_money.error sẽ xử lý commands.CheckFailure từ is_guild_owner_check.
        # Nếu lỗi CheckFailure không được xử lý ở cấp lệnh, nó sẽ đến đây.
        print(f"Lỗi CheckFailure không được xử lý cho lệnh '{ctx.command.name if ctx.command else 'unknown'}': {error}")
        await try_send(ctx, content="Bạn không đáp ứng điều kiện để sử dụng lệnh này.")
    
    # Các lỗi không mong muốn khác
    else:
        # In lỗi ra console để debug
        print(f"Lỗi không xác định trong lệnh '{ctx.command.name if ctx.command else 'unknown'}':")
        print(f"Loại lỗi: {type(error).__name__}")
        print(f"Thông điệp lỗi: {error}")
        # Gửi thông báo lỗi chung cho người dùng
        await try_send(ctx, content="Ối! Đã có lỗi không mong muốn xảy ra khi thực hiện lệnh. Vui lòng thử lại sau. 😵‍💫")


# --- Hàm Tải Cogs ---
def load_all_cogs():
    """
    Tải tất cả các file .py trong thư mục 'cogs' dưới dạng extension (cog) cho bot.
    Thư mục 'cogs' phải nằm cùng cấp với thư mục 'core'.
    """
    print(f'--------------------------------------------------')
    print(f'Đang tải các Cogs...')
    loaded_cogs_count = 0
    # Đường dẫn đến thư mục cogs, giả sử 'core' và 'cogs' nằm trong cùng thư mục 'bot'
    # và file này (bot.py) nằm trong 'core'
    cogs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cogs') # Đi lên 1 cấp từ 'core', rồi vào 'cogs'

    for filename in os.listdir(cogs_dir):
        # Chỉ load các file Python, không phải thư mục con hay file ẩn
        if filename.endswith('.py') and not filename.startswith('_'):
            cog_name = filename[:-3] # Bỏ đuôi '.py'
            try:
                # Đường dẫn để load extension là 'tên_thư_mục_cogs.tên_file_cog'
                # Ví dụ: nếu thư mục cogs tên là 'cogs', file là 'economy.py' -> 'cogs.economy'
                # Cần đảm bảo thư mục 'cogs' nằm trong PYTHONPATH hoặc cùng cấp với file chạy chính (main.py)
                # và main.py chạy từ thư mục cha của 'bot'
                bot.load_extension(f'cogs.{cog_name}') # Quan trọng: 'cogs' là tên thư mục
                print(f'  [+] Đã tải thành công Cog: {cog_name}')
                loaded_cogs_count += 1
            except Exception as e:
                print(f'  [!] LỖI khi tải Cog {cog_name}:')
                print(f'      Loại lỗi: {type(e).__name__}')
                print(f'      Thông điệp: {e}')
    print(f'--- Hoàn tất! Đã tải {loaded_cogs_count} Cogs. ---')
    print(f'--------------------------------------------------')

# Lưu ý: hàm load_all_cogs() sẽ được gọi từ file main.py trước khi bot.run()
