📘 BÀI TẬP LỚN – Lập Trình Với Python
Phân tích dữ liệu cầu thủ EPL 2024–2025
🎓 Học viện Công nghệ Bưu chính Viễn thông – PTIT
📍 Khoa Công nghệ Thông tin

Giảng viên hướng dẫn: Kim Ngọc Bách
Nhóm thực hiện: 18

Họ và tên	MSSV
Vũ Trung Đức	B23DCKH030
Ngô Văn Phương	B23DCKH086
Lê Việt Hoàng	B23DCKH044
📌 Giới thiệu chung

Bài tập lớn yêu cầu xây dựng hệ thống thu thập – phân tích – tra cứu – trực quan hóa dữ liệu cầu thủ Premier League mùa 2024–2025 với Python, bao gồm:

✔ Web crawling (Selenium / undetected_chromedriver)
✔ Lưu trữ SQLite
✔ Flask REST API
✔ Tra cứu qua terminal
✔ Phân tích thống kê – median/mean/std
✔ Định giá cầu thủ bằng học máy (Random Forest Regression)
✔ Phân cụm K-Means + trực quan PCA

📂 Cấu trúc thư mục (đề xuất)
BTL-Python/
│
├── CODE/
│   ├── src/
│   │   ├── crawler/         # Thu thập dữ liệu FBref + FootballTransfers
│   │   ├── api/             # Flask API + lookup tool
│   │   ├── analysis/        # Thống kê, ML valuation, KMeans, PCA
│   │   └── database/        # Tạo DB, merge bảng
│   └── ...
│
├── data/
│   ├── stats.db             # CSDL SQLite chính
│   ├── raw/                 # CSV gốc sau khi crawl FBref
│   └── lookup_results/      # Kết quả tra cứu
│
└── REPORT/
    └── BTL_Python_Report.pdf

🧩 I. THU THẬP DỮ LIỆU (4 điểm)
I.1 – Thu thập thống kê cầu thủ từ FBref
✔ Yêu cầu:

Lấy toàn bộ chỉ số cầu thủ thi đấu > 90 phút tại EPL 2024–2025.

Crawl từ các bảng: stats, shooting, passing, possession, defense, misc, gca, playing time…

Gộp thành một bảng duy nhất → lưu vào SQLite (PLAYER_STATS).

Chỉ số không tồn tại → để "N/A".

✔ Kỹ thuật & Thư viện:

undetected_chromedriver, selenium, BeautifulSoup

pandas, sqlite3

Chống captcha / rate-limit:

Random sleep 3–6s

Stealth Chrome

Retry 2 lần khi Timeout

✔ Output:

SQLite table: PLAYER_STATS

CSV: data/raw/player_stats.csv

I.2 – Thu thập giá trị chuyển nhượng từ FootballTransfers
✔ Yêu cầu:

Tìm kiếm từng cầu thủ từ bảng PLAYER_STATS.

Thu thập trường player-tag chứa giá trị chuyển nhượng (VD: “€85M”).

Nếu không có: "N/A"

Lưu vào bảng SQLite PLAYER_VALUES.

✔ Kỹ thuật:

Selenium + Stealth Mode (selenium_stealth)

WebDriverWait để tránh lỗi tải trang

✔ Output:

PLAYER_VALUES

value_lookup.csv (tùy chọn)

🧩 II. API TRA CỨU DỮ LIỆU (2 điểm)
II.1 – Flask REST API
✔ Endpoint hỗ trợ:
Endpoint	Chức năng
/player?name=<tên>	Trả về toàn bộ chỉ số của 1 cầu thủ
/club?club=<CLB>	Trả về toàn bộ danh sách cầu thủ của CLB
✔ Công nghệ:

Flask

SQLite

Query helper: query_db() trả về list of dict để jsonify dễ dàng.

II.2 – Công cụ tra cứu qua terminal
Câu lệnh chạy:
python lookup.py --name "Haaland"
python lookup.py --club "Manchester City"

