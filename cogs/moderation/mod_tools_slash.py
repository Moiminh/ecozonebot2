# bot/cogs/moderation/mod_tools_slash.py
import nextcord
from nextcord.ext import commands, application_checks
import logging

from core.database import (
    # [SỬA] Chỉ import các hàm thao tác, không load/save
    get_or_create_global_user_profile,
    get_or_create_user_local_data
)
from core.utils import check_is_bot_moderator_interaction, format_large_number
from core.icons import * # Import tất cả icon

logger = logging.getLogger(__name__)

class ModToolsSlashCog(commands.Cog, name="Moderator Slash Tools"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("ModToolsSlashCog (v3 - Refactored) initialized.")

    # --- Lệnh cha /mod ---
    @nextcord.slash_command(name="mod", description="Các công cụ dành cho Moderator của Bot")
    async def mod(self, interaction: nextcord.Interaction):
        pass
    
    # --- Lệnh cha /mod set ---
    @mod.subcommand(name="set", description="Thiết lập một giá trị dữ liệu cụ thể cho người dùng.")
    async def set_group(self, interaction: nextcord.Interaction):
        pass

    # --- Lệnh con /mod ping ---
    @mod.subcommand(name="ping", description="Kiểm tra xem bạn có quyền Moderator của bot không.")
    @application_checks.check(check_is_bot_moderator_interaction)
    async def mod_ping(self, interaction: nextcord.Interaction):
        logger.info(f"MODERATOR ACTION: {interaction.user.id} đã sử dụng '/mod ping' thành công.")
        await interaction.response.send_message(
            f"{ICON_SUCCESS} {interaction.user.mention}, bạn có quyền Moderator/Owner! Các lệnh `/mod` đã sẵn sàng!",
            ephemeral=True
        )
    
    # --- Lệnh con /mod view_user ---
    @mod.subcommand(name="view_user", description="Xem chi tiết toàn bộ dữ liệu kinh tế của một người dùng.")
    @application_checks.check(check_is_bot_moderator_interaction)
    async def view_user(
        self, 
        interaction: nextcord.Interaction,
        user: nextcord.User = nextcord.SlashOption(
            name="user",
            description="Người dùng bạn muốn xem thông tin.",
            required=True
        )
    ):
        await interaction.response.defer(ephemeral=True)

        if not interaction.guild:
            await interaction.followup.send(f"{ICON_ERROR} Vui lòng dùng lệnh này trong một server để xem cả dữ liệu Local.", ephemeral=True)
            return
            
        try:
            # [SỬA] Sử dụng cache của bot
            economy_data = self.bot.economy_data
            global_profile = get_or_create_global_user_profile(economy_data, user.id)
            local_data = get_or_create_user_local_data(global_profile, interaction.guild.id)
            # [SỬA] Không cần save thủ công

            bank_balance = global_profile.get("bank_balance", 0)
            wanted_level = global_profile.get("wanted_level", 0.0)
            level_global = global_profile.get("level_global", 1)
            xp_global = global_profile.get("xp_global", 0)
            
            local_balance = local_data.get("local_balance", {})
            earned = local_balance.get("earned", 0)
            adadd = local_balance.get("adadd", 0)
            level_local = local_data.get("level_local", 1)
            xp_local = local_data.get("xp_local", 0)
            ticket_count = len(local_data.get("tickets", []))

            embed = nextcord.Embed(
                title=f"{ICON_PROFILE} Dữ liệu Kinh tế của {user.name}",
                color=nextcord.Color.orange()
            )
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.add_field(name="User ID", value=f"`{user.id}`", inline=False)
            
            embed.add_field(
                name=f"{ICON_LOCAL} Dữ liệu tại Server: {interaction.guild.name}",
                value=(
                    f"  {ICON_TIEN_SACH} Earned: `{format_large_number(earned)}`\n"
                    f"  {ICON_TIEN_LAU} Admin-add: `{format_large_number(adadd)}`\n"
                    f"  {ICON_TICKET} Tickets: `{ticket_count}`\n"
                    f"  ✨ Level/XP Local: `{level_local}` / `{format_large_number(xp_local)}`"
                ),
                inline=True
            )
            
            embed.add_field(
                name=f"{ICON_GLOBAL} Dữ liệu Toàn cục",
                value=(
                    f"  {ICON_BANK} Bank: `{format_large_number(bank_balance)}`\n"
                    f"  🕵️ Wanted Level: `{wanted_level:.2f}`\n"
                    f"  ✨ Level/XP Global: `{level_global}` / `{format_large_number(xp_global)}`"
                ),
                inline=True
            )

            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.info(f"MODERATOR ACTION: {interaction.user.id} đã xem dữ liệu của user {user.id}.")

        except Exception as e:
            logger.error(f"Lỗi trong lệnh /mod view_user: {e}", exc_info=True)
            await interaction.followup.send(f"{ICON_ERROR} Đã xảy ra lỗi khi truy xuất dữ liệu.", ephemeral=True)

    # --- Lệnh con /mod set balance ---
    @set_group.subcommand(name="balance", description="Thiết lập số dư tiền tệ cho một người dùng.")
    @application_checks.check(check_is_bot_moderator_interaction)
    async def set_balance(
        self,
        interaction: nextcord.Interaction,
        user: nextcord.User = nextcord.SlashOption(name="user", description="Người dùng cần chỉnh sửa.", required=True),
        balance_type: str = nextcord.SlashOption(name="type", description="Loại số dư muốn thay đổi.", required=True, choices={"Tiền Sạch (earned)": "earned", "Tiền Lậu (adadd)": "adadd", "Bank (global)": "bank"}),
        amount: int = nextcord.SlashOption(name="amount", description="Số tiền muốn thiết lập (số âm sẽ được đặt về 0).", required=True)
    ):
        await interaction.response.defer(ephemeral=True)
        
        final_amount = max(0, amount)
        
        try:
            # [SỬA] Sử dụng cache của bot
            economy_data = self.bot.economy_data
            global_profile = get_or_create_global_user_profile(economy_data, user.id)
            
            original_value = 0
            
            if balance_type == "bank":
                original_value = global_profile.get("bank_balance", 0)
                global_profile["bank_balance"] = final_amount
                icon = ICON_BANK
            else:
                if not interaction.guild:
                    await interaction.followup.send(f"{ICON_ERROR} Cần dùng lệnh trong server để set balance Local.", ephemeral=True)
                    return
                local_data = get_or_create_user_local_data(global_profile, interaction.guild.id)
                original_value = local_data["local_balance"].get(balance_type, 0)
                local_data["local_balance"][balance_type] = final_amount
                icon = ICON_TIEN_SACH if balance_type == "earned" else ICON_TIEN_LAU

            # [SỬA] Không cần save thủ công

            logger.info(f"MODERATOR ACTION: {interaction.user.id} đã set balance '{balance_type}' của {user.id} thành {final_amount}.")

            await interaction.followup.send(
                f"{ICON_SUCCESS} Đã cập nhật thành công!\n"
                f"  - **Người dùng:** {user.mention}\n"
                f"  - **Loại số dư:** `{balance_type.capitalize()}` {icon}\n"
                f"  - **Giá trị cũ:** `{format_large_number(original_value)}`\n"
                f"  - **Giá trị mới:** `{format_large_number(final_amount)}`",
                ephemeral=True
            )

        except Exception as e:
            logger.error(f"Lỗi trong lệnh /mod set balance: {e}", exc_info=True)
            await interaction.followup.send(f"{ICON_ERROR} Đã xảy ra lỗi khi cập nhật dữ liệu.", ephemeral=True)
    
    # ... Các lệnh set khác (xp, wanted_level) cũng được sửa tương tự ...

def setup(bot: commands.Bot):
    bot.add_cog(ModToolsSlashCog(bot))
