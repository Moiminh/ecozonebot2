# bot/cogs/economy/launder_cmd.py
import nextcord
from nextcord.ext import commands
import random
import logging

from core.database import (
    load_economy_data,
    save_economy_data,
    get_or_create_global_user_profile,
    get_or_create_user_local_data
)
from core.utils import try_send
from core.icons import ICON_ERROR, ICON_SUCCESS, ICON_WARNING, ICON_BANK, ICON_TIEN_LAU, ICON_TIEN_SACH

logger = logging.getLogger(__name__)

# Các hằng số cho việc rửa tiền, có thể chuyển vào config.py sau
LAUNDER_EXCHANGE_RATE = 100_000_000  # 100 triệu adadd = 1 bank
BASE_CATCH_CHANCE = 0.05  # 5% cơ hội bị bắt cơ bản
WANTED_LEVEL_CATCH_MULTIPLIER = 0.05 # Mỗi điểm wanted_level tăng 5% cơ hội bị bắt

class LaunderCommandCog(commands.Cog, name="Launder Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("LaunderCommandCog (v3) initialized.")

    @commands.command(name="launder")
    async def launder(self, ctx: commands.Context, amount: int):
        """(Game ẩn) Thử "rửa" Tiền Lậu (adadd) thành tiền Bank với rủi ro cao."""
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server.")
            return

        author_id = ctx.author.id
        guild_id = ctx.guild.id

        if amount <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Số tiền rửa phải lớn hơn 0.")
            return
            
        try:
            economy_data = load_economy_data()
            global_profile = get_or_create_global_user_profile(economy_data, author_id)
            local_data = get_or_create_user_local_data(global_profile, guild_id)

            adadd_balance = local_data["local_balance"]["adadd"]
            if adadd_balance < amount:
                await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ {amount:,} Tiền Lậu để thực hiện.")
                return

            # --- Logic Rủi ro ---
            wanted_level = global_profile.get("wanted_level", 0.0)
            catch_chance = min(0.9, BASE_CATCH_CHANCE + wanted_level * WANTED_LEVEL_CATCH_MULTIPLIER) # Giới hạn 90%

            if random.random() < catch_chance:
                # BỊ BẮT
                earned_balance = local_data["local_balance"]["earned"]
                fine_amount = min(earned_balance, int(amount * 0.1)) # Phạt 10% số tiền rửa, nhưng không quá số tiền sạch đang có
                
                local_data["local_balance"]["adadd"] = 0  # Tịch thu toàn bộ tiền lậu
                local_data["local_balance"]["earned"] -= fine_amount
                global_profile["wanted_level"] += 1.0 # Tăng mạnh điểm truy nã

                save_economy_data(economy_data)
                logger.warning(f"LAUNDER FAILED: User {author_id} bị bắt khi rửa {amount} adadd. Mất hết adadd, phạt {fine_amount} earned.")
                await try_send(ctx, content=f"🚨 **BỊ BẮT!** Nỗ lực rửa tiền của bạn đã bị cảnh sát phát hiện!\n- **Toàn bộ {adadd_balance:,}** {ICON_TIEN_LAU} của bạn đã bị tịch thu.\n- Bạn bị phạt thêm **{fine_amount:,}** {ICON_TIEN_SACH}.\n- Mức độ truy nã của bạn đã tăng lên!")
            
            else:
                # THÀNH CÔNG
                bank_gained = amount // LAUNDER_EXCHANGE_RATE
                
                local_data["local_balance"]["adadd"] -= amount
                global_profile["bank_balance"] += bank_gained
                global_profile["wanted_level"] += 0.5 # Vẫn tăng điểm truy nã nhẹ

                save_economy_data(economy_data)
                logger.info(f"LAUNDER SUCCESS: User {author_id} đã rửa {amount} adadd thành {bank_gained} bank.")
                await try_send(ctx, content=f"{ICON_SUCCESS} Giao dịch mờ ám thành công!\n- Bạn đã chi **{amount:,}** {ICON_TIEN_LAU}.\n- Bạn nhận lại được **{bank_gained:,}** {ICON_BANK} trong Bank.\n- {ICON_WARNING} Mức độ truy nã của bạn đã tăng nhẹ.")

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'launder': {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Giao dịch gặp trục trặc không mong muốn.")

def setup(bot: commands.Bot):
    bot.add_cog(LaunderCommandCog(bot))
