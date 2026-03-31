import streamlit as st
import pandas as pd
import requests
import datetime

# --- 設定 ---
GAS_URL = "https://script.google.com/macros/s/AKfycbx8zdcF31wtnoD6sS7QcDHSvWh9NMV5zvR-3W1mUsOErcAU8b4Xgz_2M2iyFM3xfjdbmw/exec"

st.set_page_config(page_title="総合支援部 応援マネジメントシステム", layout="wide", initial_sidebar_state="expanded")

# --- 究極の視認性を追求したCSS ---
st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-top: 6px solid #1e3a8a; }
    div[data-testid="stExpander"] { background-color: #ffffff; border-radius: 10px; border: 1px solid #ddd; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px; background-color: #e2e8f0; border-radius: 10px 10px 0 0; font-weight: bold; padding: 0 25px;
    }
    .stTabs [aria-selected="true"] { background-color: #1e3a8a !important; color: white !important; }
    .section-title { font-size: 1.5rem; font-weight: bold; color: #1e3a8a; margin: 20px 0 10px 0; border-left: 10px solid #1e3a8a; padding-left: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- データ連携 ---
def fetch_data():
    try:
        # キャッシュ無効化のためのクエリパラメータ
        response = requests.get(f"{GAS_URL}?t={datetime.datetime.now().timestamp()}")
        if response.status_code == 200:
            df = pd.DataFrame(response.json())
            if not df.empty:
                df.columns = [c.strip() for c in df.columns]
                # 人数列を数値に変換（集計用）
                df["人数"] = pd.to_numeric(df["人数"], errors='coerce').fillna(0).astype(int)
                return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# --- サイドバー構成 ---
st.sidebar.title("🏨 システムメニュー")
app_mode = st.sidebar.selectbox("表示モード切替", ["📊 総合支援部（管理・俯瞰）", "➕ 応援依頼を入力（各学部用）"])

st.sidebar.divider()
st.sidebar.subheader("📅 日付選択")
# デフォルトで今日を選択。変更すれば全データから該当日のものを抽出
target_date = st.sidebar.date_input("表示する日付を選択", datetime.date.today())
date_str = target_date.strftime("%Y-%m-%d")

# --- メインコンテンツ ---

# 1. 総合支援部 モード
if app_mode == "📊 総合支援部（管理・俯瞰）":
    st.markdown(f"<div class='section-title'>{target_date.strftime('%m月%d日')} 応援状況概況</div>", unsafe_allow_html=True)
    
    raw_df = fetch_data()
    
    if not raw_df.empty and "日付" in raw_df.columns:
        # 選択された日付でフィルタリング
        df = raw_df[raw_df["日付"] == date_str].copy()
        
        if not df.empty:
            # 学部別集計カード
            summary = df.groupby("学部")["人数"].sum().reindex(["小学部", "中学部", "高等部"], fill_value=0)
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("小学部 必要数", f"{summary['小学部']}名")
            m2.metric("中学部 必要数", f"{summary['中学部']}名")
            m3.metric("高等部 必要数", f"{summary['高等部']}名")
            m4.metric("全学部 合計", f"{summary.sum()}名", delta_color="inverse")

            st.write("---")
            
            # 詳細表示（全体・個別の切り替え）
            tab_all, tab_elem, tab_mid, tab_high = st.tabs(["🌎 全学部一括表示", "🐥 小学部", "🏃 中学部", "🎓 高等部"])
            
            with tab_all:
                st.subheader("全学部の応援要請（時系列順）")
                # 時間でソートして全体を見やすく
                all_display = df.sort_values(["開始", "学部"])[["学部", "対象", "開始", "終了", "人数", "備考"]]
                st.dataframe(all_display, use_container_width=True, hide_index=True)
                
            with tab_elem:
                st.dataframe(df[df["学部"] == "小学部"][["対象", "開始", "終了", "人数", "備考"]], use_container_width=True, hide_index=True)
            with tab_mid:
                st.dataframe(df[df["学部"] == "中学部"][["対象", "開始", "終了", "人数", "備考"]], use_container_width=True, hide_index=True)
            with tab_high:
                st.dataframe(df[df["学部"] == "高等部"][["対象", "開始", "終了", "人数", "備考"]], use_container_width=True, hide_index=True)
        else:
            st.info(f"{date_str} の応援要請は登録されていません。")
    else:
        st.warning("データがありません。スプレッドシートを確認してください。")

    if st.button("🔄 情報を最新に更新"):
        st.rerun()

# 2. 入力 モード
else:
    st.markdown(f"<div class='section-title'>{target_date.strftime('%m月%d日')} の応援を依頼</div>", unsafe_allow_html=True)
    
    with st.container():
        st.write("応援が必要な時間と場所を入力してください。")
        with st.form("input_form", clear_on_submit=True):
            dept = st.selectbox("学部", ["小学部", "中学部", "高等部"])
            target = st.text_input("対象（クラス名・作業班名など）", placeholder="例: 1年1組、農耕班")
            
            c1, c2 = st.columns(2)
            s_time = c1.time_input("開始時間", datetime.time(9, 0))
            e_time = c2.time_input("終了時間", datetime.time(15, 0))
            
            count = st.number_input("必要な人数", 1, 10, 1)
            notes = st.text_area("詳細・理由", placeholder="例: 担任不在のため、授業補助をお願いします。")
            
            if st.form_submit_button("📢 応援依頼を送信"):
                if not target:
                    st.error("「対象」を入力してください。")
                else:
                    payload = {
                        "date": date_str,
                        "department": dept,
                        "target": target,
                        "startTime": s_time.strftime("%H:%M"),
                        "endTime": e_time.strftime("%H:%M"),
                        "count": count,
                        "notes": notes
                    }
                    res = requests.post(GAS_URL, json=payload)
                    if res.status_code == 200:
                        st.success(f"送信完了！ {date_str} の {dept} 応援として記録されました。")
                        st.balloons()
                    else:
                        st.error("送信に失敗しました。")