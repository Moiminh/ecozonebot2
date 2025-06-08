import nextcord
from nextcord.ext import commands
import os 
import logging 

from core.config import COMMAND_PREFIX, BARE_COMMAND_MAP 
from core.database import load_economy_data, get_or_create_guild_config
from core.utils import try_send 
from core.icons import ICON_ERROR, ICON_WARNING, ICON_INFO, ICON_LOADING, ICON_SUCCESS 

AI_ENABLED = False
try:
    # Thử import thư viện AI
    import google.generativeai as genai
    # Kiểm tra API Key (giả sử bạn lưu trong file .env)
    if os.getenv("GEMINI_API_KEY"):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        AI_ENABLED = True
        logging.info("Thư viện AI và API Key hợp lệ. Trợ lý AI sẽ được kích hoạt.")
    else:
        logging.warning("Không tìm thấy GEMINI_API_KEY. Trợ lý AI sẽ bị vô hiệu hóa.")
except ImportError:
    logging.warning("Thư viện google.generativeai chưa được cài đặt. Trợ lý AI sẽ bị vô hiệu hóa.")

intents = nextcord.Intents.default()
intents.message_content = True 
intents.members = True       
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)
logger = logging.getLogger(__name__) 

@bot.event
async def on_ready():
    logger.info(f"--------------------------------------------------")
    logger.info(f"{ICON_SUCCESS} Bot đã đăng nhập với tên: {bot.user.name} (ID: {bot.user.id})")
    logger.info(f"{ICON_INFO} Prefix lệnh: {COMMAND_PREFIX}")
    logger.info(f"Nextcord Version: {nextcord.__version__}")
    logger.info(f"Bot đã sẵn sàng và đang chờ lệnh!")
    logger.info(f"{ICON_INFO} Để xem trợ giúp, hãy gõ /menu trên Discord.")
    logger.info(f"--------------------------------------------------")

@bot.event
async def on_message(message: nextcord.Message):
    logger.debug(f"ON_MESSAGE: Received message: '{message.content}' from {message.author.name} ({message.author.id})")

    if message.author.bot or not message.guild:
        return

    content = message.content.strip()
    if not content:
        return

    economy_data = load_economy_data()
    guild_config = get_or_create_guild_config(economy_data, message.guild.id)
    active_bare_channels = guild_config.get("bare_command_active_channels", [])
    
    should_process_this_message_as_command = False 

    if message.channel.id in active_bare_channels and not content.startswith(COMMAND_PREFIX):
        parts = content.split(maxsplit=1) 
        command_candidate = parts[0].lower()

        if command_candidate in BARE_COMMAND_MAP:
            actual_command_name = BARE_COMMAND_MAP[command_candidate]
            
            if bot.get_command(actual_command_name):
                args_for_bare_command = parts[1] if len(parts) > 1 else ""
                message.content = f"{COMMAND_PREFIX}{actual_command_name} {args_for_bare_command}".strip()
                should_process_this_message_as_command = True
                logger.info(f"BARE_CMD_TRANSFORM: '{content}' by {message.author.name} -> '{message.content}'")
            else:
                logger.warning(f"BARE_CMD_INVALID_MAP: Lệnh tắt '{command_candidate}' trỏ đến lệnh gốc '{actual_command_name}' KHÔNG TỒN TẠI.")
        # [SỬA LỖI] Loại bỏ việc gửi tin nhắn lỗi cho các tin nhắn thường
        # else:
        #     if len(content.split()) <= 3: 
        #          await try_send(message.channel, content=f"{ICON_ERROR} Lệnh tắt `{command_candidate}` không hợp lệ. Dùng `/menu`.")
    
    elif content.startswith(COMMAND_PREFIX):
        should_process_this_message_as_command = True
    
    if should_process_this_message_as_command:
        logger.debug(f"WILL CALL bot.process_commands for: '{message.content}'")
        await bot.process_commands(message)
        logger.debug(f"FINISHED bot.process_commands for: '{message.content}'")

@bot.event
async def on_command_error(ctx: commands.Context, error):
    logger.debug(f"on_command_error triggered for command '{ctx.command.name if ctx.command else 'unknown'}' by {ctx.author.name}. Error: {type(error).__name__}")
    if isinstance(error, commands.CommandNotFound):
        return 
    elif isinstance(error, commands.MissingRequiredArgument):
        cmd_name = ctx.command.name if ctx.command else "lệnh này"
        help_msg_for_cmd = f"Gõ `/menu lệnh {cmd_name}` để xem chi tiết." if bot.get_command(cmd_name) else "" 
        await try_send(ctx, content=f"{ICON_WARNING} Bạn thiếu tham số `{error.param.name}` cho lệnh `{cmd_name}`. {help_msg_for_cmd}")
    elif isinstance(error, commands.BadArgument):
        await try_send(ctx, content=f"{ICON_ERROR} Đối số bạn cung cấp không hợp lệ. Lỗi chi tiết: {error}")
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
        await try_send(ctx, content=f"{ICON_ERROR} Ối! Đã có lỗi không mong muốn xảy ra khi thực hiện lệnh. 😵‍💫")

