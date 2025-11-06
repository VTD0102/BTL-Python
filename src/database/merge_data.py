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
# 2️⃣ Đọc dữ liệu từ SQLite và CSV
# =========================================
print("📥 Đang đọc dữ liệu từ cơ sở dữ liệu và CSV...")

conn = sqlite3.connect(DB_PATH)

# ⚙️ SỬA Ở ĐÂY — đọc bảng 'stats' thay vì 'player_stats'
try:
    df_stats = pd.read_sql_query("SELECT * FROM stats", conn)
    print(f"📊 Đã đọc {len(df_stats)} cầu thủ từ FBref (bảng stats)")
except Exception as e:
    print(f"❌ Không thể đọc bảng 'stats': {e}")
    conn.close()
    exit(1)

conn.close()

try:
    df_trans = pd.read_csv(TRANSFER_CSV)
    print(f"💶 Đã đọc {len(df_trans)} cầu thủ từ FootballTransfers (CSV)")
except Exception as e:
    print(f"❌ Lỗi đọc file transfer_values_full.csv: {e}")
    exit(1)

# =========================================
# 3️⃣ Chuẩn hóa tên và câu lạc bộ
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
        "b'mouth": "bournemouth",
        "nott'ham forest": "nottingham forest",
        "c. palace": "crystal palace",
        "wolves": "wolverhampton wanderers",
    }
    for k, v in replacements.items():
        if k in name:
            name = name.replace(k, v)
    return name

# Tự động phát hiện cột tên cầu thủ và CLB
player_col = "Player" if "Player" in df_stats.columns else "player_name"
club_col = "Squad" if "Squad" in df_stats.columns else "club"

df_stats["player_name_clean"] = df_stats[player_col].apply(normalize_name)
df_stats["club_clean"] = df_stats[club_col].apply(normalize_name)

df_trans["player_name_clean"] = df_trans["player_name"].apply(normalize_name)
df_trans["club_clean"] = df_trans["club"].apply(normalize_name)

# =========================================
# 4️⃣ Tạo khóa văn bản cho vector embedding
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
# 6️⃣ Ghép dữ liệu bằng cosine similarity
# =========================================
print("🔗 Đang ghép dữ liệu (so khớp cầu thủ FBref ↔ Transfer)...")

matched_records = []
for i, row in tqdm(enumerate(df_stats.itertuples()), total=len(df_stats)):
    query_emb = emb_stats[i]
    cosine_scores = util.cos_sim(query_emb, emb_trans)[0]
    best_idx = int(np.argmax(cosine_scores))
    best_score = float(cosine_scores[best_idx])

    if best_score < 0.75:  # bỏ ghép sai
        matched_row = {
            **row._asdict(),
            "skill_score": None,
            "potential_score": None,
            "market_value": "N/A",
            "similarity": round(best_score, 4)
        }
    else:
        trans_row = df_trans.iloc[best_idx]
        matched_row = {
            **row._asdict(),
            "skill_score": trans_row.get("skill_score", None),
            "potential_score": trans_row.get("potential_score", None),
            "market_value": trans_row.get("market_value", "N/A"),
            "similarity": round(best_score, 4)
        }

    matched_records.append(matched_row)

# =========================================
# 7️⃣ Lưu dữ liệu kết quả
# =========================================
df_merge = pd.DataFrame(matched_records)

if "Index" in df_merge.columns:
    df_merge.drop(columns=["Index"], inplace=True, errors="ignore")

df_merge.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
print(f"💾 Đã lưu file CSV hợp nhất: {OUTPUT_CSV}")

conn = sqlite3.connect(DB_PATH)
df_merge.to_sql("player_full_stats_vectorlite", conn, if_exists="replace", index=False)
conn.close()
print(f"✅ Đã lưu bảng 'player_full_stats_vectorlite' vào cơ sở dữ liệu {DB_PATH}")

# =========================================
# 8️⃣ Báo cáo nhanh
# =========================================
print("\n📊 Báo cáo tổng hợp:")
print(f"  🔸 Tổng cầu thủ FBref: {len(df_stats)}")
print(f"  🔸 Tổng cầu thủ Transfer: {len(df_trans)}")
print(f"  🔸 Trung bình độ tương đồng: {df_merge['similarity'].mean():.3f}")
print("🎯 Hoàn tất quá trình merge dữ liệu!")
