#!/bin/bash

# Hàm này sẽ được gọi khi script bị dừng (ví dụ: khi bạn nhấn Ctrl+C)
cleanup() {
    echo -e "\n[+] Đã nhận tín hiệu dừng từ ngrok hoặc người dùng."
    # Kiểm tra xem BOT_PID có được đặt không
    if [ ! -z "$BOT_PID" ]; then
        echo "[+] Đang dừng tiến trình của bot (PID: $BOT_PID)..."
        # Gửi tín hiệu SIGINT (giống như Ctrl+C) để bot có thể lưu dữ liệu lần cuối
        kill -SIGINT $BOT_PID
    fi
    echo "[+] Hoàn tất. Tạm biệt!"
    exit
}

# Đặt "bẫy": khi script nhận tín hiệu INT (Ctrl+C) hoặc EXIT, nó sẽ gọi hàm cleanup
trap cleanup INT EXIT

# --- Bắt đầu script chính ---
echo "[+] Đang khởi động bot Discord và dashboard Flask ở chế độ nền..."

# Chạy bot và lấy Process ID (PID) của nó
python main.py &
BOT_PID=$!

echo "[+] Bot đang chạy với PID: $BOT_PID"
echo "[+] Đợi 2 giây để máy chủ web khởi động..."
sleep 2

echo "[+] Đang khởi động ngrok cho cổng 8080..."
echo "[!] Nhấn Ctrl+C để dừng cả ngrok và bot."

# Chạy ngrok ở chế độ foreground. Script sẽ dừng ở đây cho đến khi ngrok bị tắt.
# Thay YOUR_AUTH_TOKEN bằng token của bạn nếu cần
# ngrok http 8080 --authtoken=YOUR_AUTH_TOKEN
ngrok http 8080
