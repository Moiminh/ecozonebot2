from flask import Flask, render_template, request, flash, redirect, url_for, session
import sqlite3
import subprocess
import os
from dotenv import load_dotenv

# Tải biến môi trường
load_dotenv()

# --- Cấu hình Flask ---
app = Flask(__name__)
# Cần secret key để sử dụng flash messages
app.secret_key = os.getenv("BOT_TOKEN") # Dùng tạm token bot làm key

# Lấy ID của Owner từ file moderators.json hoặc gán cứng
OWNER_IDS = []
try:
    with open('moderators.json', 'r') as f:
        data = json.load(f)
        OWNER_IDS = data.get('moderator_ids', [])
except:
    OWNER_IDS = [1370417047070048276] # ID dự phòng

DB_PATH = "data/econzone.sqlite"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Middleware để kiểm tra quyền truy cập
@app.before_request
def check_auth():
    # Bỏ qua kiểm tra cho các route không cần xác thực
    if request.endpoint in ['login', 'static']:
        return
    # Kiểm tra xem user_id có trong session và có phải là owner không
    if 'user_id' not in session or session['user_id'] not in OWNER_IDS:
        return redirect(url_for('login'))

@app.route("/login")
def login():
    # Trong một ứng dụng thực tế, bạn sẽ dùng Discord OAuth2 ở đây.
    # Để đơn giản, chúng ta dùng một trang giả lập.
    return """
    <h1>Login (Giả lập)</h1>
    <p>Trong ứng dụng thực tế, bạn sẽ đăng nhập bằng Discord.</p>
    <p>Nhập ID Owner của bạn để vào dashboard:</p>
    <form action='/login' method='post'>
        User ID: <input type='text' name='user_id'><br>
        <input type='submit' value='Login'>
    </form>
    """

@app.route("/login", methods=['POST'])
def login_post():
    user_id = int(request.form.get('user_id', 0))
    if user_id in OWNER_IDS:
        session['user_id'] = user_id
        return redirect(url_for('dashboard'))
    else:
        flash("User ID không hợp lệ!", "danger")
        return redirect(url_for('login'))

@app.route("/")
def dashboard():
    conn = get_db_connection()
    try:
        user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        top_users = conn.execute("SELECT user_id, bank_balance FROM users ORDER BY bank_balance DESC LIMIT 10").fetchall()
    except sqlite3.OperationalError: # Bảng chưa tồn tại
        user_count = 0
        top_users = []
    conn.close()
    
    # Đọc trạng thái hiện tại của .env
    current_db_type = os.getenv('DATABASE_TYPE', 'json')

    return render_template('dashboard.html', user_count=user_count, top_users=top_users, current_db_type=current_db_type)

@app.route("/migrate", methods=["POST"])
def run_migration():
    try:
        flash("Bắt đầu quá trình di chuyển dữ liệu... Vui lòng đợi.", "info")
        # Chạy script migrate_to_sqlite.py trong một tiến trình riêng
        process = subprocess.Popen(['python', 'migrate_to_sqlite.py'], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            flash(f"Di chuyển dữ liệu thành công! Output:\n<pre>{stdout}</pre>", "success")
        else:
            flash(f"Lỗi khi di chuyển:\n<pre>{stderr}</pre>", "danger")

    except Exception as e:
        flash(f"Lỗi nghiêm trọng khi chạy script migrate: {e}", "danger")
        
    return redirect(url_for('dashboard'))

if __name__ == "__main__":
    # Tạo thư mục và file template nếu chưa có
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    html_content = """
    <!doctype html>
    <html>
      <head><title>EconZone Dashboard</title></head>
      <body>
        <h1>EconZone Dashboard</h1>
        <p><strong>Trạng thái CSDL hiện tại:</strong> {{ current_db_type.upper() }}</p>
        <p><strong>Tổng số người dùng trong CSDL:</strong> {{ user_count }}</p>
        <hr>
        <h2>Hành động</h2>
        <form action="/migrate" method="post" onsubmit="return confirm('Bạn có chắc muốn chạy di chuyển dữ liệu không?');">
          <button type="submit">Chạy Script Di chuyển từ JSON sang SQLite</button>
        </form>
        <hr>
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            <ul class=flashes>
            {% for category, message in messages %}
              <li class="{{ category }}">{{ message | safe }}</li>
            {% endfor %}
            </ul>
          {% endif %}
        {% endwith %}
        <hr>
        <h2>Top 10 người dùng giàu nhất (Bank)</h2>
        <ul>
        {% for user in top_users %}
          <li>User ID: {{ user['user_id'] }} - Bank: {{ "{:,}".format(user['bank_balance']) }}</li>
        {% else %}
          <li>Chưa có dữ liệu.</li>
        {% endfor %}
        </ul>
      </body>
    </html>
    """
    with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

    app.run(debug=True, port=8080)
