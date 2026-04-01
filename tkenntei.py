import streamlit as st
import pandas as pd
import requests
import datetime
import io

# --- 設定 ---
GAS_URL = "https://script.google.com/macros/s/AKfycbw_QH8gdGWjJzhUK9SX-UaH5JU9Elf2hMIN-mO89C58ZT1es46n-iBDh7WoZMun-mRkBQ/exec"

st.set_page_config(page_title="総合支援部 応援調整ツール", layout="wide", initial_sidebar_state="expanded")

# --- 究極のデザインCSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans JP', sans-serif; background-color: #f4f7f9; }
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 1.5rem; border-radius: 0 0 20px 20px; color: white; text-align: center;
        margin-bottom: 1.5rem; box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .main-header h1 { color: white !important; font-size: 2.2rem; margin: 0; border: none !important; }
    .stat-card {
        background: white; padding: 1rem; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        text-align: center; border-top: 6px solid #1e3a8a;
    }
    .stat-val { font-size: 2rem; font-weight: bold; color: #1e3a8a; }
    .req-card {
        background: white; padding: 12px; border-radius: 10px; margin-bottom: 8px;
        border-left: 8px solid #1e3a8a; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .preview-box {
        background: #fff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 10px; margin-bottom: 15px;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background: white; border-radius: 8px 8px 0 0; padding: 10px 20px; font-weight: bold; }
    .stTabs [aria-selected="true"] { background-color: #1e3a8a !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

# --- データ操作関数 ---
def fetch_data():
    try:
        res = requests.get(f"{GAS_URL}?t={datetime.datetime.now().timestamp()}")
        df = pd.DataFrame(res.json())
        if not df.empty:
            df.columns = [c.strip() for c in df.columns]
            df["人数"] = pd.to_numeric(df["人数"], errors='coerce').fillna(0).astype(int)
        return df
    except: return pd.DataFrame()

def post_to_gas(payload):
    try:
        res = requests.post(GAS_URL, json=payload)
        return res.status_code == 200
    except: return False

# --- メインUI ---
st.markdown('<div class="main-header"><h1>🛡️ 総合支援部 応援調整ツール</h1></div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### ⚙️ メニュー")
    app_mode = st.radio("画面切替", ["📊 総合支援部（管理・集計）", "➕ 応援依頼（各学部用）"])
    st.divider()
    target_date = st.date_input("📅 対象日選択", datetime.date.today())
    date_str = target_date.strftime("%Y-%m-%d")

# --- 1. 総合支援部 モード ---
if app_mode == "📊 総合支援部（管理・集計）":
    df_raw = fetch_data()
    if not df_raw.empty:
        df_today = df_raw[df_raw["日付"] == date_str].copy()
        
        # 統計表示
        sums = df_today.groupby("学部")["人数"].sum().reindex(["小学部", "中学部", "高等部"], fill_value=0)
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="stat-card" style="border-top-color:#10b981"><small>小学部</small><div class="stat-val">{sums["小学部"]}</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="stat-card" style="border-top-color:#f59e0b"><small>中学部</small><div class="stat-val">{sums["中学部"]}</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="stat-card" style="border-top-color:#3b82f6"><small>高等部</small><div class="stat-val">{sums["高等部"]}</div></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="stat-card"><small>合計</small><div class="stat-val">{sums.sum()}</div></div>', unsafe_allow_html=True)

        st.write("---")
        t_daily, t_assign, t_monthly = st.tabs(["🌎 本日の応援詳細", "✍️ 応援者の割り当て", "📈 月次集計・Excel出力"])

        with t_daily:
            if not df_today.empty:
                for _, row in df_today.sort_values("開始").iterrows():
                    color = "#10b981" if row['学部']=="小学部" else "#f59e0b" if row['学部']=="中学部" else "#3b82f6"
                    supporters = [f"{row[f'応援者{i}']} ({row[f'時間{i}']})" for i in range(1,5) if row[f'応援者{i}']]
                    supporter_txt = " / ".join(supporters) if supporters else "未定"
                    st.markdown(f"""
                        <div class="req-card" style="border-left-color:{color}">
                            <div style="display:flex; justify-content:space-between; font-weight:bold;">
                                <span>{row['学部']} | {row['対象']}</span>
                                <span>⏰ {row['開始']} 〜 {row['終了']} (必要:{row['人数']}名)</span>
                            </div>
                            <div style="font-size:0.9rem; color:#1e3a8a; margin-top:5px;">👤 担当: {supporter_txt}</div>
                            <div style="font-size:0.8rem; color:#64748b;">📝 {row['備考']}</div>
                        </div>
                    """, unsafe_allow_html=True)
            else: st.info("本日の要請はありません。")

        with t_assign:
            if not df_today.empty:
                df_today['selector'] = df_today['学部'] + " | " + df_today['対象'] + " (" + df_today['開始'] + "~)"
                sel = st.selectbox("要請を選択", df_today['selector'].tolist())
                r = df_today[df_today['selector'] == sel].iloc[0]
                with st.form("assign_form"):
                    ca, cb = st.columns(2)
                    s1 = ca.text_input("応援者1", value=r['応援者1']); t1 = cb.text_input("時間1", value=r['時間1'])
                    s2 = ca.text_input("応援者2", value=r['応援者2']); t2 = cb.text_input("時間2", value=r['時間2'])
                    s3 = ca.text_input("応援者3", value=r['応援者3']); t3 = cb.text_input("時間3", value=r['時間3'])
                    s4 = ca.text_input("応援者4", value=r['応援者4']); t4 = cb.text_input("時間4", value=r['時間4'])
                    if st.form_submit_button("保存"):
                        p = {"action":"updateSupporters", "date":r['日付'], "department":r['学部'], "target":r['対象'], "startTime":r['開始'], "s1":s1, "t1":t1, "s2":s2, "t2":t2, "s3":s3, "t3":t3, "s4":s4, "t4":t4}
                        if post_to_gas(p): st.success("保存完了"); st.rerun()
            else: st.write("データがありません。")

        with t_monthly:
            st.subheader("📊 月次データ出力")
            month_list = sorted(list(set(pd.to_datetime(df_raw["日付"]).dt.strftime("%Y-%m"))), reverse=True)
            sel_month = st.selectbox("集計月を選択", month_list)
            df_month = df_raw[pd.to_datetime(df_raw["日付"]).dt.strftime("%Y-%m") == sel_month].copy()
            st.dataframe(df_month, use_container_width=True, hide_index=True)
            
            # Excel出力
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_month.to_excel(writer, index=False, sheet_name='応援集計')
            st.download_button(label="📥 Excel形式でダウンロード", data=output.getvalue(), file_name=f"応援集計_{sel_month}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --- 2. 各学部用 入力モード ---
else:
    df_raw = fetch_data()
    st.subheader(f"➕ 応援の依頼")
    
    # 申請済みプレビュー
    st.markdown('<div class="preview-box"><b>🔍 現在の申請状況（確認用）</b>', unsafe_allow_html=True)
    df_prev = df_raw[df_raw["日付"] == date_str]
    if not df_prev.empty:
        for _, pr in df_prev.iterrows():
            s_list = [pr[f'応援者{i}'] for i in range(1,5) if pr[f'応援者{i}']]
            s_txt = f" (担当:{' / '.join(s_list)})" if s_list else f" ({pr['人数']}名 要請済み)"
            st.write(f"✅ {pr['学部']} | {pr['対象']} {pr['開始']}〜{pr['終了']} {s_txt}")
    else: st.write("この日の要請はまだありません。")
    st.markdown('</div>', unsafe_allow_html=True)

    input_tab1, input_tab2 = st.tabs(["📍 単発入力", "🗓️ 期間一括入力"])
    
    with input_tab1:
        with st.form("single_form", clear_on_submit=True):
            d1, d2 = st.columns(2)
            dept = d1.selectbox("学部", ["小学部", "中学部", "高等部"], key="s_dept")
            target = d2.text_input("対象（クラス・班名）", placeholder="例：陶芸班")
            d3, d4, d5 = st.columns(3)
            st_t = d3.time_input("開始", datetime.time(9, 0), key="s_start")
            en_t = d4.time_input("終了", datetime.time(15, 0), key="s_end")
            num = d5.number_input("必要人数", 1, 10, 1)
            notes = st.text_area("詳細・理由")
            if st.form_submit_button("📢 応援依頼を送信"):
                p = {"date":date_str, "department":dept, "target":target, "startTime":st_t.strftime("%H:%M"), "endTime":en_t.strftime("%H:%M"), "count":num, "notes":notes}
                if post_to_gas(p): st.success("送信完了"); st.balloons(); st.rerun()

    with input_tab2:
        with st.form("range_form", clear_on_submit=True):
            st.info("指定した期間の「平日のみ」一括で登録します。")
            col_d1, col_d2 = st.columns(2)
            start_date = col_d1.date_input("開始日", datetime.date.today())
            end_date = col_d2.date_input("終了日", datetime.date.today() + datetime.timedelta(days=7))
            
            d1, d2 = st.columns(2)
            dept_r = d1.selectbox("学部", ["小学部", "中学部", "高等部"], key="r_dept")
            target_r = d2.text_input("対象（クラス・班名）", key="r_target")
            d3, d4, d5 = st.columns(3)
            st_t_r = d3.time_input("開始", datetime.time(9, 0), key="r_start")
            en_t_r = d4.time_input("終了", datetime.time(15, 0), key="r_end")
            num_r = d5.number_input("人数", 1, 10, 1, key="r_num")
            notes_r = st.text_area("理由", key="r_notes")
            
            if st.form_submit_button("🗓️ 期間一括で送信"):
                rows = []
                curr = start_date
                while curr <= end_date:
                    if curr.weekday() < 5: # 平日のみ
                        rows.append({"date":curr.strftime("%Y-%m-%d"), "department":dept_r, "target":target_r, "startTime":st_t_r.strftime("%H:%M"), "endTime":en_t_r.strftime("%H:%M"), "count":num_r, "notes":notes_r})
                    curr += datetime.timedelta(days=1)
                if post_to_gas({"rows": rows}): st.success(f"{len(rows)}日分の一括登録完了"); st.balloons(); st.rerun()