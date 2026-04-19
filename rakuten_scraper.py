import asyncio
import re
import pandas as pd
from playwright.async_api import async_playwright

async def get_specific_hotel_price(page, hotel_url):
    """手動で指定された特定ホテルの価格を取得するロジック"""
    print(f"特定ホテル取得中: {hotel_url}")
    try:
        # domcontentloadedで待機し、不要な画像の読み込みなどを待たずに高速化
        await page.goto(hotel_url, wait_until="domcontentloaded", timeout=30000)
        
        # ホテル名の取得 (タイトルタグから抽出)
        title = await page.title()
        hotel_name = title.split("【")[0].split(" -")[0].strip()
        
        # 金額を表すクラス名（楽天の一般的なクラスを複数指定）
        price_elements = await page.locator(".price, .charge, .dp-price, .c-price, dd.price strong").all_inner_texts()
        
        min_price = None
        for text in price_elements:
            match = re.search(r'([0-9,]+)', text)
            if match:
                price = int(match.group(1).replace(',', ''))
                # 最安値を記録
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

async def search_area_hotels(page, area_keyword):
    """指定エリアのホテルを検索し、自動で上位の競合をリストアップする"""
    print(f"「{area_keyword}」で競合エリア検索中...")
    results = []
    try:
        # 楽天トラベルのキーワード検索結果ページへ直接遷移
        search_url = f"https://search.travel.rakuten.co.jp/ds/hotellist/Japan?f_query={area_keyword}"
        await page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
        
        # 検索結果のホテルブロックが表示されるまで待機（複数の代表的なクラスを指定）
        await page.wait_for_selector(".section, .hotelItem, .c-hotel-item, .search-result-item", timeout=15000)
        hotel_blocks = await page.locator(".section, .hotelItem, .c-hotel-item, .search-result-item").all()
        
        if not hotel_blocks:
            page_title = await page.title()
            results.append({
                "種別": "デバッグ",
                "ホテル名": "検索結果ゼロ",
                "最安値(円)": f"タイトル: {page_title}",
                "URL": "-"
            })
            
        # 上位5件程度のデータを抽出
        for block in hotel_blocks[:5]:
            # ホテル名の抽出
            hotel_name_loc = block.locator("h1 a, h2 a, .hotelName, .c-hotel-info__name")
            if await hotel_name_loc.count() > 0:
                name = await hotel_name_loc.first.inner_text()
            else:
                continue
                
            # 価格の抽出
            price_loc = block.locator(".price, .charge, .dp-price, .c-price")
            min_price = None
            if await price_loc.count() > 0:
                price_texts = await price_loc.all_inner_texts()
                for text in price_texts:
                    match = re.search(r'([0-9,]+)円', text)
                    if match:
                        price_num = int(match.group(1).replace(',', ''))
                        if min_price is None or price_num < min_price:
                            min_price = price_num
                            
            results.append({
                "種別": "自動抽出",
                "ホテル名": name.strip(),
                "最安値(円)": min_price if min_price else "満室または取得不可",
                "URL": "-"
            })
    except Exception as e:
        results.append({
            "種別": "エラー",
            "ホテル名": "検索処理中に例外発生",
            "最安値(円)": str(e),
            "URL": "-"
        })
        
    return results

async def scrape_rakuten_travel(area_keyword="山梨県 山中湖村", custom_hotel_urls=[]):
    results = []
    
    # ユーザーエージェントを偽装してボット判定を回避
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # クラウド（サーバー）環境でもエラーが出にくいようコンテキストを設定
        context = await browser.new_context(user_agent=user_agent, viewport={"width": 1920, "height": 1080})
        page = await context.new_page()
        
        # 1. 手動指定URLのスクレイピング
        for url in custom_hotel_urls:
            if url.strip():
                data = await get_specific_hotel_price(page, url.strip())
                results.append(data)
                # 楽天サーバーへの負荷軽減とブロック回避のための待機
                await asyncio.sleep(2) 
                
        # 2. 自動で競合エリアをスクレイピング
        if area_keyword:
            auto_hotels = await search_area_hotels(page, area_keyword)
            results.extend(auto_hotels)
                
        await browser.close()
    
    return results

if __name__ == "__main__":
    area = "山梨県 山中湖村"
    # 例：適当なホテルのURLがあればここに記載（デモ用）
    custom_urls = ["https://travel.rakuten.co.jp/HOTEL/0000/0000.html"]
    
    print(f"=== スクレイピング開始 (対象: {area}) ===")
    data = asyncio.run(scrape_rakuten_travel(area, custom_urls))
    
    print("\n=== スクレイピング結果 ===")
    if data:
        # 結果をきれいに表にして表示（将来的にUI側に渡すデータ）
        df = pd.DataFrame(data)
        print(df.to_string(index=False))
    else:
        print("データが取得できませんでした。")
