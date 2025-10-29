import sqlite3
import pandas as pd
import sys
import os

# Import đường dẫn CSDL và hàm kết nối từ file db_init.py
try:
    # SỬA Ở ĐÂY: Thêm dấu chấm
    from .db_init import DB_PATH, create_connection
except ImportError:
    # Xử lý nếu chạy file này độc lập (thêm thư mục gốc vào path)
    import sys
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if project_root not in sys.path:
        sys.path.append(project_root)
    # SỬA Ở ĐÂY: Thêm 'src.'
    from src.database.db_init import DB_PATH, create_connection



# =========================================
# 1️⃣ Đảm bảo import đúng (kể cả chạy trực tiếp)
# =========================================



def save_player_stats_to_db(df_stats: pd.DataFrame):
    """
    Lưu DataFrame thống kê cầu thủ vào bảng 'player_stats'.
    Nếu bảng đã có dữ liệu, sẽ xóa toàn bộ trước khi ghi mới.
    """
    conn = create_connection()
    if conn is None:
        print(f"Không thể kết nối đến cơ sở dữ liệu tại {DB_PATH}")
        return

    cur = conn.cursor()

    try:
        # Xóa dữ liệu cũ
        cur.execute("DELETE FROM player_stats")
        print("Đã xóa dữ liệu cũ từ bảng 'player_stats'.")

        df_to_save = df_stats.where(pd.notnull(df_stats), None)
        cols = df_to_save.columns.tolist()
        col_names = ", ".join([f'"{c}"' for c in cols])
        placeholders = ", ".join(["?"] * len(cols))
        sql = f"INSERT INTO player_stats ({col_names}) VALUES ({placeholders})"
        data_tuples = [tuple(row) for row in df_to_save.itertuples(index=False)]

        cur.executemany(sql, data_tuples)
        conn.commit()
        print(f"Đã lưu thành công {len(data_tuples)} cầu thủ vào bảng 'player_stats'.")

    except sqlite3.OperationalError as e:
        print(f"Lỗi SQL (có thể sai tên cột hoặc chưa tạo bảng): {e}")
        conn.rollback()
    except sqlite3.Error as e:
        print(f"Lỗi SQLite khi chèn dữ liệu: {e}")
        conn.rollback()
    except Exception as e:
        print(f"Lỗi không xác định: {e}")
        conn.rollback()
    finally:
        conn.close()
        print(f"Đã đóng kết nối cơ sở dữ liệu ({DB_PATH})")


# =========================================
# 3️⃣ TEST NHANH
# =========================================
if __name__ == "__main__":
    print("Kiểm tra hàm save_player_stats_to_db()")
    sample_data = {
        "player_name": ["Haaland", "Saka"],
        "club": ["Man City", "Arsenal"],
        "minutes": [2450, 2100],
        "goals": [27, 16],
        "assists": [5, 9],
        "goals_per90": [1.05, 0.47],
        "matches_url": ["fbref.com/players/123", "fbref.com/players/456"]
    }
    df = pd.DataFrame(sample_data)
    save_player_stats_to_db(df)
