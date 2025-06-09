# bot/cogs/earn/daily_cmd.py
import nextcord
from nextcord.ext import commands
import random
from datetime import datetime
import logging
from core.utils import try_send
from core.config import DAILY_COOLDOWN
from core.leveling import check_and_process_levelup
from core.icons import ICON_LOADING, ICON_GIFT, ICON_MONEY_BAG, ICON_ERROR, ICON_TIEN_SACH

logger = logging.getLogger(__name__)

class DailyCommandCog(commands.Cog, name="Daily Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("DailyCommandCog (SQLite Ready) initialized.")

    @commands.command(name='daily', aliases=['d'])
    @commands.guild_only()
    async def daily(self, ctx: commands.Context):
        author_id = ctx.author.id
        guild_id = ctx.guild.id
        
        try:
            now = datetime.now().timestamp()
            last_daily = self.bot.db.get_cooldown(author_id, 'daily')
            
            if now - last_daily < DAILY_COOLDOWN:
                time_left = str(datetime.fromtimestamp(last_daily + DAILY_COOLDOWN) - datetime.now()).split('.')[0]
                await try_send(ctx, content=f"{ICON_LOADING} Bạn đã nhận thưởng ngày hôm nay rồi! Chờ: **{time_left}**.")
                return
            
            local_data = self.bot.db.get_or_create_user_local_data(author_id, guild_id)
            
            bonus = random.randint(500, 1500)
            xp_earned_local = random.randint(15, 50)
            xp_earned_global = random.randint(25, 75)

            # Cập nhật dữ liệu
            self.bot.db.update_balance(author_id, guild_id, 'local_balance_earned', local_data['local_balance_earned'] + bonus)
            self.bot.db.update_xp(author_id, guild_id, xp_earned_local, xp_earned_global)
            self.bot.db.set_cooldown(author_id, 'daily', now)
            
            new_earned_balance = local_data['local_balance_earned'] + bonus
            total_local_balance = new_earned_balance + local_data['local_balance_adadd']
            
            await try_send(
                ctx, 
                content=(
                    f"{ICON_GIFT} {ctx.author.mention}, bạn đã nhận phần thưởng hàng ngày:\n"
                    f"  {ICON_TIEN_SACH} **{bonus:,}** Tiền Sạch\n"
                    f"  ✨ **{xp_earned_local}** XP (Server) & **{xp_earned_global}** XP (Global)\n"
                    f"Tổng Ví Local của bạn giờ là: **{total_local_balance:,}** {ICON_MONEY_BAG}"
                )
            )

            # Cập nhật lại dữ liệu mới nhất để kiểm tra level up
            global_profile = self.bot.db.get_or_create_global_user_profile(author_id)
            local_data = self.bot.db.get_or_create_user_local_data(author_id, guild_id)
            await check_and_process_levelup(ctx, dict(local_data), 'local')
            await check_and_process_levelup(ctx, dict(global_profile), 'global')

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'daily' cho user {author_id}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi khi bạn nhận thưởng hàng ngày.")

def setup(bot: commands.Bot):
    bot.add_cog(DailyCommandCog(bot))
