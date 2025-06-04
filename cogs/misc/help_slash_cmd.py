# bot/cogs/misc/help_slash_cmd.py
import nextcord
from nextcord.ext import commands
import traceback 

from core.utils import try_send # Chúng ta sẽ dùng lại try_send cho an toàn
from core.config import COMMAND_PREFIX
# Đảm bảo bạn import ĐÚNG các icon bạn đã định nghĩa và muốn dùng
from core.icons import (
    ICON_INFO, ICON_ERROR, ICON_HELP, ICON_BANK, ICON_MONEY_BAG, 
    ICON_GAME, ICON_SHOP, ICON_ADMIN 
)

class HelpSlashCommandCog(commands.Cog, name="Help Slash Command V2"): # Đổi tên Cog để chắc chắn load bản mới
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"{ICON_INFO} [DEBUG] HelpSlashCommandCog (V2 - General Help Only) initialized.")

    async def _send_general_help_embed(self, interaction: nextcord.Interaction):
        """Xây dựng và gửi Embed trợ giúp chung."""
        print(f"{ICON_INFO} [DEBUG] Entering _send_general_help_embed for {interaction.user.name}")
        try:
            prefix = COMMAND_PREFIX
            embed = nextcord.Embed(
                title=f"{ICON_HELP} Menu Trợ Giúp - Bot Kinh Tế",
                description=(
                    f"Chào mừng bạn đến với Bot Kinh Tế! Dưới đây là các lệnh bạn có thể sử dụng.\n"
                    f"Để xem chi tiết một lệnh, dùng `/help lệnh <tên_lệnh>` (ví dụ: `/help lệnh work`).\n"
                    f"*Lưu ý: Hầu hết các lệnh đều có tên gọi tắt (alias) được liệt kê trong chi tiết lệnh.*\n"
                    f"Quản trị viên có thể dùng `{prefix}auto` để bật/tắt lệnh không cần prefix trong một kênh."
                ),
                color=nextcord.Color.dark_theme(), # Hoặc màu bạn thích
            )
            
            # Sử dụng các ICON bạn đã định nghĩa
            embed.add_field(name=f"{ICON_BANK} Tài Khoản & Tổng Quan",
                            value="`balance` `bank` `deposit` `withdraw` `transfer` `leaderboard` `richest` `inventory`",
                            inline=False)
            embed.add_field(name=f"{ICON_MONEY_BAG} Kiếm Tiền & Cơ Hội", # ICON_MONEY_BAG từ file icons.py của bạn
                            value="`work` `daily` `beg` `crime` `fish` `rob`",
                            inline=False)
            embed.add_field(name=f"{ICON_GAME} Giải Trí & Cờ Bạc",
                            value="`slots` `coinflip` `dice`",
                            inline=False)
            embed.add_field(name=f"{ICON_SHOP} Cửa Hàng Vật Phẩm",
                            value="`shop` `buy` `sell`", # Buy, Sell đã được thêm số lượng mặc định
                            inline=False)
            embed.add_field(name=f"{ICON_ADMIN} Quản Trị Server (Lệnh Prefix)",
                            value=f"`{prefix}addmoney` `{prefix}removemoney` `{prefix}auto` `{prefix}mutebot` `{prefix}unmutebot`",
                            inline=False)
            
            embed.set_footer(text=f"Bot được phát triển bởi MinhBeo8. Gõ /help lệnh <tên_lệnh> để biết thêm chi tiết.")
            
            print(f"{ICON_INFO} [DEBUG] General help embed created. Attempting to send followup...")
            await interaction.followup.send(embed=embed, ephemeral=True)
            print(f"{ICON_INFO} [DEBUG] General help followup sent successfully.")

        except Exception as e:
            print(f"{ICON_ERROR} [DEBUG] Error in _send_general_help_embed:")
            traceback.print_exc()
            try:
                if not interaction.is_expired():
                    await interaction.followup.send(content=f"{ICON_ERROR} Rất tiếc, đã có lỗi khi hiển thị menu trợ giúp chung.", ephemeral=True)
            except Exception as followup_e:
                print(f"{ICON_ERROR} [DEBUG] Failed to send error followup message for general help: {followup_e}")

    @nextcord.slash_command(name="help", description=f"{ICON_INFO} Hiển thị thông tin trợ giúp cho các lệnh của bot.")
    async def help_slash_command(self,
                                 interaction: nextcord.Interaction,
                                 command_name: str = nextcord.SlashOption(
                                     name="lệnh", 
                                     description="Tên lệnh prefix bạn muốn xem chi tiết.",
                                     required=False,
                                     default=None
                                 )):
        print(f"{ICON_INFO} [DEBUG] /help (V2) invoked by {interaction.user.name}. Arg: '{command_name}'")
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
                print(f"{ICON_INFO} [DEBUG] Interaction deferred for /help (V2).")
            else:
                print(f"{ICON_INFO} [DEBUG] Interaction already deferred/responded for /help (V2).")
            
            if not command_name:
                print(f"{ICON_INFO} [DEBUG] Calling _send_general_help_embed...")
                await self._send_general_help_embed(interaction)
            else:
                # Phần xử lý chi tiết lệnh sẽ được thêm lại ở bước sau
                print(f"{ICON_INFO} [DEBUG] Specific command help for '{command_name}' requested (currently disabled in V2). Sending placeholder...")
                await interaction.followup.send(content=f"{ICON_INFO} Chức năng xem chi tiết lệnh `{command_name}` sẽ được cập nhật sau. Hiện tại chỉ có menu chung.", ephemeral=True)
                print(f"{ICON_INFO} [DEBUG] Placeholder for specific command help sent.")

        except Exception as e:
            print(f"{ICON_ERROR} [DEBUG] CRITICAL Error in help_slash_command (V2):")
            traceback.print_exc()
            try:
                if not interaction.is_expired(): # Kiểm tra xem interaction có còn hợp lệ để gửi followup không
                    # Chỉ gửi followup nếu chưa có phản hồi nào được gửi hoặc defer chưa được is_done
                    # Tuy nhiên, nếu đã defer, is_done() sẽ là True.
                    # Cách an toàn là kiểm tra is_expired()
                    await interaction.followup.send(content=f"{ICON_ERROR} Đã có lỗi nghiêm trọng khi xử lý yêu cầu `/help` của bạn.", ephemeral=True)
            except Exception as final_followup_e:
                print(f"{ICON_ERROR} [DEBUG] Failed to send final CRITICAL error followup for /help (V2): {final_followup_e}")

def setup(bot: commands.Bot):
    bot.add_cog(HelpSlashCommandCog(bot))
