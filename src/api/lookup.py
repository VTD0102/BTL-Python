import requests
import argparse
import pandas as pd
import os

API_URL = "http://127.0.0.1:5000"
RESULT_DIR = os.path.join("data", "lookup_results")
os.makedirs(RESULT_DIR, exist_ok=True)

def lookup_player(name):
    print(f"🔍 Tra cứu cầu thủ: {name}")
    url = f"{API_URL}/player?name={name}"
    r = requests.get(url)
    if r.status_code != 200:
        print(f"❌ Lỗi HTTP {r.status_code}: {r.text}")
        return
    data = r.json()
    if not data:
        print(f"⚠️ Không tìm thấy cầu thủ {name}")
        return
    df = pd.DataFrame(data)
    output = os.path.join(RESULT_DIR, f"{name}_lookup.csv")
    df.to_csv(output, index=False, encoding="utf-8-sig")
    print(df.head(10))
    print(f"✅ Kết quả đã lưu: {output}")

def lookup_club(club):
    print(f"🏟️ Tra cứu câu lạc bộ: {club}")
    url = f"{API_URL}/club?club={club}"  # ✅ CHỈNH Ở ĐÂY
    r = requests.get(url)
    if r.status_code != 200:
        print(f"❌ Lỗi HTTP {r.status_code}: {r.text}")
        return
    data = r.json()
    if not data:
        print(f"⚠️ Không tìm thấy CLB {club}")
        return
    df = pd.DataFrame(data)
    output = os.path.join(RESULT_DIR, f"{club.replace(' ', '_')}_lookup.csv")
    df.to_csv(output, index=False, encoding="utf-8-sig")
    print(df.head(10))
    print(f"✅ Kết quả đã lưu: {output}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tra cứu dữ liệu cầu thủ hoặc CLB từ API")
    parser.add_argument("--name", help="Tên cầu thủ")
    parser.add_argument("--club", help="Tên câu lạc bộ")
    args = parser.parse_args()

    if args.name:
        lookup_player(args.name)
    elif args.club:
        lookup_club(args.club)
    else:
        print("⚠️ Hãy truyền thêm --name hoặc --club")
