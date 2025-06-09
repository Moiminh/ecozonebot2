from flask import Flask, render_template, request, flash, redirect, url_for, session, jsonify
import sqlite3
import subprocess
import os
import json
from dotenv import load_dotenv

load_dotenv()

# --- BIẾN TOÀN CỤC ĐỂ GIỮ ĐỐI TƯỢNG BOT ---
discord_bot = None

app = Flask(__name__)
app.secret_key = os.getenv("BOT_TOKEN", "a_default_secret_key_if_token_is_not_set")

DB_PATH = "data/econzone.sqlite"

def get_db_connection():
    # ... (Hàm này không đổi)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_owner_ids():
    # ... (Hàm này không đổi)
    try:
        with open('moderators.json', 'r') as f: data = json.load(f)
        return data.get('moderator_ids', [1370417047070048276])
    except FileNotFoundError:
        return [1370417047070048276]

OWNER_IDS = get_owner_ids()

@app.before_request
def require_login():
    # ... (Hàm này không đổi)
    allowed_routes = ['login', 'static', 'stats'] # Cho phép truy cập /stats không cần login
    if request.endpoint not in allowed_routes and 'user_id' not in session:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    # ... (Route này không đổi)
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
    # ... (Route này không đổi)
    user_count = 0
    top_users = []
    if os.path.exists(DB_PATH):
        try:
            conn = get_db_connection()
            user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            top_users = conn.execute("SELECT user_id, bank_balance FROM users ORDER BY bank_balance DESC LIMIT 10").fetchall()
            conn.close()
        except sqlite3.OperationalError:
            flash("CSDL SQLite tồn tại nhưng có vẻ trống. Hãy thử chạy script di chuyển.", "warning")
    current_db_type = os.getenv('DATABASE_TYPE', 'json')
    return render_template('dashboard.html', user_count=user_count, top_users=top_users, current_db_type=current_db_type)

@app.route("/migrate", methods=["POST"])
def run_migration():
    # ... (Route này không đổi)
    try:
        flash("Bắt đầu quá trình di chuyển dữ liệu...", "info")
        process = subprocess.Popen(['python', 'migrate_to_sqlite.py'], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
        stdout, stderr = process.communicate()
        if process.returncode == 0: flash(f"Di chuyển dữ liệu thành công! Chi tiết:\n<pre>{stdout}</pre>", "success")
        else: flash(f"Lỗi khi di chuyển:\n<pre>{stderr}</pre>", "danger")
    except Exception as e:
        flash(f"Lỗi nghiêm trọng khi chạy script migrate: {e}", "danger")
    return redirect(url_for('dashboard'))

# --- ROUTE MỚI ĐỂ HIỂN THỊ STATS ---
@app.route("/stats")
def stats():
    if discord_bot and discord_bot.is_ready():
        # Trả về dữ liệu dưới dạng JSON
        return jsonify({
            'guild_count': len(discord_bot.guilds),
            'user_count': len(discord_bot.users),
            'latency': f"{discord_bot.latency * 1000:.2f} ms",
            'is_ready': discord_bot.is_ready()
        })
    else:
        # Trả về thông báo nếu bot chưa sẵn sàng
        return jsonify({'error': 'Bot is not ready or not connected.'}), 503

# --- HÀM CHẠY DASHBOARD (ĐÃ SỬA) ---
def run_flask_app(bot_instance):
    """Lưu đối tượng bot và chạy ứng dụng Flask."""
    global discord_bot
    discord_bot = bot_instance
    app.run(host="0.0.0.0", port=8080)
