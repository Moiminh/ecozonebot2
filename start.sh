#!/bin/bash

cleanup() {
    echo -e "\n[+] Đã nhận tín hiệu dừng."
    if [ ! -z "$BOT_PID" ]; then
        echo "[+] Đang dừng tiến trình của bot (PID: $BOT_PID)..."
        kill -SIGINT $BOT_PID
    fi
    echo "[+] Hoàn tất. Tạm biệt!"
    exit
}

trap cleanup INT EXIT

if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "[+] Đang khởi động bot Discord và dashboard Flask ở chế độ nền..."
python main.py &
BOT_PID=$!

echo "[+] Bot đang chạy với PID: $BOT_PID"
echo "[+] Đợi 2 giây để máy chủ web khởi động..."
sleep 2

echo "[+] Đang khởi động đường hầm với localhost.run cho cổng 8080..."
echo "[!] Nhấn Ctrl+C để dừng cả đường hầm và bot."

# Chạy localhost.run, tạo đường hầm tới cổng 8080
ssh -R 80:localhost:8080 localhost.run
