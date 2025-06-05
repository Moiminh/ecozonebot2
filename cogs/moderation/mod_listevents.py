# bot/cogs/moderation/mod_listevents.py
import nextcord
from nextcord.ext import commands
from datetime import datetime, timedelta, timezone
import logging

# Import các thành phần cần thiết từ 'core'
from core.database import get_guild_config, save_guild_config
from core.utils import is_bot_moderator, try_send
from core.config import COMMAND_PREFIX # Để dùng trong help message nếu cần
from core.icons import ICON_SUCCESS, ICON_ERROR, ICON_INFO, ICON_ADMIN_PANEL

logger = logging.getLogger(__name__)

# Danh sách các loại sự kiện được hỗ trợ (có thể mở rộng sau)
SUPPORTED_EVENT_TYPES = {
    "work": "work",
    "fish": "fish",
    "daily": "daily",
    "crime": "crime",
    # Key: người dùng nhập, Value: key dùng trong JSON (thường là giống nhau)
}

class EventManagementCog(commands.Cog, name="Event Management"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info(f"{ICON_INFO} EventManagementCog initialized.")

    @commands.command(
        name="mod_startevent",
        aliases=["startevent", "event_start"],
        help="Bắt đầu hoặc cập nhật một sự kiện cho server được chỉ định.\n"
             "Ví dụ: `!mod_startevent <GuildID> work 0.5 1.2 24`\n"
             "Trong đó:\n"
             "- `<GuildID>`: ID của server.\n"
             "- `work`: Loại sự kiện (ví dụ: work, fish, daily).\n"
             "- `0.5`: Hệ số cooldown (0.5 = giảm 50%, 1.0 = không đổi).\n"
             "- `1.2`: Hệ số phần thưởng (1.2 = tăng 20%, 1.0 = không đổi).\n"
             "- `24`: Thời gian sự kiện (giờ). Nhập 0 nếu muốn sự kiện không tự hết hạn."
    )
    @commands.check(is_bot_moderator)
    async def mod_start_event(self, ctx: commands.Context,
                              guild_target: nextcord.Guild,
                              event_key: str,
                              cooldown_modifier: float,
                              reward_modifier: float,
                              duration_hours: float = 0.0):
        """
        (Moderator Only) Bắt đầu hoặc cập nhật một sự kiện cho một server.
        """
        actual_event_key = event_key.lower()
        if actual_event_key not in SUPPORTED_EVENT_TYPES:
            await try_send(ctx, content=f"{ICON_ERROR} Loại sự kiện `{event_key}` không được hỗ trợ. Các loại hợp lệ: `{', '.join(SUPPORTED_EVENT_TYPES.keys())}`.")
            return

        if guild_target is None:
            await try_send(ctx, content=f"{ICON_ERROR} Không tìm thấy server với ID/Tên bạn cung cấp.")
            return

        if cooldown_modifier < 0 or reward_modifier < 0:
            await try_send(ctx, content=f"{ICON_ERROR} Các hệ số điều chỉnh (modifier) không được là số âm.")
            return
        if duration_hours < 0:
            await try_send(ctx, content=f"{ICON_ERROR} Thời gian sự kiện không được là số âm.")
            return

        active_until_iso = None
        if duration_hours > 0:
            end_time = datetime.now(timezone.utc) + timedelta(hours=duration_hours)
            active_until_iso = end_time.isoformat()

        guild_config = get_guild_config(guild_target.id)

        guild_config["active_events"][actual_event_key] = {
            "cooldown_modifier": cooldown_modifier,
            "reward_modifier": reward_modifier,
            "active_until": active_until_iso
        }

        if save_guild_config(guild_target.id, guild_config):
            duration_str = f"trong {duration_hours} giờ" if duration_hours > 0 else "vô thời hạn"
            end_time_str = f" (kết thúc vào khoảng {active_until_iso.replace('T', ' ').split('.')[0]} UTC)" if active_until_iso else ""

            log_message = (f"EVENT STARTED/UPDATED by {ctx.author.name} ({ctx.author.id}) "
                           f"for Guild: {guild_target.name} ({guild_target.id}). "
                           f"Event: {actual_event_key}, CD_Mod: {cooldown_modifier}, "
                           f"Reward_Mod: {reward_modifier}, Duration: {duration_str}{end_time_str}.")
            logger.info(log_message)

            embed = nextcord.Embed(
                title=f"{ICON_SUCCESS} Sự kiện đã được bắt đầu/cập nhật!",
                description=f"**Server:** {guild_target.name} (`{guild_target.id}`)\n"
                            f"**Loại sự kiện:** `{actual_event_key}`\n"
                            f"**Hệ số Cooldown:** `{cooldown_modifier}`\n"
                            f"**Hệ số Phần thưởng:** `{reward_modifier}`\n"
                            f"**Thời gian:** {duration_str}{end_time_str}",
                color=nextcord.Color.green()
            )
            await try_send(ctx, embed=embed)
        else:
            logger.error(f"Failed to save guild config after attempting to start/update event by {ctx.author.name} for guild {guild_target.id}.")
            await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi lưu cấu hình sự kiện. Vui lòng thử lại.")

    @commands.command(
        name="mod_stopevent",
        aliases=["stopevent", "event_stop"],
        help="Dừng một sự kiện đang hoạt động trên server được chỉ định.\n"
             "Ví dụ: `!mod_stopevent <GuildID> work`"
    )
    @commands.check(is_bot_moderator)
    async def mod_stop_event(self, ctx: commands.Context,
                             guild_target: nextcord.Guild,
                             event_key: str):
        """
        (Moderator Only) Dừng một sự kiện đang hoạt động cho một server.
        """
        actual_event_key = event_key.lower()
        if actual_event_key not in SUPPORTED_EVENT_TYPES: # Kiểm tra xem có phải là key được hỗ trợ không
            await try_send(ctx, content=f"{ICON_ERROR} Loại sự kiện `{event_key}` không được hỗ trợ hoặc không đúng tên. Các loại hợp lệ: `{', '.join(SUPPORTED_EVENT_TYPES.keys())}`.")
            return

        if guild_target is None:
            await try_send(ctx, content=f"{ICON_ERROR} Không tìm thấy server với ID/Tên bạn cung cấp.")
            return

        guild_config = get_guild_config(guild_target.id)

        if actual_event_key in guild_config["active_events"]:
            del guild_config["active_events"][actual_event_key]

            if save_guild_config(guild_target.id, guild_config):
                log_message = (f"EVENT STOPPED by {ctx.author.name} ({ctx.author.id}) "
                               f"for Guild: {guild_target.name} ({guild_target.id}). "
                               f"Event: {actual_event_key}.")
                logger.info(log_message)

                embed = nextcord.Embed(
                    title=f"{ICON_SUCCESS} Sự kiện đã được dừng!",
                    description=f"**Server:** {guild_target.name} (`{guild_target.id}`)\n"
                                f"**Loại sự kiện:** `{actual_event_key}` đã được tắt.",
                    color=nextcord.Color.orange()
                )
                await try_send(ctx, embed=embed)
            else:
                logger.error(f"Failed to save guild config after attempting to stop event by {ctx.author.name} for guild {guild_target.id}.")
                await try_send(ctx, content=f"{ICON_ERROR} Đã có lỗi xảy ra khi lưu cấu hình sau khi dừng sự kiện. Vui lòng thử lại.")
        else:
            await try_send(ctx, content=f"{ICON_INFO} Không có sự kiện `{actual_event_key}` nào đang hoạt động trên server {guild_target.name} để dừng.")

    # --- LỆNH MỚI ĐỂ LIỆT KÊ SỰ KIỆN ---
    @commands.command(
        name="mod_listevents",
        aliases=["listevents", "event_list", "showevents"],
        help="Hiển thị danh sách các sự kiện đang được cấu hình cho server.\n"
             "Ví dụ: `!mod_listevents <GuildID>`"
    )
    @commands.check(is_bot_moderator)
    async def mod_list_events(self, ctx: commands.Context, guild_target: nextcord.Guild):
        """
        (Moderator Only) Hiển thị các sự kiện đang được cấu hình cho một server.
        """
        if guild_target is None:
            await try_send(ctx, content=f"{ICON_ERROR} Không tìm thấy server với ID/Tên bạn cung cấp.")
            return

        guild_config = get_guild_config(guild_target.id)
        active_events = guild_config.get("active_events", {}) # Lấy từ config, đã được database.py đảm bảo tồn tại

        if not active_events:
            await try_send(ctx, content=f"{ICON_INFO} Hiện không có sự kiện nào được cấu hình cho server {guild_target.name}.")
            return

        embed = nextcord.Embed(
            title=f"{ICON_ADMIN_PANEL or '🎉'} Danh Sách Sự Kiện - {guild_target.name}",
            color=nextcord.Color.blue()
        )

        description_parts = []
        now_utc = datetime.now(timezone.utc)

        for event_key, event_details in active_events.items():
            cd_mod = event_details.get("cooldown_modifier", "N/A")
            reward_mod = event_details.get("reward_modifier", "N/A")
            active_until_iso = event_details.get("active_until")

            status = ""
            if active_until_iso:
                try:
                    # Chuyển đổi từ ISO format về datetime object (aware)
                    # Python 3.11+ hỗ trợ 'Z' trực tiếp.
                    # Cho các phiên bản cũ hơn, nếu có 'Z', thay thế bằng '+00:00'
                    if active_until_iso.endswith('Z'):
                        active_until_dt = datetime.fromisoformat(active_until_iso.replace('Z', '+00:00'))
                    else:
                        active_until_dt = datetime.fromisoformat(active_until_iso)
                    
                    # Đảm bảo active_until_dt là timezone-aware (UTC) để so sánh với now_utc
                    if active_until_dt.tzinfo is None:
                         active_until_dt = active_until_dt.replace(tzinfo=timezone.utc)


                    if active_until_dt > now_utc:
                        time_left = active_until_dt - now_utc
                        # Làm tròn timedelta để hiển thị đẹp hơn, bỏ qua microsecond
                        days, remainder = divmod(time_left.total_seconds(), 86400)
                        hours, remainder = divmod(remainder, 3600)
                        minutes, seconds = divmod(remainder, 60)
                        if days > 0:
                            time_left_str = f"{int(days)}d {int(hours)}h"
                        elif hours > 0:
                            time_left_str = f"{int(hours)}h {int(minutes)}m"
                        else:
                            time_left_str = f"{int(minutes)}m {int(seconds)}s"
                        status = f"⏳ Hết hạn sau: {time_left_str} (lúc {active_until_dt.strftime('%Y-%m-%d %H:%M:%S')} UTC)"
                    else:
                        status = f"❌ Đã hết hạn (lúc {active_until_dt.strftime('%Y-%m-%d %H:%M:%S')} UTC)"
                except ValueError:
                    status = f"⏰ Thời gian kết thúc: {active_until_iso} (Lỗi định dạng)"
            else:
                status = "♾️ Vô thời hạn"
            
            description_parts.append(
                f"**`{event_key.capitalize()}`**:\n"
                f"  - Cooldown Mod: `{cd_mod}`\n"
                f"  - Reward Mod: `{reward_mod}`\n"
                f"  - Trạng thái: {status}"
            )

        if description_parts:
            embed.description = "\n\n".join(description_parts)
        else: # Trường hợp active_events có key nhưng value rỗng (ít khi xảy ra với logic hiện tại)
            embed.description = "Không có thông tin chi tiết sự kiện nào."

        log_message = (f"EVENT LIST VIEWED by {ctx.author.name} ({ctx.author.id}) "
                       f"for Guild: {guild_target.name} ({guild_target.id}). "
                       f"Found {len(active_events)} events.")
        logger.info(log_message)
        await try_send(ctx, embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(EventManagementCog(bot))
    logger.info(f"EventManagementCog has been loaded.")

