import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import pandas as pd
import time

def get_specific_hotel_price(hotel_url, scraperapi_key):
    print(f"特定ホテル取得中 (じゃらん): {hotel_url}")
    try:
        if scraperapi_key:
            encoded_url = urllib.parse.quote(hotel_url, safe='')
            scraper_url = f"http://api.scraperapi.com?api_key={scraperapi_key}&url={encoded_url}&country_code=jp&premium=true"
            resp = requests.get(scraper_url, timeout=60)
        else:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            resp = requests.get(hotel_url, headers=headers, timeout=30)
            
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # じゃらんのホテル詳細ページ名抽出
        title = soup.title.string if soup.title else "不明"
        hotel_name = title.split(" -")[0].split("【")[0].strip()
        
        # 価格の抽出 (じゃらんは強力な正規表現で一網打尽にする)
        price_elements = soup.select(".price, .p-searchResultItem__lowestPrice, .jln-price, strong")
        min_price = None
        
        # ページ全体のテキストからも検索フォールバック
        text_nodes = [el.get_text() for el in price_elements]
        if not text_nodes: # もし特定クラスが無ければページ全体から
            text_nodes = [soup.get_text()]
            
        for text in text_nodes:
            # {数字}円 のパターンを探す
            matches = re.finditer(r'([0-9]{1,3}(?:,[0-9]{3})+)\s*円', text)
            for match in matches:
                price = int(match.group(1).replace(',', ''))
                # 極端に安い/高い値はノイズの可能性
                if 2000 < price < 500000:
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
    print(f"じゃらんで競合エリア検索中...")
    results = []
    try:
        # じゃらん山中湖・忍野エリアの一覧ページ (これなら検索パラメータ起因の404を防げる)
        # https://www.jalan.net/150000/LRG_151600/
        raw_target_url = "https://www.jalan.net/150000/LRG_151600/"
        
        if scraperapi_key:
            encoded_target = urllib.parse.quote(raw_target_url, safe='')
            scraper_url = f"http://api.scraperapi.com?api_key={scraperapi_key}&url={encoded_target}&country_code=jp&premium=true"
            resp = requests.get(scraper_url, timeout=60)
        else:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            resp = requests.get(raw_target_url, headers=headers, timeout=30)
            
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
            
        # 宿ブロックの抽出 (じゃらんのリスト構造)
        hotel_blocks = soup.select(".p-searchResultItem, .cassette, .yadoLump")
        
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
            name_el = block.select_one(".p-searchResultItem__facilityName, .s16b, .hotelName, h2")
            if not name_el:
                continue
            name = name_el.get_text(strip=True)
            
            # 価格の抽出
            min_price = None
            text = block.get_text()
            matches = re.finditer(r'([0-9]{1,3}(?:,[0-9]{3})+)\s*円', text)
            for match in matches:
                price_num = int(match.group(1).replace(',', ''))
                if 2000 < price_num < 500000:
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

def scrape_jalan(area_keyword="山梨県 山中湖村", custom_hotel_urls=[], scraperapi_key=""):
    results = []
    
    for url in custom_hotel_urls:
        if url.strip():
            result = get_specific_hotel_price(url.strip(), scraperapi_key)
            results.append(result)
            time.sleep(1) # API負荷軽減
            
    if area_keyword:
        auto_hotels = search_area_hotels(area_keyword, scraperapi_key)
        results.extend(auto_hotels)
            
    return results

if __name__ == "__main__":
    area = "山中湖村"
    custom_urls = []
    test_key = "4a065dd5f0550a8fe85e902a64eeebaf"
    data = scrape_jalan(area, custom_urls, test_key)
    if data:
        df = pd.DataFrame(data)
        print(df.to_string(index=False))
    else:
        print("データ取得失敗")
