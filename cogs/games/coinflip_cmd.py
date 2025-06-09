# bot/cogs/games/coinflip_cmd.py
import nextcord
from nextcord.ext import commands
import random
import logging
from datetime import datetime

from core.utils import try_send, require_travel_check
from core.config import CF_COOLDOWN, BASE_CATCH_CHANCE, WANTED_LEVEL_CATCH_MULTIPLIER
from core.icons import (
    ICON_LOADING, ICON_ERROR, ICON_MONEY_BAG, ICON_ECOIN, ICON_ECOBIT,
    ICON_WARNING, ICON_COINFLIP_HEADS, ICON_COINFLIP_TAILS
)

logger = logging.getLogger(__name__)

class CoinflipBetView(nextcord.ui.View):
    # Class View không thay đổi
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
        await self.game_cog.play_coinflip_game(self, interaction, "local_balance_earned")

    @nextcord.ui.button(label="Cược bằng 🧪Ecobit (Rủi ro)", style=nextcord.ButtonStyle.red, custom_id="bet_ecobit")
    async def bet_with_ecobit(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.defer()
        await self.game_cog.play_coinflip_game(self, interaction, "local_balance_adadd")


class CoinflipCommandCog(commands.Cog, name="Coinflip Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("CoinflipCommandCog (SQLite Ready) initialized.")

    @commands.command(name='coinflip', aliases=['cf'])
    @commands.guild_only()
    @require_travel_check
    async def coinflip(self, ctx: commands.Context, bet: int, choice: str):
        if bet <= 0:
            await try_send(ctx, content=f"{ICON_ERROR} Tiền cược phải lớn hơn 0!")
            return

        valid_choices = ['heads', 'tails', 'ngửa', 'sấp', 'h', 't', 'n', 's']
        if choice.lower() not in valid_choices:
            await try_send(ctx, content=f"{ICON_ERROR} Lựa chọn không hợp lệ. Hãy chọn `heads` hoặc `tails` (ngửa/sấp).")
            return

        now = datetime.now().timestamp()
        last_cf = self.bot.db.get_cooldown(ctx.author.id, "coinflip")
        if now - last_cf < CF_COOLDOWN:
            time_left = str(datetime.fromtimestamp(last_cf + CF_COOLDOWN) - datetime.now()).split('.')[0]
            await try_send(ctx, content=f"{ICON_LOADING} Bạn cần chờ: **{time_left}** trước khi chơi tiếp.")
            return

        local_data = self.bot.db.get_or_create_user_local_data(ctx.author.id, ctx.guild.id)
        view = CoinflipBetView(ctx, self, bet, choice)
        
        view.children[0].disabled = local_data['local_balance_earned'] < bet
        view.children[1].disabled = local_data['local_balance_adadd'] < bet

        if all(btn.disabled for btn in view.children):
            await try_send(ctx, content=f"{ICON_ERROR} Bạn không đủ tiền để cược **{bet:,}** trong cả hai ví.")
            return

        msg = await try_send(ctx, content=f"🎲 Bạn chọn **{choice.upper()}** và cược **{bet:,}**.\nChọn loại tiền:", view=view)
        if msg:
            view.message = msg

    async def play_coinflip_game(self, view: CoinflipBetView, interaction: nextcord.Interaction, balance_type: str):
        ctx = view.ctx
        author_id = ctx.author.id
        guild_id = ctx.guild.id
        bet = view.bet
        choice_input = view.choice

        global_profile = self.bot.db.get_or_create_global_user_profile(author_id)
        local_data = self.bot.db.get_or_create_user_local_data(author_id, guild_id)
        
        # Trừ tiền cược
        self.bot.db.update_balance(author_id, guild_id, balance_type, local_data[balance_type] - bet)
        
        if balance_type == "local_balance_adadd":
            wanted_level = global_profile['wanted_level']
            catch_chance = min(0.9, BASE_CATCH_CHANCE + wanted_level * WANTED_LEVEL_CATCH_MULTIPLIER)
            if random.random() < catch_chance:
                fine_amount = min(local_data["local_balance_earned"], int(bet * 0.5))
                self.bot.db.update_balance(author_id, guild_id, 'local_balance_earned', local_data['local_balance_earned'] - fine_amount)
                self.bot.db.update_wanted_level(author_id, wanted_level + 0.1)
                await view.message.edit(content=f"🚨 **BỊ BẮT!** Bạn bị phạt **{fine_amount:,}** vì dùng `Ecobit` để cá cược!", view=None)
                return

        self.bot.db.set_cooldown(author_id, "coinflip", datetime.now().timestamp())
        player_choice = "heads" if choice_input.lower() in ['heads', 'ngửa', 'h', 'n'] else "tails"
        result = random.choice(['heads', 'tails'])

        result_icon = ICON_COINFLIP_HEADS if result == "heads" else ICON_COINFLIP_TAILS
        header_msg = f"🪙 Đồng xu được tung... Kết quả là {result_icon} **{result.capitalize()}**!\n"
        
        if player_choice == result:
            winnings = bet * 2
            current_balance = self.bot.db.get_or_create_user_local_data(author_id, guild_id)[balance_type]
            self.bot.db.update_balance(author_id, guild_id, balance_type, current_balance + winnings)
            winnings_icon = ICON_ECOBIT if balance_type == "local_balance_adadd" else ICON_ECOIN
            result_msg = f"🎉 Bạn đoán đúng! Nhận được **{winnings:,}** {winnings_icon}!"
        else:
            result_msg = "😭 Bạn đoán sai, chúc may mắn lần sau!"
        
        # Lấy lại dữ liệu cuối cùng để hiển thị
        final_local_data = self.bot.db.get_or_create_user_local_data(author_id, guild_id)
        new_total = final_local_data["local_balance_earned"] + final_local_data["local_balance_adadd"]
        await view.message.edit(content=f"{header_msg}{result_msg}\nVí Local hiện tại: **{new_total:,}** {ICON_MONEY_BAG}", view=None)

def setup(bot: commands.Bot):
    bot.add_cog(CoinflipCommandCog(bot))
