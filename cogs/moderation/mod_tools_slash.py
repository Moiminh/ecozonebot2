# bot/cogs/moderation/mod_tools_slash.py
import nextcord
from nextcord.ext import commands, application_checks
import logging

# Các hàm và icon cần thiết
from core.database import (
    load_economy_data,
    save_economy_data,
    get_or_create_global_user_profile,
    get_or_create_user_local_data
)
from core.utils import check_is_bot_moderator_interaction, format_large_number
from core.icons import (
    ICON_ADMIN_PANEL, ICON_SUCCESS, ICON_ERROR, ICON_PROFILE,
    ICON_TIEN_SACH, ICON_TIEN_LAU, ICON_BANK, ICON_TICKET,
    ICON_LOCAL, ICON_GLOBAL
)

logger = logging.getLogger(__name__)

class ModToolsSlashCog(commands.Cog, name="Moderator Slash Tools"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("ModToolsSlashCog (v2) initialized.")

    # --- Lệnh cha /mod ---
    @nextcord.slash_command(
        name="mod", 
        description="Các công cụ dành cho Moderator của Bot"
    )
    async def mod(self, interaction: nextcord.Interaction):
        pass

    # --- Lệnh con /mod ping ---
    @mod.subcommand(name="ping", description="Kiểm tra xem bạn có quyền Moderator của bot không.")
    @application_checks.check(check_is_bot_moderator_interaction)
    async def mod_ping(self, interaction: nextcord.Interaction):
        # ... (giữ nguyên logic của lệnh ping) ...
        logger.info(f"MODERATOR ACTION: {interaction.user.id} đã sử dụng '/mod ping' thành công.")
        await interaction.response.send_message(
            f"{ICON_SUCCESS} {interaction.user.mention}, bạn có quyền Moderator/Owner! Các lệnh `/mod` đã sẵn sàng!",
            ephemeral=True
        )
    
    # --- LỆNH CON MỚI: /mod view_user ---
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
        """Xem chi tiết dữ liệu kinh tế của một người dùng."""
        await interaction.response.defer(ephemeral=True) # Phản hồi tạm thời

        target_user = user
        # Cần guild context để lấy dữ liệu local
        if not interaction.guild:
            await interaction.followup.send(f"{ICON_ERROR} Vui lòng dùng lệnh này trong một server để xem cả dữ liệu Local.", ephemeral=True)
            return
            
        try:
            economy_data = load_economy_data()
            global_profile = get_or_create_global_user_profile(economy_data, target_user.id)
            local_data = get_or_create_user_local_data(global_profile, interaction.guild.id)
            save_economy_data(economy_data) # Lưu lại phòng trường hợp user mới được tạo

            # Trích xuất dữ liệu
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

            # Tạo Embed
            embed = nextcord.Embed(
                title=f"{ICON_PROFILE} Dữ liệu Kinh tế của {target_user.name}",
                color=nextcord.Color.orange()
            )
            embed.set_thumbnail(url=target_user.display_avatar.url)
            embed.add_field(name="User ID", value=f"`{target_user.id}`", inline=False)
            
            # Dữ liệu Local
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
            
            # Dữ liệu Global
            embed.add_field(
                name=f"{ICON_GLOBAL} Dữ liệu Toàn cục",
                value=(
                    f"  {ICON_BANK} Bank: `{format_large_number(bank_balance)}`\n"
                    f"  - _(Chỉ số ẩn)_ -\n"
                    f"  🕵️ Wanted Level: `{wanted_level:.2f}`\n"
                    f"  ✨ Level/XP Global: `{level_global}` / `{format_large_number(xp_global)}`"
                ),
                inline=True
            )

            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.info(f"MODERATOR ACTION: {interaction.user.id} đã xem dữ liệu của user {target_user.id}.")

        except Exception as e:
            logger.error(f"Lỗi trong lệnh /mod view_user: {e}", exc_info=True)
            await interaction.followup.send(f"{ICON_ERROR} Đã xảy ra lỗi khi truy xuất dữ liệu.", ephemeral=True)
# --- LỆNH CON MỚI: /mod set balance ---
    @set_group.subcommand(name="balance", description="Thiết lập số dư tiền tệ cho một người dùng.")
    @application_checks.check(check_is_bot_moderator_interaction)
    async def set_balance(
        self,
        interaction: nextcord.Interaction,
        user: nextcord.User = nextcord.SlashOption(
            name="user",
            description="Người dùng cần chỉnh sửa.",
            required=True,
        ),
        balance_type: str = nextcord.SlashOption(
            name="type",
            description="Loại số dư muốn thay đổi.",
            required=True,
            choices={"Tiền Sạch (earned)": "earned", "Tiền Lậu (adadd)": "adadd", "Bank (global)": "bank"}
        ),
        amount: int = nextcord.SlashOption(
            name="amount",
            description="Số tiền muốn thiết lập (số âm sẽ được đặt về 0).",
            required=True
        )
    ):
        """Thiết lập số dư cho một người dùng."""
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.guild:
            await interaction.followup.send(f"{ICON_ERROR} Vui lòng dùng lệnh này trong một server.", ephemeral=True)
            return

        final_amount = max(0, amount) # Đảm bảo số tiền không phải là số âm
        
        try:
            economy_data = load_economy_data()
            global_profile = get_or_create_global_user_profile(economy_data, user.id)
            
            original_value = 0
            
            if balance_type == "bank":
                original_value = global_profile.get("bank_balance", 0)
                global_profile["bank_balance"] = final_amount
                icon = ICON_BANK
            else: # earned hoặc adadd
                local_data = get_or_create_user_local_data(global_profile, interaction.guild.id)
                original_value = local_data["local_balance"].get(balance_type, 0)
                local_data["local_balance"][balance_type] = final_amount
                icon = ICON_TIEN_SACH if balance_type == "earned" else ICON_TIEN_LAU

            save_economy_data(economy_data)

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
# --- LỆNH CON MỚI: /mod set xp ---
    @set_group.subcommand(name="xp", description="Thiết lập điểm kinh nghiệm cho một người dùng.")
    @application_checks.check(check_is_bot_moderator_interaction)
    async def set_xp(
        self,
        interaction: nextcord.Interaction,
        user: nextcord.User = nextcord.SlashOption(name="user", description="Người dùng cần chỉnh sửa.", required=True),
        xp_type: str = nextcord.SlashOption(
            name="type",
            description="Loại XP muốn thay đổi.",
            required=True,
            choices={"XP Local": "local", "XP Global": "global"}
        ),
        amount: int = nextcord.SlashOption(name="amount", description="Số XP muốn thiết lập.", required=True)
    ):
        """Thiết lập XP cho một người dùng."""
        await interaction.response.defer(ephemeral=True)
        final_amount = max(0, amount)

        try:
            economy_data = load_economy_data()
            global_profile = get_or_create_global_user_profile(economy_data, user.id)
            
            xp_key = f"xp_{xp_type}"
            original_value = 0

            if xp_type == "global":
                original_value = global_profile.get(xp_key, 0)
                global_profile[xp_key] = final_amount
            else: # local
                if not interaction.guild:
                    await interaction.followup.send(f"{ICON_ERROR} Cần dùng lệnh trong server để set XP Local.", ephemeral=True)
                    return
                local_data = get_or_create_user_local_data(global_profile, interaction.guild.id)
                original_value = local_data.get(xp_key, 0)
                local_data[xp_key] = final_amount

            save_economy_data(economy_data)
            logger.info(f"MODERATOR ACTION: {interaction.user.id} đã set {xp_key} của {user.id} thành {final_amount}.")
            await interaction.followup.send(
                f"{ICON_SUCCESS} Đã cập nhật thành công!\n"
                f"  - **Người dùng:** {user.mention}\n"
                f"  - **Loại XP:** `{xp_type.capitalize()}`\n"
                f"  - **Giá trị cũ:** `{format_large_number(original_value)}`\n"
                f"  - **Giá trị mới:** `{format_large_number(final_amount)}`",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Lỗi trong lệnh /mod set xp: {e}", exc_info=True)
            await interaction.followup.send(f"{ICON_ERROR} Đã xảy ra lỗi khi cập nhật dữ liệu.", ephemeral=True)

    # --- LỆNH CON MỚI: /mod set wanted_level ---
    @set_group.subcommand(name="wanted_level", description="Thiết lập Điểm Nghi ngờ (truy nã) cho người dùng.")
    @application_checks.check(check_is_bot_moderator_interaction)
    async def set_wanted_level(
        self,
        interaction: nextcord.Interaction,
        user: nextcord.User = nextcord.SlashOption(name="user", description="Người dùng cần chỉnh sửa.", required=True),
        level: float = nextcord.SlashOption(name="level", description="Mức độ truy nã muốn thiết lập.", required=True)
    ):
        """Thiết lập wanted_level cho một người dùng."""
        await interaction.response.defer(ephemeral=True)
        final_level = max(0.0, level)

        try:
            economy_data = load_economy_data()
            global_profile = get_or_create_global_user_profile(economy_data, user.id)
            
            original_value = global_profile.get("wanted_level", 0.0)
            global_profile["wanted_level"] = final_level
            
            save_economy_data(economy_data)
            logger.info(f"MODERATOR ACTION: {interaction.user.id} đã set wanted_level của {user.id} thành {final_level}.")
            await interaction.followup.send(
                f"{ICON_SUCCESS} Đã cập nhật thành công!\n"
                f"  - **Người dùng:** {user.mention}\n"
                f"  - **Chỉ số:** `Wanted Level` 🕵️\n"
                f"  - **Giá trị cũ:** `{original_value:.2f}`\n"
                f"  - **Giá trị mới:** `{final_level:.2f}`",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Lỗi trong lệnh /mod set wanted_level: {e}", exc_info=True)
            await interaction.followup.send(f"{ICON_ERROR} Đã xảy ra lỗi khi cập nhật dữ liệu.", ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(ModToolsSlashCog(bot))
