import asyncio
from playwright.async_api import async_playwright

async def get_specific_hotel_price(page, hotel_url):
    """手動で指定された特定ホテルの価格を取得するロジック"""
    # TODO: ここでURLのページへ遷移し、実際の価格と空室状況を抽出
    await asyncio.sleep(1)
    return {"type": "手動指定", "hotel_url": hotel_url, "hotel_name": "指定されたホテル", "price": 8500}

async def search_area_hotels(page, area_keyword):
    """指定エリアのホテルを楽天トラベルで検索し、自動で上位の競合をリストアップするロジック"""
    # TODO: 楽天トラベルの検索結果ページで一覧から価格とホテル名を複数抽出
    await asyncio.sleep(2)
    return [
        {"type": "自動抽出", "hotel_name": "山中湖 競合ホテルA", "price": 8200},
        {"type": "自動抽出", "hotel_name": "山中湖 競合ホテルB", "price": 9000},
    ]

async def scrape_rakuten_travel(area_keyword="山梨県 山中湖村", custom_hotel_urls=[]):
    print(f"[{area_keyword}] のデータ収集を開始...")
    results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # 1. 自動で競合エリアをスクレイピング
        auto_hotels = await search_area_hotels(page, area_keyword)
        results.extend(auto_hotels)
        
        # 2. 手動指定URLのスクレイピング
        for url in custom_hotel_urls:
            if url.strip():
                data = await get_specific_hotel_price(page, url)
                results.append(data)
                
        await browser.close()
    
    return results

if __name__ == "__main__":
    # テスト実行
    area = "山梨県 山中湖村"
    custom_urls = ["https://travel.rakuten.co.jp/HOTEL/00000/00000.html"]
    
    print("--- スクレイピングテスト開始 ---")
    data = asyncio.run(scrape_rakuten_travel(area, custom_urls))
    
    print("=== 取得結果 ===")
    for item in data:
         print(f"[{item['type']}] {item['hotel_name']}: {item['price']}円")
