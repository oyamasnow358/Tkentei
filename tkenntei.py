import streamlit as st
import pandas as pd
import requests
import datetime

# --- 設定：GASのURLをここに貼り付け ---
GAS_URL = "https://script.google.com/macros/s/AKfycbywRXaTu5qxC873VlVAZXimbzfTInnR3r_NkMvqHNm3OMEHv_u0LycpXUOg3pzk79zKHA/exec"

# ページ設定
st.set_page_config(page_title="総合支援部 応援調整ツール", layout="wide", initial_sidebar_state="expanded")

# --- 究極のデザインCSS（省略なし） ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans JP', sans-serif; background-color: #f8fafc; }
    
    /* タイトルヘッダー */
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 2rem; border-radius: 0 0 25px 25px; color: white; text-align: center;
        margin-bottom: 2rem; box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    .main-header h1 { color: white !important; font-size: 2.2rem; border: none !important; margin: 0; }
    
    /* 統計カード */
    .stat-card {
        background: white; padding: 1.2rem; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        text-align: center; border-top: 6px solid #1e3a8a;
    }
    .stat-val { font-size: 2.2rem; font-weight: bold; color: #1e3a8a; }
    .stat-label { font-size: 1rem; color: #64748b; font-weight: bold; }

    /* 応援者表示カード（ここが重要） */
    .request-card {
        background: white; padding: 1.5rem; border-radius: 15px; margin-bottom: 1rem;
        border-left: 10px solid #1e3a8a; box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .dept-badge {
        padding: 4px 12px; border-radius: 20px; font-weight: bold; font-size: 0.8rem; color: white;
    }
    .supporter-list {
        background: #f0f9ff; padding: 10px; border-radius: 8px; margin-top: 10px; border: 1px solid #bae6fd;
    }
    .supporter-item { font-size: 1rem; color: #0369a1; font-weight: bold; margin-bottom: 4px; }
    </style>
    """, unsafe_allow_html=True)

# --- データ取得関数 ---
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
st.markdown("""<div class="main-header"><h1>🛡️ 総合支援部 応援調整ツール</h1></div>""", unsafe_allow_html=True)

# --- サイドバー構成 ---
with st.sidebar:
    st.markdown("### ⚙️ メニュー")
    app_mode = st.radio("表示画面切替", ["📊 総合支援部（表示・管理）", "➕ 各学部（応援依頼入力）"])
    st.divider()
    target_date = st.date_input("📅 表示する日付", datetime.date.today())
    date_str = target_date.strftime("%Y-%m-%d")
    st.write(f"**選択日付:** {target_date.strftime('%m/%d')}")

# --- メインコンテンツ ---

if app_mode == "📊 総合支援部（表示・管理）":
    df_raw = fetch_data()
    
    if not df_raw.empty and "日付" in df_raw.columns:
        df = df_raw[df_raw["日付"] == date_str].copy()
        
        # 1. 概況メトリクス
        sums = df.groupby("学部")["人数"].sum().reindex(["小学部", "中学部", "高等部"], fill_value=0)
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="stat-card" style="border-top-color:#10b981"><div class="stat-label">小学部</div><div class="stat-val">{sums["小学部"]}</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="stat-card" style="border-top-color:#f59e0b"><div class="stat-label">中学部</div><div class="stat-val">{sums["中学部"]}</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="stat-card" style="border-top-color:#3b82f6"><div class="stat-label">高等部</div><div class="stat-val">{sums["高等部"]}</div></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="stat-card"><div class="stat-label">合計</div><div class="stat-val">{sums.sum()}</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 2. タブ分け
        tabs = st.tabs(["🌎 全体俯瞰", "🐥 小学部", "🏃 中学部", "🎓 高等部", "✍️ 応援者を割り当てる"])

        def show_request_cards(data_df):
            if data_df.empty:
                st.info("該当する応援要請はありません。")
                return
            
            for _, row in data_df.sort_values("開始").iterrows():
                # 学部ごとの色分けバッジ
                color = "#10b981" if row['学部']=="小学部" else "#f59e0b" if row['学部']=="中学部" else "#3b82f6"
                
                # 応援者1〜4をリストアップ
                supporters = []
                for i in range(1, 5):
                    name = row.get(f'応援者{i}', '').strip()
                    time = row.get(f'時間{i}', '').strip()
                    if name: supporters.append(f"👤 {name} ({time if time else '終日'})")
                
                supporter_html = "".join([f'<div class="supporter-item">{s}</div>' for s in supporters]) if supporters else '<div style="color:#94a3b8">（未定）</div>'

                # カード型レイアウトで表示
                st.markdown(f"""
                    <div class="request-card" style="border-left-color:{color}">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span class="dept-badge" style="background:{color}">{row['学部']}</span>
                            <span style="font-weight:bold; color:#1e3a8a;">⏰ {row['開始']} 〜 {row['終了']}</span>
                        </div>
                        <h3 style="margin:10px 0; color:#1e3a8a;">{row['対象']} （必要：{row['人数']}名）</h3>
                        <p style="margin:0; color:#64748b;"><b>備考:</b> {row['備考']}</p>
                        <div class="supporter-list">
                            <div style="font-size:0.8rem; color:#64748b; margin-bottom:5px;">応援担当者：</div>
                            {supporter_html}
                        </div>
                    </div>
                """, unsafe_allow_html=True)

        with tabs[0]: # 全体
            show_request_cards(df)
        with tabs[1]: # 小
            show_request_cards(df[df["学部"]=="小学部"])
        with tabs[2]: # 中
            show_request_cards(df[df["学部"]=="中学部"])
        with tabs[3]: # 高
            show_request_cards(df[df["学部"]=="高等部"])

        with tabs[4]: # 割り当て入力
            st.subheader("応援者の詳細入力")
            if not df.empty:
                df['selector'] = df['学部'] + " | " + df['対象'] + " (" + df['開始'] + "~)"
                sel_label = st.selectbox("対象の要請を選択", df['selector'].tolist())
                r = df[df['selector'] == sel_label].iloc[0]

                with st.form("edit_form"):
                    st.info(f"編集対象：{sel_label}")
                    ca, cb = st.columns(2)
                    s1 = ca.text_input("応援者1", value=r.get('応援者1', ''))
                    t1 = cb.text_input("時間1", value=r.get('時間1', ''))
                    s2 = ca.text_input("応援者2", value=r.get('応援者2', ''))
                    t2 = cb.text_input("時間2", value=r.get('時間2', ''))
                    s3 = ca.text_input("応援者3", value=r.get('応援者3', ''))
                    t3 = cb.text_input("時間3", value=row.get('時間3', ''))
                    s4 = ca.text_input("応援者4", value=r.get('応援者4', ''))
                    t4 = cb.text_input("時間4", value=r.get('時間4', ''))
                    
                    if st.form_submit_button("応援担当情報を保存する"):
                        p = {
                            "action": "updateSupporters", "date": r['日付'], "department": r['学部'],
                            "target": r['対象'], "startTime": r['開始'],
                            "s1": s1, "t1": t1, "s2": s2, "t2": t2,
                            "s3": s3, "t3": t3, "s4": s4, "t4": t4
                        }
                        if post_to_gas(p):
                            st.success("スプレッドシートを更新しました。")
                            st.rerun()
            else: st.write("対象の要請がありません。")
    else: st.warning("データがありません。")

else:
    # 入力画面
    st.subheader(f"➕ {target_date.strftime('%m月%d日')} の新規要請")
    with st.form("req_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        d_in = col1.selectbox("依頼元の学部", ["小学部", "中学部", "高等部"])
        t_in = col2.text_input("対象（クラス・班・場所）")
        col3, col4, col5 = st.columns(3)
        s_in = col3.time_input("開始時間", datetime.time(9, 0))
        e_in = col4.time_input("終了時間", datetime.time(15, 0))
        n_in = col5.number_input("必要な人数", 1, 10, 1)
        m_in = st.text_area("詳細理由")
        
        if st.form_submit_button("📢 応援要請を送信"):
            if not t_in: st.error("対象を入力してください")
            else:
                p = {
                    "date": date_str, "department": d_in, "target": t_in,
                    "startTime": s_in.strftime("%H:%M"), "endTime": e_in.strftime("%H:%M"),
                    "count": n_in, "notes": m_in
                }
                if post_to_gas(p):
                    st.success("要請を送信しました。")
                    st.balloons()