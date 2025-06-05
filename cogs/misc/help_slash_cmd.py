# bot/cogs/misc/help_slash_cmd.py
import nextcord
from nextcord.ext import commands
import traceback 
import logging 

# Import các thành phần cần thiết từ package 'core'
# from core.utils import try_send # Hiện không dùng trực tiếp trong file này nữa
from core.config import (
    COMMAND_PREFIX, 
    WORK_COOLDOWN, DAILY_COOLDOWN, BEG_COOLDOWN, ROB_COOLDOWN, 
    CRIME_COOLDOWN, FISH_COOLDOWN, SLOTS_COOLDOWN, CF_COOLDOWN, DICE_COOLDOWN,
    BARE_COMMAND_MAP 
)
# Đảm bảo bạn đã import ĐÚNG và ĐỦ các icon bạn sử dụng từ core.icons
from core.icons import ( 
    ICON_HELP, ICON_COMMAND_DETAIL, ICON_BANK, ICON_MONEY_BAG, 
    ICON_GAME, ICON_SHOP, ICON_ADMIN, ICON_INFO, ICON_WARNING, ICON_ERROR 
)

logger = logging.getLogger(__name__)

# Đổi tên class Cog để dễ nhận biết trên terminal khi bot tải
class HelpSlashCommandCog(commands.Cog, name="HelpSlashRenamedCog"): 
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info(f"HelpSlashRenamedCog initialized (command will be /minhbeohelp).")

    async def _send_general_help_embed(self, interaction: nextcord.Interaction):
        """Xây dựng và gửi Embed trợ giúp chung."""
        # Sử dụng interaction.application_command.name để lấy tên lệnh slash hiện tại
        current_slash_command_name = interaction.application_command.name 
        logger.debug(f"Entering _send_general_help_embed for {interaction.user.name} (for /{current_slash_command_name})")
        try:
            prefix = COMMAND_PREFIX
            embed = nextcord.Embed(
                title=f"{ICON_HELP} Menu Trợ Giúp - Bot Kinh Tế",
                description=(
                    f"Chào mừng bạn đến với Bot Kinh Tế! Dưới đây là các lệnh bạn có thể sử dụng.\n"
                    f"Để xem chi tiết một lệnh, dùng `/{current_slash_command_name} lệnh <tên_lệnh>` (ví dụ: `/{current_slash_command_name} lệnh work`).\n"
                    f"*Lưu ý: Hầu hết các lệnh đều có tên gọi tắt (alias) được liệt kê trong chi tiết lệnh.*\n"
                    f"Quản trị viên có thể dùng `{prefix}auto` để bật/tắt lệnh không cần prefix trong một kênh."
                ),
                color=nextcord.Color.dark_theme(),
            )
            
            embed.add_field(name=f"{ICON_BANK} Tài Khoản & Tổng Quan",
                            value="`balance` `bank` `deposit` `withdraw` `transfer` `leaderboard` `richest` `inventory`",
                            inline=False)
            embed.add_field(name=f"{ICON_MONEY_BAG} Kiếm Tiền & Cơ Hội",
                            value="`work` `daily` `beg` `crime` `fish` `rob`",
                            inline=False)
            embed.add_field(name=f"{ICON_GAME} Giải Trí & Cờ Bạc",
                            value="`slots` `coinflip` `dice`",
                            inline=False)
            embed.add_field(name=f"{ICON_SHOP} Cửa Hàng Vật Phẩm",
                            value="`shop` `buy` `sell`",
                            inline=False)
            embed.add_field(name=f"{ICON_ADMIN} Quản Trị Server (Lệnh Prefix)",
                            value=f"`{prefix}addmoney` `{prefix}removemoney` `{prefix}auto` `{prefix}mutebot` `{prefix}unmutebot`",
                            inline=False)
            
            embed.set_footer(text=f"Bot được phát triển bởi MinhBeo8. Gõ /{current_slash_command_name} lệnh <tên_lệnh> để biết thêm chi tiết.")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.debug(f"General help followup sent successfully to {interaction.user.name} (for /{current_slash_command_name}).")

        except Exception as e:
            logger.error(f"Lỗi trong _send_general_help_embed (for /{current_slash_command_name}):", exc_info=True)
            try:
                if not interaction.is_expired():
                    await interaction.followup.send(content=f"{ICON_ERROR} Rất tiếc, đã có lỗi khi hiển thị menu trợ giúp chung.", ephemeral=True)
            except Exception as followup_e:
                logger.error(f"Không thể gửi tin nhắn lỗi followup cho general help (for /{current_slash_command_name}): {followup_e}", exc_info=True)

    async def _send_specific_command_help_embed(self, interaction: nextcord.Interaction, command_name_input: str):
        current_slash_command_name = interaction.application_command.name
        logger.debug(f"Entering _send_specific_command_help_embed for command: '{command_name_input}' by {interaction.user.name} (for /{current_slash_command_name})")
        try:
            prefix = COMMAND_PREFIX
            cmd_name_to_find_initially = command_name_input.lower().lstrip(prefix) 
            command_obj = self.bot.get_command(cmd_name_to_find_initially)
            
            if not command_obj:
                logger.debug(f"Command '{cmd_name_to_find_initially}' not found directly. Checking BARE_COMMAND_MAP...")
                actual_command_name_from_bare_map = BARE_COMMAND_MAP.get(cmd_name_to_find_initially)
                if actual_command_name_from_bare_map:
                    logger.debug(f"Bare command alias '{cmd_name_to_find_initially}' maps to '{actual_command_name_from_bare_map}'. Trying to get this command.")
                    command_obj = self.bot.get_command(actual_command_name_from_bare_map)
            
            if not command_obj:
                logger.warning(f"Command '{cmd_name_to_find_initially}' (and its potential bare map) not found for specific help requested by {interaction.user.name} (for /{current_slash_command_name}).")
                await interaction.followup.send(content=f"{ICON_WARNING} Không tìm thấy lệnh prefix nào có tên là `{command_name_input}`. Hãy chắc chắn bạn nhập đúng tên lệnh (ví dụ: `work`, `balance` hoặc tên gọi tắt của nó).", ephemeral=True)
                return

            logger.debug(f"Found command: {command_obj.name} for {interaction.user.name}. Building embed...")
            embed = nextcord.Embed(title=f"{ICON_COMMAND_DETAIL} Chi tiết lệnh: {prefix}{command_obj.name}", color=nextcord.Color.green())
            
            help_text = command_obj.help 
            if not help_text:
                help_text = command_obj.short_doc or "Lệnh này chưa có mô tả chi tiết." 
            embed.description = help_text
            usage = f"`{prefix}{command_obj.name} {command_obj.signature}`".strip()
            embed.add_field(name="📝 Cách sử dụng", value=usage, inline=False)
            if command_obj.aliases:
                aliases_str = ", ".join([f"`{prefix}{alias}`" for alias in command_obj.aliases])
                embed.add_field(name="🏷️ Tên gọi khác (Aliases)", value=aliases_str, inline=False)
            else:
                embed.add_field(name="🏷️ Tên gọi khác (Aliases)", value="Lệnh này không có tên gọi tắt.", inline=False)

            manual_cooldown_commands = {
                "work": WORK_COOLDOWN, "daily": DAILY_COOLDOWN, "beg": BEG_COOLDOWN,
                "rob": ROB_COOLDOWN, "crime": CRIME_COOLDOWN, "fish": FISH_COOLDOWN,
                "slots": SLOTS_COOLDOWN, "coinflip": CF_COOLDOWN, "dice": DICE_COOLDOWN
            }
            if command_obj.name in manual_cooldown_commands:
                cd_seconds = manual_cooldown_commands[command_obj.name]
                if cd_seconds >= 3600 and cd_seconds % 3600 == 0: cd_text = f"{cd_seconds // 3600} giờ"
                elif cd_seconds >= 60 and cd_seconds % 60 == 0: cd_text = f"{cd_seconds // 60} phút"
                else: cd_text = f"{cd_seconds} giây"
                embed.add_field(name="⏳ Thời gian chờ (Cooldown)", value=cd_text, inline=False)
            if command_obj.name in ["addmoney", "removemoney"]:
                embed.add_field(name="🔑 Yêu cầu", value="Chỉ Chủ Server (Người tạo server).", inline=False)
            elif command_obj.name in ["auto", "mutebot", "unmutebot"]:
                embed.add_field(name="🔑 Yêu cầu", value="Quyền `Administrator` trong server.", inline=False)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.debug(f"Specific help followup sent successfully for '{command_obj.name}' to {interaction.user.name} (for /{current_slash_command_name}).")
        except Exception as e:
            logger.error(f"Lỗi trong _send_specific_command_help_embed cho lệnh '{command_name_input}' (for /{current_slash_command_name}):", exc_info=True)
            try:
                if not interaction.is_expired():
                    await interaction.followup.send(content=f"{ICON_ERROR} Rất tiếc, đã có lỗi khi hiển thị chi tiết cho lệnh `{command_name_input}`.", ephemeral=True)
            except Exception as followup_e:
                logger.error(f"Không thể gửi tin nhắn lỗi followup cho specific help (for /{current_slash_command_name}): {followup_e}", exc_info=True)

    # Đổi tên lệnh slash ở đây để thử nghiệm
    @nextcord.slash_command(name="minhbeohelp", description=f"{ICON_INFO} Hiển thị thông tin trợ giúp cho các lệnh của bot.")
    async def help_slash_command(self,
                                 interaction: nextcord.Interaction,
                                 command_name: str = nextcord.SlashOption(
                                     name="lệnh", 
                                     description="Tên lệnh prefix bạn muốn xem chi tiết (ví dụ: work, balance).",
                                     required=False,
                                     default=None
                                 )):
        """Hiển thị danh sách các lệnh hoặc thông tin chi tiết về một lệnh (prefix) cụ thể."""
        
        # Lấy tên lệnh slash thực tế đang được gọi để dùng trong log và hướng dẫn
        actual_slash_command_name = interaction.application_command.name 
        logger.debug(f"/{actual_slash_command_name} slash command invoked by {interaction.user.name} (ID: {interaction.user.id}). Argument 'lệnh': '{command_name}'")
        
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
                logger.debug(f"Interaction for /{actual_slash_command_name} by {interaction.user.name} deferred.")
            else:
                logger.debug(f"Interaction for /{actual_slash_command_name} by {interaction.user.name} was already deferred/responded.")
            
            if not command_name:
                logger.debug(f"Calling _send_general_help_embed for {interaction.user.name} (for /{actual_slash_command_name})...")
                await self._send_general_help_embed(interaction)
            else:
                logger.debug(f"Calling _send_specific_command_help_embed for '{command_name}' by {interaction.user.name} (for /{actual_slash_command_name})...")
                await self._send_specific_command_help_embed(interaction, command_name)
        except Exception as e:
            logger.critical(f"Lỗi nghiêm trọng không bắt được trong /{actual_slash_command_name} bởi {interaction.user.name}:", exc_info=True)
            try:
                if not interaction.is_expired():
                    # Sử dụng followup vì đã defer
                    await interaction.followup.send(content=f"{ICON_ERROR} Đã có lỗi nghiêm trọng khi xử lý yêu cầu `/{actual_slash_command_name}` của bạn.",ephemeral=True)
            except Exception as final_followup_e:
                logger.error(f"Không thể gửi thông báo lỗi cuối cùng cho /{actual_slash_command_name}: {final_followup_e}", exc_info=True)

def setup(bot: commands.Bot):
    bot.add_cog(HelpSlashCommandCog(bot))
