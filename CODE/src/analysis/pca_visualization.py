import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import seaborn as sns
import plotly.express as px
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from mpl_toolkits.mplot3d import Axes3D
import warnings
warnings.filterwarnings("ignore")

# 1️ Đọc dữ liệu
print("Đang tải dữ liệu từ cơ sở dữ liệu SQLite...")
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "stats.db")
conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query("SELECT * FROM PLAYER_STATS", conn)
conn.close()

print(f"Đã đọc {len(df)} cầu thủ, {len(df.columns)} cột dữ liệu.\n")

# 2 Tiền xử lý dữ liệu
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
# Chuyển toàn bộ cột về dạng số
numeric_df = numeric_df.apply(pd.to_numeric, errors='coerce')

# Điền toàn bộ giá trị N/A bằng 0
numeric_df = numeric_df.fillna(0)

# 3 Chuẩn hóa dữ liệu
scaler = StandardScaler()
X_scaled = scaler.fit_transform(numeric_df)

# 4. K-MEANS VỚI 4 NHÓM 
optimal_k = 4  
print(f"\n Tiến hành phân cụm với k = {optimal_k}...\n")

kmeans = KMeans(n_clusters=optimal_k, random_state=0, n_init=40)
clusters = kmeans.fit_predict(X_scaled)
df['Cluster'] = clusters
df['Nhom'] = df['Cluster']
print("Số lượng cầu thủ trong mỗi cụm:")
print(df["Cluster"].value_counts(), "\n")
# 5. PCA 2D 
pca2 = PCA(n_components=2)
X_2d = pca2.fit_transform(X_scaled)
plt.figure(figsize=(15,10))
scatter = plt.scatter(X_2d[:,0], X_2d[:,1], c=clusters, cmap='tab10', s=60, alpha=0.8)
plt.title('Phân cụm K-Means (PCA 2D) – 4 nhóm', fontsize=18, fontweight='bold')
plt.xlabel(f'PC1 ({pca2.explained_variance_ratio_[0]:.1%} variance)')
plt.ylabel(f'PC2 ({pca2.explained_variance_ratio_[1]:.1%} variance)')
plt.colorbar(scatter, label='Nhóm')
plt.grid(True, alpha=0.3)
plt.show()
#  6. PCA 3D 
pca3 = PCA(n_components=3)
X_3d = pca3.fit_transform(X_scaled)
# TẠO DATAFRAME ĐỂ HOVER_DATA CHẠY ĐƯỢC
data_3d = pd.DataFrame(X_3d, columns=['PC1', 'PC2', 'PC3'])
data_3d['Nhom'] = df['Nhom'].astype(str)
data_3d['Player'] = df['Player']
data_3d['Squad'] = df['Squad']
data_3d['Pos'] = df['Pos']
fig = px.scatter_3d(
    data_3d, x='PC1', y='PC2', z='PC3',
    color='Nhom',
    hover_name='Player',
    hover_data=['Squad', 'Pos'],
    title='Phân cụm K-Means (PCA 3D) – 4 nhóm',
    width=1000, height=700
)
fig.update_traces(marker=dict(size=4))
fig.show()

# 7 Xuất file kết quả

output_cols = ['Player', 'Squad', 'Nation', 'Pos', 'Age', 'Cluster']
existing_cols = [c for c in output_cols if c in df.columns]

df[existing_cols].to_csv("data/data_clusters.csv", index=False, encoding="utf-8-sig")

print("\nĐÃ LƯU THÀNH CÔNG → clusters.csv")
print("   Bao gồm:", ", ".join(existing_cols))

