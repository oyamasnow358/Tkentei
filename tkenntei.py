import streamlit as st
import pandas as pd
import requests
import datetime

# --- 設定：あなたのGASのURLをここに貼り付け ---
GAS_URL = "https://script.google.com/macros/s/AKfycbw8OIWeRd4mdtCArE-xtMOmFr04w6y4sNvX1F-erj2RW8GWX8bLaNDr4Xn06hlMqqfzpA/exec"

# ページ設定
st.set_page_config(page_title="総合支援部 応援調整ツール", layout="wide", initial_sidebar_state="expanded")

# --- デザインCSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans JP', sans-serif; background-color: #f0f2f5; }
    
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 1.5rem; border-radius: 0 0 20px 20px; color: white; text-align: center;
        margin-bottom: 1.5rem; box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    .main-header h1 { color: white !important; font-size: 2.2rem; border: none !important; margin: 0; }
    
    .stat-card {
        background: white; padding: 1rem; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        text-align: center; border-top: 6px solid #1e3a8a;
    }
    .stat-val { font-size: 2rem; font-weight: bold; color: #1e3a8a; }

    /* 応援要請カード */
    .req-card {
        background: white; padding: 15px; border-radius: 12px; margin-bottom: 15px;
        border-left: 10px solid #1e3a8a; box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .supporter-grid {
        display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;
        background: #f8fafc; padding: 12px; border-radius: 8px; margin-top: 10px;
        border: 1px solid #e2e8f0;
    }
    .supporter-item {
        font-size: 0.95rem; color: #1e3a8a; font-weight: bold;
        padding: 5px; border-bottom: 1px dashed #cbd5e1;
    }
    .dept-label {
        padding: 2px 10px; border-radius: 5px; color: white; font-weight: bold; font-size: 0.8rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- データ関数 ---
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
st.markdown('<div class="main-header"><h1>🛡️ 総合支援部 応援調整ツール</h1></div>', unsafe_allow_html=True)

# --- サイドバー ---
with st.sidebar:
    st.markdown("### ⚙️ 管理メニュー")
    app_mode = st.radio("画面表示", ["📊 総合支援部（管理画面）", "➕ 各学部（応援依頼入力）"])
    st.divider()
    target_date = st.date_input("📅 対象日", datetime.date.today())
    date_str = target_date.strftime("%Y-%m-%d")

# --- メインロジック ---

if app_mode == "📊 総合支援部（管理画面）":
    df_raw = fetch_data()
    
    if not df_raw.empty and "日付" in df_raw.columns:
        df = df_raw[df_raw["日付"] == date_str].copy()
        
        # 1. 統計メトリクス
        sums = df.groupby("学部")["人数"].sum().reindex(["小学部", "中学部", "高等部"], fill_value=0)
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="stat-card" style="border-top-color:#10b981"><small>小学部</small><div class="stat-val">{sums["小学部"]}</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="stat-card" style="border-top-color:#f59e0b"><small>中学部</small><div class="stat-val">{sums["中学部"]}</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="stat-card" style="border-top-color:#3b82f6"><small>高等部</small><div class="stat-val">{sums["高等部"]}</div></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="stat-card"><small>合計</small><div class="stat-val">{sums.sum()}</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 2. タブ（全体・個別・入力）
        tabs = st.tabs(["🌎 全体俯瞰", "🐥 小学部", "🏃 中学部", "🎓 高等部", "✍️ 応援者を割り当てる"])

        def render_detail_cards(data_df):
            if data_df.empty:
                st.info("該当する応援要請はありません。")
                return
            
            for _, row in data_df.sort_values("開始").iterrows():
                # 学部別カラー
                color = "#10b981" if row['学部']=="小学部" else "#f59e0b" if row['学部']=="中学部" else "#3b82f6"
                
                # 応援者1〜4の情報をリスト化
                supporter_elements = ""
                has_any = False
                for i in range(1, 5):
                    name = row.get(f'応援者{i}', '').strip()
                    time = row.get(f'時間{i}', '').strip()
                    if name:
                        has_any = True
                        supporter_elements += f'<div class="supporter-item">👤 {name} <br> <small>({time if time else "終日"})</small></div>'
                
                if not has_any:
                    supporter_elements = '<div style="color:#94a3b8">応援者はまだ割り当てられていません</div>'

                # HTMLカードの出力（インデックスなし、全員強制表示）
                st.markdown(f"""
                    <div class="req-card" style="border-left-color:{color}">
                        <div style="display:flex; justify-content:space-between;">
                            <span class="dept-label" style="background:{color}">{row['学部']}</span>
                            <span style="font-weight:bold; color:#1e3a8a;">⏰ {row['開始']} 〜 {row['終了']}</span>
                        </div>
                        <div style="margin: 10px 0;">
                            <span style="font-size:1.2rem; font-weight:bold; color:#1e3a8a;">{row['対象']}</span>
                            <span style="margin-left:15px; color:#64748b;">(必要人数: {row['人数']}名)</span>
                        </div>
                        <div style="font-size:0.9rem; color:#475569; margin-bottom:10px;"><b>備考:</b> {row['備考']}</div>
                        <div style="font-size:0.8rem; color:#64748b; font-weight:bold;">【応援担当者】</div>
                        <div class="supporter-grid">
                            {supporter_elements}
                        </div>
                    </div>
                """, unsafe_allow_html=True)

        with tabs[0]: render_detail_cards(df)
        with tabs[1]: render_detail_cards(df[df["学部"]=="小学部"])
        with tabs[2]: render_detail_cards(df[df["学部"]=="中学部"])
        with tabs[3]: render_detail_cards(df[df["学部"]=="高等部"])

        with tabs[4]:
            st.subheader("応援者の割り当て入力")
            if not df.empty:
                df['selector'] = df['学部'] + " | " + df['対象'] + " (" + df['開始'] + "~)"
                selected_label = st.selectbox("要請を選択", df['selector'].tolist())
                target_row = df[df['selector'] == selected_label].iloc[0]

                with st.form("assignment_form"):
                    st.write(f"📝 **編集対象:** {selected_label}")
                    c_a, c_b = st.columns(2)
                    s1 = c_a.text_input("応援者1 氏名", value=target_row.get('応援者1', ''))
                    t1 = c_b.text_input("応援時間1", value=target_row.get('時間1', ''))
                    s2 = c_a.text_input("応援者2 氏名", value=target_row.get('応援者2', ''))
                    t2 = c_b.text_input("応援時間2", value=target_row.get('時間2', ''))
                    s3 = c_a.text_input("応援者3 氏名", value=target_row.get('応援者3', ''))
                    t3 = c_b.text_input("応援時間3", value=target_row.get('時間3', ''))
                    s4 = c_a.text_input("応援者4 氏名", value=target_row.get('応援者4', ''))
                    t4 = c_b.text_input("応援時間4", value=target_row.get('時間4', ''))
                    
                    if st.form_submit_button("この内容で保存する"):
                        p = {
                            "action": "updateSupporters", "date": target_row['日付'], "department": target_row['学部'],
                            "target": target_row['対象'], "startTime": target_row['開始'],
                            "s1": s1, "t1": t1, "s2": s2, "t2": t2,
                            "s3": s3, "t3": t3, "s4": s4, "t4": t4
                        }
                        if post_to_gas(p):
                            st.success("更新に成功しました！")
                            st.rerun()
            else: st.info("要請がありません。")

else:
    # 入力画面
    st.subheader(f"➕ 応援の新規依頼 ({target_date.strftime('%m/%d')})")
    with st.form("req_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        d_in = col1.selectbox("依頼元の学部", ["小学部", "中学部", "高等部"])
        t_in = col2.text_input("対象（クラス名・場所など）")
        col3, col4, col5 = st.columns(3)
        s_in = col3.time_input("開始", datetime.time(9, 0))
        e_in = col4.time_input("終了", datetime.time(15, 0))
        n_in = col5.number_input("必要人数", 1, 10, 1)
        m_in = st.text_area("詳細・理由")
        
        if st.form_submit_button("📢 応援要請を送信"):
            if not t_in: st.error("対象を入力してください。")
            else:
                p = {"date": date_str, "department": d_in, "target": t_in, "startTime": s_in.strftime("%H:%M"), "endTime": e_in.strftime("%H:%M"), "count": n_in, "notes": m_in}
                if post_to_gas(p):
                    st.success("送信完了しました。")
                    st.balloons()