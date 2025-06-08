# bot/cogs/games/dice_cmd.py
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
    ICON_LOADING, ICON_ERROR, ICON_DICE, ICON_MONEY_BAG, 
    ICON_ECOIN, ICON_ECOBIT, ICON_WARNING
)

logger = logging.getLogger(__name__)

class BetConfirmationView(nextcord.ui.View):
    def __init__(self, ctx, game_cog_instance, bet_amount, game_type):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.game_cog = game_cog_instance
        self.bet = bet_amount
        self.game = game_type
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
        if self.game == "dice":
            await self.game_cog.play_dice_game(self, interaction, "earned")

    @nextcord.ui.button(label="Cược bằng 🧪Ecobit (Rủi ro)", style=nextcord.ButtonStyle.red, custom_id="bet_ecobit")
    async def bet_with_ecobit(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.defer()
        if self.game == "dice":
            await self.game_cog.play_dice_game(self, interaction, "adadd")


class DiceCommandCog(commands.Cog, name="Dice Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("DiceCommandCog (v3 - Interactive) initialized.")

    @commands.command(name='dice', aliases=['roll'])
    async def dice(self, ctx: commands.Context, bet: int):
        """Chơi xúc xắc, tổng lớn hơn 7 thì thắng."""
        if not ctx.guild:
            await try_send(ctx, content=f"{ICON_ERROR} Lệnh này chỉ có thể sử dụng trong một server.")
            return

        if bet <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Tiền cược phải lớn hơn 0!")
            return

        economy_data = load_economy_data()
        global_profile = get_or_create_global_user_profile(economy_data, ctx.author.id)
        local_data = get_or_create_user_local_data(global_profile, ctx.guild.id)

        now = datetime.now().timestamp()
        last_dice = global_profile.get("cooldowns", {}).get("dice", 0)
        if now - last_dice < DICE_COOLDOWN:
            time_left = str(datetime.fromtimestamp(last_dice + DICE_COOLDOWN) - datetime.now()).split('.')[0]
            await try_send(ctx, content=f"{ICON_LOADING} Chơi chậm thôi! Chờ: **{time_left}**.")
            return

        view = BetConfirmationView(ctx, self, bet, "dice")
        earned_balance = local_data["local_balance"]["earned"]
        adadd_balance = local_data["local_balance"]["adadd"]

        if earned_balance < bet:
            view.children[0].disabled = True
        if adadd_balance < bet:
            view.children[1].disabled = True

        if view.children[0].disabled and view.children[1].disabled:
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ tiền trong bất kỳ ví nào để đặt cược **{bet:,}**.")
            return

        msg = await try_send(ctx, content=f"Bạn muốn đặt cược **{bet:,}** cho ván **Dice** bằng nguồn tiền nào?", view=view)
        if msg:
            view.message = msg

    async def play_dice_game(self, view: BetConfirmationView, interaction: nextcord.Interaction, payment_type: str):
        """Hàm xử lý logic cốt lõi của game Xúc xắc."""
        ctx = view.ctx
        bet = view.bet

        economy_data = load_economy_data()
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
                save_economy_data(economy_data)
                logger.warning(f"User {ctx.author.id} bị bắt khi cược {bet} bằng Ecobit.")
                await view.message.edit(content=f"🚨 **BỊ BẮT!** Cảnh sát phát hiện bạn dùng `🧪Ecobit` để cờ bạc! Bạn bị phạt **{fine_amount:,}** `🪙Ecoin`.", view=None)
                return

        global_profile["cooldowns"]["dice"] = datetime.now().timestamp()
        d1 = random.randint(1, 6)
        d2 = random.randint(1, 6)
        total_roll = d1 + d2

        dice_emojis = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}
        header_msg = f"{ICON_DICE} Bạn đổ ra: {dice_emojis[d1]} + {dice_emojis[d2]} = **{total_roll}**\n"
        winnings = 0

        if total_roll > 7:
            winnings = int(bet * 1.5)

        final_msg = ""
        if winnings > 0:
            local_data["local_balance"]["earned"] += winnings
            final_msg = f"🎉 Chúc mừng! Bạn thắng và nhận được **{winnings:,}** {ICON_ECOIN}!"
        else:
            final_msg = "😭 Tiếc quá, bạn thua rồi!"

        save_economy_data(economy_data)

        new_total_balance = local_data["local_balance"]["earned"] + local_data["local_balance"]["adadd"]
        await view.message.edit(content=f"{header_msg}{final_msg}\nVí Local của bạn giờ là: **{new_total_balance:,}** {ICON_MONEY_BAG}", view=None)

def setup(bot: commands.Bot):
    bot.add_cog(DiceCommandCog(bot))
