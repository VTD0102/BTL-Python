import sqlite3
import pandas as pd
import os

# === Tạo đường dẫn SQLite ===
DATABASE_NAME = "stats.db"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")   # DB + CSV cùng folder
DB_PATH = os.path.join(DATA_DIR, DATABASE_NAME)


def create_connection():
    """Tạo kết nối tới database"""
    os.makedirs(DATA_DIR, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def setup_database():
    """Tạo file DB nếu chưa có"""
    conn = sqlite3.connect(DB_PATH)
    conn.commit()
    conn.close()


def analyze_stats():
    conn = create_connection()

    print("DB_PATH:", DB_PATH)
    print("Exists:", os.path.exists(DB_PATH))

    # Lấy danh sách bảng trong DB
    tables = pd.read_sql_query(
        "SELECT name FROM sqlite_master WHERE type='table';",
        conn
    )
    print("Các bảng trong DB:", tables["name"].tolist())

    if "PLAYER_STATS" not in tables["name"].values:
        raise Exception("Không tìm thấy bảng 'PLAYER_STATS' trong database!")

    # Đọc bảng stats
    df = pd.read_sql_query("SELECT * FROM PLAYER_STATS;", conn)
    conn.close()

    print("Loaded stats:", df.shape)
    print(" Columns:", df.columns.tolist())

    # Convert toàn bộ cột thành số nếu có thể
    df = df.apply(pd.to_numeric, errors="ignore")

    #  Lấy cột số
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    # Nếu Squad bị detect nhầm thì bỏ
    if "Squad" in numeric_cols:
        numeric_cols.remove("Squad")

    print("\nNumeric columns:", len(numeric_cols))

    # Thay NA = 0
    df[numeric_cols] = df[numeric_cols].fillna(0)

    # ==== (1) median – mean – std theo đội ====
    stats = df.groupby("Squad")[numeric_cols].agg(["median", "mean", "std"])

    #  Flatten multi-index columns
    stats.columns = ["_".join(col) for col in stats.columns]

    stats_file = os.path.join(DATA_DIR, "team_summary_stats.csv")
    stats.to_csv(stats_file)
    print(f"Đã tạo file {stats_file}")

    # ==== (2) Tìm đội có mean cao nhất theo từng chỉ số ====
    # mean columns = *_mean
    mean_cols = [c for c in stats.columns if c.endswith("_mean")]
    best_by_metric = stats[mean_cols].idxmax()

    best_by_metric.index = [c.replace("_mean", "") for c in best_by_metric.index]
    best_by_metric.name = "BestTeam"
    best_by_metric.index.name = "Metric"

    best_metric_file = os.path.join(DATA_DIR, "best_team_each_metric.csv")
    best_by_metric.to_csv(best_metric_file)
    print(f"Đã tạo file {best_metric_file}")

    print("\n Đội mạnh nhất theo từng chỉ số:")
    print(best_by_metric)

    # ==== (3) Đội phong độ tổng thể ====
    # mean of all mean metrics → best overall
    team_mean = stats[mean_cols].mean(axis=1)
    best_team_overall = team_mean.idxmax()

    print(f"\n🔥 Đội có phong độ tổng thể tốt nhất: {best_team_overall}")

    return stats, best_by_metric, best_team_overall


if __name__ == "__main__":
    analyze_stats()
