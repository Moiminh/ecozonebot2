import nextcord
from nextcord.ext import commands
import os
import logging
import json

# Cấu hình intents cho bot
intents = nextcord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

# Khởi tạo bot với prefix và intents
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

main_logger = logging.getLogger(__name__)

# Danh sách các cogs sẽ được tải khi bot khởi động
# Đã dọn dẹp, chỉ giữ lại các cogs cần thiết cho phiên bản SQLite
INITIAL_COGS = [
    # Admin
    "cogs.admin.addmoney_cmd",
    "cogs.admin.removemoney_cmd",
    "cogs.admin.auto_cmd",
    "cogs.admin.mutebot_cmd",
    "cogs.admin.unmutebot_cmd",
    
    # AI
    "cogs.ai.assistant_cog",
    
    # Earn
    "cogs.earn.beg_cmd",
    "cogs.earn.crime_cmd",
    "cogs.earn.daily_cmd",
    "cogs.earn.fish_cmd",
    "cogs.earn.rob_cmd",
    "cogs.earn.work_cmd",
    
    # Economy
    "cogs.economy.balance_cmd",
    "cogs.economy.bank_cmd",
    "cogs.economy.deposit_cmd",
    "cogs.economy.launder_cmd",
    "cogs.economy.transfer_cmd",
    "cogs.economy.visa_cmd",
    "cogs.economy.withdraw_cmd",
    
    # Games
    "cogs.games.coinflip_cmd",
    "cogs.games.dice_cmd",
    "cogs.games.slots_cmd",
    
    # Misc
    "cogs.misc.dashboard_cmd",
    "cogs.misc.globallb_cmd",
    "cogs.misc.leaderboard_cmd",
    "cogs.misc.richest_cmd",
    "cogs.misc.help_slash_cmd",
    "cogs.misc.howtoplay_cmd",
    
    # Moderation
    "cogs.moderation.manage_mods_cmd",
    "cogs.moderation.mod_tools_slash",
    
    # Shop
    "cogs.shop.buy_cmd",
    "cogs.shop.inventory_cmd",
    "cogs.shop.sell_cmd",
    "cogs.shop.shop_cmd",

    # Actions
    "cogs.actions.use_cmd",

    # Tasks
    "cogs.tasks.dynamic_shop_task",
    "cogs.tasks.survival_task",
    
    # Test
    "cogs.test_slash_cog",
]

def load_all_cogs():
    """Tải tất cả các cogs được định nghĩa trong INITIAL_COGS."""
    main_logger.info(f"--- Bắt đầu tải {len(INITIAL_COGS)} Cogs ---")
    for extension in INITIAL_COGS:
        try:
            bot.load_extension(extension)
            main_logger.info(f"  [+] Đã tải thành công Cog: {extension}")
        except Exception as e:
            main_logger.error(f"  [!] LỖI khi tải Cog {extension}:\n{e}", exc_info=True)
    main_logger.info("--- Hoàn tất việc tải Cogs ---")

@bot.event
async def on_ready():
    """Sự kiện được kích hoạt khi bot đã sẵn sàng và kết nối với Discord."""
    main_logger.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
    main_logger.info('Bot đã sẵn sàng và đang hoạt động!')
    await bot.change_presence(activity=nextcord.Game(name="EconZone - !help"))

@bot.event
async def on_message(message: nextcord.Message):
    """Sự kiện được kích hoạt mỗi khi có tin nhắn mới."""
    # Bỏ qua tin nhắn từ bot và tin nhắn riêng
    if message.author.bot or not message.guild:
        await bot.process_commands(message)
        return
    
    guild_id = message.guild.id
    channel_id = message.channel.id
    
    try:
        # Logic được đơn giản hóa, chỉ chạy cho SQLite
        guild_config = await bot.loop.run_in_executor(None, bot.db.get_or_create_guild_config, guild_id)
        if guild_config:
            # Lấy danh sách kênh từ CSDL và chuyển từ chuỗi JSON thành list
            muted_channels = json.loads(guild_config['muted_channels'])
            bare_command_channels = json.loads(guild_config['bare_command_active_channels'])

            # Xử lý kênh bị tắt tiếng
            if channel_id in muted_channels:
                return # Dừng xử lý nếu kênh bị mute

            # Xử lý lệnh không cần prefix
            if channel_id in bare_command_channels and not message.content.startswith(bot.command_prefix):
                command_name = message.content.split(" ")[0].lower()
                if bot.get_command(command_name):
                    message.content = bot.command_prefix + message.content
    
    except Exception as e:
        main_logger.error(f"Lỗi trong on_message khi xử lý guild_config: {e}", exc_info=True)

    await bot.process_commands(message)
