# bot/core/bot.py
import nextcord
from nextcord.ext import commands
import os 
import logging # Đã có từ trước

# Import các thành phần cần thiết từ package 'core'
from .config import COMMAND_PREFIX, BARE_COMMAND_MAP # BARE_COMMAND_MAP tạm thời không dùng trong on_message này
from .database import get_guild_config 
from .utils import try_send 
from .icons import ICON_ERROR, ICON_WARNING, ICON_INFO, ICON_LOADING, ICON_SUCCESS 

# Khởi tạo Bot (giữ nguyên)
intents = nextcord.Intents.default()
intents.message_content = True 
intents.members = True       
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)
logger = logging.getLogger(__name__) # Logger cho module này (sẽ có tên là core.bot)

@bot.event
async def on_ready():
    logger.info(f"--------------------------------------------------")
    logger.info(f"{ICON_SUCCESS} Bot đã đăng nhập với tên: {bot.user.name} (ID: {bot.user.id})")
    logger.info(f"{ICON_INFO} Prefix lệnh: {COMMAND_PREFIX}")
    logger.info(f"Nextcord Version: {nextcord.__version__}")
    logger.info(f"Bot đã sẵn sàng và đang chờ lệnh!")
    logger.info(f"{ICON_INFO} Để xem trợ giúp, hãy gõ /menu trên Discord.")
    logger.info(f"--------------------------------------------------")
    # await bot.change_presence(activity=nextcord.Game(name=f"Dùng /menu"))

# --- HÀM ON_MESSAGE ĐÃ ĐƯỢC "SIÊU ĐƠN GIẢN HÓA" ĐỂ DEBUG ---
@bot.event
async def on_message(message: nextcord.Message):
    # Sử dụng print() với prefix đặc biệt để chắc chắn thấy trên console khi debug lỗi này
    print(f"SIMPLIFIED_ON_MESSAGE: >>> Received message: '{message.content}' from {message.author.name}")

    if message.author.bot:
        print(f"SIMPLIFIED_ON_MESSAGE: Message from bot, ignoring.")
        return

    # Không xử lý tin nhắn riêng trong phiên bản siêu đơn giản này nữa để tập trung vào guild
    if not message.guild:
        print(f"SIMPLIFIED_ON_MESSAGE: DM message from {message.author.name}. Ignoring for this debug version.")
        # Nếu bạn muốn test cả DM, hãy bỏ comment dòng dưới và comment dòng print trên
        # print(f"SIMPLIFIED_ON_MESSAGE: DM message from {message.author.name}. Calling process_commands.")
        # await bot.process_commands(message)
        # print(f"SIMPLIFIED_ON_MESSAGE: Finished processing DM.")
        return

    content = message.content.strip()
    if not content:
        print(f"SIMPLIFIED_ON_MESSAGE: Empty content after strip, ignoring.")
        return

    # Tạm thời bỏ qua toàn bộ logic xử lý lệnh tắt (bare commands)
    # Chỉ kiểm tra nếu có prefix thì xử lý

    if message.content.startswith(COMMAND_PREFIX):
        print(f"SIMPLIFIED_ON_MESSAGE: Message has prefix. WILL CALL bot.process_commands for: '{message.content}'")
        await bot.process_commands(message)
        print(f"SIMPLIFIED_ON_MESSAGE: FINISHED bot.process_commands for: '{message.content}'")
    else:
        # Nếu không có prefix, trong phiên bản debug này, chúng ta sẽ bỏ qua hoàn toàn
        print(f"SIMPLIFIED_ON_MESSAGE: Message does not have prefix. Ignoring as command: '{message.content}'")


@bot.event
async def on_command_error(ctx: commands.Context, error):
    logger.debug(f"on_command_error triggered for command '{ctx.command.name if ctx.command else 'unknown'}' by {ctx.author.name}. Error: {type(error).__name__} - {error}")
    if isinstance(error, commands.CommandNotFound):
        return 
    elif isinstance(error, commands.MissingRequiredArgument):
        cmd_name = ctx.command.name if ctx.command else "lệnh này"
        help_msg_for_cmd = f"Gõ `/menu lệnh {cmd_name}` để xem chi tiết." if bot.get_command(cmd_name) else "" # Giả sử lệnh help là /menu
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
        logger.warning(f"CheckFailure cho lệnh '{ctx.command.name if ctx.command else 'unknown'}' bởi user {ctx.author.id}: {error}")
        await try_send(ctx, content=f"{ICON_ERROR} Bạn không đáp ứng điều kiện để sử dụng lệnh này.")
    else:
        logger.error(f"Lỗi không xác định trong lệnh '{ctx.command.name if ctx.command else 'unknown'}' bởi user {ctx.author.id}:", exc_info=True)
        await try_send(ctx, content=f"{ICON_ERROR} Ối! Đã có lỗi không mong muốn xảy ra khi thực hiện lệnh. Vui lòng thử lại sau. 😵‍💫")

# --- Hàm Tải Cogs (PHIÊN BẢN CẬP NHẬT ĐỂ HỖ TRỢ THƯ MỤC CON) ---
def load_all_cogs():
    # ... (Hàm load_all_cogs giữ nguyên như phiên bản đã có logger và hỗ trợ thư mục con) ...
    logger.info(f"--------------------------------------------------")
    logger.info(f"Đang tải các Cogs...")
    loaded_cogs_count = 0
    cogs_main_directory = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'cogs')
    for root, dirs, files in os.walk(cogs_main_directory):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for filename in files:
            if filename.endswith('.py') and not filename.startswith('_'):
                module_name_only = filename[:-3]
                relative_path_to_cog_folder = os.path.relpath(root, cogs_main_directory)
                extension_path = ""
                if relative_path_to_cog_folder == ".":
                    extension_path = f"cogs.{module_name_only}"
                else:
                    python_module_subpath = relative_path_to_cog_folder.replace(os.sep, '.')
                    extension_path = f"cogs.{python_module_subpath}.{module_name_only}"
                try:
                    bot.load_extension(extension_path)
                    logger.info(f"  [+] Đã tải thành công Cog: {extension_path}")
                    loaded_cogs_count += 1
                except commands.ExtensionAlreadyLoaded:
                    logger.debug(f"  [~] Cog đã được tải từ trước: {extension_path}")
                except commands.NoEntryPointError:
                    logger.error(f"  [!] LỖI NoEntryPointError khi tải {extension_path}: File cog thiếu hàm setup(bot).")
                except Exception as e:
                    logger.error(f"  [!] LỖI khi tải Cog {extension_path}: Loại lỗi: {type(e).__name__} - {e}", exc_info=True) 
    logger.info(f"--- Hoàn tất! Đã tải {loaded_cogs_count} Cogs. ---")
    logger.info(f"--------------------------------------------------")
