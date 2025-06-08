# bot/cogs/shop/buy_cmd.py
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
from core.config import SHOP_ITEMS
from core.icons import (
    ICON_SUCCESS, ICON_ERROR, ICON_WARNING, ICON_MONEY_BAG,
    ICON_ECOIN, ICON_ECOBIT, ICON_ECOBANK, ICON_ECOVISA
)

logger = logging.getLogger(__name__)

# --- View tương tác cho việc thanh toán ---
class PurchaseConfirmationView(nextcord.ui.View):
    def __init__(self, ctx, buy_cog_instance, item_id, quantity, total_cost):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.buy_cog = buy_cog_instance
        self.item_id = item_id
        self.quantity = quantity
        self.total_cost = total_cost
        self.interaction_user = ctx.author
        self.message = None

    async def interaction_check(self, interaction: nextcord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("Đây không phải là giao dịch của bạn!", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        if self.message:
            for item in self.children:
                item.disabled = True
            await self.message.edit(content="⏳ Giao dịch đã hết hạn.", view=self)

    @nextcord.ui.button(label="Thanh toán bằng 🪙Ecoin", style=nextcord.ButtonStyle.green, custom_id="buy_ecoin")
    async def pay_with_ecoin(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        # Logic này sẽ được gọi khi người dùng bấm nút
        await interaction.response.defer()
        # Hàm xử lý thanh toán thực tế sẽ được gọi từ đây
        # (Để đơn giản, logic xử lý sẽ được tích hợp trực tiếp vào cog chính)
        # Trong một dự án lớn hơn, có thể tách logic này ra riêng
        await self.buy_cog.process_payment(self, interaction, "ecoin")

    @nextcord.ui.button(label="Thanh toán bằng 🧪Ecobit (Rủi ro)", style=nextcord.ButtonStyle.red, custom_id="buy_ecobit")
    async def pay_with_ecobit(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.defer()
        await self.buy_cog.process_payment(self, interaction, "ecobit")
        
    # Các nút cho Visa sẽ được thêm vào một cách động


class BuyCommandCog(commands.Cog, name="Buy Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("BuyCommandCog (v3 - Interactive) initialized.")

    @commands.command(name='buy')
    async def buy(self, ctx: commands.Context, item_id: str, quantity: int = 1):
        """Mua một vật phẩm từ cửa hàng với nhiều tùy chọn thanh toán."""
        item_id_to_buy = item_id.lower().strip()

        if quantity <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Số lượng mua phải lớn hơn 0.")
            return
        
        if item_id_to_buy not in SHOP_ITEMS:
            await try_send(ctx, content=f"{ICON_ERROR} Vật phẩm `{item_id}` không tồn tại trong cửa hàng.")
            return

        item_details = SHOP_ITEMS[item_id_to_buy]
        total_cost = item_details.get("price", 0) * quantity

        # --- Tạo View và các nút bấm ---
        view = PurchaseConfirmationView(ctx, self, item_id_to_buy, quantity, total_cost)

        economy_data = load_economy_data()
        global_profile = get_or_create_global_user_profile(economy_data, ctx.author.id)
        local_data = get_or_create_user_local_data(global_profile, ctx.guild.id)

        # Kiểm tra và vô hiệu hóa các nút nếu không đủ tiền
        if local_data["local_balance"]["earned"] < total_cost:
            view.children[0].disabled = True # Nút Ecoin
        if local_data["local_balance"]["adadd"] < total_cost:
            view.children[1].disabled = True # Nút Ecobit

        # (Logic thêm nút cho Visa sẽ phức tạp hơn và có thể được thêm ở bước sau,
        # hiện tại tập trung vào 2 nguồn tiền chính)
            
        msg = await try_send(ctx, content=f"Xác nhận mua **{quantity}x {item_details['description']}** với giá **{total_cost:,}**.\nVui lòng chọn nguồn tiền thanh toán:", view=view)
        if msg:
            view.message = msg

    async def process_payment(self, view: PurchaseConfirmationView, interaction: nextcord.Interaction, payment_type: str):
        """Hàm xử lý logic thanh toán sau khi người dùng bấm nút."""
        ctx = view.ctx
        item_id = view.item_id
        quantity = view.quantity
        total_cost = view.total_cost
        
        economy_data = load_economy_data()
        global_profile = get_or_create_global_user_profile(economy_data, ctx.author.id)
        local_data = get_or_create_user_local_data(global_profile, ctx.guild.id)
        
        is_tainted = False
        destination_inventory = None
        destination_name = ""

        # Xử lý theo loại thanh toán
        if payment_type == "ecoin":
            local_data["local_balance"]["earned"] -= total_cost
            is_tainted = False
            destination_inventory = global_profile.setdefault("inventory_global", [])
            destination_name = "Túi Đồ Toàn Cục"
        elif payment_type == "ecobit":
            local_data["local_balance"]["adadd"] -= total_cost
            is_tainted = True
            destination_inventory = local_data.setdefault("inventory_local", [])
            destination_name = "Túi Đồ Tại Server"
            # (Ở đây có thể thêm logic kiểm tra rủi ro bị bắt)

        # Tạo vật phẩm và thêm vào túi
        new_item_data = {"item_id": item_id, "is_tainted": is_tainted}
        destination_inventory.extend([new_item_data] * quantity)
        
        save_economy_data(economy_data)

        # Chỉnh sửa tin nhắn gốc, xóa các nút
        final_msg = f"{ICON_SUCCESS} Giao dịch thành công! Bạn đã mua **{quantity}x {SHOP_ITEMS[item_id]['description']}**.\nVật phẩm được thêm vào **{destination_name}**."
        if is_tainted:
            final_msg += f"\n> {ICON_WARNING} *Vật phẩm này được mua bằng 🧪Ecobit và bị coi là 'vật phẩm bẩn'*."
            
        await view.message.edit(content=final_msg, view=None)


def setup(bot: commands.Bot):
    bot.add_cog(BuyCommandCog(bot))
