# bot/cogs/economy/visa_cmd.py
import nextcord
from nextcord.ext import commands
import logging
import json
from core.utils import try_send, format_large_number, require_travel_check
from core.config import COMMAND_PREFIX
from core.icons import ICON_SUCCESS, ICON_ERROR, ICON_INFO, ICON_BANK_MAIN, ICON_ECOBANK, ICON_ECOVISA

logger = logging.getLogger(__name__)

class VisaCommandCog(commands.Cog, name="Visa Commands"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("VisaCommandCog (SQLite Ready) initialized.")

    @commands.group(name='visa', invoke_without_command=True)
    async def visa(self, ctx: commands.Context):
        await try_send(ctx, content=f"{ICON_INFO} Vui lòng sử dụng một lệnh con. Gõ `{COMMAND_PREFIX}help visa` để xem chi tiết.")

    @visa.command(name="buy")
    @commands.guild_only()
    @require_travel_check
    async def buy_visa(self, ctx: commands.Context, visa_id_str: str):
        item_id_to_buy = visa_id_str.lower().strip()
        all_items = self.bot.item_definitions

        if item_id_to_buy not in all_items or all_items[item_id_to_buy].get("type") != "visa":
            await try_send(ctx, content=f"{ICON_ERROR} Loại Visa `{visa_id_str}` không hợp lệ.")
            return

        try:
            global_profile = self.bot.db.get_or_create_global_user_profile(ctx.author.id)
            visa_details = all_items[item_id_to_buy]
            price = visa_details.get("price", 0)

            if global_profile['bank_balance'] < price:
                await try_send(ctx, content=f"{ICON_ERROR} Bạn không đủ tiền trong Bank. Cần **{price:,}**.")
                return

            self.bot.db.update_balance(ctx.author.id, None, 'bank_balance', global_profile['bank_balance'] - price)
            
            # Dữ liệu đặc biệt cho thẻ visa
            visa_custom_data = {
                "balance": 0,
                "capacity": visa_details["capacity"],
                "source_guild_name": ctx.guild.name
            }
            
            self.bot.db.add_item_to_inventory(ctx.author.id, item_id_to_buy, 1, 'global', custom_data=visa_custom_data)

            logger.info(f"User {ctx.author.id} đã mua {item_id_to_buy} với giá {price} từ bank.")
            await try_send(ctx, content=f"{ICON_SUCCESS} Bạn đã mua thành công **{visa_details['name']}**! Thẻ đã được thêm vào túi đồ toàn cục.")

        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'visa buy': {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi mua Visa.")

    @visa.command(name="balance", aliases=["bal", "list"])
    @require_travel_check
    async def visa_balance(self, ctx: commands.Context):
        try:
            inventory_global = self.bot.db.get_inventory(ctx.author.id, location='global')
            visa_items = [item for item in inventory_global if self.bot.item_definitions.get(item['item_id'], {}).get('type') == 'visa']

            if not visa_items:
                await try_send(ctx, content=f"{ICON_INFO} Bạn chưa sở hữu thẻ Visa nào.")
                return

            embed = nextcord.Embed(title=f"💳 Các Thẻ Visa của {ctx.author.name}", color=nextcord.Color.dark_purple())
            
            all_items_defs = self.bot.item_definitions
            for visa in visa_items:
                visa_def = all_items_defs.get(visa['item_id'], {})
                visa_custom_data = json.loads(visa['custom_data']) if visa['custom_data'] else {}

                visa_icon = ICON_ECOBANK if visa_def.get("visa_type") == "local" else ICON_ECOVISA
                visa_name = visa_def.get('name', 'Visa không xác định')
                source_server_name = visa_custom_data.get("source_guild_name", "Không rõ")
                balance = visa_custom_data.get("balance", 0)
                capacity = visa_custom_data.get("capacity", 0)

                embed.add_field(
                    name=f"{visa_icon} {visa_name} (ID Item: `{visa['inventory_id']}`)",
                    value=(f"**Số dư:** `{format_large_number(balance)}` / `{format_large_number(capacity)}`\n"
                           f"**Loại:** `{visa_def.get('visa_type', 'N/A').capitalize()}`\n"
                           f"**Nơi phát hành:** `{source_server_name}`"),
                    inline=False
                )
            await try_send(ctx, embed=embed)
        except Exception as e:
            logger.error(f"Lỗi trong lệnh 'visa balance': {e}", exc_info=True)
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi xem số dư Visa.")

def setup(bot: commands.Bot):
    bot.add_cog(VisaCommandCog(bot))
