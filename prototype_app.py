import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import asyncio
import os

# 楽天トラベルのスクレイピング関数を読み込む
from rakuten_scraper import scrape_rakuten_travel

# 初回起動時にPlaywrightのブラウザをインストール（Streamlit Cloud環境用）
@st.cache_resource
def install_playwright():
    os.system("playwright install chromium")

def main():
    st.set_page_config(page_title="ダイナミックプライシング プロトタイプ", layout="wide")
    st.title("ホテル ダイナミックプライシング検証画面")
    
    st.sidebar.header("共通設定")
    target_area = st.sidebar.text_input("競合分析エリア (自動抽出用)", "山梨県 山中湖村")
    
    st.sidebar.markdown("---")
    st.sidebar.header("手動での競合指定")
    st.sidebar.write("特定の監視したいホテルがあれば、楽天トラベルのURLを貼ってください。")
    custom_urls = st.sidebar.text_area("競合ホテルURL (改行で複数指定可)", placeholder="https://travel.rakuten.co.jp/HOTEL/XXXX/...")
    
    st.sidebar.markdown("---")
    st.sidebar.header("API設定 (Botブロック回避用)")
    st.sidebar.write("クラウドから実行する場合、楽天のセキュリティブロックを回避するために必須です。")
    scraperapi_key = st.sidebar.text_input("ScraperAPI 認証キー", value="4a065dd5f0550a8fe85e902a64eeebaf", type="password")

    
    # 状態の初期化
    if 'scraped_data' not in st.session_state:
        st.session_state['scraped_data'] = None

    # ======= STEP 1: データ収集 =======
    st.header("1. 競合ホテルのデータ収集 (Liveスクレイピング)")
    st.write(f"現在の分析対象エリア: **{target_area}**")
    
    url_count = len([u for u in custom_urls.split("\n") if u.strip()])
    if url_count > 0:
        st.info(f"📌 手動で指定された {url_count} 件のホテルを含めて調査します。")

    if st.button("▶ 最新の競合データを取得する"):
        with st.spinner("楽天トラベルを調査中... (※環境の初回起動時はブラウザ準備に1〜2分かかる場合があります)"):
            try:
                # 初回のみブラウザをインストール（インストール済みの場合は一瞬でスキップされます）
                install_playwright()
                
                # 非同期のPlaywright関数をStreamlit上で実行するための処理
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                custom_url_list = [u for u in custom_urls.split("\n") if u.strip()]
                # スクリプトの実行 (ScraperAPIキーを渡す)
                results = loop.run_until_complete(scrape_rakuten_travel(target_area, custom_url_list, scraperapi_key))
                
                if results:
                    st.success("✅ データの取得に成功しました！")
                    st.session_state['scraped_data'] = pd.DataFrame(results)
                else:
                    st.warning("⚠️ 情報を取得できませんでした。時間をおいて再実行してください。")
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

    # 取得したデータの表示
    if st.session_state['scraped_data'] is not None:
        st.dataframe(st.session_state['scraped_data'], use_container_width=True)
        # 最安値などの基礎データを計算に回すための準備（現在はモック）
        avg_price = 8000 # 将来的には scraped_data の平均等から算出
    else:
        st.info("↑ ボタンを押して競合データを取得してください。")


    st.markdown("---")
    
    # ======= STEP 2: 価格の算出と承認 =======
    st.header("2. 推奨価格の確認と部分反映")
    st.write("上記の競合データや自社の稼働率を加味して算出した「今後の推奨価格」です。")

    # モックデータ作成 (未来1週間)
    today = datetime.now()
    dates = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    
    data = {
        "反映": [True, True, False, True, True, True, True],
        "日付": dates,
        "自社稼働率": ["85%", "92%", "98%", "60%", "70%", "80%", "75%"],
        "従来価格": [8000, 8000, 8000, 8000, 8000, 8000, 8000],
        "推奨価格案": [8400, 10500, 14000, 7500, 7500, 7800, 7800],
    }
    df = pd.DataFrame(data)
    
    st.markdown("変更を反映したい日付の **「反映する」** 列にチェックを入れてください。（推奨価格案のセルをクリックすると手動で修正も可能です）")
    
    # 部分反映が可能なエディタ
    edited_df = st.data_editor(
        df,
        column_config={
            "反映": st.column_config.CheckboxColumn("反映する", default=True),
            "推奨価格案": st.column_config.NumberColumn("推奨価格案 (手修正可)")
        },
        disabled=["日付", "自社稼働率", "従来価格"],
        hide_index=True,
        use_container_width=True
    )
    
    # ======= STEP 3: PMSへの送信 =======
    st.write("### 価格変更の実行（ねっぱん！連動モック）")
    if st.button("選択した日付の価格をねっぱん！に反映する"):
        selected_dates = edited_df[edited_df["反映"] == True]["日付"].tolist()
        if selected_dates:
            st.success(f"✅ 以下の {len(selected_dates)} 日分の価格をねっぱん！へ送信しました:\n\n{', '.join(selected_dates)}")
        else:
            st.warning("⚠️ 反映する日付が選ばれていません。チェックボックスを入れてください。")

if __name__ == "__main__":
    main()
