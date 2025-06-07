# bot/cogs/shop/shop_cmd.py
import nextcord
from nextcord.ext import commands
import logging

from core.utils import try_send
from core.config import SHOP_ITEMS, COMMAND_PREFIX
from core.icons import ICON_SHOP, ICON_TIEN_SACH, ICON_TIEN_LAU

logger = logging.getLogger(__name__)

class ShopDisplayCommandCog(commands.Cog, name="Shop Display Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("ShopDisplayCommandCog (v2) initialized.")

    @commands.command(name='shop', aliases=['store'])
    async def shop_display(self, ctx: commands.Context):
        """Hiển thị các vật phẩm đang được bán trong cửa hàng."""
        
        embed = nextcord.Embed(
            title=f"{ICON_SHOP} Cửa Hàng Vật Phẩm", 
            description=(
                f"Sử dụng `{COMMAND_PREFIX}buy <tên_vật_phẩm> [số_lượng]` để mua.\n"
                f"Sử dụng `{COMMAND_PREFIX}sell <tên_vật_phẩm> [số_lượng]` để bán.\n\n"
                f"**Lưu ý:** Mua hàng bằng {ICON_TIEN_LAU} `Tiền Lậu` có thể khiến vật phẩm bị 'bẩn' và giảm giá trị khi bán lại!"
            ),
            color=nextcord.Color.orange()
        )

        if not SHOP_ITEMS:
            embed.description = f"{ICON_SHOP} Cửa hàng hiện đang trống hoặc đang được cập nhật."
        else:
            for item_id, details in SHOP_ITEMS.items():
                item_name_display = item_id.replace("_", " ").capitalize()
                buy_price_str = f"{details.get('price', 0):,}"
                sell_price_str = f"{details.get('sell_price', 0):,}"
                
                embed.add_field(
                    name=f"{item_name_display} - Mua: {buy_price_str} | Bán: {sell_price_str} {ICON_TIEN_SACH}",
                    value=details.get('description', 'Chưa có mô tả.'),
                    inline=False
                )
        
        await try_send(ctx, embed=embed)
        logger.debug(f"Lệnh 'shop' (v2) đã được hiển thị cho {ctx.author.name}.")

def setup(bot: commands.Bot):
    bot.add_cog(ShopDisplayCommandCog(bot))
