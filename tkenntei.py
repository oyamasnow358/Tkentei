import streamlit as st
import pandas as pd
import requests
import datetime

# --- 設定 ---
GAS_URL = "https://script.google.com/macros/s/AKfycbwi19Nv6Pn43CdN18ejxHuq4ekUduQfNxLAGUAp2ZepF5NBvpu9wIII3uz4JyzttVPZ5Q/exec"

st.set_page_config(page_title="総合支援部 応援調整ツール", layout="wide", initial_sidebar_state="expanded")

# --- 究極のカスタムデザインCSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans JP', sans-serif; background-color: #f8fafc; }
    
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 2rem; border-radius: 0 0 25px 25px; color: white; text-align: center;
        margin-bottom: 2rem; box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    .main-header h1 { color: white !important; font-size: 2.2rem; margin-bottom: 0.5rem; border: none; }
    
    .stat-card {
        background: white; padding: 1.2rem; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        text-align: center; border-top: 6px solid #1e3a8a;
    }
    .stat-val { font-size: 2.2rem; font-weight: bold; color: #1e3a8a; }
    .stat-label { font-size: 1rem; color: #64748b; font-weight: bold; }
    
    /* 学部別のアクセントカラー */
    .elem-card { border-top-color: #10b981 !important; }
    .mid-card { border-top-color: #f59e0b !important; }
    .high-card { border-top-color: #3b82f6 !important; }

    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: white; border-radius: 8px 8px 0 0; padding: 10px 20px; font-weight: bold;
    }
    .stTabs [aria-selected="true"] { background-color: #1e3a8a !important; color: white !important; }

    /* テーブル内の改行を有効にする */
    .supporter-cell { white-space: pre-wrap; line-height: 1.4; }
    </style>
    """, unsafe_allow_html=True)

# --- データ取得ロジック ---
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
    except:
        return pd.DataFrame()

def post_to_gas(payload):
    try:
        res = requests.post(GAS_URL, json=payload)
        return res.status_code == 200
    except:
        return False

# --- ヘッダー ---
st.markdown("""
    <div class="main-header">
        <h1>🛡️ 総合支援部 応援調整ツール</h1>
        <p>学校全体を俯瞰し、迅速に応援を差配する</p>
    </div>
    """, unsafe_allow_html=True)

# --- サイドバー ---
with st.sidebar:
    st.markdown("### ⚙️ メニュー")
    app_mode = st.radio("画面表示の切替", ["📊 総合支援部（管理画面）", "➕ 各学部（応援依頼入力）"])
    st.divider()
    target_date = st.date_input("📅 対象日付を選択", datetime.date.today())
    date_str = target_date.strftime("%Y-%m-%d")
    st.write(f"**選択中:** {target_date.strftime('%Y/%m/%d')}")

# --- メイン機能 ---

if app_mode == "📊 総合支援部（管理画面）":
    df_raw = fetch_data()
    
    if not df_raw.empty and "日付" in df_raw.columns:
        df = df_raw[df_raw["日付"] == date_str].copy()
        
        # 1. 概況サマリー（メトリクス）
        sum_e = int(df[df["学部"]=="小学部"]["人数"].sum())
        sum_m = int(df[df["学部"]=="中学部"]["人数"].sum())
        sum_h = int(df[df["学部"]=="高等部"]["人数"].sum())
        
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f'<div class="stat-card elem-card"><div class="stat-label">小学部</div><div class="stat-val">{sum_e}</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="stat-card mid-card"><div class="stat-label">中学部</div><div class="stat-val">{sum_m}</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="stat-card high-card"><div class="stat-label">高等部</div><div class="stat-val">{sum_h}</div></div>', unsafe_allow_html=True)
        with c4: st.markdown(f'<div class="stat-card"><div class="stat-label">全体必要数</div><div class="stat-val">{sum_e+sum_m+sum_h}</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 2. タブ分け表示（全体・小・中・高・割り当て）
        t_all, t_e, t_m, t_h, t_assign = st.tabs(["🌎 全体俯瞰", "🐥 小学部", "🏃 中学部", "🎓 高等部", "✍️ 応援者を割り当てる"])

        # 応援者1〜4をすべて表示するための共通整形関数
        def get_full_supporters(row):
            lines = []
            for i in range(1, 5):
                name = row.get(f'応援者{i}', '').strip()
                time = row.get(f'時間{i}', '').strip()
                if name:
                    lines.append(f"・{name} ({time if time else '終日'})")
            return "\n".join(lines) if lines else "（未定）"

        # 共通の表示用データ作成
        df_display = df.copy()
        if not df_display.empty:
            df_display["応援担当（時間）"] = df_display.apply(get_full_supporters, axis=1)
            display_cols = ["学部", "対象", "開始", "終了", "人数", "応援担当（時間）", "備考"]

            with t_all:
                st.subheader("学校全体 応援タイムライン")
                st.table(df_display.sort_values(["開始", "学部"])[display_cols])
            
            with t_e:
                st.subheader("小学部 詳細")
                st.table(df_display[df_display["学部"]=="小学部"][display_cols[1:]])
            
            with t_m:
                st.subheader("中学部 詳細")
                st.table(df_display[df_display["学部"]=="中学部"][display_cols[1:]])
                
            with t_h:
                st.subheader("高等部 詳細")
                st.table(df_display[df_display["学部"]=="高等部"][display_cols[1:]])

            with t_assign:
                st.subheader("応援者の割り当て入力")
                df['selector'] = df['学部'] + " | " + df['対象'] + " (" + df['開始'] + "~)"
                sel_label = st.selectbox("対象の要請を選択してください", df['selector'].tolist())
                row = df[df['selector'] == sel_label].iloc[0]

                with st.form("assignment_form"):
                    st.info(f"対象：{sel_label}")
                    c_a, c_b = st.columns(2)
                    s1 = c_a.text_input("応援者1", value=row.get('応援者1', ''))
                    t1 = c_b.text_input("時間1", value=row.get('時間1', ''), placeholder="例: 9:00-10:00")
                    s2 = c_a.text_input("応援者2", value=row.get('応援者2', ''))
                    t2 = c_b.text_input("時間2", value=row.get('時間2', ''))
                    s3 = c_a.text_input("応援者3", value=row.get('応援者3', ''))
                    t3 = c_b.text_input("時間3", value=row.get('時間3', ''))
                    s4 = c_a.text_input("応援者4", value=row.get('応援者4', ''))
                    t4 = c_b.text_input("時間4", value=row.get('時間4', ''))
                    
                    if st.form_submit_button("この内容で応援者を確定する"):
                        payload = {
                            "action": "updateSupporters", "date": row['日付'], "department": row['学部'],
                            "target": row['対象'], "startTime": row['開始'],
                            "s1": s1, "t1": t1, "s2": s2, "t2": t2,
                            "s3": s3, "t3": t3, "s4": s4, "t4": t4
                        }
                        if post_to_gas(payload):
                            st.success("スプレッドシートを更新しました。")
                            st.rerun()
        else:
            st.info(f"{date_str} の応援要請はありません。")

else:
    # 各学部の入力画面
    st.subheader(f"➕ {target_date.strftime('%m月%d日')} の応援要請")
    with st.container():
        with st.form("request_form", clear_on_submit=True):
            f_col1, f_col2 = st.columns(2)
            d_input = f_col1.selectbox("依頼元の学部", ["小学部", "中学部", "高等部"])
            t_input = f_col2.text_input("対象（クラス・班・場所）", placeholder="例：1年1組 / 木工班")
            
            f_col3, f_col4, f_col5 = st.columns(3)
            s_input = f_col3.time_input("開始", datetime.time(9, 0))
            e_input = f_col4.time_input("終了", datetime.time(15, 0))
            n_input = f_col5.number_input("必要人数", 1, 10, 1)
            
            m_input = st.text_area("詳細・備考（理由など）", placeholder="担任不在のため補助希望、等")
            
            if st.form_submit_button("📢 応援要請を送信"):
                if not t_input:
                    st.error("「対象」を記入してください。")
                else:
                    payload = {
                        "date": date_str, "department": d_input, "target": t_input,
                        "startTime": s_input.strftime("%H:%M"), "endTime": e_input.strftime("%H:%M"),
                        "count": n_input, "notes": m_input
                    }
                    if post_to_gas(payload):
                        st.success("送信完了しました！")
                        st.balloons()