import os
import sqlite3
import pandas as pd
import numpy as np
from tqdm import tqdm
from sentence_transformers import SentenceTransformer, util

# =========================================
# 1️⃣ Cấu hình đường dẫn
# =========================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "stats.db")
TRANSFER_CSV = os.path.join(DATA_DIR, "raw", "transfer_values_full.csv")
OUTPUT_CSV = os.path.join(DATA_DIR, "player_full_stats_vectorlite.csv")

os.makedirs(DATA_DIR, exist_ok=True)

# =========================================
# 2️⃣ Đọc dữ liệu
# =========================================
print("📥 Đang đọc dữ liệu...")

conn = sqlite3.connect(DB_PATH)
df_stats = pd.read_sql_query("SELECT * FROM player_stats", conn)
conn.close()
print(f"📊 Đã đọc {len(df_stats)} cầu thủ từ FBref (player_stats)")

df_trans = pd.read_csv(TRANSFER_CSV)
print(f"💶 Đã đọc {len(df_trans)} cầu thủ từ FootballTransfers (CSV)")

# =========================================
# 3️⃣ Hàm chuẩn hóa tên & CLB
# =========================================
def normalize_name(name):
    if not isinstance(name, str):
        return ""
    name = name.lower().strip()
    replacements = {
        "man utd": "manchester united",
        "man city": "manchester city",
        "spurs": "tottenham",
        "newcastle utd": "newcastle united",
        "bournemouthuth": "bournemouth",
        "b'mouth": "bournemouth",
        "nottingham forest forestest": "nottingham forest",
        "nott'ham forest": "nottingham forest",
        "c. palace": "crystal palace",
        "wolves": "wolverhampton wanderers",
    }
    for k, v in replacements.items():
        if k in name:
            name = name.replace(k, v)
    return name

df_stats["player_name_clean"] = df_stats["player_name"].apply(normalize_name)
df_stats["club_clean"] = df_stats["club"].apply(normalize_name)
df_trans["player_name_clean"] = df_trans["player_name"].apply(normalize_name)
df_trans["club_clean"] = df_trans["club"].apply(normalize_name)

# =========================================
# 4️⃣ Tạo văn bản ghép để nhúng vector
# =========================================
df_stats["key_text"] = df_stats["player_name_clean"] + " - " + df_stats["club_clean"]
df_trans["key_text"] = df_trans["player_name_clean"] + " - " + df_trans["club_clean"]

# =========================================
# 5️⃣ Tạo vector embedding
# =========================================
print("🧠 Đang tải mô hình SentenceTransformer...")
model = SentenceTransformer("all-MiniLM-L6-v2")

print("📦 Đang tạo embedding vector...")
emb_stats = model.encode(df_stats["key_text"].tolist(), convert_to_tensor=True, show_progress_bar=True)
emb_trans = model.encode(df_trans["key_text"].tolist(), convert_to_tensor=True, show_progress_bar=True)

# =========================================
# 6️⃣ So khớp vector theo cosine similarity
# =========================================
print("🔗 Đang ghép dữ liệu bằng cosine similarity...")

matched_records = []
for i, row in tqdm(enumerate(df_stats.itertuples()), total=len(df_stats)):
    query_emb = emb_stats[i]
    cosine_scores = util.cos_sim(query_emb, emb_trans)[0]
    best_idx = int(np.argmax(cosine_scores))
    best_score = float(cosine_scores[best_idx])

    if best_score < 0.75:  # ngưỡng để bỏ các ghép sai
        matched_row = {**row._asdict(), "skill_score": None, "potential_score": None, "market_value": "N/a", "similarity": best_score}
    else:
        trans_row = df_trans.iloc[best_idx]
        matched_row = {
            **row._asdict(),
            "skill_score": trans_row.get("skill_score", None),
            "potential_score": trans_row.get("potential_score", None),
            "market_value": trans_row.get("market_value", "N/a"),
            "similarity": round(best_score, 4),
        }
    matched_records.append(matched_row)

# =========================================
# 7️⃣ Tạo DataFrame kết quả
# =========================================
df_merge = pd.DataFrame(matched_records)

# Xử lý cột thừa (drop index tự động từ itertuples)
if "Index" in df_merge.columns:
    df_merge.drop(columns=["Index"], inplace=True, errors="ignore")

print(f"✅ Đã merge được {len(df_merge)} cầu thủ.")

# =========================================
# 8️⃣ Lưu dữ liệu ra CSV và SQLite
# =========================================
df_merge.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
print(f"📁 Đã lưu file CSV: {OUTPUT_CSV}")

conn = sqlite3.connect(DB_PATH)
df_merge.to_sql("player_full_stats_vectorlite", conn, if_exists="replace", index=False)
conn.close()
print(f"💾 Đã lưu bảng 'player_full_stats_vectorlite' vào CSDL: {DB_PATH}")

# =========================================
# 9️⃣ Báo cáo nhanh
# =========================================
print("\n📊 Báo cáo:")
print(f"  🔸 Tổng cầu thủ FBref: {len(df_stats)}")
print(f"  🔸 Tổng cầu thủ Transfer: {len(df_trans)}")
print(f"  🔸 Trung bình độ tương đồng: {df_merge['similarity'].mean():.3f}")
print("🎯 Hoàn tất merge_data_vector_lite.py!")
