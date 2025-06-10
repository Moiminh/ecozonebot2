# bot/cogs/economy/launder_cmd.py
import nextcord
from nextcord.ext import commands
import random
import logging
from datetime import datetime
from core.utils import try_send, require_travel_check
from core.config import BOT_NAME, COMMAND_PREFIX, FOOTER_TEXT, LAUNDER_FEE, LAUNDER_EXCHANGE_RATE
from core.icons import ICON_ERROR, ICON_SUCCESS, ICON_WARNING, ICON_BANK_MAIN, ICON_ECOBIT, ICON_ECOIN, ICON_INFO

logger = logging.getLogger(__name__)

class LaunderCommandCog(commands.Cog, name="Launder Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("LaunderCommandCog (SQLite Ready) initialized.")

    @commands.command(name="launder")
    @commands.guild_only()
    @require_travel_check
    async def launder(self, ctx: commands.Context, amount: int):
        author_id = ctx.author.id
        guild_id = ctx.guild.id

        if amount <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Số tiền cần rửa phải lớn hơn 0.")
            return
            
        try:
            global_profile = self.bot.db.get_or_create_global_user_profile(author_id)
            local_data = self.bot.db.get_or_create_user_local_data(author_id, guild_id)
            
            if local_data['local_balance_adadd'] < amount:
                await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ {amount:,} 🧪Ecobit để thực hiện.")
                return

            wanted_level = global_profile['wanted_level']
            catch_chance = min(0.9, BASE_CATCH_CHANCE + wanted_level * WANTED_LEVEL_CATCH_MULTIPLIER)
            self.bot.db.set_cooldown(author_id, "launder", datetime.now().timestamp())

            if random.random() < catch_chance:
                fine_amount = min(local_data['local_balance_earned'], int(amount * 0.1))
                self.bot.db.update_balance(author_id, guild_id, 'local_balance_adadd', 0)
                self.bot.db.update_balance(author_id, guild_id, 'local_balance_earned', local_data['local_balance_earned'] - fine_amount)
                self.bot.db.update_wanted_level(author_id, wanted_level + 1.0)
                await try_send(ctx, content=f"🚨 **BỊ BẮT!** Toàn bộ {local_data['local_balance_adadd']:,} {ICON_ECOBIT} của bạn đã bị tịch thu và bạn bị phạt thêm **{fine_amount:,}** {ICON_ECOIN}.")
            else:
                bank_gained = amount // LAUNDER_EXCHANGE_RATE
                self.bot.db.update_balance(author_id, guild_id, 'local_balance_adadd', local_data['local_balance_adadd'] - amount)
                self.bot.db.update_balance(author_id, None, 'bank_balance', global_profile['bank_balance'] + bank_gained)
                self.bot.db.update_wanted_level(author_id, max(0.0, wanted_level - 0.25))
                await try_send(ctx, content=f"{ICON_SUCCESS} Giao dịch mờ ám thành công! Bạn đã chi **{amount:,}** {ICON_ECOBIT} và nhận lại được **{bank_gained:,}** {ICON_BANK_MAIN}.")

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'launder': {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Giao dịch gặp trục trặc không mong muốn.")

def setup(bot: commands.Bot):
    bot.add_cog(LaunderCommandCog(bot))
