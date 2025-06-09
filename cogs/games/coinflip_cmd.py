# bot/cogs/games/coinflip_cmd.py
import nextcord
from nextcord.ext import commands
import random
import logging
from datetime import datetime

from core.database import get_or_create_global_user_profile, get_or_create_user_local_data
from core.utils import try_send, require_travel_check
from core.config import CF_COOLDOWN, BASE_CATCH_CHANCE, WANTED_LEVEL_CATCH_MULTIPLIER
from core.icons import (
    ICON_LOADING, ICON_ERROR, ICON_MONEY_BAG, ICON_ECOIN, ICON_ECOBIT,
    ICON_WARNING, ICON_COINFLIP_HEADS, ICON_COINFLIP_TAILS
)

logger = logging.getLogger(__name__)

class CoinflipBetView(nextcord.ui.View):
    # ... (Giữ nguyên không thay đổi)
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
        logger.info("CoinflipCommandCog (v5 - Refactored & Patched) initialized.")

    @commands.command(name='coinflip', aliases=['cf'])
    @commands.guild_only()
    @require_travel_check
    async def coinflip(self, ctx: commands.Context, bet: int, choice: str):
        """Tung đồng xu, chọn mặt (heads/tails hoặc ngửa/sấp) và đặt cược."""
        if bet <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Tiền cược phải lớn hơn 0!")
            return

        valid_choices = ['heads', 'tails', 'ngửa', 'sấp', 'h', 't', 'n', 's']
        if choice.lower() not in valid_choices:
            await try_send(ctx, content=f"{ICON_ERROR} Lựa chọn không hợp lệ. Hãy chọn `heads` hoặc `tails` (ngửa/sấp).")
            return

        # [SỬA] Sử dụng cache
        economy_data = self.bot.economy_data
        global_profile = get_or_create_global_user_profile(economy_data, ctx.author.id)
        local_data = get_or_create_user_local_data(global_profile, ctx.guild.id)

        now = datetime.now().timestamp()
        last_cf = global_profile.get("cooldowns", {}).get("coinflip", 0)
        if now - last_cf < CF_COOLDOWN:
            time_left = str(datetime.fromtimestamp(last_cf + CF_COOLDOWN) - datetime.now()).split('.')[0]
            await try_send(ctx, content=f"{ICON_LOADING} Bạn cần chờ: **{time_left}** trước khi chơi tiếp.")
            return

        view = CoinflipBetView(ctx, self, bet, choice)
        earned_balance = local_data["local_balance"]["earned"]
        adadd_balance = local_data["local_balance"]["adadd"]

        view.children[0].disabled = earned_balance < bet
        view.children[1].disabled = adadd_balance < bet

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

        economy_data = self.bot.economy_data
        global_profile = get_or_create_global_user_profile(economy_data, ctx.author.id)
        local_data = get_or_create_user_local_data(global_profile, ctx.guild.id)

        local_data["local_balance"][payment_type] -= bet

        if payment_type == "adadd":
            wanted_level = global_profile.get("wanted_level", 0.0)
            catch_chance = min(0.9, BASE_CATCH_CHANCE + wanted_level * WANTED_LEVEL_CATCH_MULTIPLIER)
            if random.random() < catch_chance:
                fine_amount = min(local_data["local_balance"]["earned"], int(bet * 0.5))
                local_data["local_balance"]["earned"] -= fine_amount
                global_profile["wanted_level"] += 0.1
                await view.message.edit(content=f"🚨 **BỊ BẮT!** Bạn bị phạt **{fine_amount:,}** vì dùng `Ecobit` để cá cược!", view=None)
                return

        global_profile.setdefault("cooldowns", {})["coinflip"] = datetime.now().timestamp()
        player_choice = "heads" if choice_input.lower() in ['heads', 'ngửa', 'h', 'n'] else "tails"
        result = random.choice(['heads', 'tails'])

        result_icon = ICON_COINFLIP_HEADS if result == "heads" else ICON_COINFLIP_TAILS
        header_msg = f"🪙 Đồng xu được tung... Kết quả là {result_icon} **{result.capitalize()}**!\n"
        
        if player_choice == result:
            winnings = bet * 2
            # [SỬA LỖI] Tiền thắng được trả về đúng loại ví đã cược
            winnings_destination = payment_type
            winnings_icon = ICON_ECOBIT if winnings_destination == "adadd" else ICON_ECOIN
            local_data["local_balance"][winnings_destination] += winnings
            result_msg = f"🎉 Bạn đoán đúng! Nhận được **{winnings:,}** {winnings_icon}!"
        else:
            result_msg = "😭 Bạn đoán sai, chúc may mắn lần sau!"

        new_total = local_data["local_balance"]["earned"] + local_data["local_balance"]["adadd"]
        await view.message.edit(content=f"{header_msg}{result_msg}\nVí Local hiện tại: **{new_total:,}** {ICON_MONEY_BAG}", view=None)

def setup(bot: commands.Bot):
    bot.add_cog(CoinflipCommandCog(bot))
