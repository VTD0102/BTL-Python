import sqlite3
import os
import pandas as pd

DB_PATH = os.path.join("data", "stats.db")
def get_connection():
    """Tạo kết nối SQLite. Nếu chưa có file data/stats.db thì báo lỗi."""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f" Database not found at {DB_PATH}. Hãy chạy db_init.py trước.")
    return sqlite3.connect(DB_PATH)

#  INSERT dữ liệu
def insert_player_stats(df: pd.DataFrame):
    """Chèn DataFrame (thống kê cầu thủ) vào bảng player_stats."""
    conn = get_connection()
    df.to_sql("player_stats", conn, if_exists="append", index=False)
    conn.close()
    print(f"Đã thêm {len(df)} cầu thủ vào bảng player_stats.")


def insert_transfer_value(name: str, club: str, market_value: str, source_url: str = None):
    # Chèn 1 bản ghi giá trị chuyển nhượng vào bảng transfer_values.
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO transfer_values (player_name, club, market_value, source_url)
        VALUES (?, ?, ?, ?)
    """, (name, club, market_value, source_url))
    conn.commit()
    conn.close()
    print(f"Đã thêm giá trị chuyển nhượng cho {name}: {market_value}")



#  SELECT / TRA CỨU dữ liệu
def get_player_by_name(name: str):
    """Trả về DataFrame thông tin cầu thủ theo tên."""
    conn = get_connection()
    query = "SELECT * FROM player_stats WHERE player_name LIKE ?"
    df = pd.read_sql_query(query, conn, params=(f"%{name}%",))
    conn.close()
    return df


def get_players_by_club(club: str):
    # Trả về DataFrame các cầu thủ thuộc CLB.
    conn = get_connection()
    query = "SELECT * FROM player_stats WHERE club LIKE ?"
    df = pd.read_sql_query(query, conn, params=(f"%{club}%",))
    conn.close()
    return df


def get_all_players():
    # Trả về toàn bộ dữ liệu player_stats.
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM player_stats", conn)
    conn.close()
    return df


# ===========================================================
#  XÓA dữ liệu (nếu cần làm sạch)
# ===========================================================
def clear_table(table_name: str):
    """Xoá toàn bộ dữ liệu trong bảng (giữ nguyên schema)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {table_name}")
    conn.commit()
    conn.close()
    print(f" Đã xoá sạch dữ liệu trong bảng {table_name}.")


# ===========================================================
# Kiểm tra số lượng dữ liệu hiện có
# ===========================================================
def count_rows(table_name: str):
    """Đếm số hàng trong bảng."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cur.fetchone()[0]
    conn.close()
    return count


# ===========================================================
# Debug nhanh khi chạy độc lập
# ===========================================================
if __name__ == "__main__":
    print("Kiểm tra cơ sở dữ liệu...")
    print("player_stats:", count_rows("player_stats"))
    print("transfer_values:", count_rows("transfer_values"))
