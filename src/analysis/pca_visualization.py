import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
import warnings
warnings.filterwarnings('ignore')
# ==================== 1. ĐỌC DỮ LIỆU ====================
print("Đang đọc dữ liệu từ stats.db...")
conn = sqlite3.connect("data/stats.db")
df = pd.read_sql_query("SELECT * FROM PLAYER_STATS", conn)
conn.close()
print(f"Đã tải {len(df):,} cầu thủ")
# ==================== 2. LOẠI BỎ CÁC CỘT GÂY LỆCH ====================
ban_list = [
    'Player', 'Squad', 'Nation', 'Pos', 'Born', 'Matches',
    'Age', 'MP', 'Starts', 'Min', '90s',
    'Mn/MP', 'Min%', 'Mn/Start', 'Mn/Sub', 'Compl', 'Subs', 'unSub', 'PPM',
    'onG', 'onGA', '+/-', '+/-90', 'On-Off', 'onxG', 'onxGA', 'xG+/-', 'xG+/-90', 'On-Off.1',
    '2CrdY', 'FK', 'CK', 'OG', 'Err'
]
df_clean = df.drop(columns=[c for c in ban_list if c in df.columns], errors='ignore')
# ==================== 3. GIỮ LẠI CHỈ SỐ PHONG CÁCH ====================
keep_cols = [
    'Gls.1', 'Ast.1', 'G+A.1', 'G-PK.1', 'xG.1', 'xAG.1', 'npxG.1',
    'PrgC', 'PrgP', 'PrgR', 'SCA90', 'GCA90', 'KP', '1/3', 'PPA', 'CrsPA',
    'Tkl', 'TklW', 'Int', 'Clr', 'Blocks', 'Recov',
    'GA90', 'Save%', 'CS%', 'PSxG+/-', 'Launch%', 'Cmp%', 'Opp', 'Stp%',
    'SoT%', 'G/Sh', 'Succ%', 'Tkld%', 'Won%'
]
final_cols = [c for c in keep_cols if c in df_clean.columns]
X_raw = df_clean[final_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
print(f"Sử dụng {len(final_cols)} chỉ số phong cách thuần túy.")
# ==================== 4. CHUẨN HÓA ====================
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_raw)

# ==================== 5. K-MEANS VỚI 4 NHÓM ====================
kmeans = KMeans(n_clusters=4, random_state=42, n_init=40, max_iter=800)
clusters = kmeans.fit_predict(X_scaled)
df['Cluster'] = clusters
df['Nhom'] = df['Cluster']
# ==================== 6. PCA 2D ====================
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
# ==================== 7. PCA 3D ====================
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
