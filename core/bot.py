# bot/core/bot.py
import nextcord
from nextcord.ext import commands
import os # Thư viện os để làm việc với hệ thống file

# Import các thành phần cần thiết từ package 'core'
from .config import COMMAND_PREFIX, BARE_COMMAND_MAP
from .database import get_guild_config
from .utils import try_send
from .icons import ICON_ERROR, ICON_WARNING, ICON_INFO, ICON_LOADING, ICON_SUCCESS # Đã thêm ở bước trước

# --- Khởi tạo Bot ---
intents = nextcord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

# --- Các Sự Kiện (Events) của Bot ---

@bot.event
async def on_ready():
    print(f'--------------------------------------------------')
    print(f'{ICON_SUCCESS} Bot đã đăng nhập với tên: {bot.user.name} (ID: {bot.user.id})')
    print(f'{ICON_INFO} Prefix lệnh: {COMMAND_PREFIX}')
    print(f'Nextcord Version: {nextcord.__version__}')
    print(f'Bot đã sẵn sàng và đang chờ lệnh!')
    print(f'{ICON_INFO} Để xem trợ giúp, hãy gõ /help trên Discord.')
    print(f'--------------------------------------------------')
    # await bot.change_presence(activity=nextcord.Game(name=f"Dùng /help"))


@bot.event
async def on_message(message: nextcord.Message):
    if message.author.bot:
        return
    if not message.guild:
        await bot.process_commands(message)
        return
    content = message.content.strip()
    if not content:
        return

    guild_config = get_guild_config(message.guild.id)
    active_bare_channels = guild_config.get("bare_command_active_channels", [])
    process_as_command = True

    if message.channel.id in active_bare_channels and not content.startswith(COMMAND_PREFIX):
        parts = content.split(maxsplit=1)
        command_candidate = parts[0].lower()
        if command_candidate in BARE_COMMAND_MAP:
            actual_command_name = BARE_COMMAND_MAP[command_candidate]
            args_for_bare_command = parts[1] if len(parts) > 1 else ""
            message.content = f"{COMMAND_PREFIX}{actual_command_name} {args_for_bare_command}".strip()
        else:
            if len(content.split()) <= 3:
                 await try_send(message.channel, content=f"{ICON_ERROR} Lệnh tắt `{command_candidate}` không hợp lệ hoặc không được hỗ trợ. Hãy dùng `/help` để xem các lệnh.")
            process_as_command = False
    
    if process_as_command:
        await bot.process_commands(message)

@bot.event
async def on_command_error(ctx: commands.Context, error):
    if isinstance(error, commands.CommandNotFound):
        return 
    elif isinstance(error, commands.MissingRequiredArgument):
        cmd_name = ctx.command.name if ctx.command else "lệnh này"
        help_msg_for_cmd = f"Gõ `/help lệnh {cmd_name}` để xem chi tiết." if bot.get_command(cmd_name) else ""
        await try_send(ctx, content=f"{ICON_WARNING} Bạn thiếu tham số `{error.param.name}` cho lệnh `{cmd_name}`. {help_msg_for_cmd}")
    elif isinstance(error, commands.BadArgument):
        await try_send(ctx, content=f"{ICON_ERROR} Đối số bạn cung cấp không hợp lệ. Vui lòng kiểm tra lại. Lỗi chi tiết: {error}")
    elif isinstance(error, commands.CommandOnCooldown):
        await try_send(ctx, content=f"{ICON_LOADING} Lệnh `{ctx.command.name}` đang trong thời gian chờ. Bạn cần đợi **{error.retry_after:.1f} giây** nữa.")
    elif isinstance(error, commands.MissingPermissions):
        perms_list = ", ".join([f"`{perm.replace('_', ' ').title()}`" for perm in error.missing_permissions])
        await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ quyền để dùng lệnh này. Thiếu quyền: {perms_list}.")
    elif isinstance(error, commands.NotOwner):
        await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ dành cho chủ sở hữu của Bot.")
    elif isinstance(error, commands.CheckFailure):
        print(f"Lỗi CheckFailure không được xử lý cho lệnh '{ctx.command.name if ctx.command else 'unknown'}': {error}")
        await try_send(ctx, content=f"{ICON_ERROR} Bạn không đáp ứng điều kiện để sử dụng lệnh này.")
    else:
        print(f"Lỗi không xác định trong lệnh '{ctx.command.name if ctx.command else 'unknown'}':")
        print(f"Loại lỗi: {type(error).__name__}")
        print(f"Thông điệp lỗi: {error}")
        await try_send(ctx, content=f"{ICON_ERROR} Ối! Đã có lỗi không mong muốn xảy ra khi thực hiện lệnh. Vui lòng thử lại sau. 😵‍💫")

# --- Hàm Tải Cogs (PHIÊN BẢN CẬP NHẬT ĐỂ HỖ TRỢ THƯ MỤC CON) ---
def load_all_cogs():
    print(f'--------------------------------------------------')
    print(f'Đang tải các Cogs...')
    loaded_cogs_count = 0
    
    cogs_main_directory = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'cogs')

    for root, dirs, files in os.walk(cogs_main_directory):
        
        dirs[:] = [d for d in dirs if d != '__pycache__']

        for filename in files:
            if filename.endswith('.py') and not filename.startswith('_'): # Chỉ lấy file .py, bỏ qua các file như __init__.py nếu bạn không muốn load chúng như cog
                module_name_only = filename[:-3] # Tên file không có .py (ví dụ: work_cmd)         
                
                relative_path_to_cog_folder = os.path.relpath(root, cogs_main_directory)
                
                extension_path = ""
                if relative_path_to_cog_folder == ".": # Nếu cog nằm trực tiếp trong thư mục 'cogs'
                    extension_path = f"cogs.{module_name_only}"
                else: # Nếu cog nằm trong thư mục con của 'cogs' (ví dụ: 'cogs/earn/')
                    # Thay thế dấu phân cách thư mục của HĐH (ví dụ \ hoặc /) bằng dấu chấm .
                    python_module_subpath = relative_path_to_cog_folder.replace(os.sep, '.')
                    extension_path = f"cogs.{python_module_subpath}.{module_name_only}"
                
                try:
                    bot.load_extension(extension_path)
                    print(f'  [+] Đã tải thành công Cog: {extension_path}')
                    loaded_cogs_count += 1
                except commands.ExtensionAlreadyLoaded:
                    print(f'  [~] Cog đã được tải từ trước: {extension_path}')
                except commands.NoEntryPointError: # Lỗi này quan trọng
                    print(f'  [!] LỖI NoEntryPointError khi tải {extension_path}: File cog thiếu hàm setup(bot).')
                except Exception as e:
                    print(f'  [!] LỖI khi tải Cog {extension_path}:')
                    print(f'      Loại lỗi: {type(e).__name__}')
                    print(f'      Thông điệp: {e}')
                    # import traceback # Để debug chi tiết hơn nếu cần
                    # traceback.print_exc()
                    
    print(f'--- Hoàn tất! Đã tải {loaded_cogs_count} Cogs. ---')
    print(f'--------------------------------------------------')

