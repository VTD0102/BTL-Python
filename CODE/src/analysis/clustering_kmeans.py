import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from mpl_toolkits.mplot3d import Axes3D
import warnings
warnings.filterwarnings("ignore")
import os
# 1 Đọc dữ liệu
print(" Đang tải dữ liệu từ cơ sở dữ liệu SQLite...")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "stats.db")
conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query("SELECT * FROM PLAYER_STATS", conn)
conn.close()

print(f"Đã đọc {len(df)} cầu thủ, {len(df.columns)} cột dữ liệu.\n")

# 2️ Tiền xử lý dữ liệu
# Loại bỏ các cột không dùng cho phân cụm
drop_cols = [    'Player', 'Squad', 'Nation', 'Pos', 'Born', 'Matches',
    'Age', 'MP', 'Starts', 'Min', '90s',
    'Mn/MP', 'Min%', 'Mn/Start', 'Mn/Sub', 'Compl', 'Subs', 'unSub', 'PPM',
    'onG', 'onGA', '+/-', '+/-90', 'On-Off', 'On-Off.1',
    '2CrdY', 'FK', 'CK', 'OG', 'Err',

#loại bỏ các cột thể hiện các chỉ số phụ thuộc vào thời gian ra sân
    'Gls', 'Ast', 'G+A', 'G-PK', 'xG','npxG', 'xAG', 'npxG+xAG' 
    'GA', 'SoTA', 'Saves', 'CS', 'PSxG', 
    'Sh', 'SoT', 'TotDist', 'PrgDist', 'SCA', 'GCA', 'Tkl', 'Touches'
    ]
numeric_df = df.drop(columns=drop_cols, errors="ignore").copy()

print("Các cột được sử dụng cho K-Means:")
for i, col in enumerate(numeric_df.columns, 1):
    print(f"{i:3}. {col}")
print(f"\nTổng cộng: {len(numeric_df.columns)} cột được dùng.")

# Chuyển toàn bộ cột về dạng số
numeric_df = numeric_df.apply(pd.to_numeric, errors='coerce')

# Điền toàn bộ giá trị N/A bằng 0
numeric_df = numeric_df.fillna(0)
print("Đã thay toàn bộ giá trị N/A bằng 0.\n")

# 3 Chuẩn hóa dữ liệu
scaler = StandardScaler()
X_scaled = scaler.fit_transform(numeric_df)

print(f" Dữ liệu đã được chuẩn hóa (StandardScaler). Tổng số đặc trưng: {X_scaled.shape[1]}\n")

# 4 Tìm số cụm tối ưu (Elbow & Silhouette)

print(" Đang tìm số cụm tối ưu...")

inertias = []
sil_scores = []
K = range(2, 11)

for k in K:
    kmeans = KMeans(n_clusters=k, random_state=0, n_init=10)
    kmeans.fit(X_scaled)
    inertias.append(kmeans.inertia_)
    labels = kmeans.labels_
    sil_scores.append(silhouette_score(X_scaled, labels))

fig1, axes = plt.subplots(1, 2, figsize=(12, 5))

# Elbow Method
axes[0].plot(K, inertias, 'o-', color='blue')
axes[0].set_xlabel('Số cụm (k)')
axes[0].set_ylabel('Inertia')
axes[0].set_title('Elbow Method - Xác định số cụm tối ưu')

# Silhouette Method
axes[1].plot(K, sil_scores, 'o-', color='green')
axes[1].set_xlabel('Số cụm (k)')
axes[1].set_ylabel('Silhouette Score')
axes[1].set_title('Silhouette Method - Đánh giá chất lượng cụm')

plt.tight_layout()
plt.show()



