# bot/cogs/ai/assistant_cog.py
import nextcord
from nextcord.ext import commands
import logging
import os
import json
# Giả định thư viện AI đã được cài đặt trong môi trường
# import google.generativeai as genai

logger = logging.getLogger(__name__)

# --- Cấu hình AI (sẽ chỉ chạy nếu AI được kích hoạt) ---
# try:
#     if os.getenv("GEMINI_API_KEY"):
#         genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
# except Exception as e:
#     logger.error(f"Lỗi khi cấu hình Gemini AI: {e}")

class AssistantCog(commands.Cog, name="AI Assistant"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # self.model = genai.GenerativeModel('gemini-pro') # Khởi tạo model
        logger.info("AI Assistant Cog initialized.")

    @nextcord.slash_command(name="yeucau", description="Gửi một yêu cầu bằng ngôn ngữ tự nhiên cho Trợ lý AI.")
    async def request_ai(
        self,
        interaction: nextcord.Interaction,
        prompt: str = nextcord.SlashOption(
            name="prompt",
            description="Nhập yêu cầu của bạn (ví dụ: 'tôi muốn mua 2 bánh mì' hoặc 'số dư của tôi là bao nhiêu?')",
            required=True
        )
    ):
        await interaction.response.defer(ephemeral=True)
        
        # --- Prompt Engineering: "Dạy" cho AI vai trò của nó ---
        system_prompt = f"""
            Bạn là một trợ lý trong game Discord có tên EconZone.
            Nhiệm vụ của bạn là phân tích yêu cầu của người dùng và chuyển nó thành một lệnh dạng JSON.
            Các lệnh hợp lệ là: 'buy', 'sell', 'balance', 'info', 'inventory'.
            Các tham số có thể có: 'item_id', 'quantity', 'user'.

            Ví dụ:
            - User: "tôi muốn mua 2 bánh mì" -> {{"command": "buy", "args": {{"item_id": "banh_mi", "quantity": 2}}}}
            - User: "xem túi đồ của tôi" -> {{"command": "inventory", "args": {{}}}}
            - User: "số dư của @user#1234" -> {{"command": "balance", "args": {{"user": "@user#1234"}}}}

            Nếu không thể xác định lệnh, trả về: {{"command": "unknown", "args": {{}}}}

            Yêu cầu của người dùng hiện tại là: "{prompt}"
        """
        
        try:
            # --- Gửi yêu cầu đến Gemini API ---
            # response = self.model.generate_content(system_prompt)
            # response_json = json.loads(response.text.strip())
            
            # GIẢ LẬP PHẢN HỒI TỪ AI ĐỂ TEST
            # (Phần code thật sẽ gọi API ở đây)
            mock_response_text = '{"command": "buy", "args": {"item_id": "banh_mi", "quantity": 2}}'
            response_json = json.loads(mock_response_text)

            # --- Xử lý phản hồi từ AI ---
            # (Phần logic này cần được xây dựng để gọi các hàm tương ứng)
            parsed_command = response_json.get("command")
            parsed_args = response_json.get("args")
            
            await interaction.followup.send(f"AI đã hiểu yêu cầu của bạn là:\nLệnh: `{parsed_command}`\nTham số: `{parsed_args}`\n(Logic thực thi sẽ được xây dựng ở đây)", ephemeral=True)

        except Exception as e:
            logger.error(f"Lỗi khi xử lý yêu cầu AI: {e}", exc_info=True)
            await interaction.followup.send("Rất tiếc, Trợ lý AI đang gặp sự cố. Vui lòng thử lại sau.", ephemeral=True)

def setup(bot: commands.Bot):
    # Cog này chỉ nên được load nếu AI_ENABLED là True
    # Logic kiểm tra sẽ nằm ở file tải cog (ví dụ: main.py hoặc core/bot.py)
    bot.add_cog(AssistantCog(bot))
