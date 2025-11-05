import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "stats.db")


def create_connection():
    """Tạo kết nối đến SQLite DB."""
    os.makedirs(DATA_DIR, exist_ok=True)
    print(f"Database path: {DB_PATH}")
    return sqlite3.connect(DB_PATH)

 # ==================================================
# BẢNG GIÁ TRỊ CHUYỂN NHƯỢNG (FOOTBALLTRANSFERS)
# ==================================================
def create_transfer_values_table(conn):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transfer_values (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT,
            club TEXT,
            age INTEGER,
            skill_score REAL,
            potential_score REAL,
            market_value TEXT
        );
    """)
    print("✅ Table 'transfer_values' checked/created successfully.")


# ==================================================
# TẠO TOÀN BỘ CSDL
# ==================================================
def create_tables():
    conn = create_connection()
    create_transfer_values_table(conn)
    conn.commit()
    conn.close()
    print("🎯 Database schema fully initialized!")

print(f"Database initialized successfully at: {DB_PATH}")
