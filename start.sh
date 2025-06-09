#!/bin/bash

# Hàm cleanup không thay đổi
cleanup() {
    echo -e "\n[+] Đã nhận tín hiệu dừng từ ngrok hoặc người dùng."
    if [ ! -z "$BOT_PID" ]; then
        echo "[+] Đang dừng tiến trình của bot (PID: $BOT_PID)..."
        kill -SIGINT $BOT_PID
    fi
    echo "[+] Hoàn tất. Tạm biệt!"
    exit
}

trap cleanup INT EXIT

# --- Bắt đầu script chính ---

# [THAY ĐỔI] Đọc các biến từ file .env
if [ -f .env ]; then
    echo "[+] Đang đọc cấu hình từ file .env..."
    # Lọc ra các dòng không phải là comment và export chúng thành biến môi trường
    export $(grep -v '^#' .env | xargs)
else
    echo "[!] Cảnh báo: Không tìm thấy file .env."
fi

echo "[+] Đang khởi động bot Discord và dashboard Flask ở chế độ nền..."
python main.py &
BOT_PID=$!

echo "[+] Bot đang chạy với PID: $BOT_PID"
echo "[+] Đợi 2 giây để máy chủ web khởi động..."
sleep 2

echo "[+] Đang khởi động ngrok cho cổng 8080..."
echo "[!] Nhấn Ctrl+C để dừng cả ngrok và bot."

# [THAY ĐỔI] Sử dụng biến NGROK_AUTH_TOKEN đã được đọc từ file .env
# Nếu biến NGROK_AUTH_TOKEN có tồn tại, sử dụng nó. Nếu không, chạy ngrok không có token.
if [ ! -z "$NGROK_AUTH_TOKEN" ]; then
    echo "[+] Tìm thấy NGROK_AUTH_TOKEN, đang sử dụng để xác thực."
    ngrok http 8080 --authtoken=$NGROK_AUTH_TOKEN
else
    echo "[!] Không tìm thấy NGROK_AUTH_TOKEN, chạy ngrok không xác thực."
    ngrok http 8080 --region ap
fi
