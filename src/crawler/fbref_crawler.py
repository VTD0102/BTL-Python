import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth
from io import StringIO
import time
import sys
import os


project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from src.database.db_init import create_tables
    from src.database.db_utils import save_player_stats_to_db
except ModuleNotFoundError:
    print("error: Không tìm thấy module 'scr.database'.")
    print("Hãy chạy script này từ thư mục gốc (BTL-Python).")
    print("Và đảm bảo có file '__init__.py' trong mỗi thư mục con.")
    sys.exit(1)


# ===================== Ánh xạ cột =====================
COLUMN_MAPPING = {
    'Player': 'player_name',
    'Nation': 'nation',
    'Pos': 'position',
    'Squad': 'club',
    'Age': 'age',
    'Playing Time_MP': 'matches_played',
    'Playing Time_Starts': 'starts',
    'Playing Time_Min': 'minutes',
    'Playing Time_90s': 'ninety_mins',
    'Performance_Gls': 'goals',
    'Performance_Ast': 'assists',
    'Performance_G+A': 'goals_plus_assists',
    'Performance_G-PK': 'goals_minus_pk',
    'Performance_PK': 'penalties_scored',
    'Performance_PKatt': 'penalties_attempted',
    'Performance_CrdY': 'yellow_cards',
    'Performance_CrdR': 'red_cards',
    'Expected_xG': 'xG',
    'Expected_npxG': 'npxG',
    'Expected_xAG': 'xAG',
    'Expected_npxG+xAG': 'npxG_plus_xAG',
    'Progression_PrgC': 'progressive_carries',
    'Progression_PrgP': 'progressive_passes',
    'Progression_PrgR': 'progressive_receptions',
    'Per 90 Minutes_Gls': 'goals_per90',
    'Per 90 Minutes_Ast': 'assists_per90',
    'Per 90 Minutes_G+A': 'g_plus_a_per90',
    'Per 90 Minutes_G-PK': 'g_minus_pk_per90',
    'Per 90 Minutes_G+A-PK': 'g_plus_a_minus_pk_per90',
    'Per 90 Minutes_xG': 'xG_per90',
    'Per 90 Minutes_xAG': 'xAG_per90',
    'Per 90 Minutes_xG+xAG': 'xG_plus_xAG_per90',
    'Per 90 Minutes_npxG': 'npxG_per90',
    'Per 90 Minutes_npxG+xAG': 'npxG_plus_xAG_per90',
}


# ===================== Hàm xử lý header phức tạp =====================
def flatten_fbref_headers(df):
    """
    Ghép 2 hàng tiêu đề của bảng FBref thành 1.
    """
    if isinstance(df.columns, pd.MultiIndex):
        new_cols = []
        for col in df.columns:
            if "Unnamed" in col[0]:
                new_cols.append(col[1])
            else:
                new_cols.append(f"{col[0]}_{col[1]}")
        df.columns = new_cols
    df = df[df['Player'] != 'Player'].reset_index(drop=True)
    return df


# ===================== Hàm cào dữ liệu chính =====================
def scrape_fbref_stats(season_url: str):
    print("Đang khởi tạo trình duyệt Chrome Stealth...")
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")  # không cần bật GUI
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("window-size=1920,1080")

    driver = webdriver.Chrome(service=service, options=options)

    # Cấu hình Selenium Stealth
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True)

    try:
        print(f"Truy cập: {season_url}")
        driver.get(season_url)

        # Kiểm tra CAPTCHA
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[title='reCAPTCHA']"))
            )
            print("PHÁT HIỆN CAPTCHA! Vui lòng giải thủ công trong 30 giây...")
            time.sleep(30)
        except:
            print("Không phát hiện CAPTCHA, tiếp tục...")

        # Chấp nhận cookie (nếu có)
        try:
            wait = WebDriverWait(driver, 5)
            accept_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept All')]")))
            accept_btn.click()
            print("Đã chấp nhận cookie banner.")
            time.sleep(1)
        except:
            pass

        # Chờ bảng chính hiển thị
        print("Đang chờ bảng 'stats_standard' tải...")
        table = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "stats_standard"))
        )
        time.sleep(2)

        html = table.get_attribute('outerHTML')
        df = pd.read_html(StringIO(html))[0]
        df = flatten_fbref_headers(df)

        # Chuyển kiểu dữ liệu
        for col in df.columns:
            if col not in ['Player', 'Nation', 'Pos', 'Squad', 'Age']:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Lọc cầu thủ > 90 phút
        df = df[df['Playing Time_Min'] > 90].copy()
        print(f"Thu thập được {len(df)} cầu thủ có > 90 phút thi đấu.")

        # Giữ các cột hợp lệ
        valid_cols = [c for c in COLUMN_MAPPING.keys() if c in df.columns]
        df = df[valid_cols].rename(columns=COLUMN_MAPPING)

        # Điền giá trị thiếu
        df.fillna(pd.NA, inplace=True)

        # Ghi vào database
        print("Ghi dữ liệu vào SQLite...")
        save_player_stats_to_db(df)

        print("Hoàn thành bước I.1: Thu thập dữ liệu cầu thủ Premier League!")

    except Exception as e:
        print(f"Lỗi khi thu thập dữ liệu: {e}")
    finally:
        print("Đóng trình duyệt.")
        driver.quit()


# ===================== Chạy chính =====================
if __name__ == "__main__":
    print("Khởi tạo CSDL (nếu chưa có)...")
    create_tables()

    URL = "https://fbref.com/en/comps/9/2024-2025/stats/2024-2025-Premier-League-Stats"
    print("\nBắt đầu thu thập dữ liệu FBref...\n")
    scrape_fbref_stats(URL)
