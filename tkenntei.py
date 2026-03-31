import streamlit as st
import pandas as pd
import requests
import datetime

# --- 基本設定 ---
GAS_URL = "https://script.google.com/macros/s/AKfycbxifAM_LLMyT4EY8z7iiLMfiECexi2uLwLmTty0XBiwjlWLxD0rPClTppn-t8GiZgNjog/exec"
st.set_page_config(page_title="総合支援部 応援調整ツール", layout="wide")

# --- CSS (前回よりさらに洗練) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans JP', sans-serif; background-color: #f8fafc; }
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 1.5rem; border-radius: 0 0 20px 20px; color: white; text-align: center;
        margin-bottom: 2rem; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .stat-card {
        background: white; padding: 1.2rem; border-radius: 15px; text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-top: 6px solid #1e3a8a;
    }
    .supporter-tag {
        background: #e0f2fe; color: #0369a1; padding: 2px 8px; border-radius: 5px;
        font-size: 0.85rem; font-weight: bold; margin-right: 5px; border: 1px solid #bae6fd;
    }
    .stTabs [aria-selected="true"] { background-color: #1e3a8a !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

def fetch_data():
    try:
        res = requests.get(f"{GAS_URL}?t={datetime.datetime.now().timestamp()}")
        df = pd.DataFrame(res.json())
        if not df.empty:
            df.columns = [c.strip() for c in df.columns]
            df["人数"] = pd.to_numeric(df["人数"], errors='coerce').fillna(0).astype(int)
        return df
    except: return pd.DataFrame()

# --- タイトル ---
st.markdown('<div class="main-header"><h1>🛡️ 総合支援部 応援調整ツール</h1></div>', unsafe_allow_html=True)

# --- サイドバー ---
with st.sidebar:
    app_mode = st.radio("表示モード", ["📊 総合支援部（管理）", "➕ 応援依頼（各学部）"])
    target_date = st.date_input("📅 対象日", datetime.date.today())
    date_str = target_date.strftime("%Y-%m-%d")

# --- 1. 総合支援部（管理画面） ---
if app_mode == "📊 総合支援部（管理）":
    df_raw = fetch_data()
    if not df_raw.empty:
        df = df_raw[df_raw["日付"] == date_str].copy()
        
        # 集計
        sums = df.groupby("学部")["人数"].sum().reindex(["小学部", "中学部", "高等部"], fill_value=0)
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="stat-card" style="border-color:#10b981"><small>小学部</small><br><b style="font-size:2rem">{sums["小学部"]}</b></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="stat-card" style="border-color:#f59e0b"><small>中学部</small><br><b style="font-size:2rem">{sums["中学部"]}</b></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="stat-card" style="border-color:#3b82f6"><small>高等部</small><br><b style="font-size:2rem">{sums["高等部"]}</b></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="stat-card" style="border-color:#6366f1"><small>合計</small><br><b style="font-size:2rem">{sums.sum()}</b></div>', unsafe_allow_html=True)

        st.write("---")
        
        tab_all, tab_assign = st.tabs(["🌎 全体表示", "✍️ 応援者を割り当てる"])

        with tab_all:
            # 応援者の情報を分かりやすくまとめる
            def format_supporters(row):
                items = []
                for i in range(1, 5):
                    s = row.get(f'応援者{i}', '')
                    t = row.get(f'時間{i}', '')
                    if s: items.append(f"👤{s}({t})")
                return "  ".join(items) if items else "（未定）"

            if not df.empty:
                display_df = df.copy()
                display_df["応援者割り当て状況"] = display_df.apply(format_supporters, axis=1)
                st.table(display_df[["学部", "対象", "開始", "終了", "人数", "応援者割り当て状況", "備考"]])
            else:
                st.info("要請はありません。")

        with tab_assign:
            st.subheader("応援者の入力・編集")
            if not df.empty:
                # 編集対象を選択
                df['selector'] = df['学部'] + " | " + df['対象'] + " (" + df['開始'] + "~)"
                selected_req = st.selectbox("編集する要請を選択", df['selector'].tolist())
                row = df[df['selector'] == selected_req].iloc[0]

                with st.form("assign_form"):
                    st.write(f"📍 {selected_req}")
                    cols = st.columns(4)
                    s1 = cols[0].text_input("応援者1", value=row.get('応援者1', ''))
                    t1 = cols[0].text_input("時間1", value=row.get('時間1', ''), placeholder="9:00〜10:00")
                    s2 = cols[1].text_input("応援者2", value=row.get('応援者2', ''))
                    t2 = cols[1].text_input("時間2", value=row.get('時間2', ''))
                    s3 = cols[2].text_input("応援者3", value=row.get('応援者3', ''))
                    t3 = cols[2].text_input("時間3", value=row.get('時間3', ''))
                    s4 = cols[3].text_input("応援者4", value=row.get('応援者4', ''))
                    t4 = cols[3].text_input("時間4", value=row.get('時間4', ''))
                    
                    if st.form_submit_button("この内容でスプレッドシートを更新"):
                        payload = {
                            "action": "updateSupporters",
                            "date": row['日付'], "department": row['学部'], "target": row['対象'], "startTime": row['開始'],
                            "s1": s1, "t1": t1, "s2": s2, "t2": t2, "s3": s3, "t3": t3, "s4": s4, "t4": t4
                        }
                        if requests.post(GAS_URL, json=payload).status_code == 200:
                            st.success("応援者を更新しました！")
                            st.rerun()
            else:
                st.write("対象となる要請がありません。")

# --- 2. 各学部（入力画面） ---
else:
    st.subheader(f"➕ {target_date.strftime('%m月%d日')} の要請入力")
    with st.form("input_form", clear_on_submit=True):
        dept = st.selectbox("学部", ["小学部", "中学部", "高等部"])
        target = st.text_input("対象（クラス・作業班）")
        c1, c2, c3 = st.columns(3)
        s_t = c1.time_input("開始", datetime.time(9, 0))
        e_t = c2.time_input("終了", datetime.time(15, 0))
        num = c3.number_input("人数", 1, 10, 1)
        notes = st.text_area("備考")
        
        if st.form_submit_button("送信"):
            payload = {
                "date": date_str, "department": dept, "target": target,
                "startTime": s_t.strftime("%H:%M"), "endTime": e_t.strftime("%H:%M"),
                "count": num, "notes": notes
            }
            requests.post(GAS_URL, json=payload)
            st.success("要請を送信しました。")
            st.balloons()