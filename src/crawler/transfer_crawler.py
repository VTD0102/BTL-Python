import pandas as pd
import requests
from urllib.parse import quote_plus
import time
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from src.database.db_init import create_tables
    from src.database.db_utils import read_player_list, save_transfer_values
    from src.crawler.utils import get_soup_from_session
except ImportError:
    print("Lỗi: Không thể import 'src.database' hoặc 'src.crawler.utils'.")
    print("Vui lòng kiểm tra các file __init__.py và các hàm trong db_utils.py")
    sys.exit(1)

def get_transfer_value(session, player_name):
    base_url = "https://www.footballtransfers.com"
    search_query = quote_plus(player_name)
    search_url = f"{base_url}/en/players/search/{search_query}"
    
    player_data = {
        'market_value': 'N/a',
        'position': 'N/a',
        'age': 'N/a',
        'nationality': 'N/a'
    }

    try:
        search_soup = get_soup_from_session(session, search_url)
        if search_soup is None:
            return player_data
        
        player_link_element = search_soup.find('a', class_='player-name-search')
        
        if not player_link_element or not player_link_element.get('href'):
            return player_data

        player_page_url = player_link_element['href']
        if not player_page_url.startswith('http'):
            player_page_url = base_url + player_page_url
        
        time.sleep(1)
        player_soup = get_soup_from_session(session, player_page_url)
        if player_soup is None:
            return player_data
        
        value_el = player_soup.find('span', class_='player-value')
        if value_el:
            player_data['market_value'] = value_el.text.strip()
            
        pos_el = player_soup.find('span', {'data-qa': 'player-position'})
        if pos_el:
            player_data['position'] = pos_el.text.strip()
            
        age_el = player_soup.find('span', {'data-qa': 'player-age'})
        if age_el:
            age_text = age_el.text.strip().replace('(', '').replace(')', '')
            try:
                player_data['age'] = int(age_text)
            except ValueError:
                player_data['age'] = 'N/a'
        
        nat_el = player_soup.find('span', {'data-qa': 'player-nationality'})
        if nat_el:
            player_data['nationality'] = nat_el.text.strip()

        return player_data
            
    except Exception as e:
        print(f"   > Lỗi khi cào {player_name}: {e}")
        return player_data

def scrape_all_transfer_values():
    print("--- Bước 1: Khởi tạo CSDL (kiểm tra bảng 'transfer_values') ---")
    create_tables()
    
    print("\n--- Bước 2: Đọc danh sách cầu thủ từ 'player_stats' ---")
    players_df = read_player_list()
    
    if players_df.empty:
        print("Lỗi: Không tìm thấy dữ liệu trong bảng 'player_stats'.")
        print("Vui lòng chạy 'fbref_crawler.py' trước.")
        return

    print(f"Đã đọc được {len(players_df)} cầu thủ từ CSDL.")
    
    results_list = []
    session = requests.Session()
    
    print("\n--- Bước 3: Bắt đầu cào dữ liệu giá chuyển nhượng (Quá trình này sẽ chậm) ---")
    
    for index, row in players_df.iterrows():
        player_name = row['player_name']
        club = row['club']
        
        print(f"({index + 1}/{len(players_df)}) Đang cào: {player_name} ({club})...")
        
        player_data = get_transfer_value(session, player_name)
        
        full_record = {
            'player_name': player_name,
            'club': club,
            **player_data
        }
        results_list.append(full_record)
        
        print(f"   > Kết quả: {player_data['market_value']}, {player_data['position']}")
        
        time.sleep(2)

    print("\n--- Bước 4: Đã cào xong. Chuẩn bị lưu vào 'transfer_values' ---")
    values_df = pd.DataFrame(results_list)
    
    save_transfer_values(values_df)
    
    print(f"--- Hoàn thành I.2! ---")

if __name__ == "__main__":
    scrape_all_transfer_values()