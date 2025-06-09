# bot/cogs/misc/dashboard_cmd.py
import nextcord
from nextcord.ext import commands
import logging
from core.utils import get_player_title, format_large_number
from core.icons import *

logger = logging.getLogger(__name__)

# --- View và các hàm check không thay đổi ---
async def is_guild_owner_interaction(interaction: nextcord.Interaction) -> bool:
    return interaction.user.id == interaction.guild.owner_id

class DashboardView(nextcord.ui.View):
    def __init__(self, interaction: nextcord.Interaction, is_mafia: bool, is_police: bool, is_owner: bool):
        super().__init__(timeout=None)
        self.interaction_user = interaction.user
        if is_mafia:
            self.add_item(nextcord.ui.Button(label="🏛️ Chợ Đen", style=nextcord.ButtonStyle.grey, custom_id="dash_blackmarket"))
        if is_police:
            self.add_item(nextcord.ui.Button(label="⚖️ Bắt giữ", style=nextcord.ButtonStyle.primary, custom_id="dash_arrest"))
        if is_owner:
            self.add_item(nextcord.ui.Button(label="👑 Thưởng Ecobit", style=nextcord.ButtonStyle.blurple, custom_id="dash_addmoney"))
    
    async def interaction_check(self, interaction: nextcord.Interaction) -> bool:
        if interaction.data.get("custom_id") == "dash_addmoney":
            if not await is_guild_owner_interaction(interaction):
                await interaction.response.send_message("Chỉ chủ server mới có thể dùng nút này!", ephemeral=True)
                return False
        return interaction.user.id == self.interaction_user.id

class DashboardCommandCog(commands.Cog, name="Dashboard Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("DashboardCommandCog (SQLite Ready) initialized.")

    @nextcord.slash_command(name="dashboard", description="Xem bảng thông tin cá nhân và các hành động của bạn.")
    async def dashboard(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)

        if not interaction.guild:
            await interaction.followup.send(f"{ICON_ERROR} Lệnh này chỉ hoạt động trong server.", ephemeral=True)
            return

        user = interaction.user
        global_profile = self.bot.db.get_or_create_global_user_profile(user.id)
        local_data = self.bot.db.get_or_create_user_local_data(user.id, interaction.guild.id)
        
        embed = nextcord.Embed(title=f"Bảng điều khiển của {user.name}", color=user.color)
        embed.set_thumbnail(url=user.display_avatar.url)
        
        title = get_player_title(local_data['level_local'], global_profile['wanted_level'])
        embed.add_field(name="Chức danh tại Server", value=title, inline=False)
        
        embed.add_field(
            name="Tài chính",
            value=f"{ICON_ECOIN} **Ecoin:** `{format_large_number(local_data['local_balance_earned'])}`\n"
                  f"{ICON_ECOBIT} **Ecobit:** `{format_large_number(local_data['local_balance_adadd'])}`\n"
                  f"{ICON_BANK_MAIN} **Bank:** `{format_large_number(global_profile['bank_balance'])}`",
            inline=True
        )

        embed.add_field(
            name="Sinh tồn",
            value=f"❤️ **Máu:** `{local_data['health']}/100`\n"
                  f"🍔 **Độ no:** `{local_data['hunger']}/100`\n"
                  f"⚡ **Năng lượng:** `{local_data['energy']}/100`",
            inline=True
        )
        
        embed.add_field(
            name="Trạng thái",
            value=f"🕵️ **Điểm Nghi ngờ:** `{global_profile['wanted_level']:.2f}`",
            inline=True
        )

        is_owner = await is_guild_owner_interaction(interaction)
        # is_mafia, is_police cần logic để xác định, tạm thời là False
        view = DashboardView(interaction, is_mafia=False, is_police=False, is_owner=is_owner)

        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

def setup(bot: commands.Bot):
    bot.add_cog(DashboardCommandCog(bot))
