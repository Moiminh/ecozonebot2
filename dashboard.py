# dashboard.py
from flask import Flask, render_template, request, flash, redirect, url_for, session
import sqlite3
import subprocess
import os
import json
from dotenv import load_dotenv

# Tải các biến môi trường từ file .env
load_dotenv()

# --- Cấu hình ứng dụng Flask ---
app = Flask(__name__)
# Flask cần một "secret_key" để quản lý session và hiển thị thông báo an toàn.
# Chúng ta có thể dùng tạm BOT_TOKEN cho việc này.
app.secret_key = os.getenv("BOT_TOKEN", "a_default_secret_key_if_token_is_not_set")

# --- Các hàm tiện ích ---
def get_db_connection():
    """Tạo kết nối tới CSDL SQLite."""
    conn = sqlite3.connect("data/econzone.sqlite")
    conn.row_factory = sqlite3.Row
    return conn

def get_owner_ids():
    """Đọc danh sách ID của Owner/Moderator từ file moderators.json."""
    try:
        with open('moderators.json', 'r') as f:
            data = json.load(f)
        # Lấy danh sách ID từ file, nếu không có thì dùng ID mặc định
        return data.get('moderator_ids', [1370417047070048276])
    except FileNotFoundError:
        # Trả về ID mặc định nếu file không tồn tại
        return [1370417047070048276]

OWNER_IDS = get_owner_ids()

# --- Các Route (đường dẫn) của trang web ---

# Route chính, hiển thị trang dashboard
@app.route("/")
def dashboard():
    # Phần này sẽ được thêm ở các bước sau
    return "<h1>Trang Dashboard (đang xây dựng)</h1>"

# Chạy ứng dụng web
if __name__ == "__main__":
    # Chạy ở chế độ debug để dễ dàng phát triển
    app.run(debug=True, port=5000)
