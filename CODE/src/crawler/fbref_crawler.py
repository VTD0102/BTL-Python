# ===============================================
# FBREF PLAYER STATS CRAWLER (Optimized)
# ===============================================

import pandas as pd
from io import StringIO
import sqlite3
import os
import time
import random

from tqdm import tqdm
from bs4 import BeautifulSoup
import undetected_chromedriver as UC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "stats.db")


# ===============================================
# FBREF ENDPOINTS (EPL 2024–2025)
# ===============================================
ALL_STATS_URL = [
   "https://fbref.com/en/comps/9/2024-2025/stats/2024-2025-Premier-League-Stats",
   "https://fbref.com/en/comps/9/2024-2025/keepers/2024-2025-Premier-League-Stats",
   "https://fbref.com/en/comps/9/2024-2025/keepersadv/2024-2025-Premier-League-Stats",
   "https://fbref.com/en/comps/9/2024-2025/shooting/2024-2025-Premier-League-Stats",
   "https://fbref.com/en/comps/9/2024-2025/passing/2024-2025-Premier-League-Stats",
   "https://fbref.com/en/comps/9/2024-2025/passing_types/2024-2025-Premier-League-Stats",
   "https://fbref.com/en/comps/9/2024-2025/gca/2024-2025-Premier-League-Stats",
   "https://fbref.com/en/comps/9/2024-2025/defense/2024-2025-Premier-League-Stats",
   "https://fbref.com/en/comps/9/2024-2025/possession/2024-2025-Premier-League-Stats",
   "https://fbref.com/en/comps/9/2024-2025/playingtime/2024-2025-Premier-League-Stats",
   "https://fbref.com/en/comps/9/2024-2025/misc/2024-2025-Premier-League-Stats"
]



# ===============================================
# INIT UC DRIVER
# ===============================================
def get_driver():
    opts = Options()
    opts.page_load_strategy = "eager"
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-dev-shm-usage")
    driver = UC.Chrome(version_main=141, options=opts)
    driver.set_page_load_timeout(120)
    return driver


# ===============================================
# DB INIT
# ===============================================
def setup_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS PLAYER_STATS")
    conn.commit()
    conn.close()
    print(f"Database path: {DB_PATH}")
    print(f"Đã reset bảng PLAYER_STATS trong stats.db\n")


# ===============================================
# SAVE TO DB
# ===============================================
def save_to_database(df, table_name):
    try:
        conn = sqlite3.connect(DB_PATH)
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        conn.commit()
        conn.close()
        print(f"Đã lưu vào bảng '{table_name}' trong stats.db!\n")
    except Exception as e:
        print(f"Lỗi khi lưu bảng {table_name}: {e}")


# ===============================================
# CORE CRAWL
# ===============================================
def get_player_stats():
    df_list = []
    driver = get_driver()

    for url in tqdm(ALL_STATS_URL, total=len(ALL_STATS_URL), desc="Đang thu thập stats"):
        success = False

        for attempt in range(2):
            try:
                driver.get(url)
                for _ in range(25):
                    state = driver.execute_script("return document.readyState;")
                    if state == "complete":
                        break
                    time.sleep(1)

                success = True
                break

            except TimeoutException:
                print(f"Timeout — thử lại {attempt+1}/2 ...")
                time.sleep(3)
            except Exception as e:
                print(f"Lỗi load URL: {url} — {e}")
                time.sleep(3)
        if not success:
            print(f"Bỏ qua URL: {url}\n")
            continue
        time.sleep(random.uniform(3, 6))
        soup = BeautifulSoup(driver.page_source, "html.parser")
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

    driver.quit()
    if not df_list:
        print("Không có dữ liệu")
        return pd.DataFrame()
    merge_df = pd.concat(df_list, axis=1)
    merge_df = merge_df.loc[:, ~merge_df.columns.duplicated()]
    merge_df = merge_df.reset_index()

    # lọc cầu thủ có > 90 phút
    if "Min" in merge_df.columns:
        merge_df["Min"] = pd.to_numeric(merge_df["Min"], errors="coerce")
        merge_df = merge_df[merge_df["Min"] > 90]
    merge_df.fillna("N/A", inplace=True)

    print(f"Thu thập thành công dữ liệu của {len(merge_df)} cầu thủ!\n")

    return merge_df


# ===============================================
# EXPORT RAW CSV
# ===============================================
RAW_DIR = os.path.join(DATA_DIR, "raw")
CSV_PATH = os.path.join(RAW_DIR, "player_stats.csv")
def save_to_csv(df):
    try:
        os.makedirs(RAW_DIR, exist_ok=True)
        df.to_csv(CSV_PATH, index=False)
        print(f"Đã lưu CSV: {CSV_PATH}\n")
    except Exception as e:
        print(f"Lỗi lưu CSV: {e}")

# ===============================================
# MAIN
# ===============================================
if __name__=="__main__":
    setup_database()

    stats_df = get_player_stats()

    save_to_database(stats_df, "PLAYER_STATS")
    save_to_csv(stats_df)

    print("Hoàn tất chương trình!")



