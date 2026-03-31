import streamlit as st
import pandas as pd
import requests
import datetime

# --- 設定 ---
GAS_URL = "https://script.google.com/macros/s/AKfycbyRVRdwV9EIQIH_Tqz_mHdOVgQ_yhMLsD1pZRGUG8nronUta-GWkJxYYa0n4vB-dvHeMw/exec"

st.set_page_config(page_title="総合支援部 応援調整ツール", layout="wide", initial_sidebar_state="expanded")

# --- 究極のカスタムCSS（インデックス消去と表のデザイン） ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans JP', sans-serif; background-color: #f8fafc; }
    
    /* ヘッダー */
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 2rem; border-radius: 0 0 25px 25px; color: white; text-align: center;
        margin-bottom: 2rem; box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    .main-header h1 { color: white !important; font-size: 2.2rem; margin-bottom: 0.5rem; border: none !important; }
    
    /* 統計カード */
    .stat-card {
        background: white; padding: 1.2rem; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        text-align: center; border-top: 6px solid #1e3a8a;
    }
    .stat-val { font-size: 2.2rem; font-weight: bold; color: #1e3a8a; }
    .stat-label { font-size: 1rem; color: #64748b; font-weight: bold; }

    /* 学部別タブ */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: white; border-radius: 8px 8px 0 0; padding: 10px 20px; font-weight: bold;
    }
    .stTabs [aria-selected="true"] { background-color: #1e3a8a !important; color: white !important; }

    /* テーブルのインデックスを非表示にするための設定 */
    [data-testid="stTable"] { width: 100%; border-collapse: collapse; border-radius: 10px; overflow: hidden; }
    [data-testid="stTable"] thead tr th { background-color: #f1f5f9 !important; color: #1e3a8a !important; }
    
    /* 応援担当欄の改行を有効にするCSS（超重要） */
    .supporter-text { white-space: pre-line; line-height: 1.5; font-size: 0.9rem; }
    </style>
    """, unsafe_allow_html=True)

# --- データ取得 ---
def fetch_data():
    try:
        res = requests.get(f"{GAS_URL}?t={datetime.datetime.now().timestamp()}")
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            if not df.empty:
                df.columns = [c.strip() for c in df.columns]
                df["人数"] = pd.to_numeric(df["人数"], errors='coerce').fillna(0).astype(int)
                return df
        return pd.DataFrame()
    except: return pd.DataFrame()

def post_to_gas(payload):
    try:
        res = requests.post(GAS_URL, json=payload)
        return res.status_code == 200
    except: return False

# --- ヘッダー表示 ---
st.markdown("""<div class="main-header"><h1>🛡️ 総合支援部 応援調整ツール</h1><p>全学部の状況を把握し、最適な人員配置を支援する</p></div>""", unsafe_allow_html=True)

# --- サイドバー ---
with st.sidebar:
    st.markdown("### ⚙️ メニュー")
    app_mode = st.radio("画面表示", ["📊 総合支援部（管理）", "➕ 応援依頼入力（各学部）"])
    st.divider()
    target_date = st.date_input("📅 対象日付", datetime.date.today())
    date_str = target_date.strftime("%Y-%m-%d")

# --- メイン機能 ---

if app_mode == "📊 総合支援部（管理）":
    df_raw = fetch_data()
    
    if not df_raw.empty and "日付" in df_raw.columns:
        df = df_raw[df_raw["日付"] == date_str].copy()
        
        # 1. 概況メトリクス
        sums = df.groupby("学部")["人数"].sum().reindex(["小学部", "中学部", "高等部"], fill_value=0)
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="stat-card" style="border-top-color:#10b981"><div class="stat-label">小学部</div><div class="stat-val">{sums["小学部"]}</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="stat-card" style="border-top-color:#f59e0b"><div class="stat-label">中学部</div><div class="stat-val">{sums["中学部"]}</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="stat-card" style="border-top-color:#3b82f6"><div class="stat-label">高等部</div><div class="stat-val">{sums["高等部"]}</div></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="stat-card"><div class="stat-label">全体合計</div><div class="stat-val">{sums.sum()}</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 2. タブ構成（全体・各学部・入力）
        t_all, t_e, t_m, t_h, t_assign = st.tabs(["🌎 全体俯瞰", "🐥 小学部", "🏃 中学部", "🎓 高等部", "✍️ 応援者を割り当てる"])

        # 応援者1〜4を改行して結合する関数
        def get_supporter_html(row):
            lines = []
            for i in range(1, 5):
                name = row.get(f'応援者{i}', '').strip()
                time = row.get(f'時間{i}', '').strip()
                if name: lines.append(f"・{name} ({time if time else '終日'})")
            return "\n".join(lines) if lines else "（未定）"

        if not df.empty:
            df["応援担当（時間）"] = df.apply(get_supporter_html, axis=1)
            display_cols = ["学部", "対象", "開始", "終了", "人数", "応援担当（時間）", "備考"]

            # 各タブの表示（すべて index=False に修正）
            with t_all:
                st.subheader("学校全体 応援タイムライン")
                st.dataframe(df.sort_values(["開始", "学部"])[display_cols], use_container_width=True, hide_index=True)
            
            with t_e:
                st.subheader("小学部 応援詳細")
                st.dataframe(df[df["学部"]=="小学部"][display_cols[1:]], use_container_width=True, hide_index=True)
            
            with t_m:
                st.subheader("中学部 応援詳細")
                st.dataframe(df[df["学部"]=="中学部"][display_cols[1:]], use_container_width=True, hide_index=True)
                
            with t_h:
                st.subheader("高等部 応援詳細")
                st.dataframe(df[df["学部"]=="高等部"][display_cols[1:]], use_container_width=True, hide_index=True)

            with t_assign:
                st.subheader("応援者の詳細入力")
                df['selector'] = df['学部'] + " | " + df['対象'] + " (" + df['開始'] + "~)"
                sel_label = st.selectbox("対象の要請を選択", df['selector'].tolist())
                row = df[df['selector'] == sel_label].iloc[0]

                with st.form("edit_form"):
                    st.info(f"【編集対象】 {sel_label}")
                    ca, cb = st.columns(2)
                    s1 = ca.text_input("応援者1", value=row.get('応援者1', ''))
                    t1 = cb.text_input("時間1", value=row.get('時間1', ''))
                    s2 = ca.text_input("応援者2", value=row.get('応援者2', ''))
                    t2 = cb.text_input("時間2", value=row.get('時間2', ''))
                    s3 = ca.text_input("応援者3", value=row.get('応援者3', ''))
                    t3 = cb.text_input("時間3", value=row.get('時間3', ''))
                    s4 = ca.text_input("応援者4", value=row.get('応援者4', ''))
                    t4 = cb.text_input("時間4", value=row.get('時間4', ''))
                    
                    if st.form_submit_button("応援者情報を保存"):
                        p = {
                            "action": "updateSupporters", "date": row['日付'], "department": row['学部'],
                            "target": row['対象'], "startTime": row['開始'],
                            "s1": s1, "t1": t1, "s2": s2, "t2": t2,
                            "s3": s3, "t3": t3, "s4": s4, "t4": t4
                        }
                        if post_to_gas(p):
                            st.success("更新しました。")
                            st.rerun()
        else:
            st.info(f"{date_str} の要請はありません。")
else:
    # 各学部の入力画面
    st.subheader(f"➕ {target_date.strftime('%m月%d日')} の要請入力")
    with st.form("req_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        d_in = col1.selectbox("学部", ["小学部", "中学部", "高等部"])
        t_in = col2.text_input("対象（クラス・班）")
        col3, col4, col5 = st.columns(3)
        s_in = col3.time_input("開始", datetime.time(9, 0))
        e_in = col4.time_input("終了", datetime.time(15, 0))
        n_in = col5.number_input("人数", 1, 10, 1)
        m_in = st.text_area("詳細・備考")
        if st.form_submit_button("応援要請を送信"):
            if not t_in: st.error("対象を入力してください")
            else:
                payload = {
                    "date": date_str, "department": d_in, "target": t_in,
                    "startTime": s_in.strftime("%H:%M"), "endTime": e_in.strftime("%H:%M"),
                    "count": n_in, "notes": m_in
                }
                if post_to_gas(payload):
                    st.success("送信完了")
                    st.balloons()