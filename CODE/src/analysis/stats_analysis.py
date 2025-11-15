import sqlite3
import pandas as pd
import os

# === Tạo đường dẫn SQLite ===
DATABASE_NAME = "stats.db"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, DATABASE_NAME)


def create_connection():
    os.makedirs(DATA_DIR, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def analyze_stats():
    conn = create_connection()

    df = pd.read_sql_query("SELECT * FROM PLAYER_STATS;", conn)
    conn.close()

    print("Loaded stats:", df.shape)

    # ============================
    # 1. Loại cột không cần thiết
    # ============================
    drop_cols = [
        "Player", "Squad", "Pos", "Nation", "Comp", "Born",
        "Age", "Matches", "Games", "MP", "Starts", "Min"
    ]
    df_numeric = df.drop(columns=[c for c in drop_cols if c in df.columns], errors="ignore")

    # ============================
    # 2. Convert sang số
    # ============================
    df_numeric = df_numeric.apply(pd.to_numeric, errors="coerce")

    # ============================
    # 3. Lọc cột số + ghép Squad
    # ============================
    numeric_cols = df_numeric.select_dtypes(include="number").columns.tolist()
    df_numeric["Squad"] = df["Squad"]
    df_numeric[numeric_cols] = df_numeric[numeric_cols].fillna(0)

    # ============================
    # 4. Tính median / mean / std theo đội
    # ============================
    stats = df_numeric.groupby("Squad")[numeric_cols].agg(["median", "mean", "std"])
    stats.columns = ["_".join(col) for col in stats.columns]
    stats = stats.round(2)

    stats_file = os.path.join(DATA_DIR, "team_summary_stats.csv")
    stats.to_csv(stats_file)
    print(f"✔Đã tạo file thống kê: {stats_file}")

    # ============================
    # 5. Tìm đội mạnh nhất từng chỉ số (mean) — bỏ metric tiêu cực
    # ============================
    mean_cols = [c for c in stats.columns if c.endswith("_mean")]
    negative_patterns = [
        "foul", "crdy", "crdr", "2crdy",
        "dispos", "mis", "error",
        "pkcon", "off",
        "tkl_dribbled", "dribbled_past"
    ]
    positive_mean_cols = [
        c for c in mean_cols
        if not any(neg in c.lower() for neg in negative_patterns)
    ]
    print(f"Số metric tích cực dùng để tìm best team: {len(positive_mean_cols)}")
    best_by_metric = stats[positive_mean_cols].idxmax()
    best_by_metric.index = [c.replace("_mean", "") for c in best_by_metric.index]
    best_by_metric.name = "BestTeam"
    best_by_metric.index.name = "Metric"
    best_metric_file = os.path.join(DATA_DIR, "best_team_each_metric.csv")
    best_by_metric.to_csv(best_metric_file)
    print(f"Đã tạo file đội mạnh nhất từng chỉ số (positive metrics only): {best_metric_file}")
    print("\nĐội mạnh nhất theo từng metric:")
    print(best_by_metric)

    # ============================
    # 6. TÍNH ĐỘI CÓ PHONG ĐỘ CAO NHẤT (chỉ in, không lưu CSV)
    # ============================

    team_overall_score = stats[positive_mean_cols].mean(axis=1).round(2)
    best_team_overall = team_overall_score.idxmax()
    print(f"\nĐội có phong độ tổng thể cao nhất EPL 2024–2025:")
    print(f"{best_team_overall} ")
    return stats, best_by_metric


if __name__ == "__main__":
    analyze_stats()
