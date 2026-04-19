import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def main():
    st.set_page_config(page_title="ダイナミックプライシング プロトタイプ", layout="wide")
    st.title("ホテル ダイナミックプライシング検証画面 (プロトタイプ)")
    
    st.sidebar.header("設定項目")
    target_area = st.sidebar.text_input("競合分析エリア", "山梨県 山中湖村")
    
    st.write(f"### 現在の分析対象エリア: {target_area}")
    
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
        
    st.markdown("""
    ---
    **ロジックのポイント**:
    - **エリア満室率が100%に近い日**（例: 3日目）は、強気に価格を上げています。
    - **自社稼働率が高い日**も同様に値上げ傾向としています。
    """)

if __name__ == "__main__":
    main()
