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
    from scr.database.db_init import create_tables
    from scr.database.db_utils import save_player_stats_to_db
except ModuleNotFoundError:
    print("Lỗi: Không tìm thấy module 'src.database'.")
    print("Hãy đảm bảo bạn đang chạy script này từ thư mục gốc (BTL-Python)")
    print("Và đảm bảo các file __init__.py đã tồn tại.")
    sys.exit(1)

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

def flatten_fbref_headers(df):
    new_cols = []
    for col in df.columns:
        if "Unnamed" in col[0]:
            new_cols.append(col[1])
        else:
            new_cols.append(f"{col[0]}_{col[1]}")
    df.columns = new_cols
    df = df[df['Player'] != 'Player'].reset_index(drop=True)
    return df

def scrape_fbref_stats(season_url):
    print("Đang khởi tạo trình duyệt (Selenium Stealth)...")
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    
    options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(service=service, options=options)

    stealth(driver, languages=["en-US", "en"], vendor="Google Inc.",
            platform="Win32", webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine", fix_hairline=True)
    
    try:
        print(f"Đang truy cập URL: {season_url}")
        driver.get(season_url)
        
        print("Bạn có 30 giây để giải CAPTCHA nếu nó xuất hiện...")
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[title='reCAPTCHA']"))
            )
            print("!!! PHÁT HIỆN CAPTCHA !!! Vui lòng giải CAPTCHA...")
            time.sleep(30)
        except:
            print("Không phát hiện CAPTCHA, tiếp tục...")

        try:
            wait = WebDriverWait(driver, 5)
            accept_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept All')]")))
            accept_button.click()
            print("Đã đồng ý cookie.")
            time.sleep(1)
        except Exception as e:
            print("Không tìm thấy banner cookie.")

        table_id = "stats_standard"
        wait = WebDriverWait(driver, 20)
        print(f"Đang chờ bảng '{table_id}' tải...")
        table_element = wait.until(EC.presence_of_element_located((By.ID, table_id)))
        
        driver.execute_script("window.scrollTo(0, arguments[0].offsetTop - 200);", table_element)
        time.sleep(2)

        print("Đang đọc dữ liệu từ bảng HTML...")
        table_html = table_element.get_attribute('outerHTML')
        
        df = pd.read_html(StringIO(table_html))[0]

        print("Đang xử lý dữ liệu...")
        
        df = flatten_fbref_headers(df)

        fbref_cols_to_process = list(COLUMN_MAPPING.keys())
        for col in fbref_cols_to_process:
            if col not in df.columns:
                print(f"Cảnh báo: Cột {col} không tìm thấy trong FBref, sẽ bỏ qua.")
                continue
            if col not in ['Player', 'Nation', 'Pos', 'Squad', 'Age']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df_filtered = df[df['Playing Time_Min'] > 90].copy()
        
        if df_filtered.empty:
            print("Không tìm thấy cầu thủ nào có > 90 phút thi đấu.")
            return

        print(f"Thu thập được {len(df_filtered)} cầu thủ có > 90 phút thi đấu.")

        valid_fbref_cols = [col for col in COLUMN_MAPPING.keys() if col in df.columns]
        df_to_save = df_filtered[valid_fbref_cols].copy()

        df_to_save.rename(columns=COLUMN_MAPPING, inplace=True)
        
        df_to_save.fillna(pd.NA, inplace=True)

        print("\nChuẩn bị lưu dữ liệu vào CSDL...")
        save_player_stats_to_db(df_to_save)
        
        print(f"--- Hoàn thành I.1! ---")

    except Exception as e:
        print(f"Đã xảy ra lỗi trong quá trình thu thập dữ liệu: {e}")
    finally:
        print("Đóng trình duyệt sau 5 giây.")
        time.sleep(5)
        driver.quit()

if __name__ == "__main__":
    
    print("--- Bước 1: Khởi tạo CSDL (nếu chưa có) ---")
    create_tables()
    
    URL = "https://fbref.com/en/comps/9/stats/Premier-League-Stats"
    
    print("\n--- Bước 2: Bắt đầu cào dữ liệu ---")
    scrape_fbref_stats(season_url=URL)