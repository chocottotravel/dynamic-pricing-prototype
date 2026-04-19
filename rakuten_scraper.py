import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import pandas as pd
import time

def get_specific_hotel_price(hotel_url, scraperapi_key):
    print(f"特定ホテル取得中: {hotel_url}")
    try:
        if scraperapi_key:
            payload = {'api_key': scraperapi_key, 'url': hotel_url, 'country_code': 'jp'}
            resp = requests.get('http://api.scraperapi.com', params=payload, timeout=60)
        else:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            resp = requests.get(hotel_url, headers=headers, timeout=30)
            
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        title = soup.title.string if soup.title else "不明"
        hotel_name = title.split("【")[0].split(" -")[0].strip()
        
        price_elements = soup.select(".price, .charge, .dp-price, .c-price, dd.price strong")
        min_price = None
        for el in price_elements:
            text = el.get_text()
            match = re.search(r'([0-9,]+)', text)
            if match:
                price = int(match.group(1).replace(',', ''))
                if min_price is None or price < min_price:
                    min_price = price
                    
        return {
            "種別": "手動指定", 
            "ホテル名": hotel_name, 
            "最安値(円)": min_price if min_price else "満室または取得不可",
            "URL": hotel_url
        }
    except Exception as e:
        print(f"エラー発生 ({hotel_url}): {e}")
        return {"種別": "手動指定", "ホテル名": "不明", "最安値(円)": "エラー", "URL": hotel_url}

def search_area_hotels(area_keyword, scraperapi_key):
    print(f"「{area_keyword}」で競合エリア検索中...")
    results = []
    try:
        search_url = f"https://search.travel.rakuten.co.jp/ds/hotellist/Japan?f_query={area_keyword}"
        
        if scraperapi_key:
            payload = {
                'api_key': scraperapi_key, 
                'url': search_url, 
                'country_code': 'jp'
            }
            resp = requests.get('http://api.scraperapi.com', params=payload, timeout=60)
        else:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            resp = requests.get(search_url, headers=headers, timeout=30)
            
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        page_title = soup.title.string if soup.title else ""
        if "Access Denied" in page_title or "Just a moment" in page_title:
            results.append({
                "種別": "エラー",
                "ホテル名": "ScraperAPI使用時もブロックを検知しました",
                "最安値(円)": f"タイトル: {page_title}",
                "URL": "-"
            })
            return results
            
        hotel_blocks = soup.select(".section, .hotelItem, .c-hotel-item, .search-result-item, section.hotel")
        
        if not hotel_blocks:
            results.append({
                "種別": "デバッグ",
                "ホテル名": "検索結果ゼロ（セレクタ不一致）",
                "最安値(円)": f"タイトル: {page_title[:15]}...",
                "URL": "-"
            })
            return results
            
        for block in hotel_blocks[:5]:
            # ホテル名の抽出
            name_el = block.select_one("h1 a, h2 a, .hotelName, .c-hotel-info__name, h2")
            if not name_el:
                continue
            name = name_el.get_text(strip=True)
            
            # 価格の抽出
            price_els = block.select(".price, .charge, .dp-price, .c-price")
            min_price = None
            for el in price_els:
                text = el.get_text()
                match = re.search(r'([0-9,]+)円', text)
                if match:
                    price_num = int(match.group(1).replace(',', ''))
                    if min_price is None or price_num < min_price:
                        min_price = price_num
                        
            results.append({
                "種別": "自動抽出",
                "ホテル名": name,
                "最安値(円)": min_price if min_price else "満室または取得不可",
                "URL": "-"
            })
    except Exception as e:
        results.append({
            "種別": "エラー",
            "ホテル名": "通信処理中に例外発生",
            "最安値(円)": str(e),
            "URL": "-"
        })
        
    return results

def scrape_rakuten_travel(area_keyword="山梨県 山中湖村", custom_hotel_urls=[], scraperapi_key=""):
    results = []
    
    for url in custom_hotel_urls:
        if url.strip():
            data = get_specific_hotel_price(url.strip(), scraperapi_key)
            results.append(data)
            time.sleep(1) # APIに負荷をかけないよう待機
            
    if area_keyword:
        auto_hotels = search_area_hotels(area_keyword, scraperapi_key)
        results.extend(auto_hotels)
            
    return results

if __name__ == "__main__":
    area = "山梨県 山中湖村"
    custom_urls = []
    test_key = "4a065dd5f0550a8fe85e902a64eeebaf"
    
    print(f"=== スクレイピング開始 (対象: {area}) ===")
    data = scrape_rakuten_travel(area, custom_urls, test_key)
    
    print("\n=== スクレイピング結果 ===")
    if data:
        df = pd.DataFrame(data)
        print(df.to_string(index=False))
    else:
        print("データが取得できませんでした。")
