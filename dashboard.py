from flask import Flask, render_template, request, flash, redirect, url_for, session, jsonify
import sqlite3
import os
import json
from dotenv import load_dotenv

# Tải các biến môi trường từ file .env hoặc Secrets
load_dotenv()

# --- BIẾN TOÀN CỤC ĐỂ GIỮ ĐỐI TƯỢNG BOT ---
# Biến này sẽ được gán giá trị từ main.py khi bot khởi động
discord_bot = None

# Khởi tạo ứng dụng Flask
app = Flask(__name__)
app.secret_key = os.getenv("BOT_TOKEN", "a_default_secret_key_for_development")

# Đường dẫn tới file CSDL
DB_PATH = "data/econzone.sqlite"

def get_db_connection():
    """Tạo kết nối tới CSDL SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_owner_ids():
    """Đọc danh sách ID của Owner/Moderator từ file moderators.json."""
    try:
        with open('moderators.json', 'r') as f:
            data = json.load(f)
        # Lấy danh sách ID từ file, nếu không có thì dùng ID mặc định
        return data.get('moderator_ids', [])
    except FileNotFoundError:
        # Trả về danh sách rỗng nếu file không tồn tại
        return []

OWNER_IDS = get_owner_ids()

@app.before_request
def require_login():
    """Middleware kiểm tra xem người dùng đã đăng nhập chưa trước mỗi yêu cầu."""
    # Các trang không yêu cầu đăng nhập
    allowed_routes = ['login', 'static', 'stats']
    if request.endpoint not in allowed_routes and 'user_id' not in session:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Xử lý việc đăng nhập."""
    if request.method == 'POST':
        user_id_input = request.form.get('user_id', type=int)
        if user_id_input in OWNER_IDS:
            session['user_id'] = user_id_input
            flash('Đăng nhập thành công!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('ID của bạn không có quyền truy cập!', 'danger')
    return render_template('login.html')

@app.route("/")
def dashboard():
    """Hiển thị trang dashboard chính."""
    user_count = 0
    top_users = []
    # Chỉ truy vấn nếu file CSDL tồn tại
    if os.path.exists(DB_PATH):
        try:
            conn = get_db_connection()
            user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            top_users = conn.execute("SELECT user_id, bank_balance FROM users ORDER BY bank_balance DESC LIMIT 10").fetchall()
            conn.close()
        except sqlite3.OperationalError:
            flash("CSDL SQLite tồn tại nhưng có vẻ trống.", "warning")

    return render_template('dashboard.html', user_count=user_count, top_users=top_users)

@app.route("/stats")
def stats():
    """Cung cấp các chỉ số trực tiếp từ bot dưới dạng JSON."""
    if discord_bot and discord_bot.is_ready():
        return jsonify({
            'guild_count': len(discord_bot.guilds),
            'user_count': len(discord_bot.users),
            'latency': f"{discord_bot.latency * 1000:.2f} ms",
            'is_ready': discord_bot.is_ready()
        })
    else:
        return jsonify({'error': 'Bot is not ready or not connected.'}), 503

# --- HÀM CHÍNH ĐỂ CHẠY DASHBOARD ---
def run_flask_app(bot_instance):
    """
    Hàm này được gọi từ main.py, nhận đối tượng bot và khởi chạy máy chủ Flask.
    """
    global discord_bot
    discord_bot = bot_instance
    # Chạy trên host 0.0.0.0 để Replit có thể hiển thị webview
    app.run(host="0.0.0.0", port=8080)

# Đoạn mã này cho phép chạy dashboard riêng lẻ để kiểm tra giao diện
if __name__ == "__main__":
    print("Để chạy dashboard cùng bot, hãy chạy file main.py")
    print("Chạy dashboard ở chế độ test riêng lẻ...")
    app.run(debug=True, port=5000)
