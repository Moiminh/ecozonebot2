# bot/cogs/misc/howtoplay_cmd.py
import nextcord
from nextcord.ext import commands
import logging

from core.utils import try_send
from core.icons import (ICON_INFO, ICON_BOOK, ICON_MONEY_BAG, ICON_BANK_MAIN, ICON_ECOBIT,
                        ICON_LEVEL_UP, ICON_XP, ICON_WORK, ICON_DAILY, ICON_CRIME, ICON_ROB,
                        ICON_FISH, ICON_BEG, ICON_SLOTS, ICON_DICE, ICON_COIN_FLIP,
                        ICON_HEALTH, ICON_HUNGER, ICON_ENERGY, ICON_SHOP, ICON_USE,
                        ICON_INVENTORY, ICON_TRAVEL, ICON_BACKPACK, ICON_TRANSFER,
                        ICON_ECOVISA, ICON_WANTED, ICON_LAUNDER, ICON_TAINTED, ICON_POLICE_CAR,
                        ICON_MAFIA, ICON_DOCTOR)

logger = logging.getLogger(__name__)

# --- View cho Paginator ---
class HowToPlayView(nextcord.ui.View):
    def __init__(self, pages, author):
        super().__init__(timeout=300)
        self.pages = pages
        self.current_page = 0
        self.author = author
        self.update_buttons()

    async def interaction_check(self, interaction: nextcord.Interaction) -> bool:
        return interaction.user == self.author

    def update_buttons(self):
        self.children[0].disabled = self.current_page == 0
        self.children[1].disabled = self.current_page == len(self.pages) - 1
        for child in self.children:
            if isinstance(child, nextcord.ui.Button):
                child.style = nextcord.ButtonStyle.primary if not child.disabled else nextcord.ButtonStyle.secondary

    @nextcord.ui.button(label="⬅️ Trước", style=nextcord.ButtonStyle.primary)
    async def prev_button(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @nextcord.ui.button(label="Sau ➡️", style=nextcord.ButtonStyle.primary)
    async def next_button(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)


# --- Cog chính ---
class HowToPlayCommandCog(commands.Cog, name="HowToPlay Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.pages = self.create_help_pages()
        logger.info("HowToPlayCommandCog (v2 - Refactored) initialized.")

    def create_help_pages(self):
        pages = []
        
        # Trang 1: Những điều Cơ bản
        embed1 = nextcord.Embed(
            title=f"{ICON_BOOK} Sách Hướng Dẫn EconZone - Trang 1/7",
            description="Chào mừng đến với thế giới EconZone! Dưới đây là những khái niệm cơ bản nhất.",
            color=nextcord.Color.green()
        )
        embed1.add_field(name=f"{ICON_MONEY_BAG} Tiền Sạch (Ecoin)", value="Đơn vị tiền tệ chính, dùng để mua bán hợp pháp. Có thể kiếm từ `!work`, `!daily` và các hoạt động lương thiện khác. Nằm trong **Ví Local**.", inline=False)
        embed1.add_field(name=f"{ICON_ECOBIT} Tiền Lậu (Ecobit)", value="Tiền từ các hoạt động phi pháp. Cần được 'rửa' để sử dụng. Cũng nằm trong **Ví Local**.", inline=False)
        embed1.add_field(name=f"{ICON_BANK_MAIN} Bank (Ngân hàng)", value="Ví tiền toàn cầu, an toàn và không bị ảnh hưởng khi bạn di chuyển giữa các server. Dùng để giao dịch lớn và mua Visa.", inline=False)
        embed1.add_field(name=f"{ICON_LEVEL_UP} Level & {ICON_XP} XP", value="Thực hiện các lệnh sẽ cho bạn XP. Đủ XP sẽ giúp bạn lên Level, mở khóa các tính năng và danh hiệu mới.", inline=False)
        pages.append(embed1)

        # Trang 2: Kiếm tiền & Làm giàu
        embed2 = nextcord.Embed(title=f"{ICON_BOOK} Hướng Dẫn - Trang 2/7: Kiếm Tiền", color=nextcord.Color.gold())
        embed2.add_field(name=f"{ICON_WORK} `!work`", value="Công việc ổn định, kiếm Ecoin đều đặn.", inline=False)
        embed2.add_field(name=f"{ICON_DAILY} `!daily`", value="Nhận thưởng Ecoin miễn phí mỗi 24 giờ.", inline=False)
        embed2.add_field(name=f"{ICON_FISH} `!fish`", value="Câu cá để kiếm vật phẩm bán lấy Ecoin.", inline=False)
        embed2.add_field(name=f"{ICON_CRIME} `!crime`", value="Thực hiện phi vụ nhỏ để kiếm Ecobit, có rủi ro.", inline=False)
        embed2.add_field(name=f"{ICON_ROB} `!rob <@user>`", value="Cướp tiền từ người khác, rủi ro bị bắt rất cao.", inline=False)
        embed2.add_field(name=f"{ICON_BEG} `!beg`", value="Xin tiền, có thể nhận được một ít Ecoin.", inline=False)
        pages.append(embed2)

        # Trang 3: Cờ bạc & Giải trí
        embed3 = nextcord.Embed(title=f"{ICON_BOOK} Hướng Dẫn - Trang 3/7: Cờ Bạc", color=nextcord.Color.orange())
        embed3.set_footer(text="Cờ bạc có thể giúp bạn giàu nhanh nhưng cũng dễ khiến bạn phá sản!")
        embed3.add_field(name=f"{ICON_COIN_FLIP} `!coinflip`", value="Tung đồng xu, 50/50. Cược Ecoin hoặc Ecobit.", inline=False)
        embed3.add_field(name=f"{ICON_DICE} `!dice`", value="Đổ xúc xắc, đoán kết quả để nhận thưởng lớn.", inline=False)
        embed3.add_field(name=f"{ICON_SLOTS} `!slots`", value="Chơi máy đánh bạc, cơ hội trúng Jackpot cực lớn.", inline=False)
        pages.append(embed3)

        # Trang 4: Sinh tồn & Vật phẩm
        embed4 = nextcord.Embed(title=f"{ICON_BOOK} Hướng Dẫn - Trang 4/7: Sinh Tồn", color=nextcord.Color.red())
        embed4.add_field(name=f"{ICON_HEALTH} Máu, {ICON_HUNGER} Độ no, {ICON_ENERGY} Năng lượng", value="Các chỉ số này sẽ giảm dần theo thời gian và khi bạn hoạt động. Nếu về 0, bạn sẽ gặp bất lợi. Hãy ăn uống để hồi phục.", inline=False)
        embed4.add_field(name=f"{ICON_SHOP} `!shop`", value="Xem các vật phẩm đang được bán.", inline=False)
        embed4.add_field(name=f"{ICON_USE} `!use <item>`", value="Sử dụng vật phẩm (thức ăn, nước uống) để hồi phục chỉ số sinh tồn.", inline=False)
        embed4.add_field(name=f"{ICON_INVENTORY} `!inventory`", value="Kiểm tra túi đồ của bạn.", inline=False)
        pages.append(embed4)

        # Trang 5: Du lịch & Toàn cầu
        embed5 = nextcord.Embed(title=f"{ICON_BOOK} Hướng Dẫn - Trang 5/7: Du Lịch", color=nextcord.Color.blue())
        embed5.add_field(name=f"{ICON_TRAVEL} Du Lịch", value="Khi bạn chat ở một server mới, bạn sẽ 'du lịch' đến đó. Ví Local của bạn ở server cũ sẽ được đóng băng.", inline=False)
        embed5.add_field(name=f"{ICON_BACKPACK} Balo", value="Một số vật phẩm đặc biệt như 'Balo' giúp bạn mang một phần tài sản từ Ví Local cũ sang server mới.", inline=False)
        embed5.add_field(name=f"{ICON_ECOVISA} Hệ thống Visa", value="Mua các thẻ Visa để có một 'ngân hàng di động', giúp bạn truy cập và sử dụng tiền ở bất kỳ đâu.", inline=False)
        embed5.add_field(name=f"{ICON_TRANSFER} `!transfer <@user> <amount>`", value="Chuyển tiền từ Bank của bạn cho người chơi khác.", inline=False)
        pages.append(embed5)

        # Trang 6: Thế giới Ngầm
        embed6 = nextcord.Embed(title=f"{ICON_BOOK} Hướng Dẫn - Trang 6/7: Thế Giới Ngầm", color=nextcord.Color.purple())
        embed6.add_field(name=f"{ICON_WANTED} Điểm Nghi ngờ (Wanted Level)", value="Thực hiện các hành vi phi pháp sẽ làm tăng điểm này. Càng cao, bạn càng dễ bị cảnh sát chú ý và rủi ro khi làm việc xấu càng lớn.", inline=False)
        embed6.add_field(name=f"{ICON_LAUNDER} Rửa tiền (`!launder`)", value="Cách duy nhất để biến `Ecobit` thành tiền Bank, nhưng với tỉ giá cực tệ và rủi ro bị bắt rất cao.", inline=False)
        embed6.add_field(name=f"{ICON_TAINTED} Vật phẩm bẩn/ngoại lai", value="Vật phẩm mua bằng `Ecobit` hoặc mang từ server khác về sẽ có giá trị bán lại rất thấp và có thể làm tăng Điểm Nghi ngờ của bạn.", inline=False)
        pages.append(embed6)

        # Trang 7: Các Vai trò Đặc biệt
        embed7 = nextcord.Embed(title=f"{ICON_BOOK} Hướng Dẫn - Trang 7/7: Vai Trò", color=nextcord.Color.dark_grey())
        embed7.add_field(name=f"{ICON_MAFIA} Mafia", value="Có thể thực hiện các phi vụ lớn, bảo kê và có các特quyền trong thế giới ngầm.", inline=False)
        embed7.add_field(name=f"{ICON_POLICE_CAR} Cảnh sát", value="Thực thi pháp luật, bắt giữ tội phạm và nhận thưởng.", inline=False)
        embed7.add_field(name=f"{ICON_DOCTOR} Bác sĩ", value="Chữa trị cho những người bị thương, hồi phục chỉ số sinh tồn cho người khác.", inline=False)
        pages.append(embed7)

        return pages

    @nextcord.slash_command(name="howtoplay", description="Sách hướng dẫn toàn diện về thế giới EconZone.")
    async def howtoplay(self, interaction: nextcord.Interaction):
        """Hiển thị sách hướng dẫn chơi game."""
        await interaction.response.defer()
        
        initial_embed = self.pages[0]
        view = HowToPlayView(self.pages, interaction.user)
        
        await try_send(interaction, embed=initial_embed, view=view)

def setup(bot: commands.Bot):
    bot.add_cog(HowToPlayCommandCog(bot))
