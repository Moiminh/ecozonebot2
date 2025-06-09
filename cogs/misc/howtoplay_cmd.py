# bot/cogs/misc/howtoplay_cmd.py
import nextcord
from nextcord.ext import commands
import logging

from core.config import COMMAND_PREFIX
from core.icons import * # Import tất cả icon

logger = logging.getLogger(__name__)

# --- View phân trang cho sách hướng dẫn ---
class HowToPlayPaginator(nextcord.ui.View):
    def __init__(self, pages: list, interaction: nextcord.Interaction):
        super().__init__(timeout=300)
        self.pages = pages
        self.current_page = 0
        self.interaction_user = interaction.user
        self.update_buttons()

    async def interaction_check(self, interaction: nextcord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("Đây không phải sách hướng dẫn của bạn!", ephemeral=True)
            return False
        return True

    def update_buttons(self):
        # Nút trang trước
        self.children[0].disabled = self.current_page == 0
        # Nút trang sau
        self.children[1].disabled = self.current_page == len(self.pages) - 1
        # Cập nhật label của nút trang hiện tại
        self.children[2].label = f"Trang {self.current_page + 1}/{len(self.pages)}"

    @nextcord.ui.button(label="Trang trước", style=nextcord.ButtonStyle.secondary, custom_id="prev_page")
    async def prev_page(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)
        
    @nextcord.ui.button(label="Trang sau", style=nextcord.ButtonStyle.primary, custom_id="next_page")
    async def next_page(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    # Nút ở giữa để hiển thị trang hiện tại, không có chức năng khi bấm
    @nextcord.ui.button(label="Trang X/Y", style=nextcord.ButtonStyle.grey, disabled=True)
    async def page_indicator(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        pass


class HowToPlayCommandCog(commands.Cog, name="HowToPlay Command"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("HowToPlayCommandCog initialized.")

    @nextcord.slash_command(name="howtoplay", description="Sách hướng dẫn toàn diện về thế giới EconZone.")
    async def howtoplay(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)

        pages = self.create_help_pages()
        view = HowToPlayPaginator(pages, interaction)
        
        await interaction.followup.send(embed=pages[0], view=view, ephemeral=True)

   def create_help_pages(self):
    pages = []

    # Trang 1: Những điều Cơ bản
    p1 = nextcord.Embed(title="📖 Hướng dẫn EconZone - Trang 1: Những điều Cơ bản", color=nextcord.Color.green())
    p1.add_field(name=f"{ICON_ECOIN} Ecoin (Tiền Sạch)", value="Loại tiền tệ chính, kiếm được từ các hoạt động hợp pháp như `!work`, `!daily`. Dùng để mua bán và gửi vào Bank.", inline=False)
    p1.add_field(name=f"{ICON_ECOBIT} Ecobit (Tiền Lậu)", value="Loại tiền đặc biệt, nhận từ admin hoặc các event phi pháp. Dùng Ecobit luôn đi kèm rủi ro!", inline=False)
    p1.add_field(name=f"{ICON_BANK_MAIN} Bank Trung tâm", value="Là tài khoản tiết kiệm toàn cục của bạn. Dùng `!deposit` để gửi `Ecoin` vào đây.", inline=False)
    p1.add_field(name="✨ Level & XP", value="Thực hiện các hoạt động kiếm Ecoin sẽ cho bạn XP. Lên cấp để mở khóa các tính năng và quyền lợi mới.", inline=False)
    pages.append(p1)

    # Trang 2: Hệ thống Visa
    p2 = nextcord.Embed(title="📖 Hướng dẫn EconZone - Trang 2: Hệ thống Visa", color=nextcord.Color.blue())
    p2.add_field(name=f"{ICON_ECOBANK} Ecobank (Visa Nội địa)", value="Là thẻ thanh toán an toàn trong server gốc. Mua và nạp tiền bằng lệnh `!visa`.", inline=False)
    p2.add_field(name=f"{ICON_ECOVISA} Ecovisa (Visa Quốc tế)", value="Là thẻ thanh toán liên server. Khi dùng ở server khác, bạn sẽ bị tính phí chênh lệch dựa trên cấp độ server.", inline=False)
    p2.add_field(name="Nâng cấp", value=f"Bạn có thể dùng lệnh `!visa upgrade` để nâng cấp Ecobank thành Ecovisa (mất phí).", inline=False)
    pages.append(p2)

    # Trang 3: Thế giới Ngầm
    p3 = nextcord.Embed(title="📖 Hướng dẫn EconZone - Trang 3: Thế giới Ngầm", color=nextcord.Color.red())
    p3.add_field(name="🕵️ Điểm Nghi ngờ (Wanted Level)", value="Tăng lên khi bạn thực hiện các hành vi phi pháp. Càng cao, rủi ro bị cảnh sát phát hiện càng lớn.", inline=False)
    p3.add_field(name="💸 Rửa tiền (!launder)", value="Cách duy nhất để biến `Ecobit` thành tiền Bank, nhưng với tỉ giá cực tệ và rủi ro bị bắt rất cao.", inline=False)
    p3.add_field(name="🛍️ Vật phẩm bẩn/ngoại lai", value="Vật phẩm mua bằng `Ecobit` hoặc mang từ server khác về sẽ có giá trị bán lại rất thấp.", inline=False)
    pages.append(p3)

    # Trang 4: Hệ thống Sinh tồn
    p4 = nextcord.Embed(title="📖 Hướng dẫn EconZone - Trang 4: Sinh tồn", color=nextcord.Color.orange())
    p4.add_field(name="❤️ Máu, 🍔 Độ no, ⚡ Năng lượng", value="Các chỉ số này sẽ giảm dần theo thời gian. Các hành động như `!work`, `!crime` sẽ tiêu tốn chúng.", inline=False)
    p4.add_field(name="Hồi phục", value=f"Mua các vật phẩm như 'bánh mì', 'nước tăng lực' từ `!shop` và dùng lệnh `!use` để hồi phục các chỉ số.", inline=False)
    pages.append(p4)

    # Trang 5: Các Vai trò Đặc biệt
    p5 = nextcord.Embed(title="📖 Hướng dẫn EconZone - Trang 5: Các Vai trò Đặc biệt", color=nextcord.Color.purple())
    p5.add_field(name="🕴️ Mafia", value="Tự động nhận được khi có nhiều `Ecobit` hoặc `wanted_level` cao. Có thể truy cập Chợ Đen.", inline=False)
    p5.add_field(name="👮 Cảnh sát", value="Là một nghề nghiệp cần đăng ký (`!apply police`). Có khả năng điều tra và bắt giữ tội phạm.", inline=False)
    p5.add_field(name="⚕️ Bác sĩ", value="Là một nghề nghiệp cần đăng ký (`!apply doctor`). Có khả năng chữa trị cho người chơi khác.", inline=False)
    pages.append(p5)

    # Trang 6: Cờ bạc & Giải trí
    p6 = nextcord.Embed(title="📖 Hướng dẫn EconZone - Trang 6: Cờ bạc & Giải trí", color=nextcord.Color.gold())
    p6.add_field(name="🎰 Slots", value="Thử vận may của bạn bằng lệnh `!slots` để quay máy xèng.", inline=False)
    p6.add_field(name="🎲 Dice", value="Lệnh `!dice` cho phép bạn đặt cược và tung xúc xắc.", inline=False)
    p6.add_field(name="🪙 Coinflip", value="Chơi tung đồng xu để cược tiền với người khác (`!coinflip`).", inline=False)
    pages.append(p6)

    # Trang 7: Du lịch & Toàn cầu
    p7 = nextcord.Embed(title="📖 Hướng dẫn EconZone - Trang 7: Du lịch & Toàn cầu", color=nextcord.Color.teal())
    p7.add_field(name=f"{ICON_BANK_MAIN} Bank", value="Hệ thống ngân hàng dùng để gửi và rút tiền khi đi du lịch.", inline=False)
    p7.add_field(name="💼 Balo", value="Đựng các vật phẩm quan trọng khi bạn di chuyển giữa các server.", inline=False)
    p7.add_field(name="🌍 Du lịch", value="Dùng lệnh `!travel` để tham gia các server khác và giao lưu, trao đổi hàng hóa.", inline=False)
    p7.add_field(name="💸 Transfer", value="Chuyển tiền cho người khác qua lệnh `!transfer` (áp dụng phí).", inline=False)
    pages.append(p7)

    # Trang 8: Kiếm tiền (mở rộng)
    p8 = nextcord.Embed(title="📖 Hướng dẫn EconZone - Trang 8: Kiếm tiền (Mở rộng)", color=nextcord.Color.green())
    p8.add_field(name="💼 Work", value="Lệnh `!work` giúp bạn kiếm tiền đều đặn mỗi ngày.", inline=False)
    p8.add_field(name="🎣 Fish", value="Thử câu cá để kiếm thêm Ecoin hoặc vật phẩm bằng lệnh `!fish`.", inline=False)
    p8.add_field(name="🔫 Rob", value="Dùng `!rob` để cướp tiền người khác, nhưng rủi ro khá cao.", inline=False)
    p8.add_field(name="🙏 Beg", value="Lệnh `!beg` để xin tiền từ cộng đồng, thu nhập ít nhưng dễ dàng.", inline=False)
    pages.append(p8)

    return pages


def setup(bot: commands.Bot):
    bot.add_cog(HowToPlayCommandCog(bot))
