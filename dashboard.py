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
# (Giữ nguyên các dòng import và cấu hình ở trên)
# ...

# --- Middleware kiểm tra đăng nhập ---
@app.before_request
def require_login():
    """Hàm này sẽ chạy trước mỗi yêu cầu."""
    # Các trang không yêu cầu đăng nhập
    allowed_routes = ['login', 'static']
    if request.endpoint not in allowed_routes and 'user_id' not in session:
        return redirect(url_for('login'))

# --- Các Route (đường dẫn) của trang web ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id_input = request.form.get('user_id', type=int)
        if user_id_input in OWNER_IDS:
            session['user_id'] = user_id_input
            flash('Đăng nhập thành công!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('ID của bạn không có quyền truy cập!', 'danger')
    # Hiển thị form đăng nhập
    return """
        <!doctype html>
        <title>Login</title>
        <h1>Đăng nhập vào Dashboard</h1>
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, message in messages %}
              <p style="color:red;">{{ message }}</p>
            {% endfor %}
          {% endif %}
        {% endwith %}
        <form method=post>
          <p>User ID: <input type=text name=user_id></p>
          <p><input type=submit value=Login></p>
        </form>
    """

@app.route("/")
def dashboard():
    # (Phần này sẽ được thêm ở các bước sau)
    return f"<h1>Xin chào, {session['user_id']}!</h1><p>Đây là trang Dashboard.</p>"

# (Giữ nguyên phần if __name__ == "__main__": ở cuối)
# ...
