# bot/cogs/economy/visa_cmd.py
import nextcord
from nextcord.ext import commands
import logging
import uuid

from core.database import (
    load_economy_data,
    save_economy_data,
    get_or_create_global_user_profile
)
from core.utils import try_send, format_large_number
from core.config import UTILITY_ITEMS, COMMAND_PREFIX, UPGRADE_VISA_COST
from core.icons import (
    ICON_SUCCESS, ICON_ERROR, ICON_WARNING, ICON_INFO, 
    ICON_BANK_MAIN, ICON_ECOBANK, ICON_ECOVISA
)

logger = logging.getLogger(__name__)

class VisaCommandCog(commands.Cog, name="Visa Commands"):
    """
    Cog chứa tất cả các lệnh liên quan đến việc quản lý và sử dụng
    Ecobank (Visa Nội địa) và Ecovisa (Visa Quốc tế).
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("VisaCommandCog (v3 - Full) initialized.")

    @commands.group(name='visa', invoke_without_command=True)
    async def visa(self, ctx: commands.Context):
        """Lệnh cha cho các hoạt động liên quan đến thẻ Visa. Gõ !help visa để xem các lệnh con."""
        await try_send(ctx, content=f"{ICON_INFO} Vui lòng sử dụng một lệnh con. Gõ `{COMMAND_PREFIX}help visa` để xem chi tiết.")

    @visa.command(name="buy")
    async def buy_visa(self, ctx: commands.Context, visa_id_str: str):
        """Mua một thẻ Visa mới bằng tiền từ Bank trung tâm của bạn."""
        item_id_to_buy = visa_id_str.lower().strip()

        if item_id_to_buy not in UTILITY_ITEMS or UTILITY_ITEMS[item_id_to_buy].get("type") != "visa":
            await try_send(ctx, content=f"{ICON_ERROR} Loại Visa `{visa_id_str}` không hợp lệ. Hãy xem các loại thẻ có trong shop.")
            return

        if not ctx.guild and UTILITY_ITEMS[item_id_to_buy].get("visa_type") == "local":
            await try_send(ctx, content=f"{ICON_ERROR} Bạn phải ở trong một server để mua `Ecobank` (Visa Nội địa).")
            return

        try:
            economy_data = load_economy_data()
            global_profile = get_or_create_global_user_profile(economy_data, ctx.author.id)
            
            visa_details = UTILITY_ITEMS[item_id_to_buy]
            price = visa_details.get("price", 0)

            if global_profile["bank_balance"] < price:
                await try_send(ctx, content=f"{ICON_ERROR} Bạn không đủ tiền trong Bank trung tâm. Cần **{price:,}**, bạn có **{global_profile['bank_balance']:,}**.")
                return

            global_profile["bank_balance"] -= price
            
            new_visa_item = {
                "item_id": item_id_to_buy,
                "unique_id": str(uuid.uuid4())[:8],
                "type": "visa",
                "visa_type": visa_details["visa_type"],
                "source_guild_id": ctx.guild.id if ctx.guild else None,
                "balance": 0,
                "capacity": visa_details["capacity"]
            }
            
            global_profile.setdefault("inventory_global", []).append(new_visa_item)
            save_economy_data(economy_data)

            logger.info(f"User {ctx.author.id} đã mua {item_id_to_buy} với giá {price} từ bank.")
            await try_send(ctx, content=f"{ICON_SUCCESS} Bạn đã mua thành công **{visa_details['name']}**! Thẻ đã được thêm vào túi đồ toàn cục. Dùng `{COMMAND_PREFIX}visa topup` để nạp tiền vào thẻ.")

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'visa buy': {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi mua Visa.")

    @visa.command(name="balance", aliases=["bal", "list"])
    async def visa_balance(self, ctx: commands.Context):
        """Xem số dư của tất cả các thẻ Visa bạn đang sở hữu."""
        try:
            economy_data = load_economy_data()
            global_profile = get_or_create_global_user_profile(economy_data, ctx.author.id)
            inventory_global = global_profile.get("inventory_global", [])
            
            visa_items = [item for item in inventory_global if isinstance(item, dict) and item.get("type") == "visa"]

            if not visa_items:
                await try_send(ctx, content=f"{ICON_INFO} Bạn chưa sở hữu thẻ Visa nào. Dùng `{COMMAND_PREFIX}visa buy` để mua.")
                return

            embed = nextcord.Embed(title=f"💳 Các Thẻ Visa của {ctx.author.name}", color=nextcord.Color.dark_purple())
            embed.set_footer(text=f"Dùng {COMMAND_PREFIX}visa topup <ID_thẻ> <số_tiền> để nạp tiền.")

            for visa in visa_items:
                visa_icon = ICON_ECOBANK if visa.get("visa_type") == "local" else ICON_ECOVISA
                visa_name = UTILITY_ITEMS.get(visa['item_id'], {}).get('name', 'Visa không xác định')
                
                source_server_name = "Toàn cầu"
                if source_guild_id := visa.get("source_guild_id"):
                    source_guild = self.bot.get_guild(source_guild_id)
                    if source_guild:
                        source_server_name = source_guild.name
                
                embed.add_field(
                    name=f"{visa_icon} {visa_name} (ID: `{visa.get('unique_id')}`)",
                    value=(f"**Số dư:** `{format_large_number(visa.get('balance', 0))}` / `{format_large_number(visa.get('capacity', 0))}`\n"
                           f"**Loại:** `{visa.get('visa_type', 'N/A').capitalize()}`\n"
                           f"**Nơi phát hành:** `{source_server_name}`"),
                    inline=False
                )

            await try_send(ctx, embed=embed)

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'visa balance': {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi xem số dư Visa.")

    @visa.command(name="topup")
    async def topup_visa(self, ctx: commands.Context, unique_visa_id: str, amount: int):
        """Nạp tiền từ Bank trung tâm vào một thẻ Visa cụ thể."""
        if amount <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Số tiền nạp phải lớn hơn 0.")
            return

        try:
            economy_data = load_economy_data()
            global_profile = get_or_create_global_user_profile(economy_data, ctx.author.id)
            
            if global_profile["bank_balance"] < amount:
                await try_send(ctx, content=f"{ICON_ERROR} Bạn không đủ tiền trong Bank trung tâm. Cần **{amount:,}**, bạn có **{global_profile['bank_balance']:,}**.")
                return

            target_visa = next((item for item in global_profile.get("inventory_global", []) if isinstance(item, dict) and item.get("unique_id") == unique_visa_id), None)
            
            if not target_visa:
                await try_send(ctx, content=f"{ICON_ERROR} Không tìm thấy thẻ Visa nào có ID `{unique_visa_id}`.")
                return

            current_balance = target_visa.get("balance", 0)
            capacity = target_visa.get("capacity", 0)
            if current_balance + amount > capacity:
                await try_send(ctx, content=f"{ICON_ERROR} Thẻ này không đủ sức chứa. Cần nạp **{amount:,}**, nhưng chỉ còn trống **{capacity - current_balance:,}**.")
                return

            global_profile["bank_balance"] -= amount
            target_visa["balance"] += amount
            save_economy_data(economy_data)
            
            logger.info(f"User {ctx.author.id} đã topup {amount} vào visa {unique_visa_id}.")
            await try_send(ctx, content=f"{ICON_SUCCESS} Đã nạp thành công **{amount:,}** vào thẻ `{unique_visa_id}`.\nSố dư mới của thẻ: **{target_visa['balance']:,}** / `{format_large_number(capacity)}`")

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'visa topup': {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi nạp tiền.")

    @visa.command(name="withdraw")
    async def withdraw_visa(self, ctx: commands.Context, unique_visa_id: str, amount: int):
        """Rút tiền từ một thẻ Visa cụ thể về Bank trung tâm (miễn phí)."""
        if amount <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Số tiền rút phải lớn hơn 0.")
            return

        try:
            economy_data = load_economy_data()
            global_profile = get_or_create_global_user_profile(economy_data, ctx.author.id)
            
            target_visa = next((item for item in global_profile.get("inventory_global", []) if isinstance(item, dict) and item.get("unique_id") == unique_visa_id), None)
            
            if not target_visa:
                await try_send(ctx, content=f"{ICON_ERROR} Không tìm thấy thẻ Visa nào có ID `{unique_visa_id}`.")
                return

            if target_visa.get("balance", 0) < amount:
                await try_send(ctx, content=f"{ICON_ERROR} Thẻ `{unique_visa_id}` không đủ số dư. Cần rút **{amount:,}**, nhưng thẻ chỉ có **{target_visa.get('balance', 0):,}**.")
                return

            target_visa["balance"] -= amount
            global_profile["bank_balance"] += amount
            save_economy_data(economy_data)
            
            logger.info(f"User {ctx.author.id} đã withdraw {amount} từ visa {unique_visa_id}.")
            await try_send(ctx, content=f"{ICON_SUCCESS} Đã rút thành công **{amount:,}** từ thẻ `{unique_visa_id}` về Bank trung tâm.\nSố dư Bank mới của bạn: **{global_profile['bank_balance']:,}** {ICON_BANK_MAIN}")

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'visa withdraw': {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi rút tiền.")

    @visa.command(name="upgrade")
    async def upgrade_visa(self, ctx: commands.Context, unique_visa_id: str):
        """Nâng cấp một Ecobank (Visa Nội địa) thành Ecovisa (Visa Quốc tế)."""
        try:
            economy_data = load_economy_data()
            global_profile = get_or_create_global_user_profile(economy_data, ctx.author.id)
            
            target_visa = next((item for item in global_profile.get("inventory_global", []) if isinstance(item, dict) and item.get("unique_id") == unique_visa_id), None)
            
            if not target_visa:
                await try_send(ctx, content=f"{ICON_ERROR} Không tìm thấy thẻ Visa nào có ID `{unique_visa_id}`.")
                return

            if target_visa.get("visa_type") != "local":
                await try_send(ctx, content=f"{ICON_ERROR} Thẻ này không phải là `Ecobank` (Visa Nội địa) nên không thể nâng cấp.")
                return

            upgrade_target_id = "ecovisa_standard"
            upgrade_details = UTILITY_ITEMS.get(upgrade_target_id)
            if not upgrade_details:
                await try_send(ctx, content=f"{ICON_ERROR} Lỗi hệ thống: không tìm thấy thông tin nâng cấp `{upgrade_target_id}`.")
                return
            
            upgrade_cost = UPGRADE_VISA_COST
            if global_profile["bank_balance"] < upgrade_cost:
                await try_send(ctx, content=f"{ICON_ERROR} Bạn không đủ tiền trong Bank để nâng cấp. Cần **{upgrade_cost:,}**, bạn có **{global_profile['bank_balance']:,}**.")
                return

            global_profile["bank_balance"] -= upgrade_cost
            original_name = UTILITY_ITEMS.get(target_visa['item_id'], {}).get('name', 'Visa cũ')
            
            target_visa["item_id"] = upgrade_target_id
            target_visa["visa_type"] = "international"
            target_visa["capacity"] = upgrade_details["capacity"]
            
            save_economy_data(economy_data)

            logger.info(f"User {ctx.author.id} đã nâng cấp visa {unique_visa_id} lên {upgrade_target_id}.")
            await try_send(ctx, content=(
                f"{ICON_SUCCESS} Nâng cấp thành công!\n"
                f"  - Đã trừ phí: **{upgrade_cost:,}** {ICON_BANK_MAIN} từ Bank trung tâm.\n"
                f"  - Thẻ `{unique_visa_id}` (`{original_name}`) của bạn giờ đã là **{upgrade_details['name']}**!"
            ))

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'visa upgrade': {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi nâng cấp thẻ.")

def setup(bot: commands.Bot):
    bot.add_cog(VisaCommandCog(bot))
