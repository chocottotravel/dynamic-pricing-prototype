import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def main():
    st.set_page_config(page_title="ダイナミックプライシング プロトタイプ", layout="wide")
    st.title("ホテル ダイナミックプライシング検証画面 (プロトタイプ)")
    
    st.sidebar.header("共通設定")
    target_area = st.sidebar.text_input("競合分析エリア (自動抽出用)", "山梨県 山中湖村")
    
    st.sidebar.markdown("---")
    st.sidebar.header("手動での競合指定")
    st.sidebar.write("特定の監視したいホテルがあれば、楽天トラベルのURLを貼ってください。")
    custom_urls = st.sidebar.text_area("競合ホテルURL (改行で複数指定可)", placeholder="https://travel.rakuten.co.jp/HOTEL/XXXX/...")
    
    st.write(f"### 現在の分析対象エリア: {target_area}")
    url_count = len([u for u in custom_urls.split("\n") if u.strip()])
    if url_count > 0:
        st.info(f"📌 手動で指定された {url_count} 件のホテルも価格調査の対象として組み込みます。")
    
    # モックデータ作成
    today = datetime.now()
    dates = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    
    data = {
        "日付": dates,
        "自社稼働率": ["85%", "92%", "98%", "60%", "70%", "80%", "75%"],
        "エリア満室率": ["80%", "95%", "100%", "50%", "60%", "70%", "65%"],
        "競合最安値(平均)": [8500, 11000, 15000, 7000, 7500, 8000, 8000],
        "従来価格": [8000, 8000, 8000, 8000, 8000, 8000, 8000],
        "推奨価格案": [8400, 10500, 14000, 7500, 7500, 7800, 7800],
    }
    
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)
    
    st.write("### 価格変更の実行（ねっぱん！連動モック）")
    if st.button("推奨価格をねっぱん！に一括反映する"):
        st.success("✅ ねっぱん！への価格反映処理を開始しました（※プロトタイプのため実際には送信されません）")

if __name__ == "__main__":
    main()
