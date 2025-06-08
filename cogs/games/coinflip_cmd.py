import nextcord
from nextcord.ext import commands
import random
import logging
from datetime import datetime

from core.database import (
    load_economy_data,
    save_economy_data,
    get_or_create_global_user_profile,
    get_or_create_user_local_data
)
from core.utils import try_send
from core.config import DICE_COOLDOWN, BASE_CATCH_CHANCE, WANTED_LEVEL_CATCH_MULTIPLIER
from core.icons import (
    ICON_LOADING, ICON_ERROR, ICON_MONEY_BAG, ICON_ECOIN, ICON_ECOBIT,
    ICON_WARNING, ICON_COINFLIP_HEADS, ICON_COINFLIP_TAILS
)
from core.travel_manager import handle_travel_event

logger = logging.getLogger(__name__)

class CoinflipBetView(nextcord.ui.View):
    def __init__(self, ctx, game_cog_instance, bet_amount, choice):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.game_cog = game_cog_instance
        self.bet = bet_amount
        self.choice = choice
        self.interaction_user = ctx.author
        self.message = None

    async def interaction_check(self, interaction: nextcord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("Đây không phải là ván cược của bạn!", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        if self.message:
            for item in self.children:
                item.disabled = True
            await self.message.edit(content="⏳ Ván cược đã hết hạn.", view=self)

    @nextcord.ui.button(label="Cược bằng 🪙Ecoin (An toàn)", style=nextcord.ButtonStyle.green, custom_id="bet_ecoin")
    async def bet_with_ecoin(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.defer()
        await self.game_cog.play_coinflip_game(self, interaction, "earned")

    @nextcord.ui.button(label="Cược bằng 🧪Ecobit (Rủi ro)", style=nextcord.ButtonStyle.red, custom_id="bet_ecobit")
    async def bet_with_ecobit(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.defer()
        await self.game_cog.play_coinflip_game(self, interaction, "adadd")


class CoinflipCommandCog(commands.Cog, name="Coinflip Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("CoinflipCommandCog (v4 - with Travel) initialized.")

    @commands.command(name='coinflip', aliases=['cf'])
    async def coinflip(self, ctx: commands.Context, bet: int, choice: str):
        """Tung đồng xu, chọn mặt (heads/tails hoặc ngửa/sấp) và đặt cược."""
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ sử dụng trong server.")
            return

        if bet <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Tiền cược phải lớn hơn 0!")
            return

        valid_choices = ['heads', 'tails', 'ngửa', 'sấp', 'h', 't', 'n', 's']
        if choice.lower() not in valid_choices:
            await try_send(ctx, content=f"{ICON_ERROR} Lựa chọn không hợp lệ. Hãy chọn `heads` hoặc `tails` (ngửa/sấp).")
            return

        economy_data = load_economy_data()
        global_profile = get_or_create_global_user_profile(economy_data, ctx.author.id)

        # --- Kiểm tra Last Active Guild ---
        guild_id = ctx.guild.id
        if global_profile.get("last_active_guild_id") != guild_id:
            await handle_travel_event(ctx, self.bot)
            logger.info(f"User {ctx.author.id} has 'traveled' to guild {guild_id}.")
        global_profile["last_active_guild_id"] = guild_id

        local_data = get_or_create_user_local_data(global_profile, guild_id)

        now = datetime.now().timestamp()
        last_cf = global_profile.get("cooldowns", {}).get("coinflip", 0)
        if now - last_cf < DICE_COOLDOWN:
            time_left = str(datetime.fromtimestamp(last_cf + DICE_COOLDOWN) - datetime.now()).split('.')[0]
            await try_send(ctx, content=f"{ICON_LOADING} Bạn cần chờ: **{time_left}** trước khi chơi tiếp.")
            return

        view = CoinflipBetView(ctx, self, bet, choice)
        earned_balance = local_data["local_balance"]["earned"]
        adadd_balance = local_data["local_balance"]["adadd"]

        if earned_balance < bet:
            view.children[0].disabled = True
        if adadd_balance < bet:
            view.children[1].disabled = True

        if all(btn.disabled for btn in view.children):
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không đủ tiền để cược **{bet:,}** trong cả hai ví.")
            return

        msg = await try_send(ctx, content=f"🎲 Bạn chọn **{choice.upper()}** và cược **{bet:,}**.\nChọn loại tiền:", view=view)
        if msg:
            view.message = msg

    async def play_coinflip_game(self, view: CoinflipBetView, interaction: nextcord.Interaction, payment_type: str):
        ctx = view.ctx
        bet = view.bet
        choice_input = view.choice

        economy_data = load_economy_data()
        global_profile = get_or_create_global_user_profile(economy_data, ctx.author.id)

        # --- Kiểm tra Last Active Guild ---
        guild_id = ctx.guild.id
        if global_profile.get("last_active_guild_id") != guild_id:
            await handle_travel_event(ctx, self.bot)
            logger.info(f"User {ctx.author.id} has 'traveled' to guild {guild_id}.")
        global_profile["last_active_guild_id"] = guild_id

        local_data = get_or_create_user_local_data(global_profile, guild_id)

        local_data["local_balance"][payment_type] -= bet

        if payment_type == "adadd":
            wanted_level = global_profile.get("wanted_level", 0.0)
            catch_chance = min(0.9, BASE_CATCH_CHANCE + wanted_level * WANTED_LEVEL_CATCH_MULTIPLIER)
            if random.random() < catch_chance:
                fine_amount = min(local_data["local_balance"]["earned"], int(bet * 0.5))
                local_data["local_balance"]["earned"] -= fine_amount
                global_profile["wanted_level"] += 0.1
                save_economy_data(economy_data)
                await view.message.edit(content=f"🚨 **BỊ BẮT!** Bạn bị phạt **{fine_amount:,}** vì dùng `Ecobit` để cá cược!", view=None)
                return

        global_profile.setdefault("cooldowns", {})["coinflip"] = datetime.now().timestamp()
        player_choice = "heads" if choice_input.lower() in ['heads', 'ngửa', 'h', 'n'] else "tails"
        result = random.choice(['heads', 'tails'])

        result_icon = ICON_COINFLIP_HEADS if result == "heads" else ICON_COINFLIP_TAILS
        header_msg = f"🪙 Đồng xu được tung... Kết quả là {result_icon} **{result.capitalize()}**!\n"
        winnings = 0

        if player_choice == result:
            winnings = bet * 2
            local_data["local_balance"]["earned"] += winnings
            result_msg = f"🎉 Bạn đoán đúng! Nhận được **{winnings:,}** {ICON_ECOIN}!"
        else:
            result_msg = "😭 Bạn đoán sai, chúc may mắn lần sau!"

        save_economy_data(economy_data)
        new_total = local_data["local_balance"]["earned"] + local_data["local_balance"]["adadd"]

        await view.message.edit(content=f"{header_msg}{result_msg}\nVí Local hiện tại: **{new_total:,}** {ICON_MONEY_BAG}", view=None)

def setup(bot: commands.Bot):
    bot.add_cog(CoinflipCommandCog(bot))
