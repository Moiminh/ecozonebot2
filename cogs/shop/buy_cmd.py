# bot/cogs/shop/buy_cmd.py
import nextcord
from nextcord.ext import commands
import logging
import random

from core.database import get_or_create_global_user_profile, get_or_create_user_local_data
from core.utils import try_send, format_large_number
from core.config import BASE_CATCH_CHANCE, WANTED_LEVEL_CATCH_MULTIPLIER
from core.icons import ICON_SUCCESS, ICON_ERROR, ICON_WARNING, ICON_ECOIN, ICON_ECOBIT

logger = logging.getLogger(__name__)

class PurchaseConfirmationView(nextcord.ui.View):
    # Giữ nguyên class View này
    def __init__(self, ctx, buy_cog_instance, item_id, quantity, total_cost, payment_options):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.buy_cog = buy_cog_instance
        self.item_id = item_id
        self.quantity = quantity
        self.total_cost = total_cost
        self.interaction_user = ctx.author
        self.message = None

        for option in payment_options:
            button = nextcord.ui.Button(
                label=option["label"],
                style=option["style"],
                custom_id=f"buy_{option['id']}",
                disabled=option["disabled"]
            )
            button.callback = self.create_callback(option["id"])
            self.add_item(button)

    async def interaction_check(self, interaction: nextcord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("Đây không phải là giao dịch của bạn!", ephemeral=True)
            return False
        return True
    
    def create_callback(self, payment_id):
        async def callback(interaction: nextcord.Interaction):
            await interaction.response.defer()
            await self.buy_cog.process_payment(self, interaction, payment_id)
        return callback

    async def on_timeout(self):
        if self.message:
            for item in self.children:
                item.disabled = True
            await self.message.edit(content="⏳ Giao dịch đã hết hạn.", view=self)

class BuyCommandCog(commands.Cog, name="Buy Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("BuyCommandCog (v4 - Refactored) initialized.")

    @commands.command(name='buy')
    async def buy(self, ctx: commands.Context, item_id: str, quantity: int = 1):
        """Mua một vật phẩm từ cửa hàng với nhiều tùy chọn thanh toán."""
        item_id_to_buy = item_id.lower().strip()

        if quantity <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Số lượng mua phải lớn hơn 0.")
            return
        
        # [SỬA] Sử dụng item definitions từ cache của bot
        if item_id_to_buy not in self.bot.item_definitions:
            await try_send(ctx, content=f"{ICON_ERROR} Vật phẩm `{item_id}` không tồn tại trong cửa hàng.")
            return

        item_details = self.bot.item_definitions[item_id_to_buy]
        total_cost = item_details.get("price", 0) * quantity

        # [SỬA] Sử dụng cache của bot
        economy_data = self.bot.economy_data
        global_profile = get_or_create_global_user_profile(economy_data, ctx.author.id)
        local_data = get_or_create_user_local_data(global_profile, ctx.guild.id)
        
        payment_options = []
        earned_balance = local_data["local_balance"]["earned"]
        payment_options.append({
            "id": "ecoin",
            "label": f"Trả bằng 🪙Ecoin ({format_large_number(earned_balance)})",
            "style": nextcord.ButtonStyle.green,
            "disabled": earned_balance < total_cost
        })
        
        adadd_balance = local_data["local_balance"]["adadd"]
        payment_options.append({
            "id": "ecobit",
            "label": f"Trả bằng 🧪Ecobit ({format_large_number(adadd_balance)}) - Rủi ro!",
            "style": nextcord.ButtonStyle.red,
            "disabled": adadd_balance < total_cost
        })

        if all(opt['disabled'] for opt in payment_options):
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ tiền từ bất kỳ nguồn nào để mua vật phẩm này.")
            return

        view = PurchaseConfirmationView(ctx, self, item_id_to_buy, quantity, total_cost, payment_options)
        msg = await try_send(ctx, content=f"Xác nhận mua **{quantity}x {item_details['description']}** với giá **{total_cost:,}**.\nVui lòng chọn nguồn tiền thanh toán:", view=view)
        if msg:
            view.message = msg

    async def process_payment(self, view: PurchaseConfirmationView, interaction: nextcord.Interaction, payment_type: str):
        ctx = view.ctx
        item_id = view.item_id
        quantity = view.quantity
        total_cost = view.total_cost
        
        # [SỬA] Sử dụng cache của bot và không save thủ công
        economy_data = self.bot.economy_data
        global_profile = get_or_create_global_user_profile(economy_data, ctx.author.id)
        local_data = get_or_create_user_local_data(global_profile, ctx.guild.id)
        
        is_tainted = False
        destination_inventory = None
        destination_name = ""

        if payment_type == "ecoin":
            local_data["local_balance"]["earned"] -= total_cost
            is_tainted = False
            destination_inventory = global_profile.setdefault("inventory_global", [])
            destination_name = "Túi Đồ Toàn Cục"
        elif payment_type == "ecobit":
            wanted_level = global_profile.get("wanted_level", 0.0)
            catch_chance = min(0.9, BASE_CATCH_CHANCE + wanted_level * WANTED_LEVEL_CATCH_MULTIPLIER * 0.5)
            if random.random() < catch_chance:
                fine_amount = min(local_data["local_balance"]["earned"], int(total_cost * 0.2))
                local_data["local_balance"]["earned"] -= fine_amount
                global_profile["wanted_level"] = global_profile.get("wanted_level", 0.0) + 0.2
                final_msg = f"🚨 **BỊ PHÁT HIỆN!** Giao dịch mờ ám của bạn đã bị cảnh sát chú ý! Bạn bị phạt **{fine_amount:,}** `🪙Ecoin`."
                await view.message.edit(content=final_msg, view=None)
                return

            local_data["local_balance"]["adadd"] -= total_cost
            is_tainted = True
            destination_inventory = local_data.setdefault("inventory_local", [])
            destination_name = "Túi Đồ Tại Server"
        
        new_item_data = {"item_id": item_id, "is_tainted": is_tainted}
        destination_inventory.extend([new_item_data] * quantity)

        item_details = self.bot.item_definitions.get(item_id, {})
        final_msg = f"{ICON_SUCCESS} Giao dịch thành công! Bạn đã mua **{quantity}x {item_details.get('description', item_id)}**.\nVật phẩm được thêm vào **{destination_name}**."
        if is_tainted:
            final_msg += f"\n> {ICON_WARNING} *Vật phẩm này được mua bằng 🧪Ecobit và bị coi là 'vật phẩm bẩn'*."
            
        await view.message.edit(content=final_msg, view=None)

def setup(bot: commands.Bot):
    bot.add_cog(BuyCommandCog(bot))
