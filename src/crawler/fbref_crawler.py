# Các module cần cho việc đọc mã nguồn trang web và thao tác với CSDL
import pandas as pd
from io import StringIO
import sqlite3

# Module debug thanh tiến trình
from tqdm import tqdm

# Web crawler
from bs4 import BeautifulSoup
import undetected_chromedriver as UC
import time
import random
import os

DATABASE_NAME = "stats.db"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "stats.db")


# Tất cả endpoint FBREF cho EPL 2024-2025
ALL_STATS_URL = [
    "https://fbref.com/en/comps/9/stats/Premier-League-Stats",
    "https://fbref.com/en/comps/9/keepers/Premier-League-Stats",
    "https://fbref.com/en/comps/9/keepersadv/Premier-League-Stats",
    "https://fbref.com/en/comps/9/shooting/Premier-League-Stats",
    "https://fbref.com/en/comps/9/passing/Premier-League-Stats",
    "https://fbref.com/en/comps/9/passing_types/Premier-League-Stats",
    "https://fbref.com/en/comps/9/gca/Premier-League-Stats",
    "https://fbref.com/en/comps/9/defense/Premier-League-Stats",
    "https://fbref.com/en/comps/9/possession/Premier-League-Stats",
    "https://fbref.com/en/comps/9/playingtime/Premier-League-Stats",
    "https://fbref.com/en/comps/9/misc/Premier-League-Stats"
]

# ----------------------
# DB INIT
# ----------------------
def setup_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS stats")

    conn.commit()
    conn.close()

    print(f"Database path: {DB_PATH}")
    print(f"Đã reset bảng stats trong {DATABASE_NAME}\n")

# ----------------------
# SAVE TO DB
# ----------------------
def save_to_database(df, table_name):
    try:
        conn = sqlite3.connect(DB_PATH)
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        conn.commit()
        conn.close()

        print(f"Đã lưu vào bảng '{table_name}' trong {DATABASE_NAME}!\n")
    except Exception as e:
        print(f"Lỗi khi lưu bảng {table_name}: {e}")


# ----------------------
# MAIN CRAWLER
# ----------------------
def get_player_stats():
    df_list = []
    driver = UC.Chrome(version_main=141)

    for url in tqdm(ALL_STATS_URL, total=len(ALL_STATS_URL), desc="Đang thu thập stats"):
        driver.get(url)

        time.sleep(random.randint(5, 7))

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        stats_table = soup.find('table', id=lambda x: x and x.startswith('stats_') and 'squads' not in x)

        if stats_table is None:
            print(f"Không tìm thấy bảng ở URL: {url}")
            continue

        df = pd.read_html(StringIO(str(stats_table)), header=1)[0]

        df = df[df['Rk'] != 'Rk'].reset_index(drop=True)

        if 'Rk' in df.columns:
            df = df.drop(columns=['Rk'])

        df = df.set_index(['Player', 'Squad'])

        df_list.append(df)

        time.sleep(random.randint(3, 5))

    driver.quit()

    if not df_list:
        print("Không có dữ liệu")
        return pd.DataFrame()

    merge_df = pd.concat(df_list, axis=1)
    merge_df = merge_df.loc[:, ~merge_df.columns.duplicated()]
    merge_df = merge_df.reset_index()

    if "Min" in merge_df.columns:
        merge_df["Min"] = pd.to_numeric(merge_df["Min"], errors="coerce")
        merge_df = merge_df[merge_df["Min"] > 90]

    merge_df.fillna("N/A", inplace=True)

    print(f"Thu thập thành công dữ liệu của {len(merge_df)} cầu thủ!\n")

    return merge_df


# ----------------------
# MAIN
# ----------------------
def main():
    setup_database()

    stats_df = get_player_stats()

    save_to_database(stats_df, 'stats')

    print("Hoàn tất chương trình!")


if __name__ == "__main__":
    print("--- Bước 1: Khởi tạo CSDL (nếu chưa có) ---")
    create_tables()

    # Sử dụng URL 2024-2025 cụ thể
    URL = "https://fbref.com/en/comps/9/stats/Premier-League-Stats"

    print("\n--- Bước 2: Bắt đầu cào dữ liệu ---")
    scrape_fbref_stats(season_url=URL)

