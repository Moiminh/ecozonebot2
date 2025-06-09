# bot/cogs/shop/buy_cmd.py
import nextcord
from nextcord.ext import commands
import logging
import random

from core.utils import try_send, format_large_number
from core.config import BASE_CATCH_CHANCE, WANTED_LEVEL_CATCH_MULTIPLIER
from core.icons import ICON_SUCCESS, ICON_ERROR, ICON_WARNING, ICON_ECOIN, ICON_ECOBIT

logger = logging.getLogger(__name__)

class PurchaseConfirmationView(nextcord.ui.View):
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
        logger.info("BuyCommandCog (SQLite Ready) initialized.")

    @commands.command(name='buy')
    async def buy(self, ctx: commands.Context, item_id: str, quantity: int = 1):
        item_id_to_buy = item_id.lower().strip()

        if quantity <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Số lượng mua phải lớn hơn 0.")
            return
        
        if item_id_to_buy not in self.bot.item_definitions:
            await try_send(ctx, content=f"{ICON_ERROR} Vật phẩm `{item_id}` không tồn tại.")
            return

        item_details = self.bot.item_definitions[item_id_to_buy]
        total_cost = item_details.get("price", 0) * quantity

        local_data = self.bot.db.get_or_create_user_local_data(ctx.author.id, ctx.guild.id)
        
        payment_options = []
        earned_balance = local_data["local_balance_earned"]
        payment_options.append({
            "id": "ecoin",
            "label": f"Trả bằng 🪙Ecoin ({format_large_number(earned_balance)})",
            "style": nextcord.ButtonStyle.green,
            "disabled": earned_balance < total_cost
        })
        
        adadd_balance = local_data["local_balance_adadd"]
        payment_options.append({
            "id": "ecobit",
            "label": f"Trả bằng 🧪Ecobit ({format_large_number(adadd_balance)}) - Rủi ro!",
            "style": nextcord.ButtonStyle.red,
            "disabled": adadd_balance < total_cost
        })

        if all(opt['disabled'] for opt in payment_options):
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ tiền để mua vật phẩm này.")
            return

        view = PurchaseConfirmationView(ctx, self, item_id_to_buy, quantity, total_cost, payment_options)
        msg = await try_send(ctx, content=f"Xác nhận mua **{quantity}x {item_details['description']}** với giá **{total_cost:,}**.\nVui lòng chọn nguồn tiền thanh toán:", view=view)
        if msg:
            view.message = msg

    async def process_payment(self, view: PurchaseConfirmationView, interaction: nextcord.Interaction, payment_type: str):
        ctx = view.ctx
        author_id = ctx.author.id
        guild_id = ctx.guild.id
        item_id = view.item_id
        quantity = view.quantity
        total_cost = view.total_cost
        
        global_profile = self.bot.db.get_or_create_global_user_profile(author_id)
        local_data = self.bot.db.get_or_create_user_local_data(author_id, guild_id)
        
        is_tainted = False
        destination_location = ""
        destination_guild_id = None
        destination_name = ""

        if payment_type == "ecoin":
            self.bot.db.update_balance(author_id, guild_id, 'local_balance_earned', local_data['local_balance_earned'] - total_cost)
            is_tainted = False
            destination_location = "global"
            destination_name = "Túi Đồ Toàn Cục"
        elif payment_type == "ecobit":
            wanted_level = global_profile['wanted_level']
            catch_chance = min(0.9, BASE_CATCH_CHANCE + wanted_level * WANTED_LEVEL_CATCH_MULTIPLIER * 0.5)
            if random.random() < catch_chance:
                fine_amount = min(local_data["local_balance_earned"], int(total_cost * 0.2))
                self.bot.db.update_balance(author_id, guild_id, 'local_balance_earned', local_data['local_balance_earned'] - fine_amount)
                self.bot.db.update_wanted_level(author_id, wanted_level + 0.2)
                await view.message.edit(content=f"🚨 **BỊ PHÁT HIỆN!** Bạn bị phạt **{fine_amount:,}** `🪙Ecoin`.", view=None)
                return

            self.bot.db.update_balance(author_id, guild_id, 'local_balance_adadd', local_data['local_balance_adadd'] - total_cost)
            is_tainted = True
            destination_location = "local"
            destination_guild_id = guild_id
            destination_name = "Túi Đồ Tại Server"
        
        self.bot.db.add_item_to_inventory(author_id, item_id, quantity, destination_location, destination_guild_id, is_tainted)

        item_details = self.bot.item_definitions.get(item_id, {})
        final_msg = f"{ICON_SUCCESS} Giao dịch thành công! Bạn đã mua **{quantity}x {item_details.get('description', item_id)}**.\nVật phẩm được thêm vào **{destination_name}**."
        if is_tainted:
            final_msg += f"\n> {ICON_WARNING} *Vật phẩm này được mua bằng 🧪Ecobit và bị coi là 'vật phẩm bẩn'*."
            
        await view.message.edit(content=final_msg, view=None)

def setup(bot: commands.Bot):
    bot.add_cog(BuyCommandCog(bot))
