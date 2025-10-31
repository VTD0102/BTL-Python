import sqlite3
import pandas as pd
import os
import sys

try:
    from .db_init import DB_PATH, create_connection
except ImportError:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from src.database.db_init import DB_PATH, create_connection

def save_player_stats_to_db(df_stats):
    conn = create_connection()
    cur = conn.cursor()

    try:
        cur.execute("PRAGMA table_info(player_stats)")
        db_cols = [row[1] for row in cur.fetchall()]
        df_cols = df_stats.columns.tolist()
        
        valid_cols = [c for c in df_cols if c in db_cols]
        df_to_save = df_stats[valid_cols]

        cur.execute("DELETE FROM player_stats")
        print("Đã xóa dữ liệu cũ từ bảng 'player_stats'.")
        
        col_names = ", ".join([f'"{c}"' for c in valid_cols])
        placeholders = ", ".join(["?"] * len(valid_cols))
        sql = f"INSERT INTO player_stats ({col_names}) VALUES ({placeholders})"
        
        data_tuples = [tuple(row) for row in df_to_save.where(pd.notnull(df_to_save), None).itertuples(index=False)]

        cur.executemany(sql, data_tuples)
        conn.commit()
        print(f"Đã lưu thành công {len(data_tuples)} cầu thủ vào 'player_stats'.")

    except sqlite3.Error as e:
        print(f"Lỗi SQLite khi chèn dữ liệu 'player_stats': {e}")
        conn.rollback() 
    except Exception as e:
        print(f"Lỗi không xác định: {e}")
        conn.rollback()
    finally:
        conn.close()
        print(f"Đã đóng kết nối cơ sở dữ liệu ({DB_PATH})")

def read_player_list():
    conn = create_connection()
    try:
        query = "SELECT player_name, club FROM player_stats"
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        print(f"Lỗi khi đọc 'player_stats': {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

def save_transfer_values(df_values):
    conn = create_connection()
    cur = conn.cursor()
    
    db_cols = ['player_name', 'club', 'market_value', 'position', 'age', 'nationality']
    
    df_to_save = df_values[[col for col in db_cols if col in df_values.columns]]

    try:
        cur.execute("DELETE FROM transfer_values")
        print("Đã xóa dữ liệu cũ từ bảng 'transfer_values'.")

        col_names = ", ".join([f'"{c}"' for c in df_to_save.columns])
        placeholders = ", ".join(["?"] * len(df_to_save.columns))
        sql = f"INSERT INTO transfer_values ({col_names}) VALUES ({placeholders})"
        
        data_tuples = [tuple(row) for row in df_to_save.where(pd.notnull(df_to_save), None).itertuples(index=False)]

        cur.executemany(sql, data_tuples)
        conn.commit()
        print(f"Đã lưu thành công {len(data_tuples)} cầu thủ vào 'transfer_values'.")

    except sqlite3.Error as e:
        print(f"Lỗi SQLite khi chèn dữ liệu 'transfer_values': {e}")
        conn.rollback()
    except Exception as e:
        print(f"Lỗi không xác định: {e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()
            print(f"Đã đóng kết nối cơ sở dữ liệu ({DB_PATH})")