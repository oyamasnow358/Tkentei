import streamlit as st
import pandas as pd
import requests
import datetime

# --- 設定：GASのURLをここに貼り付け ---
GAS_URL = "https://script.google.com/macros/s/AKfycbxTyVi6BW4TL-TiVx4fW6OY7JMKj_DPQJTU1iuJJUcxOpKiwYVlXa-oCWe57hYTrjsHsw/exec"

st.set_page_config(page_title="総合支援部 応援調整ツール", layout="wide", initial_sidebar_state="expanded")

# --- 究極のコンパクトデザインCSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans JP', sans-serif; background-color: #f1f5f9; }
    
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 1.5rem; border-radius: 0 0 20px 20px; color: white; text-align: center;
        margin-bottom: 1.5rem; box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .main-header h1 { color: white !important; font-size: 2rem; border: none !important; margin: 0; }
    
    .stat-card {
        background: white; padding: 1rem; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        text-align: center; border-top: 5px solid #1e3a8a;
    }
    .stat-val { font-size: 1.8rem; font-weight: bold; color: #1e3a8a; }

    /* 高密度リスト形式のデザイン */
    .compact-row {
        background: white; padding: 10px 15px; border-radius: 8px; margin-bottom: 8px;
        border-left: 6px solid #1e3a8a; display: flex; align-items: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .badge {
        padding: 2px 10px; border-radius: 4px; color: white; font-size: 0.75rem; font-weight: bold; min-width: 70px; text-align: center;
    }
    .time-info { font-weight: bold; color: #1e3a8a; min-width: 120px; font-size: 0.9rem; }
    .target-info { font-weight: bold; font-size: 1rem; min-width: 180px; }
    .supporter-area {
        flex-grow: 1; background: #f0f9ff; border-radius: 6px; padding: 5px 12px;
        font-size: 0.85rem; border: 1px solid #bae6fd; display: flex; flex-wrap: wrap; gap: 10px;
    }
    .supporter-chip { color: #0369a1; font-weight: bold; white-space: nowrap; }
    </style>
    """, unsafe_allow_html=True)

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

# --- ヘッダー ---
st.markdown("""<div class="main-header"><h1>🛡️ 総合支援部 応援調整ツール</h1></div>""", unsafe_allow_html=True)

# --- サイドバー ---
with st.sidebar:
    app_mode = st.radio("表示画面切替", ["📊 総合支援部（管理）", "➕ 応援依頼（各学部）"])
    st.divider()
    target_date = st.date_input("📅 対象日", datetime.date.today())
    date_str = target_date.strftime("%Y-%m-%d")

# --- メイン機能 ---

if app_mode == "📊 総合支援部（管理）":
    df_raw = fetch_data()
    
    if not df_raw.empty and "日付" in df_raw.columns:
        df = df_raw[df_raw["日付"] == date_str].copy()
        
        # 統計
        sums = df.groupby("学部")["人数"].sum().reindex(["小学部", "中学部", "高等部"], fill_value=0)
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="stat-card" style="border-top-color:#10b981"><small>小学部</small><div class="stat-val">{sums["小学部"]}</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="stat-card" style="border-top-color:#f59e0b"><small>中学部</small><div class="stat-val">{sums["中学部"]}</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="stat-card" style="border-top-color:#3b82f6"><small>高等部</small><div class="stat-val">{sums["高等部"]}</div></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="stat-card"><small>合計</small><div class="stat-val">{sums.sum()}</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        tabs = st.tabs(["🌎 全体俯瞰", "🐥 小学部", "🏃 中学部", "🎓 高等部", "✍️ 応援者を割り当てる"])

        def render_compact_list(data_df):
            if data_df.empty:
                st.info("応援要請はありません。")
                return
            
            for _, row in data_df.sort_values("開始").iterrows():
                color = "#10b981" if row['学部']=="小学部" else "#f59e0b" if row['学部']=="中学部" else "#3b82f6"
                
                # 応援者1〜4をチップ形式でまとめる
                chips = []
                for i in range(1, 5):
                    name = row.get(f'応援者{i}', '').strip()
                    time = row.get(f'時間{i}', '').strip()
                    if name: chips.append(f'<span class="supporter-chip">👤{name}({time})</span>')
                
                chips_html = "".join(chips) if chips else '<span style="color:#94a3b8">未定</span>'

                st.markdown(f"""
                    <div class="compact-row" style="border-left-color:{color}">
                        <div class="badge" style="background:{color}">{row['学部']}</div>
                        <div class="time-info" style="margin-left:15px;">{row['開始']}〜{row['終了']}</div>
                        <div class="target-info">{row['対象']} <small>(必要:{row['人数']})</small></div>
                        <div class="supporter-area">{chips_html}</div>
                        <div style="font-size:0.8rem; color:#64748b; margin-left:15px; max-width:200px;">{row['備考']}</div>
                    </div>
                """, unsafe_allow_html=True)

        with tabs[0]: render_compact_list(df)
        with tabs[1]: render_compact_list(df[df["学部"]=="小学部"])
        with tabs[2]: render_compact_list(df[df["学部"]=="中学部"])
        with tabs[3]: render_compact_list(df[df["学部"]=="高等部"])

        with tabs[4]:
            st.subheader("応援者の入力・編集")
            if not df.empty:
                df['selector'] = df['学部'] + " | " + df['対象'] + " (" + df['開始'] + "~)"
                sel_label = st.selectbox("対象を選択", df['selector'].tolist())
                # ここで 'row' ではなく 'target_row' を使い、NameErrorを防止
                target_row = df[df['selector'] == sel_label].iloc[0]

                with st.form("edit_form"):
                    st.info(f"編集：{sel_label}")
                    ca, cb = st.columns(2)
                    s1 = ca.text_input("応援者1", value=target_row.get('応援者1', ''))
                    t1 = cb.text_input("時間1", value=target_row.get('時間1', ''))
                    s2 = ca.text_input("応援者2", value=target_row.get('応援者2', ''))
                    t2 = cb.text_input("時間2", value=target_row.get('時間2', ''))
                    s3 = ca.text_input("応援者3", value=target_row.get('応援者3', ''))
                    t3 = cb.text_input("時間3", value=target_row.get('時間3', ''))
                    s4 = ca.text_input("応援者4", value=target_row.get('応援者4', ''))
                    t4 = cb.text_input("時間4", value=target_row.get('時間4', ''))
                    
                    if st.form_submit_button("保存する"):
                        p = {
                            "action": "updateSupporters", "date": target_row['日付'], "department": target_row['学部'],
                            "target": target_row['対象'], "startTime": target_row['開始'],
                            "s1": s1, "t1": t1, "s2": s2, "t2": t2,
                            "s3": s3, "t3": t3, "s4": s4, "t4": t4
                        }
                        if post_to_gas(p):
                            st.success("更新完了")
                            st.rerun()
            else: st.write("要請がありません。")
else:
    st.subheader(f"➕ 新規応援依頼 ({target_date.strftime('%m/%d')})")
    with st.form("req_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        d_in = col1.selectbox("学部", ["小学部", "中学部", "高等部"])
        t_in = col2.text_input("対象（場所・クラス・班）")
        col3, col4, col5 = st.columns(3)
        s_in = col3.time_input("開始", datetime.time(9, 0))
        e_in = col4.time_input("終了", datetime.time(15, 0))
        n_in = col5.number_input("人数", 1, 10, 1)
        m_in = st.text_area("詳細理由")
        if st.form_submit_button("📢 応援依頼を送信"):
            if not t_in: st.error("対象を入力してください")
            else:
                p = {"date": date_str, "department": d_in, "target": t_in, "startTime": s_in.strftime("%H:%M"), "endTime": e_in.strftime("%H:%M"), "count": n_in, "notes": m_in}
                if post_to_gas(p):
                    st.success("送信しました")
                    st.balloons()