# bot/cogs/games/dice_cmd.py
import nextcord
from nextcord.ext import commands
import random
import logging
from datetime import datetime

from core.utils import try_send, require_travel_check
from core.config import DICE_COOLDOWN, BASE_CATCH_CHANCE, WANTED_LEVEL_CATCH_MULTIPLIER
from core.icons import ICON_LOADING, ICON_ERROR, ICON_DICE, ICON_MONEY_BAG, ICON_ECOIN, ICON_ECOBIT, ICON_WARNING

logger = logging.getLogger(__name__)

class BetConfirmationView(nextcord.ui.View):
    # Class View không thay đổi
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
        await self.game_cog.play_dice_game(self, interaction, "local_balance_earned")

    @nextcord.ui.button(label="Cược bằng 🧪Ecobit (Rủi ro)", style=nextcord.ButtonStyle.red, custom_id="bet_ecobit")
    async def bet_with_ecobit(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.defer()
        await self.game_cog.play_dice_game(self, interaction, "local_balance_adadd")

class DiceCommandCog(commands.Cog, name="Dice Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("DiceCommandCog (SQLite Ready) initialized.")

    @commands.command(name='dice', aliases=['roll'])
    @commands.guild_only()
    @require_travel_check
    async def dice(self, ctx: commands.Context, bet: int):
        if bet <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Tiền cược phải lớn hơn 0!")
            return

        now = datetime.now().timestamp()
        last_dice = self.bot.db.get_cooldown(ctx.author.id, "dice")
        if now - last_dice < DICE_COOLDOWN:
            time_left = str(datetime.fromtimestamp(last_dice + DICE_COOLDOWN) - datetime.now()).split('.')[0]
            await try_send(ctx, content=f"{ICON_LOADING} Chơi chậm thôi! Chờ: **{time_left}**.")
            return

        local_data = self.bot.db.get_or_create_user_local_data(ctx.author.id, ctx.guild.id)
        view = BetConfirmationView(ctx, self, bet)
        view.children[0].disabled = local_data['local_balance_earned'] < bet
        view.children[1].disabled = local_data['local_balance_adadd'] < bet

        if view.children[0].disabled and view.children[1].disabled:
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không có đủ tiền trong bất kỳ ví nào để đặt cược **{bet:,}**.")
            return

        msg = await try_send(ctx, content=f"Bạn muốn đặt cược **{bet:,}** cho ván **Dice** bằng nguồn tiền nào?", view=view)
        if msg:
            view.message = msg

    async def play_dice_game(self, view: BetConfirmationView, interaction: nextcord.Interaction, balance_type: str):
        ctx = view.ctx
        author_id = ctx.author.id
        guild_id = ctx.guild.id
        bet = view.bet

        global_profile = self.bot.db.get_or_create_global_user_profile(author_id)
        local_data = self.bot.db.get_or_create_user_local_data(author_id, guild_id)

        self.bot.db.update_balance(author_id, guild_id, balance_type, local_data[balance_type] - bet)
        
        if balance_type == "local_balance_adadd":
            wanted_level = global_profile['wanted_level']
            catch_chance = min(0.9, BASE_CATCH_CHANCE + wanted_level * WANTED_LEVEL_CATCH_MULTIPLIER)
            if random.random() < catch_chance:
                fine_amount = min(local_data["local_balance_earned"], int(bet * 0.5))
                self.bot.db.update_balance(author_id, guild_id, 'local_balance_earned', local_data['local_balance_earned'] - fine_amount)
                self.bot.db.update_wanted_level(author_id, wanted_level + 0.1)
                await view.message.edit(content=f"🚨 **BỊ BẮT!** Cảnh sát phát hiện bạn dùng `🧪Ecobit` để cờ bạc! Bạn bị phạt **{fine_amount:,}** `🪙Ecoin`.", view=None)
                return

        self.bot.db.set_cooldown(author_id, "dice", datetime.now().timestamp())
        
        d1 = random.randint(1, 6)
        d2 = random.randint(1, 6)
        total_roll = d1 + d2

        dice_emojis = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}
        header_msg = f"{ICON_DICE} Bạn đổ ra: {dice_emojis[d1]} + {dice_emojis[d2]} = **{total_roll}**\n"
        winnings = 0

        if total_roll > 7:
            winnings = int(bet * 1.5)

        if winnings > 0:
            current_balance = self.bot.db.get_or_create_user_local_data(author_id, guild_id)[balance_type]
            self.bot.db.update_balance(author_id, guild_id, balance_type, current_balance + winnings)
            winnings_icon = ICON_ECOBIT if balance_type == "local_balance_adadd" else ICON_ECOIN
            final_msg = f"🎉 Chúc mừng! Bạn thắng và nhận được **{winnings:,}** {winnings_icon}!"
        else:
            final_msg = "😭 Tiếc quá, bạn thua rồi!"

        final_local_data = self.bot.db.get_or_create_user_local_data(author_id, guild_id)
        new_total_balance = final_local_data["local_balance_earned"] + final_local_data["local_balance_adadd"]
        await view.message.edit(content=f"{header_msg}{final_msg}\nVí Local của bạn giờ là: **{new_total_balance:,}** {ICON_MONEY_BAG}", view=None)

def setup(bot: commands.Bot):
    bot.add_cog(DiceCommandCog(bot))
