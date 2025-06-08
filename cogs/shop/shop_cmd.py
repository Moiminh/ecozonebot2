# bot/cogs/shop/shop_cmd.py
import nextcord
from nextcord.ext import commands
import logging

from core.utils import try_send
# [CẢI TIẾN] Import hàm load items và config
from core.database import load_item_definitions
from core.config import COMMAND_PREFIX
from core.icons import ICON_SHOP, ICON_ECOIN, ICON_ECOBIT # Sửa tên icon cho đúng

logger = logging.getLogger(__name__)

class ShopDisplayCommandCog(commands.Cog, name="Shop Display Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # [CẢI TIẾN] Load item vào bộ nhớ của bot khi khởi động
        self.bot.item_definitions = load_item_definitions()
        logger.info("ShopDisplayCommandCog (v3 - Dynamic Items) initialized.")

    @commands.command(name='shop', aliases=['store'])
    async def shop_display(self, ctx: commands.Context):
        """Hiển thị các vật phẩm đang được bán trong cửa hàng."""
        
        # [CẢI TIẾN] Lấy item definitions từ cache của bot
        SHOP_ITEMS = self.bot.item_definitions

        embed = nextcord.Embed(
            title=f"{ICON_SHOP} Cửa Hàng Vật Phẩm", 
            description=(
                f"Sử dụng `{COMMAND_PREFIX}buy <tên_vật_phẩm> [số_lượng]` để mua.\n"
                f"Sử dụng `{COMMAND_PREFIX}sell <tên_vật_phẩm> [số_lượng]` để bán.\n\n"
                # Sửa tên icon cho đúng
                f"**Lưu ý:** Mua hàng bằng {ICON_ECOBIT} `Ecobit` có thể khiến vật phẩm bị 'bẩn' và giảm giá trị khi bán lại!"
            ),
            color=nextcord.Color.orange()
        )

        if not SHOP_ITEMS:
            embed.description = f"{ICON_SHOP} Cửa hàng hiện đang trống hoặc đang được cập nhật."
        else:
            for item_id, details in SHOP_ITEMS.items():
                # Chỉ hiển thị các vật phẩm có giá bán (không hiển thị visa, balo ở đây)
                if details.get("type") in ["visa", "backpack"]:
                    continue

                item_name_display = details.get("name", item_id.replace("_", " ").capitalize())
                buy_price_str = f"{details.get('price', 0):,}"
                sell_price_str = f"{details.get('sell_price', 0):,}"
                
                embed.add_field(
                    # Sửa tên icon cho đúng
                    name=f"{item_name_display} - Mua: {buy_price_str} | Bán: {sell_price_str} {ICON_ECOIN}",
                    value=details.get('description', 'Chưa có mô tả.'),
                    inline=False
                )
        
        await try_send(ctx, embed=embed)
        logger.debug(f"Lệnh 'shop' (v3) đã được hiển thị cho {ctx.author.name}.")

def setup(bot: commands.Bot):
    bot.add_cog(ShopDisplayCommandCog(bot))
