import sqlite3
import pandas as pd
import os

# Import đường dẫn CSDL và hàm kết nối từ file db_init.py
try:
    from db_init import DB_PATH, create_connection
except ImportError:
    # Xử lý nếu chạy file này độc lập (thêm thư mục gốc vào path)
    import sys
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from src.database.db_init import DB_PATH, create_connection



# =========================================
# 1 Đảm bảo import đúng (kể cả chạy trực tiếp)
# =========================================



def save_player_stats_to_db(df_stats: pd.DataFrame):
    conn = create_connection()
    if conn is None:
        print(f"Không thể kết nối đến cơ sở dữ liệu tại {DB_PATH}")
        return

    try:
        cur = conn.cursor()
        # 1) Xoá dữ liệu cũ
        cur.execute("DELETE FROM player_stats")
        # 2) Reset AUTOINCREMENT cho bảng này
        cur.execute("DELETE FROM sqlite_sequence WHERE name = 'player_stats'")
        print("Đã xóa dữ liệu cũ & reset ID của bảng 'player_stats'.")

        # 3) Chuẩn bị dữ liệu mới
        df_to_save = df_stats.where(pd.notnull(df_stats), None)
        cols = df_to_save.columns.tolist()
        col_names = ", ".join([f'"{c}"' for c in cols])
        placeholders = ", ".join(["?"] * len(cols))
        sql = f"INSERT INTO player_stats ({col_names}) VALUES ({placeholders})"
        data_tuples = [tuple(row) for row in df_to_save.itertuples(index=False)]

        # 4) Ghi & xác nhận
        cur.executemany(sql, data_tuples)
        conn.commit()
        print(f"Đã lưu thành công {len(data_tuples)} cầu thủ vào 'player_stats'.")

    except sqlite3.OperationalError as e:
        print(f"Lỗi SQL: {e}")
        conn.rollback()
    finally:
        conn.close()
        print(f"Đã đóng kết nối CSDL ({DB_PATH})")



def save_transfer_values_to_db(df_transfer: pd.DataFrame):
    from src.database.db_init import create_connection, DB_PATH
    conn = create_connection()
    cur = conn.cursor()
    try:
        df_to_save = df_transfer.where(pd.notnull(df_transfer), None)
        cols = df_to_save.columns.tolist()
        col_names = ", ".join([f'"{c}"' for c in cols])
        placeholders = ", ".join(["?"] * len(cols))
        sql = f"INSERT INTO transfer_values ({col_names}) VALUES ({placeholders})"
        data_tuples = [tuple(row) for row in df_to_save.itertuples(index=False)]

        cur.executemany(sql, data_tuples)
        conn.commit()
        print(f"🧩 Đã thêm {len(data_tuples)} cầu thủ vào bảng 'transfer_values'.")

    except Exception as e:
        print(f"⚠️ Lỗi khi lưu DB: {e}")
        conn.rollback()
    finally:
        conn.close()

import sqlite3
from src.database.db_init import create_connection, DB_PATH

def clear_table(table_name: str):
    """
    Xóa toàn bộ dữ liệu trong bảng chỉ định và reset lại ID tự tăng (AUTOINCREMENT).
    """
    conn = create_connection()
    if conn is None:
        print(f"❌ Không thể kết nối đến cơ sở dữ liệu tại {DB_PATH}")
        return

    try:
        cur = conn.cursor()
        cur.execute(f"DELETE FROM {table_name};")
        cur.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}';")  # reset AUTOINCREMENT
        conn.commit()
        print(f"🧹 Đã xóa toàn bộ dữ liệu cũ trong bảng '{table_name}' và reset ID.")
    except sqlite3.Error as e:
        print(f"⚠️ Lỗi khi xóa bảng '{table_name}': {e}")
        conn.rollback()
    finally:
        conn.close()