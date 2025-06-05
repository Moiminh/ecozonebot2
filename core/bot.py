# bot/core/bot.py
import nextcord
from nextcord.ext import commands
import os 
import logging # Vẫn cần logging cho các phần khác

# Import các thành phần cần thiết từ package 'core'
from .config import COMMAND_PREFIX, BARE_COMMAND_MAP 
from .database import get_guild_config 
from .utils import try_send 
from .icons import ICON_ERROR, ICON_WARNING, ICON_INFO, ICON_LOADING, ICON_SUCCESS 

# Khởi tạo bot (giữ nguyên)
intents = nextcord.Intents.default()
intents.message_content = True 
intents.members = True       
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)
logger = logging.getLogger(__name__) # Logger cho module này

@bot.event
async def on_ready():
    # Sử dụng logger thay vì print ở đây cho nhất quán
    logger.info(f"--------------------------------------------------")
    logger.info(f"{ICON_SUCCESS} Bot đã đăng nhập với tên: {bot.user.name} (ID: {bot.user.id})")
    logger.info(f"{ICON_INFO} Prefix lệnh: {COMMAND_PREFIX}")
    logger.info(f"Nextcord Version: {nextcord.__version__}")
    logger.info(f"Bot đã sẵn sàng và đang chờ lệnh!")
    logger.info(f"{ICON_INFO} Để xem trợ giúp, hãy gõ /menu trên Discord.") # Giả sử lệnh help đã đổi tên thành /menu
    logger.info(f"--------------------------------------------------")
    # await bot.change_presence(activity=nextcord.Game(name=f"Dùng /menu"))

# --- HÀM ON_MESSAGE ĐÃ ĐƯỢC THÊM DEBUG PRINT ---
@bot.event
async def on_message(message: nextcord.Message):
    # Sử dụng print() với prefix đặc biệt để chắc chắn thấy trên console khi debug lỗi này
    print(f"DEBUG_ON_MESSAGE: >>> Received message: '{message.content}' from {message.author.name} ({message.author.id}) in G:{message.guild.id}/C:{message.channel.id}")

    if message.author.bot:
        print(f"DEBUG_ON_MESSAGE: Message from bot {message.author.name}, ignoring.")
        return

    if not message.guild:
        print(f"DEBUG_ON_MESSAGE: DM message from {message.author.name}. Calling process_commands (1st potential call).")
        await bot.process_commands(message)
        print(f"DEBUG_ON_MESSAGE: Finished processing DM for {message.author.name}.")
        return

    content = message.content.strip()
    if not content:
        print(f"DEBUG_ON_MESSAGE: Empty content after strip, ignoring.")
        return

    guild_config = get_guild_config(message.guild.id)
    active_bare_channels = guild_config.get("bare_command_active_channels", [])
    
    # Mặc định là không xử lý như lệnh cho đến khi được xác nhận rõ ràng
    should_process_this_message_as_command = False 

    if message.channel.id in active_bare_channels and not content.startswith(COMMAND_PREFIX):
        print(f"DEBUG_ON_MESSAGE: Auto-channel detected, no prefix. Attempting bare command: '{content}'")
        parts = content.split(maxsplit=1) 
        command_candidate = parts[0].lower()

        if command_candidate in BARE_COMMAND_MAP:
            actual_command_name = BARE_COMMAND_MAP[command_candidate]
            args_for_bare_command = parts[1] if len(parts) > 1 else ""
            
            if bot.get_command(actual_command_name):
                message.content = f"{COMMAND_PREFIX}{actual_command_name} {args_for_bare_command}".strip()
                should_process_this_message_as_command = True
                print(f"DEBUG_ON_MESSAGE: Valid bare command. Transformed message.content to: '{message.content}'. Flagged for processing.")
            else:
                print(f"DEBUG_ON_MESSAGE: Bare command '{command_candidate}' maps to UNKNOWN prefix command '{actual_command_name}'. Ignoring.")
                # process_as_command vẫn là False
        else:
            if len(content.split()) <= 3:
                 await try_send(message.channel, content=f"{ICON_ERROR} Lệnh tắt `{command_candidate}` không hợp lệ. Dùng `/menu` hoặc `{COMMAND_PREFIX}help`.")
            print(f"DEBUG_ON_MESSAGE: Word '{command_candidate}' is not a valid bare command in auto-channel. Ignoring as command.")
            # process_as_command vẫn là False
    
    elif content.startswith(COMMAND_PREFIX):
        print(f"DEBUG_ON_MESSAGE: Message has prefix '{COMMAND_PREFIX}'. Flagged for processing.")
        should_process_this_message_as_command = True
    
    else:
        # Tin nhắn không có prefix VÀ không trong kênh auto => chat thường
        print(f"DEBUG_ON_MESSAGE: Normal chat message (no prefix, not auto-channel). Ignoring as command: '{content}'")
        should_process_this_message_as_command = False # Đảm bảo là False

    # --- Xử lý lệnh cuối cùng ---
    if should_process_this_message_as_command:
        print(f"DEBUG_ON_MESSAGE: FINAL DECISION - WILL CALL bot.process_commands for: '{message.content}'")
        await bot.process_commands(message)
        print(f"DEBUG_ON_MESSAGE: FINAL DECISION - FINISHED bot.process_commands for: '{message.content}'")
    else:
        print(f"DEBUG_ON_MESSAGE: FINAL DECISION - Message '{content}' WILL NOT be processed as a command.")

@bot.event
async def on_command_error(ctx: commands.Context, error):
    # ... (hàm on_command_error giữ nguyên như phiên bản đã có logger) ...
    # Sử dụng logger cho nhất quán
    logger.debug(f"on_command_error triggered for command '{ctx.command.name if ctx.command else 'unknown'}' by {ctx.author.name}. Error: {type(error).__name__} - {error}")
    if isinstance(error, commands.CommandNotFound):
        # logger.debug(f"CommandNotFound: {ctx.invoked_with}") # Có thể log nếu muốn theo dõi các lệnh gõ sai
        return 
    elif isinstance(error, commands.MissingRequiredArgument):
        cmd_name = ctx.command.name if ctx.command else "lệnh này"
        # Giả sử lệnh help slash của bạn tên là 'menu'
        help_msg_for_cmd = f"Gõ `/menu lệnh {cmd_name}` để xem chi tiết." if bot.get_command(cmd_name) else ""
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
# ... (hàm load_all_cogs() giữ nguyên như phiên bản trước) ...
def load_all_cogs():
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
                    logger.error(f"  [!] LỖI khi tải Cog {extension_path}: Loại lỗi: {type(e).__name__} - {e}", exc_info=True) # Thêm exc_info
    logger.info(f"--- Hoàn tất! Đã tải {loaded_cogs_count} Cogs. ---")
    logger.info(f"--------------------------------------------------")
