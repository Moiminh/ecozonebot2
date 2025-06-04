# bot/cogs/misc/help_slash_cmd.py
import nextcord
from nextcord.ext import commands
import traceback # Để in traceback lỗi chi tiết

# Chúng ta sẽ không dùng try_send ở đây để test trực tiếp interaction
# from core.utils import try_send 
from core.config import COMMAND_PREFIX # Vẫn cần cho một số logic (dù có thể không dùng đến trong test này)
from core.icons import ICON_INFO, ICON_ERROR # Chỉ dùng vài icon cơ bản cho test

class HelpSlashCommandCog(commands.Cog, name="Help Slash Command DEBUG"): # Đổi tên Cog để chắc chắn load bản mới
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"{ICON_INFO} [DEBUG] HelpSlashCommandCog (DEBUG version) initialized.")

    @nextcord.slash_command(name="help", description=f"{ICON_INFO} Hiển thị thông tin trợ giúp cho các lệnh của bot.")
    async def help_slash_command(self,
                                 interaction: nextcord.Interaction,
                                 command_name: str = nextcord.SlashOption(
                                     name="lệnh", 
                                     description="Tên lệnh prefix bạn muốn xem chi tiết.",
                                     required=False,
                                     default=None
                                 )):
        """Phiên bản gỡ lỗi của lệnh /help."""
        
        print(f"{ICON_INFO} [DEBUG] /help command invoked by {interaction.user.name} with arg: '{command_name}'. Guild: {interaction.guild_id}, Channel: {interaction.channel_id}")
        
        try:
            print(f"{ICON_INFO} [DEBUG] Attempting to defer interaction...")
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
                print(f"{ICON_INFO} [DEBUG] Interaction deferred successfully.")
            else:
                print(f"{ICON_INFO} [DEBUG] Interaction was already responded to or deferred.")

            # Gửi một tin nhắn followup cực kỳ đơn giản
            test_message_content = f"{ICON_INFO} Đây là phản hồi test cho lệnh /help."
            if command_name:
                test_message_content += f" Bạn đã hỏi về lệnh: `{command_name}`."
            
            print(f"{ICON_INFO} [DEBUG] Attempting to send followup: '{test_message_content}'")
            await interaction.followup.send(content=test_message_content, ephemeral=True)
            print(f"{ICON_INFO} [DEBUG] Followup sent successfully for /help.")

        except Exception as e:
            print(f"{ICON_ERROR} [CRITICAL DEBUG] An error occurred in /help slash command:")
            traceback.print_exc() # In traceback đầy đủ ra console
            try:
                # Cố gắng gửi thông báo lỗi cho người dùng nếu interaction còn hiệu lực
                # is_done() sẽ là True nếu defer thành công
                if interaction.response.is_done() and not interaction.is_expired():
                    await interaction.followup.send(content=f"{ICON_ERROR} Lỗi nghiêm trọng khi xử lý lệnh /help. Chi tiết đã được ghi lại.", ephemeral=True)
                else:
                     print(f"{ICON_ERROR} [DEBUG] Could not send error followup. Interaction state: is_done={interaction.response.is_done()}, is_expired={interaction.is_expired()}")
            except Exception as followup_exception:
                print(f"{ICON_ERROR} [DEBUG] Failed to send error followup message for /help: {followup_exception}")

def setup(bot: commands.Bot):
    bot.add_cog(HelpSlashCommandCog(bot)) # Đảm bảo tên class Cog khớp
