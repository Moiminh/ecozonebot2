#!/bin/bash

# Dừng lại ngay nếu có lỗi
set -e

echo "--- Bắt đầu Script khởi động (Phương pháp Base64) ---"

# 1. Giải mã khóa SSH từ biến môi trường
echo ">>> Đang thiết lập SSH..."
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Đọc biến môi trường, giải mã base64, và ghi vào file id_ed25519
echo "$SSH_PRIVATE_KEY" | base64 -d > ~/.ssh/id_ed25519
chmod 600 ~/.ssh/id_ed25519

# Tự động chấp nhận host của GitHub
ssh-keyscan github.com >> ~/.ssh/known_hosts

# 2. Clone kho chứa CSDL riêng tư
# !!! THAY ĐỔI ĐƯỜNG DẪN NÀY THÀNH CỦA BẠN !!!
DB_REPO_URL="git@github.com:minhbeo8/econzone-database.git" 
echo ">>> Đang clone CSDL từ $DB_REPO_URL..."

# Xóa thư mục data cũ và clone bản mới nhất
rm -rf data
git clone $DB_REPO_URL data

echo ">>> Clone CSDL thành công."

# 3. Chạy máy chủ web Gunicorn
echo ">>> Đang khởi động máy chủ Gunicorn..."
gunicorn dashboard:app --log-level debug --access-logfile - --error-logfile -

echo "--- Script khởi động hoàn tất ---"
