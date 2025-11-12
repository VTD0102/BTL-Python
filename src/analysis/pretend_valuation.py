# ===============================================================
# PRETEND PLAYER VALUATION MODEL (Final Verified Version)
# Dự đoán giá trị cầu thủ dựa vào PLAYER_STATS + so sánh với PLAYER_VALUES
# ===============================================================

import pandas as pd
import numpy as np
import sqlite3
import os
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score


# ===============================================================
# 1️⃣ KẾT NỐI DATABASE
# ===============================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "stats.db")

print(f"📂 Database path: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)

# Gộp dữ liệu từ bảng PLAYER_STATS và PLAYER_VALUES
query = """
SELECT 
    s.Player,
    s.Age, s.Min, s.Gls, s.Ast, s.xG, s.xA, s.PrgP, s.Tkl, s.Int, s."Pass%", s.Pos, s.Squad,
    v.transfer_value
FROM PLAYER_STATS s
LEFT JOIN PLAYER_VALUES v 
ON s.Player = v.player_name
"""
df = pd.read_sql_query(query, conn)
conn.close()

print(f"📊 Đã đọc {len(df)} cầu thủ từ database.")


# ===============================================================
# 2️⃣ TIỀN XỬ LÝ DỮ LIỆU
# ===============================================================
def parse_value(v):
    """Chuyển '€18.5M' -> 18.5"""
    if pd.isna(v):
        return np.nan
    try:
        return float(v.replace("€", "").replace("M", "").strip())
    except:
        return np.nan

df["transfer_value_num"] = df["transfer_value"].apply(parse_value)

# Chỉ giữ cầu thủ có giá trị thực
df = df.dropna(subset=["transfer_value_num"])

# Giữ cột cần thiết
features = ["Age", "Min", "Gls", "Ast", "xG", "xA", "PrgP", "Tkl", "Int", "Pass%", "Pos", "Squad"]
df = df[[*features, "Player", "transfer_value_num"]].fillna(0)

X = df[features]
y = df["transfer_value_num"]

print(f"✅ Dữ liệu sẵn sàng với {X.shape[0]} cầu thủ và {X.shape[1]} đặc trưng.")


# ===============================================================
# 3️⃣ CHIA TRAIN/TEST
# ===============================================================
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)


# ===============================================================
# 4️⃣ PIPELINE TIỀN XỬ LÝ
# ===============================================================
num_cols = ["Age", "Min", "Gls", "Ast", "xG", "xA", "PrgP", "Tkl", "Int", "Pass%"]
cat_cols = ["Pos", "Squad"]

preprocess = ColumnTransformer([
    ("num", StandardScaler(), num_cols),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols)
])


# ===============================================================
# 5️⃣ HUẤN LUYỆN MÔ HÌNH
# ===============================================================
model = RandomForestRegressor(
    n_estimators=400,
    max_depth=10,
    random_state=42
)

pipeline = Pipeline([
    ("preprocess", preprocess),
    ("model", model)
])

print("\n🚀 Đang huấn luyện mô hình định giá ...")
pipeline.fit(X_train, y_train)

y_pred = pipeline.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"📈 MAE trung bình: {mae:.2f} M€")
print(f"📊 R² (độ phù hợp mô hình): {r2:.3f}")


# ===============================================================
# 6️⃣ DỰ ĐOÁN TẤT CẢ CẦU THỦ & SO SÁNH
# ===============================================================
df["Predicted_Value"] = pipeline.predict(X)
df["Difference"] = df["Predicted_Value"] - df["transfer_value_num"]
df["Abs_Error"] = df["Difference"].abs()

# Xuất file CSV
raw_dir = os.path.join(BASE_DIR, "data", "raw")
os.makedirs(raw_dir, exist_ok=True)
csv_path = os.path.join(raw_dir, "predicted_values.csv")

df_export = df[["Player", "Squad", "Pos", "transfer_value_num", "Predicted_Value", "Difference", "Abs_Error"]]
df_export.to_csv(csv_path, index=False, encoding="utf-8-sig")

print(f"\n💾 Đã xuất kết quả so sánh sang: {csv_path}")


# ===============================================================
# 7️⃣ THỐNG KÊ & TỔNG HỢP
# ===============================================================
overall_mae = df["Abs_Error"].mean()
avg_diff = df["Difference"].mean()

top_over = df.nlargest(5, "Difference")[["Player", "Squad", "Difference", "transfer_value_num", "Predicted_Value"]]
top_under = df.nsmallest(5, "Difference")[["Player", "Squad", "Difference", "transfer_value_num", "Predicted_Value"]]

print("\n📊 ===== TỔNG HỢP KẾT QUẢ =====")
print(f"👉 Sai số trung bình (MAE): {overall_mae:.2f} M€")
print(f"👉 Chênh lệch trung bình (Predicted - Real): {avg_diff:.2f} M€")

print("\n⚡ TOP 5 cầu thủ được mô hình định giá CAO HƠN thực tế:")
print(top_over.to_string(index=False))

print("\n⚡ TOP 5 cầu thủ được mô hình định giá THẤP HƠN thực tế:")
print(top_under.to_string(index=False))

# Sai số theo CLB và vị trí
mae_team = df.groupby("Squad")["Abs_Error"].mean().sort_values()
mae_pos = df.groupby("Pos")["Abs_Error"].mean().sort_values()

summary_path = os.path.join(raw_dir, "valuation_summary.csv")
summary = pd.DataFrame({
    "MAE_by_Team": mae_team,
    "MAE_by_Position": mae_pos
})
summary.to_csv(summary_path, encoding="utf-8-sig")

print(f"\n💾 Đã lưu bảng tổng hợp sai số: {summary_path}")


# ===============================================================
# 8️⃣ BIỂU ĐỒ SO SÁNH
# ===============================================================
plt.figure(figsize=(6, 6))
plt.scatter(df["transfer_value_num"], df["Predicted_Value"], alpha=0.7, color="#1f77b4")
plt.plot([0, max(df["transfer_value_num"])], [0, max(df["transfer_value_num"])], "r--")
plt.xlabel("Giá trị thực (€M)")
plt.ylabel("Giá trị dự đoán (€M)")
plt.title("⚽ So sánh Giá trị Thực tế vs Dự đoán (Player Valuation)")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()


# ===============================================================
# 9️⃣ HÀM DỰ ĐOÁN CẦU THỦ MỚI
# ===============================================================
def predict_player(data: dict):
    """Dự đoán giá trị cầu thủ mới"""
    df_in = pd.DataFrame([data])
    value = pipeline.predict(df_in)[0]
    return round(value, 2)

example = {
    "Age": 21, "Min": 1800, "Gls": 4, "Ast": 2, "xG": 3.2, "xA": 2.1,
    "PrgP": 20, "Tkl": 25, "Int": 18, "Pass%": 85, "Pos": "DF", "Squad": "Chelsea"
}
print(f"\n🔮 Dự đoán cầu thủ mới: €{predict_player(example)}M")

print("\n✅ Hoàn tất mô hình pretend_valuation!")
