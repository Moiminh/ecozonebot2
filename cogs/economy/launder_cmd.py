# bot/cogs/economy/launder_cmd.py
import nextcord
from nextcord.ext import commands
import random
import logging
from datetime import datetime

from core.database import get_or_create_global_user_profile, get_or_create_user_local_data
from core.utils import try_send, require_travel_check
from core.config import LAUNDER_EXCHANGE_RATE, BASE_CATCH_CHANCE, WANTED_LEVEL_CATCH_MULTIPLIER
from core.icons import ICON_ERROR, ICON_SUCCESS, ICON_WARNING, ICON_BANK_MAIN, ICON_ECOBIT, ICON_ECOIN

logger = logging.getLogger(__name__)

class LaunderCommandCog(commands.Cog, name="Launder Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("LaunderCommandCog (v3 - Refactored) initialized.")

    @commands.command(name="launder")
    @commands.guild_only()
    @require_travel_check
    async def launder(self, ctx: commands.Context, amount: int):
        """(Game ẩn) Thử "rửa" 🧪Ecobit thành tiền Bank với rủi ro bị bắt."""
        author_id = ctx.author.id

        if amount <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Số tiền cần rửa phải lớn hơn 0.")
            return
            
        try:
            economy_data = self.bot.economy_data
            global_profile = get_or_create_global_user_profile(economy_data, author_id)
            local_data = get_or_create_user_local_data(global_profile, ctx.guild.id)
            adadd_balance = local_data["local_balance"]["adadd"]
            if adadd_balance < amount:
                await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ {amount:,} 🧪Ecobit để thực hiện.")
                return

            # --- Logic Rủi ro ---
            wanted_level = global_profile.get("wanted_level", 0.0)
            catch_chance = min(0.9, BASE_CATCH_CHANCE + wanted_level * WANTED_LEVEL_CATCH_MULTIPLIER) # Giới hạn 90%

            # Đặt cooldown ngay lập tức
            global_profile.setdefault("cooldowns", {})["launder"] = datetime.now().timestamp()

            if random.random() < catch_chance:
                # BỊ BẮT
                earned_balance = local_data["local_balance"]["earned"]
                fine_amount = min(earned_balance, int(amount * 0.1)) # Phạt 10% số tiền rửa vào tiền sạch
                
                local_data["local_balance"]["adadd"] = 0  # Tịch thu toàn bộ tiền lậu
                local_data["local_balance"]["earned"] -= fine_amount
                global_profile["wanted_level"] += 1.0 # Tăng mạnh điểm truy nã

                logger.warning(f"LAUNDER FAILED: User {author_id} bị bắt khi rửa {amount} Ecobit. Mất hết Ecobit, phạt {fine_amount} Ecoin.")
                await try_send(ctx, content=f"🚨 **BỊ BẮT!** Nỗ lực rửa tiền của bạn đã bị cảnh sát phát hiện!\n- **Toàn bộ {adadd_balance:,}** {ICON_ECOBIT} của bạn đã bị tịch thu.\n- Bạn bị phạt thêm **{fine_amount:,}** {ICON_ECOIN}.\n- Mức độ truy nã của bạn đã tăng lên!")
            
            else:
                # THÀNH CÔNG
                bank_gained = amount // LAUNDER_EXCHANGE_RATE
                
                local_data["local_balance"]["adadd"] -= amount
                global_profile["bank_balance"] += bank_gained
                global_profile["wanted_level"] += 0.5 # Vẫn tăng điểm truy nã nhẹ

                logger.info(f"LAUNDER SUCCESS: User {author_id} đã rửa {amount} Ecobit thành {bank_gained} bank.")
                await try_send(ctx, content=f"{ICON_SUCCESS} Giao dịch mờ ám thành công!\n- Bạn đã chi **{amount:,}** {ICON_ECOBIT}.\n- Bạn nhận lại được **{bank_gained:,}** {ICON_BANK_MAIN} trong Bank.\n- {ICON_WARNING} Mức độ truy nã của bạn đã tăng nhẹ.")

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'launder': {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Giao dịch gặp trục trặc không mong muốn.")

def setup(bot: commands.Bot):
    bot.add_cog(LaunderCommandCog(bot))
