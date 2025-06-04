# bot/cogs/test_slash_cog.py
import nextcord
from nextcord.ext import commands
import traceback
import time # Để đo thời gian
from core.icons import ICON_INFO, ICON_ERROR, ICON_PING # Import ICON_PING mới

class PingCommandCog(commands.Cog, name="Ping Command"): # Đổi tên class Cog
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"{ICON_INFO} [PING COG] PingCommandCog initialized.")

    @nextcord.slash_command(name="ping", description="Kiểm tra độ trễ của bot tới Discord.")
    async def ping(self, interaction: nextcord.Interaction): # Đổi tên hàm cho khớp lệnh
        print(f"{ICON_INFO} [PING COG] /{interaction.application_command.name} invoked by {interaction.user.name}")
        try:
            
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=False) 
            print(f"{ICON_INFO} [PING COG] /{interaction.application_command.name} deferred.")

            # Ghi lại thời điểm bắt đầu gửi tin nhắn đầu tiên (sau khi defer)
            start_time = time.monotonic() # Dùng monotonic cho khoảng thời gian chính xác hơn


            await interaction.followup.send(content=f"{ICON_PING} Pong! Đang đo độ trễ...")
            
            # Ghi lại thời điểm sau khi tin nhắn tạm thời đã được gửi
            end_time = time.monotonic()

            # Tính toán độ trễ phản hồi (round-trip cho việc gửi tin nhắn followup)
            round_trip_latency = round((end_time - start_time) * 1000) # Chuyển sang miligiây

            # Lấy độ trễ WebSocket (API Latency)
            websocket_latency = round(self.bot.latency * 1000) # Chuyển sang miligiây

            # Tạo Embed để hiển thị kết quả giống ảnh
            embed = nextcord.Embed(
                title=f"{ICON_PING} Pong!",
                color=nextcord.Color.green() # Bạn có thể chọn màu khác
            )
            embed.add_field(name="Độ trễ phản hồi", value=f"`{round_trip_latency}ms`", inline=False)
            embed.add_field(name="Độ trễ API (WebSocket)", value=f"`{websocket_latency}ms`", inline=False)
            
            # Chỉnh sửa tin nhắn gốc đã gửi (tin nhắn "Đang đo độ trễ...")
            await interaction.edit_original_message(content=None, embed=embed) # Bỏ content cũ, thay bằng embed
            
            print(f"{ICON_INFO} [PING COG] /{interaction.application_command.name} response edited. Roundtrip: {round_trip_latency}ms, WS: {websocket_latency}ms")

        except Exception as e:
            error_message_for_user = f"{ICON_ERROR} Rất tiếc, đã có lỗi xảy ra khi thực hiện lệnh ping."
            print(f"{ICON_ERROR} [PING COG] Error in /{interaction.application_command.name}:")
            traceback.print_exc()
            try:
                # Cố gắng chỉnh sửa tin nhắn gốc với thông báo lỗi
                if not interaction.is_expired():
                     await interaction.edit_original_message(content=error_message_for_user, embed=None, view=None) # Xóa embed/view nếu có
            except Exception as followup_exception:
                # Nếu edit cũng lỗi, thử gửi followup mới (ít khả năng hơn)
                print(f"{ICON_ERROR} [PING COG] Failed to edit original message with error. Attempting new followup: {followup_exception}")
                try:
                    if not interaction.is_expired():
                        await interaction.followup.send(content=error_message_for_user, ephemeral=True)
                except Exception as final_error:
                    print(f"{ICON_ERROR} [PING COG] Failed to send any error followup: {final_error}")


def setup(bot: commands.Bot):
    bot.add_cog(PingCommandCog(bot)) # Đảm bảo tên class Cog khớp
