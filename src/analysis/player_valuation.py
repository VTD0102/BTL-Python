import sqlite3
import pandas as pd
import os


# === Đường dẫn DB ===
DATABASE_NAME = "stats.db"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, DATABASE_NAME)


def create_connection():
    os.makedirs(DATA_DIR, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def load_stats():
    """Đọc bảng stats và chuyển đổi numeric an toàn"""
    conn = create_connection()
    df = pd.read_sql_query("SELECT * FROM player_stats;", conn)
    conn.close()

    # ✅ convert tất cả cột (trừ Player/Squad/Pos) về số
    for col in df.columns:
        if col not in ["Squad", "Player", "Pos"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.fillna(0)
    return df


def normalize(df, columns):
    """Chuẩn hóa Min-Max [0,1]"""
    result = df.copy()
    for col in columns:
        min_v = df[col].min()
        max_v = df[col].max()
        if max_v > min_v:
            result[col] = (df[col] - min_v) / (max_v - min_v)
        else:
            result[col] = 0
    return result


def get_position_weights(pos):
    """Trọng số theo vị trí"""
    pos = str(pos).upper()

    # ST
    if pos in ["ST", "FW", "CF"]:
        return {
            "Gls": 0.45, "SoT": 0.20, "xG": 0.15, "Ast": 0.10, "Min": 0.05, "TeamFactor": 0.05
        }

    # MF
    if pos in ["CM", "DM", "AM", "MF"]:
        return {
            "Ast": 0.30, "KP": 0.25, "Cmp%": 0.20, "xA": 0.15, "Min": 0.05, "TeamFactor": 0.05
        }

    # DF
    if pos in ["DF", "CB", "RB", "LB"]:
        return {
            "Tkl": 0.30, "Int": 0.25, "Clr": 0.20, "Blocks": 0.15, "Min": 0.05, "TeamFactor": 0.05
        }

    # GK
    if pos in ["GK"]:
        return {
            "Save%": 0.45, "CS": 0.30, "PSxG": 0.20, "TeamFactor": 0.05
        }

    # fallback
    return {"Min": 1.0}


def compute_player_value():
    df = load_stats()

    # numeric cols
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if "Squad" in numeric_cols:
        numeric_cols.remove("Squad")

    # normalize
    norm_df = normalize(df, numeric_cols)

    # TEAM FACTOR -----------------------
    stats = df.groupby("Squad")[numeric_cols].agg(["mean"])
    stats.columns = ["_".join(col) for col in stats.columns]
    mean_cols = [c for c in stats.columns if c.endswith("_mean")]

    team_mean = stats[mean_cols].mean(axis=1)
    team_factor = team_mean / team_mean.max()
    team_factor.name = "TeamFactor"

    df = df.merge(team_factor, left_on="Squad", right_index=True, how="left")
    norm_df = norm_df.merge(team_factor, left_on="Squad", right_index=True, how="left")

    # VALUE SCORE -----------------------
    value_scores = []

    for i, row in norm_df.iterrows():
        pos = df.loc[i, "Pos"] if "Pos" in df.columns else "FW"
        weights = get_position_weights(pos)

        score = 0
        for stat, w in weights.items():
            if stat in norm_df.columns:
                score += float(row[stat]) * w

        value_scores.append(score)

    norm_df["ValueScore"] = value_scores

    # TIER -----------------------
    def value_to_tier(v):
        if v >= 0.80: return "Elite"
        if v >= 0.65: return "Top"
        if v >= 0.50: return "Starter"
        if v >= 0.30: return "Rotation"
        return "Backup"

    norm_df["Tier"] = norm_df["ValueScore"].apply(value_to_tier)

    # Market Value (M€)
    norm_df["MarketValue(M€)"] = (norm_df["ValueScore"] * 120).round(2)

    # sort
    norm_df = norm_df.sort_values("MarketValue(M€)", ascending=False)

    # SAVE CSV -----------------------
    out_file = os.path.join(DATA_DIR, "player_value.csv")
    keep = ["Player", "Squad", "Pos", "ValueScore", "Tier", "MarketValue(M€)"]
    norm_df[keep].to_csv(out_file, index=False)

    print(f"✅ CSV đã tạo: {out_file}")
    return norm_df


if __name__ == "__main__":
    df_value = compute_player_value()
    print(df_value.head(10))
