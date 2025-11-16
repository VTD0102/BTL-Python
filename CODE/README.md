📘 BÀI TẬP LỚN – Lập Trình Với Python
Phân tích dữ liệu cầu thủ Premier League 2024–2025
🎓 Học Viện Công Nghệ Bưu Chính Viễn Thông – PTIT
📍 Khoa Công Nghệ Thông Tin

Giảng viên hướng dẫn: Kim Ngọc Bách

Nhóm thực hiện: 18

Họ và tên	MSSV
Vũ Trung Đức	B23DCKH030
Ngô Văn Phương	B23DCKH086
Lê Việt Hoàng	B23DCKH044
📂 Cấu trúc thư mục dự án

Dự án được tổ chức đúng chuẩn theo yêu cầu BTL:

BTL-PYTHON/
│
├── Báo cáo/
│   └── Báo cáo bài tập lớn.pdf
│
├── CODE/
│   ├── data/
│   │   ├── raw/
│   │   │   └── player_stats.csv
│   │   ├── lookup_results/          # Lưu kết quả tra cứu
│   │   ├── predicted_values.csv
│   │   ├── best_team_each_metric.csv
│   │   ├── team_summary_stats.csv
│   │   └── stats.db                  # SQLite database
│   │
│   └── src/
│       ├── crawler/
│       │   ├── fbref_crawler.py      # Crawl stats FBref
│       │   └── transfer_crawler.py   # Crawl giá chuyển nhượng
│       │
│       ├── api/
│       │   ├── app.py                # Flask REST API
│       │   └── lookup.py             # Tool tra cứu CLI
│       │
│       └── analysis/
│           ├── stats_analysis.py     # Median/mean/std + best team
│           ├── pretend_valuation.py  # ML định giá cầu thủ
│           ├── clustering_kmeans.py  # KMeans phân cụm
│           └── pca_visualization.py  # PCA 2D/3D visualization
│
└── README.md

🧩 I. THU THẬP DỮ LIỆU (4 điểm)
I.1 Crawl dữ liệu thống kê từ FBref

Thu thập dữ liệu tất cả cầu thủ thi đấu > 90 phút EPL 2024–2025

Crawl từ 11 bảng thống kê (stats, shooting, passing, defense, possession, misc, keepers, …)

Kết hợp thành một bảng duy nhất → PLAYER_STATS trong stats.db

Xuất file CSV: /CODE/data/raw/player_stats.csv

🏷️ Chạy:
python -m CODE.src.crawler.fbref_crawler

I.2 Crawl giá chuyển nhượng từ FootballTransfers

Tìm kiếm từng cầu thủ theo tên

Thu thập giá trị chuyển nhượng (VD: €78M)

Nếu không có → "N/A"

Lưu vào bảng PLAYER_VALUES

🏷️ Chạy:
python -m CODE.src.crawler.transfer_crawler

🧩 II. XÂY DỰNG API & TRA CỨU (2 điểm)
II.1 Flask REST API
✔ Các endpoint:
Endpoint	Mô tả
/player?name=	Tra cứu theo tên cầu thủ
/club?club=	Tra cứu theo tên câu lạc bộ
🏷️ Chạy server:
python -m CODE.src.api.app


API mặc định chạy tại:

http://127.0.0.1:5000

II.2 Tool tra cứu qua dòng lệnh (lookup)
🏷️ Tra cứu cầu thủ:
python -m CODE.src.api.lookup --name "Haaland"

🏷️ Tra cứu CLB:
python -m CODE.src.api.lookup --club "Manchester City"


Kết quả:

In bảng ra terminal

Lưu file CSV vào CODE/data/lookup_results/

🧩 III. PHÂN TÍCH THỐNG KÊ (2 điểm)
III.1 Tính median – mean – std theo từng đội

Tính thống kê từng chỉ số của mỗi đội

Loại bỏ chỉ số tiêu cực

Tìm đội mạnh nhất theo từng chỉ số

Tính đội có phong độ tổng thể tốt nhất EPL

🏷️ Chạy:
python -m CODE.src.analysis.stats_analysis

📁 Output:

team_summary_stats.csv

best_team_each_metric.csv

III.2 Định giá cầu thủ bằng Machine Learning

Dùng RandomForestRegressor

Feature gồm thống kê cầu thủ + vị trí + đội bóng

Chuẩn hóa numeric + OneHotEncode categorical

Train/test split

Tính sai số MAE, R²

Xuất bảng giá trị dự đoán

🏷️ Chạy:
python -m CODE.src.analysis.pretend_valuation

📁 Output:

predicted_values.csv

Biểu đồ value_actual vs value_predicted

🧩 IV. PHÂN CỤM & TRỰC QUAN (2 điểm)
IV.1 Phân cụm K-Means

Chuẩn hóa dữ liệu

Chạy K từ 2 → 10

Vẽ Elbow + Silhouette

Quyết định chọn K = 4

🏷️ Chạy:
python -m CODE.src.analysis.clustering_kmeans

IV.2 Visualization PCA 2D & 3D

PCA giảm chiều để trực quan hóa

Vẽ scatter plot 2D (Matplotlib)

Vẽ 3D interactive (Plotly)

🏷️ Chạy:
python -m CODE.src.analysis.pca_visualization

🚀 Hướng dẫn cài đặt
1) Tạo môi trường
pip install -r requirements.txt

2) Chạy tuần tự:
1. Crawl FBref stats
2. Crawl transfer values
3. Chạy Flask API
4. lookup.py để tra cứu
5. stats_analysis để tính thống kê
6. pretend_valuation để định giá cầu thủ
7. clustering_kmeans để phân cụm
8. pca_visualization để vẽ biểu đồ PCA

📤 Hướng dẫn nộp bài

Tối đa 3 thành viên / nhóm

Nộp source code + báo cáo PDF

Tạo GitHub repo: private

Add giảng viên: bachknk49@gmail.com

Repo gồm:

/Báo cáo      → file PDF
/CODE         → toàn bộ code


Deadline: 23:59 – Chủ Nhật, 16/11/2025

🎯 Kết luận

Dự án hoàn thiện đầy đủ yêu cầu BTL:

✔ Crawl dữ liệu tự động

✔ Lưu trữ SQLite

✔ Xây dựng API

✔ Tool tra cứu CLI

✔ Phân tích thống kê

✔ Dự đoán giá trị cầu thủ bằng ML

✔ Phân cụm KMeans

✔ PCA visualization

Hệ thống hoạt động hoàn chỉnh, có thể chạy demo trực tiếp trên lớp.