# bot/core/database.py
import json
import os
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# --- CÁC CẤU TRÚC DỮ LIỆU MẶC ĐỊNH ---

DEFAULT_USER_LOCAL_DATA = {
    "local_balance": {"earned": 0, "adadd": 0},
    "inventory_local": [],
    "tickets": [],
    "level_local": 1,
    "xp_local": 0,
}

DEFAULT_GLOBAL_USER_PROFILE = {
    "bank_balance": 0, # <<< GIỮ LẠI BANK TRUNG TÂM
    "inventory_global": [],
    "wanted_level": 0.0,
    "level_global": 1,
    "xp_global": 0,
    "last_active_guild_id": None,
    "preferred_language": "vi",
    "cooldowns": {
        "work": 0, "daily": 0, "beg": 0, "rob": 0, "crime": 0, "fish": 0,
        "slots": 0, "coinflip": 0, "dice": 0, "launder": 0,
        "last_tainted_sell_date": "1970-01-01",
        "tainted_sells_today": 0
    },
    "server_data": {}
}

DEFAULT_GUILD_CONFIG = {
    "server_level": 1,
    "bare_command_active_channels": [],
    "muted_channels": [],
    "active_events": {}
}

DEFAULT_ECONOMY_STRUCTURE = {
    "users": {},
    "guild_configs": {},
    "bot_metadata": {
        "data_structure_version": "EconZone_v3.0_Final_Architecture",
        "notes": "Hệ thống Bank trung tâm, Ví Local (Ecoin/Ecobit), và hệ thống Visa."
    }
}

# --- CÁC HÀM QUẢN LÝ DỮ LIỆU ---
# (Toàn bộ các hàm load_economy_data, save_economy_data, get_or_create...,
# load/save_moderator_ids sẽ được giữ nguyên như phiên bản trước đó
# vì chúng đã được thiết kế để tự động cập nhật cấu trúc (schema migration)
# dựa trên các hằng số DEFAULT ở trên. Đây chính là sức mạnh của thiết kế ban đầu.)
