import sqlite3
import os
DB_PATH = os.path.join("data", "stats.db")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "stats.db")

def create_connection():
    """Tạo kết nối đến SQLite DB."""
    os.makedirs(DATA_DIR, exist_ok=True)
    print(f"Database path: {DB_PATH}")
    return sqlite3.connect(DB_PATH)

def create_tables():
    conn = create_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS player_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT,
            nation TEXT,
            position TEXT,
            age INTEGER,
            club TEXT,
            
            matches_played INTEGER,
            starts INTEGER,
            minutes INTEGER,
            ninety_mins REAL,
            
            goals INTEGER,
            assists INTEGER,
            goals_plus_assists INTEGER,
            goals_minus_pk INTEGER,
            penalties_scored INTEGER,
            penalties_attempted INTEGER,
            yellow_cards INTEGER,
            red_cards INTEGER,
            
            xG REAL,
            npxG REAL,
            xAG REAL,
            npxG_plus_xAG REAL,
            
            progressive_carries INTEGER,
            progressive_passes INTEGER,
            progressive_receptions INTEGER,
            
            goals_per90 REAL,
            assists_per90 REAL,
            g_plus_a_per90 REAL,
            g_minus_pk_per90 REAL,
            g_plus_a_minus_pk_per90 REAL,
            xG_per90 REAL,
            xAG_per90 REAL,
            xG_plus_xAG_per90 REAL,
            npxG_per90 REAL,
            npxG_plus_xAG_per90 REAL
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS transfer_values (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT,
            club TEXT,
            market_value TEXT,
            position TEXT,
            age INTEGER,
            nationality TEXT
        );
    """)

    conn.commit()
    conn.close()
    print(f" Database initialized successfully at {DB_PATH}")
   
if __name__ == "__main__":
    create_tables()
