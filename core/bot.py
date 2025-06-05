# bot/core/bot.py
import nextcord
from nextcord.ext import commands
import os 
import logging # Sử dụng logging

# Import các thành phần cần thiết từ package 'core'
from .config import COMMAND_PREFIX, BARE_COMMAND_MAP 
from .database import get_guild_config 
from .utils import try_send 
# Đảm bảo bạn import đủ các icon cần thiết cho on_command_error và on_ready
from .icons import ICON_ERROR, ICON_WARNING, ICON_INFO, ICON_LOADING, ICON_SUCCESS 

# --- Khởi tạo Bot ---
intents = nextcord.Intents.default()
intents.message_content = True 
intents.members = True       
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)
# Tạo logger cho module này (sẽ có tên là 'core.bot' khi được import từ nơi khác)
logger = logging.getLogger(__name__) 

@bot.event
async def on_ready():
    logger.info(f"--------------------------------------------------")
    logger.info(f"{ICON_SUCCESS} Bot đã đăng nhập với tên: {bot.user.name} (ID: {bot.user.id})")
    logger.info(f"{ICON_INFO} Prefix lệnh: {COMMAND_PREFIX}")
    logger.info(f"Nextcord Version: {nextcord.__version__}")
    logger.info(f"Bot đã sẵn sàng và đang chờ lệnh!")
    logger.info(f"{ICON_INFO} Để xem trợ giúp, hãy gõ /menu trên Discord.") # Giả sử lệnh help slash là /menu
    logger.info(f"--------------------------------------------------")
    
# --- HÀM ON_MESSAGE PHIÊN BẢN ĐẦY ĐỦ (ĐÃ CÓ LOGGER) ---
@bot.event
async def on_message(message: nextcord.Message):
    # Log mọi tin nhắn nhận được ở mức DEBUG để theo dõi chi tiết trong file log
    logger.debug(f"ON_MESSAGE: Received message: '{message.content}' from {message.author.name} ({message.author.id}) in G:{message.guild.id if message.guild else 'DM'}/C:{message.channel.id}")

    if message.author.bot:
        logger.debug(f"ON_MESSAGE: Message from bot {message.author.name}, ignoring.")
        return

    if not message.guild: # Xử lý tin nhắn riêng
        logger.debug(f"ON_MESSAGE: DM message from {message.author.name}. Processing commands.")
        await bot.process_commands(message)
        logger.debug(f"ON_MESSAGE: Finished processing DM for {message.author.name}.")
        return

    content = message.content.strip()
    if not content:
        logger.debug(f"ON_MESSAGE: Empty content after strip, ignoring.")
        return

    guild_config = get_guild_config(message.guild.id)
    active_bare_channels = guild_config.get("bare_command_active_channels", [])
    
    should_process_this_message_as_command = False # Khởi tạo là False

    if message.channel.id in active_bare_channels and not content.startswith(COMMAND_PREFIX):
        logger.debug(f"ON_MESSAGE: Auto-channel detected for '{message.channel.id}', no prefix. Attempting bare command: '{content}'")
        parts = content.split(maxsplit=1) 
        command_candidate = parts[0].lower() # Chuyển lệnh tắt thành chữ thường

        if command_candidate in BARE_COMMAND_MAP: # So sánh với các key chữ thường trong map
            actual_command_name = BARE_COMMAND_MAP[command_candidate]
            args_for_bare_command = parts[1] if len(parts) > 1 else ""
            
            if bot.get_command(actual_command_name): # Kiểm tra lệnh gốc có tồn tại không
                message.content = f"{COMMAND_PREFIX}{actual_command_name} {args_for_bare_command}".strip()
                should_process_this_message_as_command = True # Đánh dấu để xử lý
                # Log INFO cho hành động biến đổi lệnh tắt thành công
                logger.info(f"BARE_CMD_TRANSFORM: '{command_candidate}' by {message.author.name} -> '{message.content}'")
            else:
                logger.warning(f"BARE_CMD_INVALID_MAP: Lệnh tắt '{command_candidate}' trỏ đến lệnh gốc '{actual_command_name}' KHÔNG TỒN TẠI. Bỏ qua.")
                # should_process_this_message_as_command vẫn là False
        else:
            # Từ không có trong BARE_COMMAND_MAP trong kênh auto
            # Chỉ gửi cảnh báo nếu tin nhắn ngắn, có thể là gõ nhầm lệnh tắt
            if len(content.split()) <= 3: 
                 logger.debug(f"ON_MESSAGE: Potential invalid bare command '{command_candidate}' by {message.author.name} in auto-channel. Sending warning.")
                 await try_send(message.channel, content=f"{ICON_ERROR} Lệnh tắt `{command_candidate}` không hợp lệ hoặc không được hỗ trợ. Dùng `/menu` hoặc `{COMMAND_PREFIX}help`.")
            # else: (tin nhắn dài hơn, coi như chat thường, không làm gì cả)
            #    logger.debug(f"ON_MESSAGE: Content '{content}' in auto-channel not a recognized bare command. Treating as normal chat.")
            # should_process_this_message_as_command vẫn là False
    
    elif content.startswith(COMMAND_PREFIX): # Nếu tin nhắn có prefix
        logger.debug(f"ON_MESSAGE: Message from {message.author.name} has prefix '{COMMAND_PREFIX}'. Flagged for processing: '{message.content}'")
        should_process_this_message_as_command = True # Đánh dấu để xử lý
    
    # Else: tin nhắn không có prefix VÀ không trong kênh auto => chat thường, 
    # should_process_this_message_as_command giữ nguyên giá trị False ban đầu của nó.

    if should_process_this_message_as_command:
        logger.debug(f"ON_MESSAGE: FINAL DECISION - WILL CALL bot.process_commands for: '{message.content}' by {message.author.name}")
        await bot.process_commands(message)
        logger.debug(f"ON_MESSAGE: FINAL DECISION - FINISHED bot.process_commands for: '{message.content}' by {message.author.name}")
    # else: # Không cần log cho mọi tin nhắn thường để tránh spam log file trừ khi debug rất sâu
        # logger.debug(f"ON_MESSAGE: FINAL DECISION - Message '{content}' WILL NOT be processed as a command by {message.author.name}.")


