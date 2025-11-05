import argparse
import requests
import pandas as pd
import os
import sys

API_URL = "http://127.0.0.1:5000"  # Flask API phải đang chạy
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../../data/lookup_results")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def fetch_data(endpoint: str, param_name: str, value: str):
    """
    Gọi API Flask để lấy dữ liệu cầu thủ theo tên hoặc câu lạc bộ.
    """
    try:
        url = f"{API_URL}/{endpoint}"
        response = requests.get(url, params={param_name: value})
        if response.status_code == 200:
            data = response.json()
            if data:
                print(f"✅ Nhận được {len(data)} kết quả từ API.")
                return data
            else:
                print("⚠️ Không tìm thấy kết quả phù hợp.")
                return []
        else:
            print(f"❌ Lỗi HTTP {response.status_code}: {response.text}")
            return []
    except requests.exceptions.ConnectionError:
        print("❌ Không thể kết nối đến API. Hãy chắc chắn rằng Flask đang chạy (python src/api/app.py).")
        sys.exit(1)
    except Exception as e:
        print(f"⚠️ Lỗi khi gọi API: {e}")
        return []


def save_to_csv(data, filename):
    """
    Lưu dữ liệu vào file CSV trong thư mục data/lookup_results
    """
    if not data:
        return
    df = pd.DataFrame(data)
    output_path = os.path.join(OUTPUT_DIR, filename)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"💾 Đã lưu kết quả vào: {output_path}")


def lookup(name=None, club=None):
    """
    Hàm chính: gọi API tương ứng và hiển thị kết quả dạng bảng
    """
    if name:
        print(f"🔍 Tra cứu cầu thủ: {name}")
        data = fetch_data("player", "name", name)
        if data:
            df = pd.DataFrame(data)
            print(df.head(10).to_string(index=False))  # In 10 kết quả đầu
            save_to_csv(data, f"{name.replace(' ', '_')}.csv")

    elif club:
        print(f"🔍 Tra cứu câu lạc bộ: {club}")
        data = fetch_data("club", "club", club)
        if data:
            df = pd.DataFrame(data)
            print(df.head(10).to_string(index=False))
            save_to_csv(data, f"{club.replace(' ', '_')}.csv")

    else:
        print("⚠️ Bạn phải cung cấp ít nhất một trong hai tham số: --name hoặc --club")


def main():
    parser = argparse.ArgumentParser(description="Tra cứu dữ liệu cầu thủ từ API Flask")
    parser.add_argument("--name", type=str, help="Tên cầu thủ cần tra cứu")
    parser.add_argument("--club", type=str, help="Tên câu lạc bộ cần tra cứu")
    args = parser.parse_args()

    lookup(name=args.name, club=args.club)


if __name__ == "__main__":
    main()
