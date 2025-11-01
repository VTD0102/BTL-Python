import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth
import time, os, sys

# ====== Setup project path ======
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from src.database.db_init import create_tables
    from src.database.db_utils import save_transfer_values_to_db
except ModuleNotFoundError:
    print("❌ Lỗi: Không tìm thấy module database.")
    sys.exit(1)

RAW_DIR = os.path.join(project_root, "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

COLUMN_MAPPING = {
    "Player": "player_name",
    "Club": "club",
    "Age": "age",
    "Skill": "skill_score",
    "Pot": "potential_score",
    "Value": "market_value"
}


def scrape_transfer_values_all_pages(base_url: str, total_pages: int = 22, delay: float = 2.0):
    print("🚀 Đang khởi tạo trình duyệt Stealth Chrome...")
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("window-size=1920,1080")
    driver = webdriver.Chrome(service=service, options=options)

    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True)

    all_records = []

    try:
        page_urls = [base_url] + [f"{base_url}/{i}" for i in range(2, total_pages + 1)]

        for idx, page_url in enumerate(page_urls, start=1):
            print(f"\n🌍 Trang {idx}/{total_pages}: {page_url}")
            driver.get(page_url)

            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table tbody tr"))
                )
            except:
                print("⚠️ Không tìm thấy bảng, bỏ qua trang.")
                continue

            time.sleep(2)
            rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
            print(f"  → Tìm thấy {len(rows)} hàng trên trang {idx}")

            page_data = []
            for row in rows:
                try:
                    skill = row.find_element(By.CSS_SELECTOR, "div.table-skill__skill").text.strip()
                    pot = row.find_element(By.CSS_SELECTOR, "div.table-skill__pot").text.strip()
                    name = row.find_element(By.CSS_SELECTOR, "td.td-player a").text.strip()
                    club = row.find_element(By.CSS_SELECTOR, "span.td-team__teamname").text.strip()
                    age_text = row.find_element(By.CSS_SELECTOR, "td.m-hide.age").text.strip()
                    value = row.find_element(By.CSS_SELECTOR, "span.player-tag").text.strip()

                    if name:
                        page_data.append({
                            "Player": name,
                            "Club": club,
                            "Age": int(age_text) if age_text.isdigit() else None,
                            "Skill": float(skill) if skill.replace('.', '', 1).isdigit() else None,
                            "Pot": float(pot) if pot.replace('.', '', 1).isdigit() else None,
                            "Value": value
                        })
                except Exception:
                    continue

            print(f"  ✅ Trang {idx}: thu được {len(page_data)} cầu thủ hợp lệ.")

            if page_data:
                df_page = pd.DataFrame(page_data)
                df_page.rename(columns=COLUMN_MAPPING, inplace=True)
                df_page = df_page.where(pd.notnull(df_page), None)

                # lưu luôn vào DB
                save_transfer_values_to_db(df_page)
                print(f"  💾 Đã lưu {len(df_page)} bản ghi trang {idx} vào stats.db.")

                # gom tất cả để lưu CSV cuối
                all_records.extend(page_data)

            time.sleep(delay)

        if all_records:
            df_all = pd.DataFrame(all_records)
            df_all.rename(columns=COLUMN_MAPPING, inplace=True)
            df_all.to_csv(os.path.join(RAW_DIR, "transfer_values_full.csv"), index=False, encoding="utf-8-sig")
            print(f"\n📁 Đã lưu toàn bộ dữ liệu vào: data/raw/transfer_values_full.csv")
        else:
            print("⚠️ Không có dữ liệu nào được thu thập!")

    except Exception as e:
        print(f"❌ Lỗi trong quá trình cào: {e}")
    finally:
        driver.quit()
        print("🧹 Đã đóng trình duyệt.")


if __name__ == "__main__":
    print("--- Bước 1: Khởi tạo CSDL (nếu chưa có) ---")
    create_tables()

    # 🧹 Xóa dữ liệu cũ trong bảng transfer_values trước khi cào mới
    from src.database.db_utils import clear_table
    clear_table("transfer_values")

    BASE_URL = "https://www.footballtransfers.com/us/players/uk-premier-league"
    TOTAL_PAGES = 22

    print("\n--- Bước 2: Bắt đầu cào dữ liệu ---")
    scrape_transfer_values_all_pages(BASE_URL, total_pages=TOTAL_PAGES)
