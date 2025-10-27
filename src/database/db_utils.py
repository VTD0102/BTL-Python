import sqlite3
import pandas as pd
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

# --- (Hàm save_player_stats_to_db giữ nguyên như cũ) ---
def save_player_stats_to_db(df_stats):
    """
    Lưu DataFrame thống kê cầu thủ vào bảng 'player_stats'.
    Hàm này sẽ xóa dữ liệu cũ trước khi chèn dữ liệu mới.
    
    Args:
        df_stats (pd.DataFrame): DataFrame đã được làm sạch và
                                 ánh xạ (map) cột đúng với schema CSDL.
    """
    conn = create_connection()
    cur = conn.cursor()

    try:
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
        print(f"Đã lưu thành công {len(data_tuples)} cầu thủ vào 'player_stats'.")

    except sqlite3.Error as e:
        print(f"Lỗi SQLite khi chèn dữ liệu: {e}")
        conn.rollback() 
    except Exception as e:
        print(f"Lỗi không xác định: {e}")
        conn.rollback()
    finally:
        conn.close()