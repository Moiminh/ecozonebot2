# bot/core/leveling.py
import logging
from typing import Dict, Any, Union

import nextcord
from nextcord.ext import commands

from .utils import try_send
from .icons import ICON_LEVEL_UP, ICON_GLOBAL, ICON_LOCAL

logger = logging.getLogger(__name__)

def xp_for_level(level: int) -> int:
    """
    Tính toán lượng XP cần thiết để đạt đến một cấp độ nhất định.
    Công thức: 5 * (level^2) + 50 * level + 100
    """
    return 5 * (level ** 2) + (50 * level) + 100

async def check_and_process_levelup(
    ctx: commands.Context, 
    user_data: Dict[str, Any], 
    level_type: str
):
    """
    Kiểm tra và xử lý việc lên cấp cho người dùng (cả local và global).
    Hàm này sẽ tự động tăng cấp, trừ XP và gửi thông báo nếu cần.

    Args:
        ctx: Context của lệnh để gửi thông báo.
        user_data: Dữ liệu của người dùng (có thể là global_profile hoặc local_data).
        level_type: Loại level cần kiểm tra ('local' hoặc 'global').
    """
    if level_type not in ['local', 'global']:
        logger.error(f"Loại level không hợp lệ được cung cấp cho check_and_process_levelup: {level_type}")
        return

    level_key = f"level_{level_type}"
    xp_key = f"xp_{level_type}"

    current_level = user_data.get(level_key, 1)
    current_xp = user_data.get(xp_key, 0)
    
    xp_to_next_level = xp_for_level(current_level)

    # Sử dụng vòng lặp while để xử lý trường hợp lên nhiều cấp một lúc
    while current_xp >= xp_to_next_level:
        # Tăng cấp và trừ XP
        current_level += 1
        current_xp -= xp_to_next_level
        
        # Cập nhật lại dữ liệu của người dùng
        user_data[level_key] = current_level
        user_data[xp_key] = current_xp
        
        # Lấy thông tin cấp độ và icon tương ứng
        level_scope_icon = ICON_LOCAL if level_type == 'local' else ICON_GLOBAL
        level_scope_name = "Server" if level_type == 'local' else "Toàn Cục"

        logger.info(f"User {ctx.author.id} đã lên cấp {level_scope_name} {current_level} tại guild {ctx.guild.id if ctx.guild else 'N/A'}.")

        # Gửi thông báo chúc mừng
        await try_send(
            ctx,
            content=(
                f"{ICON_LEVEL_UP} Chúc mừng {ctx.author.mention}! "
                f"Bạn đã đạt **Cấp {current_level} ({level_scope_name})** {level_scope_icon}!"
            )
        )
        
        # Cập nhật lại lượng XP cần cho cấp độ tiếp theo
        xp_to_next_level = xp_for_level(current_level)