# [SỬA LỖI] Sửa lại toàn bộ hàm load_all_cogs và loại bỏ code thừa
def load_all_cogs():
    logger.info(f"--------------------------------------------------")
    logger.info(f"Đang tải các Cogs...")
    loaded_cogs_count = 0
    # Đường dẫn đến thư mục cogs từ file bot.py
    cogs_main_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'cogs')
    
    for root, dirs, files in os.walk(cogs_main_directory):
        # Bỏ qua thư mục __pycache__
        if '__pycache__' in dirs:
            dirs.remove('__pycache__')
            
        for filename in files:
            if filename.endswith('.py') and not filename.startswith('_'): 
                # Lấy đường dẫn tương đối từ 'cogs'
                relative_path = os.path.relpath(root, cogs_main_directory)
                
                # Xác định xem cog có nằm trong thư mục con hay không
                # Ví dụ: 'ai' hoặc 'earn'
                sub_folder_name = relative_path.split(os.sep)[0] if relative_path != '.' else None

                # <<< LOGIC KIỂM TRA ĐIỀU KIỆN MỚI >>>
                if sub_folder_name == 'ai' and not AI_ENABLED:
                    logger.warning(f"  [~] Bỏ qua việc tải Cog AI do bị vô hiệu hóa: cogs.{sub_folder_name}.{filename[:-3]}")
                    continue
                
                # Tạo chuỗi extension path để load
                if relative_path == ".": 
                    extension_path = f"cogs.{filename[:-3]}"
                else: 
                    python_module_path = relative_path.replace(os.sep, '.')
                    extension_path = f"cogs.{python_module_path}.{filename[:-3]}"
                
                try:
                    bot.load_extension(extension_path)
                    logger.info(f"  [+] Đã tải thành công Cog: {extension_path}")
                    loaded_cogs_count += 1
                except Exception as e: 
                    logger.error(f"  [!] LỖI khi tải Cog {extension_path}:", exc_info=True) 

    logger.info(f"--- Hoàn tất! Đã tải {loaded_cogs_count} Cogs. ---")
    logger.info(f"--------------------------------------------------")import nextcord
from nextcord.ext import commands
import os 
import logging 

from core.config import COMMAND_PREFIX, BARE_COMMAND_MAP 
from core.database import load_economy_data, get_or_create_guild_config
from core.utils import try_send 
from core.icons import ICON_ERROR, ICON_WARNING, ICON_INFO, ICON_LOADING, ICON_SUCCESS 

AI_ENABLED = False
try:
    # Thử import thư viện AI
    import google.generativeai as genai
    # Kiểm tra API Key (giả sử bạn lưu trong file .env)
    if os.getenv("GEMINI_API_KEY"):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        AI_ENABLED = True
        logging.info("Thư viện AI và API Key hợp lệ. Trợ lý AI sẽ được kích hoạt.")
    else:
        logging.warning("Không tìm thấy GEMINI_API_KEY. Trợ lý AI sẽ bị vô hiệu hóa.")
except ImportError:
    logging.warning("Thư viện google.generativeai chưa được cài đặt. Trợ lý AI sẽ bị vô hiệu hóa.")

intents = nextcord.Intents.default()
intents.message_content = True 
intents.members = True       
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)
logger = logging.getLogger(__name__) 

@bot.event
async def on_ready():
    logger.info(f"--------------------------------------------------")
    logger.info(f"{ICON_SUCCESS} Bot đã đăng nhập với tên: {bot.user.name} (ID: {bot.user.id})")
    logger.info(f"{ICON_INFO} Prefix lệnh: {COMMAND_PREFIX}")
    logger.info(f"Nextcord Version: {nextcord.__version__}")
    logger.info(f"Bot đã sẵn sàng và đang chờ lệnh!")
    logger.info(f"{ICON_INFO} Để xem trợ giúp, hãy gõ /menu trên Discord.")
    logger.info(f"--------------------------------------------------")

@bot.event
async def on_message(message: nextcord.Message):
    logger.debug(f"ON_MESSAGE: Received message: '{message.content}' from {message.author.name} ({message.author.id})")

    if message.author.bot or not message.guild:
        return

            for filename in os.listdir(f'./cogs/{foldername}'):
                    if filename.endswith('.py'):
                        cog_name = f"cogs.{foldername}.{filename[:-3]}"
                        
                        # <<< LOGIC KIỂM TRA ĐIỀU KIỆN MỚI >>>
                        if foldername == 'ai' and not AI_ENABLED:
                            logger.info(f"Bỏ qua việc tải Cog AI: {cog_name}")
                            continue
                        
                        try:
                            self.load_extension(cog_name)
                            logger.info(f"Đã tải Cog: {cog_name}")
                        except Exception as e:
                            logger.error(f"Không thể tải Cog {cog_name}: {e}", exc_info=True)
