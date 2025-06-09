#!/bin/bash

# Hàm cleanup để dừng bot khi script bị tắt
cleanup() {
    echo -e "\n[+] Đã nhận tín hiệu dừng."
    if [ ! -z "$BOT_PID" ]; then
        echo "[+] Đang dừng tiến trình của bot (PID: $BOT_PID)..."
        kill -SIGINT $BOT_PID
    fi
    echo "[+] Hoàn tất. Tạm biệt!"
    exit
}

# Đặt bẫy để chạy hàm cleanup khi nhấn Ctrl+C
trap cleanup INT EXIT

# Đọc file .env
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "[+] Đang khởi động bot Discord và dashboard Flask ở chế độ nền..."
python main.py &
BOT_PID=$!

echo "[+] Bot đang chạy với PID: $BOT_PID"
echo "[+] Đợi 2 giây để máy chủ web khởi động..."
sleep 2

echo "[+] Đang khởi động đường hầm với localtunnel cho cổng 8080..."
echo "[!] Nhấn Ctrl+C để dừng cả đường hầm và bot."

# Chạy localtunnel với subdomain bạn muốn
lt --port 8080 --subdomain econzonebot
