Gold Price Tracker
Gold Price Tracker là một ứng dụng Python giúp theo dõi và so sánh giá vàng thế giới (XAU) và giá vàng SJC (Việt Nam) theo thời gian thực. Ứng dụng hiển thị giá vàng thế giới (chuyển đổi sang VND/cây), giá vàng SJC, tỷ giá USD/VND, và tính toán chênh lệch phần trăm giữa hai loại giá vàng này. Dữ liệu được cập nhật tự động theo khoảng thời gian do người dùng chọn và lưu trữ trong cơ sở dữ liệu SQLite để theo dõi lịch sử.
Tính năng
Giá vàng thế giới: Trích xuất từ Trading Economics (USD/ounce) và chuyển đổi sang VND/cây.

Giá vàng SJC: Lấy từ vnstock.

Tỷ giá USD/VND: Lấy từ Vietcombank thông qua vnstock.

Chênh lệch (Basic): Tính phần trăm chênh lệch giữa giá vàng SJC và giá vàng thế giới.

Cập nhật tự động: Hỗ trợ cập nhật dữ liệu mỗi 1, 5 hoặc 10 phút theo lựa chọn của người dùng.

Lưu trữ lịch sử: Dữ liệu được lưu trong cơ sở dữ liệu SQLite (gold_prices.db).

Hiển thị màu sắc: Sử dụng màu sắc để biểu thị xu hướng tăng/giảm giá so với lần cập nhật trước.

Yêu cầu
Python: 3.x

Thư viện cần thiết:
requests

beautifulsoup4

sqlite3 (có sẵn trong Python)

vnstock

tabulate

colorama

pip install requests beautifulsoup4 vnstock tabulate colorama
