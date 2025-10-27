import sqlite3
import os
DB_PATH = os.path.join("data", "starts.db")

def create_connection():
    if not os.path.exists("data"):
        os.makedirs("data")
    conn = sqlite3.connect(DB_PATH)
    return conn


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
                                                    npxG_plus_xAG_per90 REAL,

                                                    matches_url TEXT
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS transfer_values (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT,
            club TEXT,
            market_value TEXT,
            source_url TEXT
        );
    """)

    conn.commit()
    conn.close()
    print(f"Database initialized successfully at: {DB_PATH}")


if __name__ == "__main__":
    create_tables()
