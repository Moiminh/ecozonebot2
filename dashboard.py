
from flask import Flask, render_template, request, flash, redirect, url_for, session
import sqlite3
import subprocess
import os
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("BOT_TOKEN", "a_default_secret_key_if_token_is_not_set")

DB_PATH = "data/econzone.sqlite"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_owner_ids():
    try:
        with open('moderators.json', 'r') as f:
            data = json.load(f)
        return data.get('moderator_ids', [1370417047070048276])
    except FileNotFoundError:
        return [1370417047070048276]

OWNER_IDS = get_owner_ids()

@app.before_request
def require_login():
    allowed_routes = ['login', 'static']
    if request.endpoint not in allowed_routes and 'user_id' not in session:
        return redirect(url_for('login'))

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
    return render_template('login.html')  # Tạo file login.html đơn giản

@app.route("/")
def dashboard():
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
    try:
        flash("Bắt đầu quá trình di chuyển dữ liệu... Việc này có thể mất một chút thời gian. Vui lòng không đóng trang.", "info")
        process = subprocess.Popen(['python', 'migrate_to_sqlite.py'], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
        stdout, stderr = process.communicate()
        if process.returncode == 0:
            flash(f"Di chuyển dữ liệu thành công! Chi tiết:\n<pre>{stdout}</pre>", "success")
        else:
            flash(f"Lỗi khi di chuyển:\n<pre>{stderr}</pre>", "danger")
    except FileNotFoundError:
        flash("Lỗi: Không tìm thấy file 'migrate_to_sqlite.py'. Hãy đảm bảo nó nằm ở thư mục gốc.", "danger")
    except Exception as e:
        flash(f"Lỗi nghiêm trọng khi chạy script migrate: {e}", "danger")

    return redirect(url_for('dashboard'))

if __name__ == "__main__":
    if not os.path.exists('templates'):
        os.makedirs('templates')

    login_html = """
        <!doctype html><title>Login</title><h1>Đăng nhập</h1>
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}{% for category, message in messages %}
            <p style='color:red;'>{{ message }}</p>
          {% endfor %}{% endif %}
        {% endwith %}
        <form method=post>
          <p>User ID: <input type=text name=user_id></p>
          <p><input type=submit value=Login></p>
        </form>
    """
    with open('templates/login.html', 'w', encoding='utf-8') as f:
        f.write(login_html)

    app.run(debug=True, port=5000)
