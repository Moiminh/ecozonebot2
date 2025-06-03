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
    # await bot.change_presence(activity=nextcord.Game(name=f"Dùng {COMMAND_PREFIX}help hoặc /help"))


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
    guild_config = get_guild_config(message.guild.id)
    active_bare_channels = guild_config.get("bare_command_active_channels", [])
    
    process_as_command = True # Mặc định là sẽ cho bot xử lý lệnh

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
            # print(f"Bare command (transformed): '{content}' -> '{message.content}'")
            # Vẫn để process_as_command = True vì đây là lệnh tắt hợp lệ
        else:
            # Đây là trường hợp từ không có trong BARE_COMMAND_MAP trong kênh auto
            # và không có prefix. Có thể là chat thường hoặc gõ nhầm lệnh tắt.
            # Chúng ta sẽ gửi cảnh báo nếu tin nhắn trông giống một nỗ lực dùng lệnh tắt (ngắn).
            if len(content.split()) <= 3: # Ngưỡng tùy chỉnh, ví dụ 3 từ để coi là nỗ lực gõ lệnh
                 await try_send(message.channel, content=f"❌ Lệnh tắt `{command_candidate}` không hợp lệ hoặc không được hỗ trợ trong chế độ này. Hãy dùng `/help` để xem các lệnh và lệnh tắt có sẵn.")
            
            process_as_command = False # Không xử lý như một lệnh nữa vì nó không phải lệnh tắt hợp lệ (hoặc là chat thường)
            # print(f"Bare command (ignored/warned): '{content}' in G:{message.guild.id} C:{message.channel.id}")
    
    # Chỉ xử lý lệnh nếu process_as_command là True
    if process_as_command:
        await bot.process_commands(message)


@bot.event
async def on_command_error(ctx: commands.Context, error):
    """
    Sự kiện này được kích hoạt khi có lỗi xảy ra trong quá trình thực thi một lệnh.
    """
    # Bỏ qua lỗi CommandNotFound để tránh spam console hoặc chat
    if isinstance(error, commands.CommandNotFound):
        return 

    elif isinstance(error, commands.MissingRequiredArgument):
        cmd_name = ctx.command.name if ctx.command else "lệnh này"
        help_msg_for_cmd = f"Gõ `/help lệnh {cmd_name}` để xem chi tiết." if bot.get_command(cmd_name) else ""
        await try_send(ctx, content=f"Bạn thiếu tham số `{error.param.name}` cho lệnh `{cmd_name}`. {help_msg_for_cmd}")

    elif isinstance(error, commands.BadArgument):
        await try_send(ctx, content=f"Đối số bạn cung cấp không hợp lệ. Vui lòng kiểm tra lại. Lỗi chi tiết: {error}")

    elif isinstance(error, commands.CommandOnCooldown):
        await try_send(ctx, content=f"Lệnh `{ctx.command.name}` đang trong thời gian chờ. Bạn cần đợi **{error.retry_after:.1f} giây** nữa.")

    elif isinstance(error, commands.MissingPermissions):
        perms_list = ", ".join([f"`{perm.replace('_', ' ').title()}`" for perm in error.missing_permissions])
        await try_send(ctx, content=f"Bạn không có đủ quyền để dùng lệnh này. Thiếu quyền: {perms_list}.")

    elif isinstance(error, commands.NotOwner):
        await try_send(ctx, content="Lệnh này chỉ dành cho chủ sở hữu của Bot.")

    elif isinstance(error, commands.CheckFailure):
        # Các hàm error handler riêng của lệnh (ví dụ @add_money.error) nên xử lý CheckFailure của chính nó.
        # Đây là fallback.
        print(f"Lỗi CheckFailure không được xử lý cho lệnh '{ctx.command.name if ctx.command else 'unknown'}': {error}")
        await try_send(ctx, content="Bạn không đáp ứng điều kiện để sử dụng lệnh này.")
    
    else:
        print(f"Lỗi không xác định trong lệnh '{ctx.command.name if ctx.command else 'unknown'}':")
        print(f"Loại lỗi: {type(error).__name__}")
        print(f"Thông điệp lỗi: {error}")
        await try_send(ctx, content="Ối! Đã có lỗi không mong muốn xảy ra khi thực hiện lệnh. Vui lòng thử lại sau. 😵‍💫")


# --- Hàm Tải Cogs ---
def load_all_cogs():
    """
    Tải tất cả các file .py trong thư mục 'cogs' dưới dạng extension (cog) cho bot.
    """
    print(f'--------------------------------------------------')
    print(f'Đang tải các Cogs...')
    loaded_cogs_count = 0
    # Giả định rằng file này (bot.py) nằm trong thư mục 'core'
    # và thư mục 'cogs' nằm cùng cấp với 'core' (tức là trong 'bot/cogs')
    # __file__ là đường dẫn đến file hiện tại (bot/core/bot.py)
    # os.path.dirname(__file__) -> bot/core
    # os.path.dirname(os.path.dirname(__file__)) -> bot
    # os.path.join(..., 'cogs') -> bot/cogs
    current_script_path = os.path.dirname(os.path.abspath(__file__)) # bot/core
    cogs_directory_path = os.path.join(os.path.dirname(current_script_path), 'cogs') # bot/cogs


    for filename in os.listdir(cogs_directory_path):
        if filename.endswith('.py') and not filename.startswith('_'): # Bỏ qua các file như __init__.py
            cog_name = filename[:-3]
            try:
                # Đường dẫn để load extension là 'tên_thư_mục_cha_của_cogs.tên_thư_mục_cogs.tên_file_cog'
                # Nếu main.py chạy từ thư mục cha của 'bot', và cấu trúc là bot/cogs/cog.py
                # thì đường dẫn sẽ là 'bot.cogs.cog_name'
                # Tuy nhiên, vì main.py nằm trong bot/, và load_all_cogs được gọi từ đó (thông qua import core.bot)
                # và bot instance cũng được tạo ở đây (core.bot),
                # thì khi load_extension, nó sẽ tìm từ thư mục làm việc của main.py hoặc PYTHONPATH.
                # Nếu main.py nằm trong `bot/` và chạy bằng `python main.py` (từ trong thư mục `bot`),
                # thì đường dẫn load sẽ là `cogs.cog_name`.
                # Đây là cách Nextcord thường xử lý khi file chạy chính và thư mục cogs có mối quan hệ rõ ràng.
                bot.load_extension(f'cogs.{cog_name}')
                print(f'  [+] Đã tải thành công Cog: {cog_name}')
                loaded_cogs_count += 1
            except Exception as e:
                print(f'  [!] LỖI khi tải Cog {cog_name}:')
                print(f'      Loại lỗi: {type(e).__name__}')
                print(f'      Thông điệp: {e}')
    print(f'--- Hoàn tất! Đã tải {loaded_cogs_count} Cogs. ---')
    print(f'--------------------------------------------------')
