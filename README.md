# Bot Kinh Tế EconZone 🤖

EconZone là một bot Discord kinh tế đa năng được xây dựng bằng `nextcord`, mang đến một thế giới ảo với nhiều hệ thống phức tạp và thú vị. Người chơi có thể làm việc, kinh doanh, phạm tội, du lịch giữa các server và tương tác với một nền kinh tế năng động.

## ✨ Tính năng nổi bật

* **Hệ thống Kinh tế Kép:** Bot quản lý hai loại ví riêng biệt:
    * **Ví Local:** Tiền tệ và vật phẩm kiếm được trong một server cụ thể.
    * **Ví Global (Bank):** Tài khoản ngân hàng toàn cục, an toàn và có thể truy cập từ bất kỳ server nào.
* **Tiền tệ Đa dạng:**
    * **🪙 Ecoin (Tiền Sạch):** Kiếm được từ các hoạt động hợp pháp.
    * **🧪 Ecobit (Tiền Lậu):** Kiếm được từ các hoạt động phi pháp hoặc từ admin, cần được "rửa" để sử dụng an toàn.
* **Hệ thống Sinh tồn:** Người chơi cần quản lý các chỉ số Máu (❤️), Năng lượng (⚡), và Độ no (🍔). Các hoạt động sẽ tiêu tốn chỉ số này, cần được hồi phục bằng vật phẩm.
* **Cơ chế Du lịch & Balo độc đáo:** Khi người chơi di chuyển sang một server mới, họ có thể sử dụng "Balo" để mang theo một số vật phẩm từ server cũ.
* **Hệ thống Visa:** Cho phép người chơi tạo thẻ thanh toán di động để quản lý tài chính linh hoạt hơn giữa các server.
* **Nhiều cách Kiếm tiền:** Từ làm việc (`!work`), nhận thưởng hàng ngày (`!daily`), câu cá (`!fish`) đến các hoạt động mạo hiểm hơn như phạm tội (`!crime`) và cướp (`!rob`).
* **Cờ bạc & Giải trí:** Thử vận may với các trò chơi như `!slots`, `!dice`, và `!coinflip`.
* **Cửa hàng & Vật phẩm:** Hệ thống shop động, người chơi có thể mua, bán và sử dụng các vật phẩm đa dạng.
* **Hệ thống Moderator:** Các công cụ mạnh mẽ dành cho moderator để quản lý kinh tế của người chơi.
* **Hệ thống Level & Danh hiệu:** Người chơi nhận XP và lên cấp để mở khóa các danh hiệu và quyền lợi mới.

## 🛠️ Cài đặt và Khởi chạy

Để chạy bot này trên máy của bạn, hãy làm theo các bước sau:

### Yêu cầu

* Python 3.10 trở lên
* Git

### Các bước cài đặt

1.  **Clone Repository**
    * Sao chép dự án này về máy của bạn:
        ```bash
        git clone <URL_repository_của_bạn>
        cd <tên_thư_mục_dự_án>
        ```

2.  **Cài đặt các gói phụ thuộc**
    * Tạo một môi trường ảo (khuyến khích) và cài đặt các thư viện cần thiết từ file `requirements.txt`:
        ```bash
        # Tạo môi trường ảo (tùy chọn nhưng nên làm)
        python -m venv venv
        source venv/bin/activate  # Trên Windows: venv\Scripts\activate

        # Cài đặt các gói
        pip install -r requirements.txt
        ```

3.  **Cấu hình Biến môi trường**
    * Tạo một file mới trong thư mục gốc của dự án và đặt tên là `.env`.
    * Sao chép nội dung dưới đây vào file `.env` và điền các giá trị của bạn vào:
        ```env
        # Lấy từ Discord Developer Portal
        BOT_TOKEN=Your_Discord_Bot_Token_Here

        # (Tùy chọn) Lấy từ Google AI Studio nếu bạn muốn dùng tính năng AI
        GEMINI_API_KEY=Your_Google_AI_API_Key_Here

        # (Tùy chọn) Lấy từ một kênh Discord để ghi log lỗi
        DISCORD_WEBHOOK_URL=Your_Discord_Webhook_URL_Here
        ```
    * **QUAN TRỌNG:** Hãy chắc chắn rằng file `.env` đã được thêm vào file `.gitignore` của bạn để không làm lộ token.

4.  **Cấu hình Moderator (Tùy chọn)**
    * Mở file `moderators.json`.
    * Thêm ID của những người dùng bạn muốn cấp quyền moderator cho bot vào danh sách `moderator_ids`.
        ```json
        {
          "moderator_ids": [1370417047070048276, 123456789012345678]
        }
        ```

5.  **Chạy Bot**
    * Sau khi hoàn tất các bước trên, khởi động bot bằng lệnh:
        ```bash
        python main.py
        chmod +x start.sh
        ./start.sh
        ```

## 📖 Hướng dẫn sử dụng

Sau khi mời bot vào server của bạn, người dùng có thể bắt đầu bằng các lệnh sau:

* `/howtoplay`: Mở sách hướng dẫn chi tiết về các luật chơi và cơ chế của game.
* `/menu`: Xem danh sách các lệnh có sẵn và cách sử dụng chi tiết của từng lệnh.

## 📂 Cấu trúc Thư mục

```
├── cogs/             # Chứa các module lệnh (cogs) được phân loại theo chức năng
│   ├── admin/
│   ├── earn/
│   ├── economy/
│   └── ...
├── core/             # Chứa logic cốt lõi của bot
│   ├── bot.py
│   ├── database.py
│   ├── checks.py
│   └── ...
├── data/             # (Nên tạo) Để chứa các file dữ liệu
│   ├── economy.json
│   ├── items.json
│   └── moderators.json
├── logs/             # Thư mục chứa các file log hoạt động của bot
├── .env              # File cấu hình biến môi trường (token, API key) - KHÔNG ĐƯA LÊN GITHUB
├── .gitignore        # Các file và thư mục mà Git sẽ bỏ qua
├── main.py           # Điểm khởi đầu của bot
└── requirements.txt  # Danh sách các thư viện Python cần thiết
```