@bot.event
async def on_command_error(ctx: commands.Context, error):
    logger.debug(f"on_command_error triggered for command '{ctx.command.name if ctx.command else 'unknown'}' by {ctx.author.name}. Error: {type(error).__name__} - {error}")
    if isinstance(error, commands.CommandNotFound):
        # logger.debug(f"CommandNotFound: {ctx.invoked_with} by {ctx.author.name}") # Có thể log nếu muốn
        return # Bỏ qua lỗi không tìm thấy lệnh một cách lặng lẽ
    elif isinstance(error, commands.MissingRequiredArgument):
        cmd_name = ctx.command.name if ctx.command else "lệnh này"
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
        logger.error(f"Lỗi không xác định trong lệnh '{ctx.command.name if ctx.command else 'unknown'}' bởi user {ctx.author.id}:", exc_info=True) # Ghi cả traceback
        await try_send(ctx, content=f"{ICON_ERROR} Ối! Đã có lỗi không mong muốn xảy ra khi thực hiện lệnh. Vui lòng thử lại sau. 😵‍💫")

# --- Hàm Tải Cogs (PHIÊN BẢN CẬP NHẬT ĐỂ HỖ TRỢ THƯ MỤC CON) ---
def load_all_cogs():
    logger.info(f"--------------------------------------------------")
    logger.info(f"Đang tải các Cogs...")
    loaded_cogs_count = 0
    # Đường dẫn đến thư mục 'cogs' chính
    cogs_main_directory = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'cogs')
    
    for root, dirs, files in os.walk(cogs_main_directory):
        # Bỏ qua các thư mục đặc biệt như __pycache__ để tránh lỗi không cần thiết
        dirs[:] = [d for d in dirs if d != '__pycache__']
        
        for filename in files:
            # Chỉ load các file Python, không phải thư mục con hay file ẩn (bỏ qua __init__.py)
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
                except commands.ExtensionAlreadyLoaded: # Bắt lỗi nếu Cog đã được tải
                    logger.debug(f"  [~] Cog đã được tải từ trước: {extension_path}")
                except commands.NoEntryPointError: # Lỗi Cog không có hàm setup
                    logger.error(f"  [!] LỖI NoEntryPointError khi tải {extension_path}: File cog thiếu hàm setup(bot).")
                except Exception as e: # Bắt các lỗi khác khi load Cog
                    logger.error(f"  [!] LỖI khi tải Cog {extension_path}: Loại lỗi: {type(e).__name__} - {e}", exc_info=True) 
                    
    logger.info(f"--- Hoàn tất! Đã tải {loaded_cogs_count} Cogs. ---")
    logger.info(f"--------------------------------------------------")
