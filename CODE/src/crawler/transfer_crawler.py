import pandas as pd
import sqlite3
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth
import time, os, sys, random


# ===================== DB PATH =====================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "stats.db")
DATABASE_NAME = "stats.db"

print("DB_PATH =", DB_PATH)


# ===================== CREATE PLAYER_VALUES TABLE =====================
def create_PLAYER_VALUES():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS "PLAYER_VALUES" (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT,
            transfer_value TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("Table 'PLAYER_VALUES' checked/created successfully.")


# ===================== CLEAR PLAYER_VALUES =====================
def clear_PLAYER_VALUES():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('DELETE FROM "PLAYER_VALUES"')
    cur.execute("DELETE FROM sqlite_sequence WHERE name='PLAYER_VALUES'")
    conn.commit()
    conn.close()
    print("Đã xóa dữ liệu cũ trong bảng 'PLAYER_VALUES' và reset ID.")
# ===================== INSERT =====================
def insert_PLAYER_VALUES(df):
    conn = sqlite3.connect(DB_PATH)
    df.to_sql("PLAYER_VALUES", conn, if_exists="append", index=False)
    conn.commit()
    conn.close()
    print(f"Đã lưu {len(df)} bản ghi vào bảng PLAYER_VALUES")


# ===================== CHROME STEALTH =====================
def get_driver():
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=service, options=options)
    stealth(
        driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True
    )
    return driver


# =============================================================
# GET TRANSFER VALUE (NO RATE LIMIT HANDLING)
# =============================================================
def get_transfer_value(driver, player_name: str):
    q = player_name.replace(" ", "%20")
    search_url = f"https://www.footballtransfers.com/us/search?search_value={q}"

    try:
        driver.get(search_url)

        el = WebDriverWait(driver, 8).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span.player-tag"))
        )

        return el.text.strip()

    except Exception:
        return None


# =============================================================
# ✅ MAIN CRAWL
# =============================================================
def scrape_value_for_player_list(players: list, delay: float = 1.0):
    driver = get_driver()
    collected = []
    try:
        total = len(players)
        for idx, name in enumerate(players, start=1):
            print(f"\n({idx}/{total}) Đang lấy: {name}")
            value = get_transfer_value(driver, name)
            if not value or value.strip() == "":
                value = "NA"
            print(f"  {name} → {value}")
            collected.append({
                "player_name": name,
                "transfer_value": value
            })
            time.sleep(delay + random.uniform(0.2, 0.6))
        if collected:
            df = pd.DataFrame(collected)
            insert_PLAYER_VALUES(df)
        else:
            print("Không có dữ liệu!")
    except Exception as e:
        print(f"Lỗi khi cào dữ liệu: {e}")
    finally:
        driver.quit()
        print("Đã đóng trình duyệt.")


# =============================================================
# MAIN
# =============================================================
if __name__ == "__main__":

    # 1) Tạo bảng
    create_PLAYER_VALUES()

    # 2) Xóa dữ liệu cũ
    clear_PLAYER_VALUES()

    # 3) Load from PLAYER_STATS
    try:
        print("\nĐang load danh sách từ bảng PLAYER_STATS...")

        conn = sqlite3.connect(DB_PATH)
        df_stats = pd.read_sql_query('SELECT Player FROM "PLAYER_STATS"', conn)
        conn.close()

        df_stats.rename(columns={"Player": "player_name"}, inplace=True)
        player_list = df_stats["player_name"].dropna().tolist()

        print(f"Load thành công {len(player_list)} cầu thủ từ bảng PLAYER_STATS")

    except Exception as e:
        print("\nKhông load được danh sách từ PLAYER_STATS.")
        print(e)
        sys.exit(1)

    # 4) Crawl
    print("\n---BẮT ĐẦU CRAWL---")
    scrape_value_for_player_list(player_list)