import sqlite3
import pandas as pd
import os
import sys

# =========================================
# 1️⃣ Đảm bảo import đúng (kể cả chạy trực tiếp)
# =========================================
try:
    from .db_init import DB_PATH, create_connection
except ImportError:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from src.database.db_init import (DB_PATH, create_connection)


# =========================================
# 2️⃣ HÀM LƯU DỮ LIỆU CẦU THỦ VÀO DATABASE
# =========================================
def save_player_stats_to_db(df_stats: pd.DataFrame):
    """
    Lưu DataFrame thống kê cầu thủ vào bảng 'player_stats'.
    Nếu bảng đã có dữ liệu, sẽ xóa toàn bộ trước khi ghi mới.
    """
    conn = create_connection()
    if conn is None:
        print(f"❌ Không thể kết nối đến cơ sở dữ liệu tại {DB_PATH}")
        return

    cur = conn.cursor()

    try:
        # Xóa dữ liệu cũ
        cur.execute("DELETE FROM player_stats")
        print("🧹 Đã xóa dữ liệu cũ từ bảng 'player_stats'.")

        # Chuẩn bị dữ liệu
        df_to_save = df_stats.where(pd.notnull(df_stats), None)
        cols = df_to_save.columns.tolist()
        col_names = ", ".join([f'"{c}"' for c in cols])
        placeholders = ", ".join(["?"] * len(cols))
        sql = f"INSERT INTO player_stats ({col_names}) VALUES ({placeholders})"
        data_tuples = [tuple(row) for row in df_to_save.itertuples(index=False)]

        # Ghi dữ liệu
        cur.executemany(sql, data_tuples)
        conn.commit()
        print(f"✅ Đã lưu thành công {len(data_tuples)} cầu thủ vào bảng 'player_stats'.")

    except sqlite3.OperationalError as e:
        print(f"Lỗi SQL (có thể sai tên cột hoặc chưa tạo bảng): {e}")
        conn.rollback()
    except sqlite3.Error as e:
        print(f"Lỗi SQLite khi chèn dữ liệu: {e}")
        conn.rollback()
    except Exception as e:
        print(f"❗ Lỗi không xác định: {e}")
        conn.rollback()
    finally:
        conn.close()
        print(f"🔒 Đã đóng kết nối cơ sở dữ liệu ({DB_PATH})")


# =========================================
# 3️⃣ HÀM KIỂM TRA NHANH (KHI CHẠY TRỰC TIẾP)
# =========================================
if __name__ == "__main__":
    import pandas as pd

    # Ví dụ test nhanh
    print("🧪 Kiểm tra hàm save_player_stats_to_db()")
    sample_data = {
        "player_name": ["Haaland", "Saka"],
        "club": ["Man City", "Arsenal"],
        "minutes": [2450, 2100],
        "goals": [27, 16],
        "assists": [5, 9],
        "goals_per90": [1.05, 0.47]
    }
    df = pd.DataFrame(sample_data)
    save_player_stats_to_db(df)
