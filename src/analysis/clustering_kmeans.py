# -*- coding: utf-8 -*-
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import warnings
warnings.filterwarnings('ignore')

# ==================== 1. ĐỌC DỮ LIỆU ====================
print("Đang đọc dữ liệu từ stats.db...")
conn = sqlite3.connect("data/stats.db")
df = pd.read_sql_query("SELECT * FROM PLAYER_STATS", conn)
conn.close()
print(f"Đã tải {len(df):,} cầu thủ")

# ==================== 2. LOẠI BỎ CÁC CỘT KHÔNG DÙNG ====================
ban_list = [
    'Player', 'Squad', 'Nation', 'Pos', 'Born', 'Matches',
    'Age', 'MP', 'Starts', 'Min', '90s',
    'Mn/MP', 'Min%', 'Mn/Start', 'Mn/Sub', 'Compl', 'Subs', 'unSub', 'PPM',
    'onG', 'onGA', '+/-', '+/-90', 'On-Off', 'onxG', 'onxGA', 'xG+/-', 'xG+/-90', 'On-Off.1',
    '2CrdY', 'FK', 'CK', 'OG', 'Err'
]
df_clean = df.drop(columns=[c for c in ban_list if c in df.columns], errors='ignore')

# ==================== 3. GIỮ CHỈ SỐ PHONG CÁCH ====================
keep_cols = [
    'Gls.1', 'Ast.1', 'G+A.1', 'G-PK.1', 'xG.1', 'xAG.1', 'npxG.1',
    'PrgC', 'PrgP', 'PrgR', 'SCA90', 'GCA90', 'KP', '1/3', 'PPA', 'CrsPA',
    'Tkl', 'TklW', 'Int', 'Clr', 'Blocks', 'Recov',
    'GA90', 'Save%', 'CS%', 'PSxG+/-', 'Launch%', 'Cmp%', 'Opp', 'Stp%',
    'SoT%', 'G/Sh', 'Succ%', 'Tkld%', 'Won%'
]
final_cols = [c for c in keep_cols if c in df_clean.columns]
X_raw = df_clean[final_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
print(f"Sử dụng {len(final_cols)} chỉ số phong cách.")

# ==================== 4. CHUẨN HÓA DỮ LIỆU ====================
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_raw)

# ==================== 5. TÌM K TỐI ƯU: ELBOW + SILHOUETTE ====================
inertias, sil_scores = [], []
K_range = range(2, 12)

for k in K_range:
    km = KMeans(n_clusters=k, random_state=42, n_init=40, max_iter=800)
    km.fit(X_scaled)
    inertias.append(km.inertia_)
    sil_scores.append(silhouette_score(X_scaled, km.labels_))

# VẼ BIỂU ĐỒ
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16,6))

ax1.plot(K_range, inertias, 'bo-', linewidth=3)
ax1.set_title('Phương pháp Elbow', fontsize=16)
ax1.set_xlabel('k')
ax1.grid(True, alpha=0.3)

ax2.plot(K_range, sil_scores, 'rs-', linewidth=3)
ax2.set_title('Chỉ số Silhouette', fontsize=16)
ax2.set_xlabel('k')
ax2.grid(True, alpha=0.3)

best_k = 4  
ax1.axvline(best_k, color='green', linestyle='--', linewidth=2)
ax2.axvline(best_k, color='green', linestyle='--', linewidth=2)

plt.suptitle(f'Chọn số cụm tối ưu: {best_k}', fontsize=18)
plt.tight_layout()
plt.show()

print("\nSilhouette Scores:")
for k, s in zip(K_range, sil_scores):
    print(f"k={k}: {s:.4f}")

# ==================== 6. CHẠY K-MEANS ====================
kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=40, max_iter=800)
clusters = kmeans.fit_predict(X_scaled)

df['Cluster'] = clusters
df['Nhom'] = clusters

# ==================== 7. LƯU FILE CSV ====================
output_cols = ['Player', 'Squad', 'Nation', 'Pos', 'Age', 'Cluster']
existing_cols = [c for c in output_cols if c in df.columns]

df[existing_cols].to_csv("data/data_clusters.csv", index=False, encoding="utf-8-sig")

print("\n✅ ĐÃ LƯU THÀNH CÔNG → data_clusters.csv")
print("   Bao gồm:", ", ".join(existing_cols))
