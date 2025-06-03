# bot/core/utils.py
import nextcord
from nextcord.ext import commands
from datetime import datetime, timedelta
# Dùng relative import để import get_guild_config từ file database.py trong cùng package 'core'
from .database import get_guild_config

# --- Helper function for Guild Owner Check ---
def is_guild_owner_check(interaction_or_ctx):
    """
    Kiểm tra xem người dùng có phải là chủ sở hữu của server (guild) hay không.
    Áp dụng cho cả Context (lệnh prefix) và Interaction (lệnh slash).
    """
    # Lấy đối tượng user và guild từ interaction hoặc context
    if isinstance(interaction_or_ctx, nextcord.Interaction):
        user = interaction_or_ctx.user
        guild = interaction_or_ctx.guild
    elif isinstance(interaction_or_ctx, commands.Context):
        user = interaction_or_ctx.author
        guild = interaction_or_ctx.guild
    else:
        # Nếu không phải Interaction hay Context, không thể kiểm tra
        return False

    if guild is None: # Lệnh có thể được dùng trong DM, nơi không có guild
        return False
    return user.id == guild.owner_id


def get_time_left_str(last_timestamp, cooldown_seconds):
    """
    Tính toán và trả về chuỗi thời gian còn lại cho một cooldown.
    Ví dụ: "0:15:30" (giờ:phút:giây)
    Trả về None nếu cooldown đã hết.
    """
    if not last_timestamp: # Nếu chưa từng thực hiện hành động (timestamp là 0 hoặc None)
        return None
        
    now = datetime.now().timestamp() # Thời gian hiện tại dưới dạng timestamp
    time_passed = now - last_timestamp # Thời gian đã trôi qua kể từ lần cuối
    
    if time_passed >= cooldown_seconds: # Nếu thời gian đã qua lớn hơn hoặc bằng cooldown
        return None # Cooldown đã kết thúc
        
    time_left_seconds = cooldown_seconds - time_passed # Thời gian còn lại (giây)
    # Chuyển đổi giây thành đối tượng timedelta để dễ định dạng
    delta = timedelta(seconds=int(time_left_seconds))
    # Định dạng thành chuỗi HH:MM:SS, loại bỏ phần microsecond nếu có
    return str(delta).split('.')[0]


# --- Safe Message Sending ---
async def try_send(target, content=None, embed=None, ephemeral=False):
    """
    Hàm gửi tin nhắn an toàn, xử lý các trường hợp Context và Interaction,
    đồng thời kiểm tra kênh có bị mute không.
    `target` có thể là `commands.Context` hoặc `nextcord.Interaction`.
    `ephemeral` chỉ áp dụng cho Interaction.
    """
    channel = None
    guild = None
    is_interaction = isinstance(target, nextcord.Interaction)
    is_context = isinstance(target, commands.Context)

    if is_interaction:
        channel = target.channel
        guild = target.guild
    elif is_context:
        channel = target.channel
        guild = target.guild
    else:
        print(f"Lỗi try_send: `target` không phải Context hay Interaction.")
        return None # Không thể gửi nếu không xác định được target

    # Kiểm tra kênh có bị mute không (chỉ áp dụng nếu có guild và channel)
    if guild and channel:
        # Lấy guild_config mới nhất mỗi lần, có thể không hiệu quả nếu gọi liên tục
        # Nhưng đảm bảo tính đúng đắn nếu config thay đổi thường xuyên
        guild_config_data = get_guild_config(guild.id)
        
        # Kiểm tra nếu channel.id có trong danh sách muted_channels của config
        # và tin nhắn không phải là ephemeral (tin nhắn tạm thời)
        if channel.id in guild_config_data.get("muted_channels", []) and not ephemeral:
            # Nếu người dùng là admin của server và đang dùng interaction, gửi tin nhắn ephemeral cảnh báo
            user_for_perms_check = target.user if is_interaction else target.author
            if hasattr(user_for_perms_check, 'guild_permissions') and user_for_perms_check.guild_permissions.administrator:
                try:
                    # Đối với interaction, cần kiểm tra response đã được gửi chưa
                    if is_interaction and not target.response.is_done():
                        await target.response.send_message(
                            "Bot đang bị tắt tiếng công khai trong kênh này. Tin nhắn này chỉ bạn thấy.",
                            ephemeral=True,
                            delete_after=10 # Tự xóa sau 10 giây
                        )
                    # Không gửi tin nhắn thường nếu kênh bị mute và không phải ephemeral
                except Exception as e:
                    print(f"Lỗi khi gửi tin nhắn cảnh báo mute (ephemeral): {e}")
            return None # Không gửi tin nhắn công khai nếu kênh bị mute

    # Gửi tin nhắn
    try:
        if is_context:
            return await target.send(content=content, embed=embed)
        elif is_interaction:
            # Nếu interaction đã được phản hồi (ví dụ: defer), dùng followup
            if target.response.is_done():
                return await target.followup.send(content=content, embed=embed, ephemeral=ephemeral)
            else:
                # Nếu chưa phản hồi, dùng send_message
                return await target.response.send_message(content=content, embed=embed, ephemeral=ephemeral)
    except nextcord.errors.HTTPException as e:
        print(f"Lỗi khi gửi tin nhắn trong try_send: {e} (Kênh: {channel.id if channel else 'N/A'}, Guild: {guild.id if guild else 'N/A'})")
    except Exception as e: # Bắt các lỗi khác có thể xảy ra
        print(f"Lỗi không xác định trong try_send: {e}")
    return None
