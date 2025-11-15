# ===============================================================
# PRETEND PLAYER VALUATION MODEL (fixed for real stats.db schema)
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
# 1. KẾT NỐI DATABASE
# ===============================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "stats.db")
conn = sqlite3.connect(DB_PATH)
query = """
SELECT 
    s.Player,
    s.Squad,
    s.Pos,
    s.Age,
    s.Min,
    s.Gls,
    s.Ast,
    s.xG,
    s.xAG,
    s.PrgP,
    s.Tkl,
    s.Int,
    s."Cmp%",
    v.transfer_value
FROM PLAYER_STATS s
LEFT JOIN PLAYER_VALUES v
ON s.Player = v.player_name
"""
df = pd.read_sql_query(query, conn)
conn.close()

print(f"Đã đọc {len(df)} cầu thủ từ database.")


# ===============================================================
# 2. TIỀN XỬ LÝ DỮ LIỆU
# ===============================================================
def parse_value(v):
    if pd.isna(v):
        return np.nan
    try:
        return float(v.replace("€", "").replace("M", "").strip())
    except:
        return np.nan
df["transfer_value_num"] = df["transfer_value"].apply(parse_value)
df = df.dropna(subset=["transfer_value_num"])

numeric_cols = ["Age", "Min", "Gls", "Ast", "xG", "xAG", "PrgP", "Tkl", "Int", "Cmp%"]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")
df[numeric_cols] = df[numeric_cols].fillna(0)

features = numeric_cols + ["Pos", "Squad"]
X = df[features]
y = df["transfer_value_num"]

print(f"Dữ liệu sẵn sàng với {X.shape[0]} cầu thủ và {X.shape[1]} đặc trưng.")


# ===============================================================
# 3. CHIA TRAIN / TEST
# ===============================================================
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)


# ===============================================================
# 4. PIPELINE TIỀN XỬ LÝ
# ===============================================================
num_cols = ["Age", "Min", "Gls", "Ast", "xG", "xAG", "PrgP", "Tkl", "Int", "Cmp%"]
cat_cols = ["Pos", "Squad"]

preprocess = ColumnTransformer([
    ("num", StandardScaler(), num_cols),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols)
])


# ===============================================================
# 5. HUẤN LUYỆN MÔ HÌNH
# ===============================================================
model = RandomForestRegressor(n_estimators=400, max_depth=10, random_state=42)
pipeline = Pipeline([("preprocess", preprocess), ("model", model)])
pipeline.fit(X_train, y_train)

y_pred = pipeline.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"Sai số MAE: {mae:.2f} M€")
print(f"Hệ số R²: {r2:.3f}")


# ===============================================================
# 6. DỰ ĐOÁN & SO SÁNH
# ===============================================================
df["Predicted_Value"] = pipeline.predict(X)
df["Difference"] = df["Predicted_Value"] - df["transfer_value_num"]
df["Abs_Error"] = df["Difference"].abs()

raw_dir = os.path.join(BASE_DIR, "data", "raw")
os.makedirs(raw_dir, exist_ok=True)

csv_path = os.path.join(raw_dir, "predicted_values.csv")
df.to_csv(csv_path, index=False, encoding="utf-8-sig")

print(f"\nĐã lưu kết quả sang: {csv_path}")


# ===============================================================
# 7. TỔNG HỢP KẾT QUẢ
# ===============================================================
overall_mae = df["Abs_Error"].mean()
avg_diff = df["Difference"].mean()

print("\n===== Tổng hợp =====")
print(f"MAE trung bình: {overall_mae:.2f} M€")
print(f"Chênh lệch trung bình: {avg_diff:.2f} M€")

top_over = df.nlargest(5, "Difference")[["Player", "Squad", "Pos", "transfer_value_num", "Predicted_Value", "Difference"]]
top_under = df.nsmallest(5, "Difference")[["Player", "Squad", "Pos", "transfer_value_num", "Predicted_Value", "Difference"]]

print("\nTop 5 cầu thủ được định giá cao hơn thực tế:")
print(top_over.to_string(index=False))

print("\nTop 5 cầu thủ được định giá thấp hơn thực tế:")
print(top_under.to_string(index=False))
# ===============================================================
# 8. BIỂU ĐỒ
# ===============================================================
plt.figure(figsize=(6, 6))
plt.scatter(df["transfer_value_num"], df["Predicted_Value"], alpha=0.7)
plt.plot([0, max(df["transfer_value_num"])], [0, max(df["transfer_value_num"])], "r--")
plt.xlabel("Giá trị thực (€M)")
plt.ylabel("Giá trị dự đoán (€M)")
plt.title("So sánh Giá trị Thực tế vs Dự đoán")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()
