import asyncio
from playwright.async_api import async_playwright

async def scrape_rakuten_travel(area_keyword):
    print(f"[{area_keyword}] の楽天トラベル検索を開始します...")
    
    async with async_playwright() as p:
        # 実際にはブロック回避のため headless=False で運用することが多いですが、テスト中はTrueでOK
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # 楽天トラベルのトップページへ
        await page.goto("https://travel.rakuten.co.jp/")
        
        # TODO: 検索窓にarea_keywordを入力して検索ボタンを押す等、実際のDOM操作をここに実装
        await asyncio.sleep(2)
        print("検索結果ページをロード中... (プロトタイプモック待機)")
        
        # モックデータとしての戻り値
        results = [
            {"hotel_name": "ホテルA", "price": 8500},
            {"hotel_name": "ホテルB", "price": 8200},
            {"hotel_name": "ホテルC", "price": 9000},
        ]
        
        await browser.close()
        return results

if __name__ == "__main__":
    # テスト実行
    area = "山中湖村"
    print("--- スクレイピングテスト開始 ---")
    data = asyncio.run(scrape_rakuten_travel(area))
    print("=== 取得結果 ===")
    for item in data:
         print(f"{item['hotel_name']}: {item['price']}円")
