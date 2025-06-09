# bot/cogs/games/slots_cmd.py
import nextcord
from nextcord.ext import commands
import random
import logging
from datetime import datetime

from core.database import get_or_create_global_user_profile, get_or_create_user_local_data
from core.utils import try_send, require_travel_check
from core.config import SLOTS_COOLDOWN, SLOTS_EMOJIS, BASE_CATCH_CHANCE, WANTED_LEVEL_CATCH_MULTIPLIER
from core.icons import (
    ICON_LOADING, ICON_ERROR, ICON_SLOTS, ICON_MONEY_BAG, 
    ICON_ECOIN, ICON_ECOBIT, ICON_WARNING
)

logger = logging.getLogger(__name__)

class BetConfirmationView(nextcord.ui.View):
    # ... (Giữ nguyên không thay đổi)
    def __init__(self, ctx, game_cog_instance, bet_amount):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.game_cog = game_cog_instance
        self.bet = bet_amount
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
        await self.game_cog.play_slots_game(self, interaction, "earned")

    @nextcord.ui.button(label="Cược bằng 🧪Ecobit (Rủi ro)", style=nextcord.ButtonStyle.red, custom_id="bet_ecobit")
    async def bet_with_ecobit(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.defer()
        await self.game_cog.play_slots_game(self, interaction, "adadd")

class SlotsCommandCog(commands.Cog, name="Slots Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("SlotsCommandCog (v6 - Refactored & Patched) initialized.")

    @commands.command(name='slots', aliases=['sl'])
    @commands.guild_only()
    @require_travel_check
    async def slots(self, ctx: commands.Context, bet: int):
        """Quay máy xèng để thử vận may."""
        if bet <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Tiền cược phải lớn hơn 0!")
            return

        # [SỬA] Sử dụng cache
        economy_data = self.bot.economy_data
        global_profile = get_or_create_global_user_profile(economy_data, ctx.author.id)
        local_data = get_or_create_user_local_data(global_profile, ctx.guild.id)

        now = datetime.now().timestamp()
        last_slots = global_profile.get("cooldowns", {}).get("slots", 0)
        if now - last_slots < SLOTS_COOLDOWN:
            time_left = str(datetime.fromtimestamp(last_slots + SLOTS_COOLDOWN) - datetime.now()).split('.')[0]
            await try_send(ctx, content=f"{ICON_LOADING} Chơi chậm thôi! Chờ: **{time_left}**.")
            return

        view = BetConfirmationView(ctx, self, bet)
        earned_balance = local_data["local_balance"]["earned"]
        adadd_balance = local_data["local_balance"]["adadd"]

        view.children[0].disabled = earned_balance < bet
        view.children[1].disabled = adadd_balance < bet

        if view.children[0].disabled and view.children[1].disabled:
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ tiền trong bất kỳ ví nào để đặt cược **{bet:,}**.")
            return

        msg = await try_send(ctx, content=f"Bạn muốn đặt cược **{bet:,}** cho ván **Slots** bằng nguồn tiền nào?", view=view)
        if msg:
            view.message = msg

    async def play_slots_game(self, view: BetConfirmationView, interaction: nextcord.Interaction, payment_type: str):
        ctx = view.ctx
        bet = view.bet

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
                global_profile["wanted_level"] = global_profile.get("wanted_level", 0.0) + 0.1
                logger.warning(f"User {ctx.author.id} bị bắt khi cược {bet} bằng Ecobit.")
                await view.message.edit(content=f"🚨 **BỊ BẮT!** Cảnh sát phát hiện bạn dùng `🧪Ecobit` để cờ bạc! Bạn bị phạt **{fine_amount:,}** `🪙Ecoin`.", view=None)
                return

        global_profile.setdefault("cooldowns", {})["slots"] = datetime.now().timestamp()
        
        rolls = [random.choice(SLOTS_EMOJIS) for _ in range(3)]
        header_msg = f"{ICON_SLOTS} Máy xèng quay: **[{' | '.join(rolls)}]** {ICON_SLOTS}\n"
        winnings = 0

        if rolls[0] == rolls[1] == rolls[2]:
            winnings = bet * 10
        elif rolls[0] == rolls[1] or rolls[1] == rolls[2]:
            winnings = bet * 2
        
        if winnings > 0:
            # [SỬA LỖI] Tiền thắng được trả về đúng loại ví đã cược
            winnings_destination = payment_type
            winnings_icon = ICON_ECOBIT if winnings_destination == "adadd" else ICON_ECOIN
            local_data["local_balance"][winnings_destination] += winnings
            final_msg = f"🎉 Chúc mừng! Bạn thắng và nhận được **{winnings:,}** {winnings_icon}!"
        else:
            final_msg = "😭 Tiếc quá, bạn thua rồi!"
        
        new_total_balance = local_data["local_balance"]["earned"] + local_data["local_balance"]["adadd"]
        await view.message.edit(content=f"{header_msg}{final_msg}\nVí Local của bạn giờ là: **{new_total_balance:,}** {ICON_MONEY_BAG}", view=None)

def setup(bot: commands.Bot):
    bot.add_cog(SlotsCommandCog(bot))
