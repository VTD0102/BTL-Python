import re
import time
import random
import requests
from functools import wraps
from fake_useragent import UserAgent
import os
import time
import pandas as pd
ua = UserAgent()


# =====================================
# 1 Hàm tải HTML có retry tự động
# =====================================
def get_html(url, max_retries=3, delay=5):
    """
    Tải nội dung HTML của một trang web, retry khi bị lỗi mạng hoặc rate-limit.
    """
    headers = {"User-Agent": ua.random}
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Tải {url} (lần {attempt})...")
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.text
            else:
                print(f"Mã phản hồi: {response.status_code}")
        except requests.RequestException as e:
            print(f"Lỗi khi tải {url}: {e}")
        time.sleep(delay + random.uniform(0, 3))
    raise ConnectionError(f"Không thể tải {url} sau {max_retries} lần thử.")


# =====================================
# 2️ Chuẩn hoá tên cầu thủ
# =====================================
def normalize_name(name: str) -> str:
    """
    Chuẩn hoá tên cầu thủ để khớp giữa FBref và FootballTransfers.
    """
    if not name:
        return None
    name = name.strip().lower()
    name = re.sub(r"[^a-z\s]", "", name)
    name = re.sub(r"\s+", " ", name)
    parts = name.split(" ")
    if len(parts) > 1:
        return " ".join(sorted(parts))  # Ví dụ: “Haaland Erling” -> “erling haaland”
    return name


# =====================================
# 3 Chuẩn hoá giá trị tiền tệ
# =====================================
def clean_value(value: str):
    """
    Chuyển giá trị như “€80.5m”, “£50k”, “N/A” -> float (đơn vị euro).
    """
    if not value or value in ["N/A", "-", ""]:
        return None
    value = value.replace("€", "").replace("£", "").replace(",", "").strip().lower()
    try:
        if value.endswith("m"):
            return float(value[:-1]) * 1_000_000
        elif value.endswith("k"):
            return float(value[:-1]) * 1_000
        else:
            return float(value)
    except ValueError:
        return None


# =====================================
# 4 Decorator retry chung
# =====================================
def retry_on_fail(max_retries=3, delay=3):
    """
    Decorator tự động thử lại khi hàm gặp lỗi mạng hoặc timeout.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"Lỗi lần {attempt + 1}: {e}")
                    time.sleep(delay)
            raise RuntimeError(f"Hàm {func.__name__} thất bại sau {max_retries} lần thử.")
        return wrapper
    return decorator

def save_raw_data(html_content: str, df: pd.DataFrame, prefix: str = "data_dump"):
    """
    Lưu dữ liệu thô (HTML và DataFrame) vào thư mục data/raw.
    - html_content: nội dung HTML gốc (chuỗi)
    - df: DataFrame đã xử lý
    - prefix: tiền tố tên file (vd: 'fbref', 'transfer', 'premier_league')

    Output:
      data/raw/<prefix>_<timestamp>.html
      data/raw/<prefix>_<timestamp>.csv
    """
    # Xác định đường dẫn thư mục data/raw
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    raw_dir = os.path.join(project_root, 'data', 'raw')
    os.makedirs(raw_dir, exist_ok=True)

    # Tạo timestamp cho tên file
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    # Đường dẫn file HTML và CSV
    html_path = os.path.join(raw_dir, f"{prefix}_{timestamp}.html")
    csv_path = os.path.join(raw_dir, f"{prefix}_{timestamp}.csv")

    # Lưu HTML
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Lưu CSV
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    print(f"[RAW] HTML saved to: {html_path}")
    print(f"[RAW] CSV saved to:  {csv_path}")

    return html_path, csv_path