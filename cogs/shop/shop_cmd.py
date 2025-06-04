# bot/cogs/shop/shop_cmd.py
import nextcord
from nextcord.ext import commands

# Import các thành phần cần thiết từ package 'core'
# from core.database import ... # Lệnh shop thuần túy hiển thị, không cần database trực tiếp
from core.utils import try_send
from core.config import CURRENCY_SYMBOL, SHOP_ITEMS, COMMAND_PREFIX
from core.icons import ICON_SHOP # Đảm bảo icon này có trong core/icons.py

class ShopDisplayCommandCog(commands.Cog, name="Shop Display Command"): # Đổi tên class Cog cho rõ ràng
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='shop', aliases=['store'])
    async def shop_display(self, ctx: commands.Context): # Đổi tên hàm lệnh để tránh trùng tên với alias/command name nếu cần
        """Hiển thị các vật phẩm đang được bán trong cửa hàng.
        Sử dụng lệnh `buy <tên_vật_phẩm> [số_lượng]` để mua.
        Sử dụng lệnh `sell <tên_vật_phẩm> [số_lượng]` để bán.
        """
        embed = nextcord.Embed(
            title=f"{ICON_SHOP} Cửa Hàng Vật Phẩm", 
            description=f"Mua: `{COMMAND_PREFIX}buy <tên_vật_phẩm> [số_lượng]` (mặc định số lượng là 1)\nBán: `{COMMAND_PREFIX}sell <tên_vật_phẩm> [số_lượng]` (mặc định số lượng là 1)",
            color=nextcord.Color.orange()
        )
        if not SHOP_ITEMS:
            embed.description = f"{ICON_SHOP} Cửa hàng hiện đang trống hoặc đang được cập nhật."
        else:
            for item_id, details in SHOP_ITEMS.items():
                item_name_display = item_id.replace("_", " ").capitalize()
                buy_price_str = f"{details['price']:,}"
                
                sell_price_val = details.get('sell_price')
                if sell_price_val is not None:
                    sell_price_str = f"{sell_price_val:,} {CURRENCY_SYMBOL}"
                else:
                    sell_price_str = "Không thể bán"
                
                embed.add_field(
                    name=f"{item_name_display} - Mua: {buy_price_str} {CURRENCY_SYMBOL} | Bán: {sell_price_str}",
                    value=details['description'],
                    inline=False
                )
        await try_send(ctx, embed=embed)

def setup(bot: commands.Bot):
    bot.add_cog(ShopDisplayCommandCog(bot))