✔ Output:

In bảng ra màn hình

Lưu file CSV vào data/lookup_results/

VD: Haaland_lookup.csv, Manchester_City_lookup.csv

🧩 III. PHÂN TÍCH THỐNG KÊ (2 điểm)
III.1 – Median, Mean, Std theo từng đội
✔ Yêu cầu:

Tính median – mean – std của mọi chỉ số per–team.

Xuất file CSV:

team_summary_stats.csv

best_team_each_metric.csv

Tìm đội mạnh nhất theo từng chỉ số

Tính đội phong độ tổng thể tốt nhất EPL 2024–2025.

✔ Phương pháp:

Drop các cột không liên quan (Player, Age, Min, Pos…)

Ép toàn bộ numerical column → numeric

Loại chỉ số tiêu cực (foul, lỗi, mất bóng…)

Chỉ giữ metric tích cực để đánh giá

III.2 – Phương pháp tự động định giá cầu thủ
✔ Pipeline dự đoán giá trị:

Feature engineering:

Stats: Gls, Ast, xG, xAG, PrgP, Tkl, Int, Cmp%, Age, Min…

Categorical: Pos, Squad (OneHot)

Chuẩn hóa: StandardScaler

Thuật toán: RandomForestRegressor

Đánh giá:

MAE

R²

Vẽ biểu đồ predicted vs actual

✔ Output:

predicted_values.csv

Biểu đồ scatter

🧩 IV. PHÂN CỤM VÀ TRỰC QUAN (2 điểm)
IV.1 – K-means Clustering
✔ Quy trình:

Làm sạch & chuẩn hóa dữ liệu

Chọn K dựa trên:

Elbow → K = 4

Silhouette → K = 2 nhưng không hiệu quả

Quyết định chọn K = 4 để phân loại chi tiết hơn.

✔ Nhận xét 4 nhóm:

Nhóm 1 – Thủ môn

Nhóm 2 – Hậu vệ / tiền vệ trụ (phòng ngự mạnh)

Nhóm 3 – Tiền đạo / cầu thủ tấn công (Gls, Ast cao)

Nhóm 4 – Tiền vệ đa năng (balanced)

IV.2 – PCA Visualization
✔ Mục tiêu:

Giảm chiều → 2D và 3D

Vẽ scatter plot:

Matplotlib (2D)

Plotly (3D)

✔ Output:

pca_2d.png

pca_3d.html (interactive)

📝 Hướng dẫn chạy chương trình
1️⃣ Cài đặt môi trường
pip install -r requirements.txt

2️⃣ Crawl dữ liệu
python -m CODE.src.crawler.fbref_crawler
python -m CODE.src.crawler.value_crawler

3️⃣ Chạy Flask API
python -m CODE.src.api.app

4️⃣ Tra cứu
python -m CODE.src.api.lookup --name "Salah"
python -m CODE.src.api.lookup --club "Arsenal"

5️⃣ Phân tích thống kê
python -m CODE.src.analysis.team_stats

6️⃣ Định giá cầu thủ
python -m CODE.src.analysis.pretend_valuation

7️⃣ KMeans & PCA
python -m CODE.src.analysis.kmeans_clustering
python -m CODE.src.analysis.pca_visualization

📤 Hướng dẫn nộp bài

Mỗi nhóm tối đa 3 thành viên

Nộp mã nguồn + báo cáo PDF

Repo GitHub để private

Add giảng viên: bachknk49@gmail.com

Cấu trúc repo:

/REPORT   → chứa báo cáo PDF
/CODE     → chứa toàn bộ source code

🎯 Kết luận

Dự án đã hoàn thiện đầy đủ:

Thu thập dữ liệu EPL

Lưu trữ & xây dựng API

Công cụ tra cứu terminal

Phân tích thống kê

Định giá bằng học máy

Phân cụm KMeans và PCA

Hệ thống được xây dựng module hoá, chạy tự động, phục vụ đầy đủ yêu cầu bài tập lớn.