# bot/cogs/economy/balance_cmd.py
import nextcord
from nextcord.ext import commands
import logging

from core.database import (
    load_economy_data,
    save_economy_data,
    get_or_create_global_user_profile,
    get_or_create_user_local_data
)
from core.utils import try_send
from core.icons import (
    ICON_PROFILE, ICON_ERROR, ICON_MONEY_BAG,
    ICON_TIEN_SACH, ICON_TIEN_LAU, ICON_BANK, ICON_TICKET
)

# Lấy logger cho module này
logger = logging.getLogger(__name__)

class BalanceCommandCog(commands.Cog, name="Balance Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info(f"BalanceCommandCog (v2) initialized.")

    @commands.command(name='balance', aliases=['bal', 'cash', 'money', '$'])
    async def balance(self, ctx: commands.Context, user: nextcord.Member = None):
        """Hiển thị chi tiết tài sản của bạn hoặc một người dùng khác."""
        target_user = user or ctx.author
        
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Vui lòng sử dụng lệnh này trong một server để xem đầy đủ các loại tài sản.")
            return

        author_id = target_user.id
        guild_id = ctx.guild.id

        logger.debug(f"Lệnh 'balance' (v2) được gọi cho {target_user.name} ({author_id}) tại guild '{ctx.guild.name}' ({guild_id}).")

        try:
            # Tải dữ liệu
            economy_data = load_economy_data()
            
            # Lấy/tạo profile toàn cục và local bằng các hàm mới
            global_profile = get_or_create_global_user_profile(economy_data, author_id)
            local_data = get_or_create_user_local_data(global_profile, guild_id)

            # Lưu lại dữ liệu (quan trọng, vì các hàm get_or_create có thể đã thay đổi cấu trúc)
            save_economy_data(economy_data)

            # Trích xuất các loại số dư từ cấu trúc dữ liệu mới
            bank_balance = global_profile.get("bank_balance", 0)
            
            local_balance_dict = local_data.get("local_balance", {})
            earned_balance = local_balance_dict.get("earned", 0)
            adadd_balance = local_balance_dict.get("adadd", 0)
            total_local_balance = earned_balance + adadd_balance
            
            tickets = local_data.get("tickets", [])
            ticket_count = len(tickets)

            # Tạo embed để hiển thị
            embed = nextcord.Embed(
                title=f"{ICON_PROFILE} Tổng Quan Tài Sản của {target_user.display_name}",
                color=nextcord.Color.gold()
            )
            embed.set_thumbnail(url=target_user.display_avatar.url)
            
            # Field cho Ví Local
            embed.add_field(
                name=f"{ICON_MONEY_BAG} Ví Local (tại Server: {ctx.guild.name})",
                value=f"**Tổng cộng:** `{total_local_balance:,}`\n"
                      f"  {ICON_TIEN_SACH} Tiền Sạch (Earned): `{earned_balance:,}`\n"
                      f"  {ICON_TIEN_LAU} Tiền Lậu (Admin-add): `{adadd_balance:,}`",
                inline=False
            )
            
            # Field cho Bank (Global)
            embed.add_field(
                name=f"{ICON_BANK} Ví Global (Bank)",
                value=f"`{bank_balance:,}`",
                inline=True
            )

            # Field cho Ticket
            embed.add_field(
                name=f"{ICON_TICKET} Ticket Sự kiện",
                value=f"`{ticket_count}`",
                inline=True
            )

            await try_send(ctx, embed=embed)

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'balance' (v2) cho user {target_user.name}: {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã xảy ra lỗi không xác định khi xem số dư của {target_user.mention}.")

def setup(bot: commands.Bot):
    bot.add_cog(BalanceCommandCog(bot))
