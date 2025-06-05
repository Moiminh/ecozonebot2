# bot/cogs/moderation/event_cmds.py
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
        if actual_event_key not in SUPPORTED_EVENT_TYPES:
            await try_send(ctx, content=f"{ICON_ERROR} Loại sự kiện `{event_key}` không được hỗ trợ. Các loại hợp lệ: `{', '.join(SUPPORTED_EVENT_TYPES.keys())}`.")
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

    # Bạn có thể thêm error handler cục bộ cho Cog này ở đây nếu muốn,
    # hoặc sử dụng on_command_error chung của bot trong core/bot.py
    # async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
    #     # ... (xử lý lỗi cụ thể cho Cog này) ...
    #     # logger.debug(f"EventManagementCog error handler caught: {error}")
    #     # if isinstance(error, commands.GuildNotFound):
    #     #    await try_send(ctx, f"{ICON_ERROR} Không tìm thấy server: `{error.argument}`.")
    #     #    return
    #     # # Để các lỗi khác được xử lý bởi handler chung, không re-raise hoặc pass
    #     # # Hoặc gọi self.bot.on_command_error(ctx, error) nếu muốn xử lý và chuyển tiếp


def setup(bot: commands.Bot):
    bot.add_cog(EventManagementCog(bot))
    logger.info(f"EventManagementCog has been loaded.") # Thêm log khi cog được load
