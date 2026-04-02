import streamlit as st
import pandas as pd
import requests
import datetime
import io
import calendar

# ==========================================
# 1. 設定：あなたのGASのURL
# ==========================================
GAS_URL = "https://script.google.com/macros/s/AKfycbw9s16VnR-Y67agtcaSv6Tuot9H1wAdPciPrMwYXgp_6J2A1lob3DFs3NL8p2iBynQxkw/exec"

st.set_page_config(page_title="総合支援部 応援調整ツール", layout="wide", initial_sidebar_state="expanded")

# --- 究極のデザインCSS（テーブル専用） ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans JP', sans-serif; background-color: #f1f5f9; }
    
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 1rem; border-radius: 0 0 15px 15px; color: white; text-align: center;
        margin-bottom: 1rem; box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    .main-header h1 { color: white !important; font-size: 1.6rem; border: none !important; margin: 0; }
    
    /* 統計カード */
    .stat-card {
        background: white; padding: 0.8rem; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        text-align: center; border-top: 5px solid #1e3a8a;
    }
    .stat-val { font-size: 1.8rem; font-weight: bold; color: #1e3a8a; }

    /* 【独自実装】HTMLカレンダーテーブルのCSS */
    .calendar-container { width: 100%; overflow-x: auto; background: white; padding: 10px; border-radius: 10px; }
    .cal-table {
        width: 100%; border-collapse: collapse; font-size: 12px !important; line-height: 1.3;
    }
    .cal-table th {
        background-color: #1e3a8a !important; color: white !important;
        padding: 8px; border: 1px solid #cbd5e1; text-align: center; font-weight: bold;
    }
    .cal-table td {
        padding: 6px; border: 1px solid #cbd5e1; vertical-align: top; white-space: pre-wrap;
    }
    .cal-table tr:nth-child(even) { background-color: #f8fafc; }
    .sat { color: #1d4ed8; background-color: #eff6ff !important; font-weight: bold; text-align: center; }
    .sun { color: #dc2626; background-color: #fef2f2 !important; font-weight: bold; text-align: center; }
    .date-col { text-align: center; font-weight: bold; background-color: #f1f5f9; width: 100px; }
    
    .stTabs [aria-selected="true"] { background-color: #1e3a8a !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

# --- 通信関数 ---
def fetch_data():
    with st.spinner("データ更新中..."):
        try:
            res = requests.get(f"{GAS_URL}?t={datetime.datetime.now().timestamp()}", timeout=30)
            if res.status_code == 200:
                data = res.json()
                if not data: return pd.DataFrame()
                df = pd.DataFrame(data)
                df.columns = [c.strip() for c in df.columns]
                df["日付_DT"] = pd.to_datetime(df["日付"], errors='coerce')
                df = df.dropna(subset=["日付_DT"])
                df["人数"] = pd.to_numeric(df["人数"], errors='coerce').fillna(0).astype(int)
                return df.sort_values(["日付_DT", "開始"])
            return pd.DataFrame()
        except: return pd.DataFrame()

def post_to_gas(payload):
    with st.spinner("通信中..."):
        try:
            res = requests.post(GAS_URL, json=payload, timeout=60)
            return res.status_code == 200
        except: return False

# --- カレンダーHTML生成ロジック ---
def render_calendar_html(df_month, sel_month):
    year, month = map(int, sel_month.split('-'))
    num_days = calendar.monthrange(year, month)[1]
    depts = ["小学部", "中学部", "高等部"]
    
    html = '<div class="calendar-container"><table class="cal-table">'
    html += '<thead><tr><th>日付</th><th>小学部</th><th>中学部</th><th>高等部</th></tr></thead><tbody>'
    
    for d in range(1, num_days + 1):
        day = datetime.date(year, month, d)
        d_str = day.strftime("%Y-%m-%d")
        weekday_ja = ["月","火","水","木","金","土","日"][day.weekday()]
        
        date_class = "date-col"
        if day.weekday() == 5: date_class = "date-col sat"
        if day.weekday() == 6: date_class = "date-col sun"
        
        html += f'<tr><td class="{date_class}">{d}日({weekday_ja})</td>'
        
        for dept in depts:
            targets = df_month[(df_month["日付"] == d_str) & (df_month["学部"] == dept)]
            cell_content = ""
            for _, r in targets.iterrows():
                s_list = []
                for i in range(1, 5):
                    n = str(r.get(f'応援者{i}', '')).strip()
                    t = str(r.get(f'時間{i}', '')).strip()
                    if n and n != 'nan' and n != '':
                        s_list.append(f"└ 👤{n}({t if t else '終日'})")
                
                supps_info = "<br>".join(s_list) if s_list else "└ (未定)"
                cell_content += f"<b>【{r['対象']}】</b> {r['開始']}~({r['人数']}名)<br>{supps_info}<br><hr style='border:0; border-top:1px dashed #ccc; margin:4px 0;'>"
            html += f'<td>{cell_content}</td>'
        html += '</tr>'
    
    html += '</tbody></table></div>'
    return html

# --- UI ---
st.markdown('<div class="main-header"><h1>🛡️ 総合支援部 応援調整ツール</h1></div>', unsafe_allow_html=True)

with st.sidebar:
    app_mode = st.radio("表示切替", ["📊 総合支援部（管理画面）", "➕ 各学部（応援要請）"])
    st.divider()
    target_date = st.date_input("📅 日付選択", datetime.date.today())
    date_str = target_date.strftime("%Y-%m-%d")
    if st.button("🔄 情報を更新"): st.rerun()

if app_mode == "📊 総合支援部（管理画面）":
    df_raw = fetch_data()
    if not df_raw.empty:
        df_today = df_raw[df_raw["日付"] == date_str].copy()
        sums = df_today.groupby("学部")["人数"].sum().reindex(["小学部", "中学部", "高等部"], fill_value=0)
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="stat-card" style="border-top-color:#10b981"><small>小学部</small><div class="stat-val">{sums["小学部"]}</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="stat-card" style="border-top-color:#f59e0b"><small>中学部</small><div class="stat-val">{sums["中学部"]}</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="stat-card" style="border-top-color:#3b82f6"><small>高等部</small><div class="stat-val">{sums["高等部"]}</div></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="stat-card"><small>合計</small><div class="stat-val">{sums.sum()}</div></div>', unsafe_allow_html=True)

        st.write("---")
        t_daily, t_cal, t_assign, t_excel = st.tabs(["🌎 本日の状況詳細", "📅 月間カレンダー表示", "✍️ 応援者を割り当てる", "📥 Excel出力"])

        with t_daily:
            if not df_today.empty:
                for _, row in df_today.iterrows():
                    color = "#10b981" if row['学部']=="小学部" else "#f59e0b" if row['学部']=="中学部" else "#3b82f6"
                    with st.container():
                        st.markdown(f"### {row['学部']} | {row['対象']}")
                        st.write(f"⏰ {row['開始']} 〜 {row['終了']}　👥 {row['人数']}名　📝 {row['備考']}")
                        st.write("**【応援担当者】**")
                        any_s = False
                        for i in [1, 3]:
                            ca, cb = st.columns(2)
                            n1 = str(row.get(f'応援者{i}', '')).strip(); t1 = str(row.get(f'時間{i}', '')).strip()
                            if n1 and n1 != 'nan' and n1 != '': ca.info(f"👤 **{n1}**\n⏰ {t1 if t1 else '終日'}"); any_s = True
                            n2 = str(row.get(f'応援者{i+1}', '')).strip(); t2 = str(row.get(f'時間{i+1}', '')).strip()
                            if n2 and n2 != 'nan' and n2 != '': cb.info(f"👤 **{n2}**\n⏰ {t2 if t2 else '終日'}"); any_s = True
                        if not any_s: st.caption("（未定）")
                        st.divider()
            else: st.info("本日の要請はありません。")

        with t_cal:
            df_raw['年月'] = df_raw['日付_DT'].dt.strftime('%Y-%m')
            sel_m = st.selectbox("月を選択", sorted(df_raw['年月'].unique(), reverse=True))
            if sel_m:
                st.markdown(render_calendar_html(df_raw[df_raw['年月'] == sel_m], sel_m), unsafe_allow_html=True)

        with t_assign:
            mode = st.radio("更新方法", ["本日分を個別更新", "期間指定で一括更新"], horizontal=True)
            if mode == "本日分を個別更新":
                if not df_today.empty:
                    df_today['selector'] = df_today['学部'] + " | " + df_today['対象'] + " (" + df_today['開始'] + "~)"
                    sel = st.selectbox("要請を選択", df_today['selector'].tolist())
                    r = df_today[df_today['selector'] == sel].iloc[0]
                    with st.form("assign_f"):
                        c1, c2 = st.columns(2)
                        s1=c1.text_input("応援者1", value=r.get('応援者1','')); t1=c2.text_input("時間1", value=r.get('時間1',''))
                        s2=c1.text_input("応援者2", value=r.get('応援者2','')); t2=c2.text_input("時間2", value=r.get('時間2',''))
                        s3=c1.text_input("応援者3", value=r.get('応援者3','')); t3=c2.text_input("時間3", value=r.get('時間3',''))
                        s4=c1.text_input("応援者4", value=r.get('応援者4','')); t4=c2.text_input("時間4", value=r.get('時間4',''))
                        if st.form_submit_button("保存"):
                            p = {"action":"updateSupporters", "isBulk":False, "date":r['日付'], "department":r['学部'], "target":r['対象'], "startTime":r['開始'], "s1":s1, "t1":t1, "s2":s2, "t2":t2, "s3":s3, "t3":t3, "s4":s4, "t4":t4}
                            if post_to_gas(p): st.success("完了"); st.rerun()
            else:
                with st.form("bulk_assign"):
                    st.info("過去の要請から選んで一括更新します。")
                    df_raw['dt'] = df_raw['学部'] + " | " + df_raw['対象']
                    unique_targets = sorted(df_raw['dt'].unique().tolist())
                    b1, b2 = st.columns(2)
                    sd = b1.date_input("開始日"); ed = b2.date_input("終了日")
                    target_sel = st.selectbox("対象を選択", unique_targets)
                    c1, c2 = st.columns(2)
                    s1=c1.text_input("応援者1"); t1=c2.text_input("時間1"); s2=c1.text_input("応援者2"); t2=c2.text_input("時間2")
                    s3=c1.text_input("応援者3"); t3=c2.text_input("時間3"); s4=c1.text_input("応援者4"); t4=c2.text_input("時間4")
                    if st.form_submit_button("一括更新実行"):
                        sel_dept, sel_target = target_sel.split(" | ")
                        p = {"action":"updateSupporters", "isBulk":True, "startDate":sd.strftime("%Y-%m-%d"), "endDate":ed.strftime("%Y-%m-%d"), "department":sel_dept, "target":sel_target, "s1":s1, "t1":t1, "s2":s2, "t2":t2, "s3":s3, "t3":t3, "s4":s4, "t4":t4}
                        if post_to_gas(p): st.success("一括更新完了"); st.rerun()

        with t_excel:
            sel_ex = st.selectbox("Excel出力月", sorted(df_raw['年月'].unique(), reverse=True), key="ex")
            if st.button("📅 画像形式のExcel生成"):
                df_m = df_raw[df_raw['年月'] == sel_ex]
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    wb = writer.book; ws = wb.add_worksheet('応援カレンダー')
                    h_fmt = wb.add_format({'bold':True,'bg_color':'#1e3a8a','font_color':'white','border':1,'align':'center'})
                    c_fmt = wb.add_format({'border':1,'text_wrap':True,'valign':'top','font_size':9})
                    sat_fmt = wb.add_format({'border':1,'bg_color':'#f8fafc','align':'center','font_color':'#1d4ed8','bold':True})
                    sun_fmt = wb.add_format({'border':1,'bg_color':'#fef2f2','align':'center','font_color':'#dc2626','bold':True})
                    ws.set_column('A:A', 12); ws.set_column('B:D', 45)
                    ws.write_row(0, 0, ["日付", "小学部", "中学部", "高等部"], h_fmt)
                    year, month = map(int, sel_ex.split('-'))
                    num_days = calendar.monthrange(year, month)[1]
                    for d in range(1, num_days+1):
                        day = datetime.date(year, month, d)
                        d_str = day.strftime("%Y-%m-%d")
                        d_fmt = sat_fmt if day.weekday()==5 else sun_fmt if day.weekday()==6 else wb.add_format({'border':1,'align':'center','bold':True})
                        ws.write(d, 0, f"{d}日({['月','火','水','木','金','土','日'][day.weekday()]})", d_fmt)
                        for col, dept in enumerate(["小学部","中学部","高等部"], 1):
                            targets = df_m[(df_m["日付"] == d_str) & (df_m["学部"] == dept)]
                            cell_text = ""
                            for _, r in targets.iterrows():
                                s_list = [f"👤{r[f'応援者{i}']}({r[f'時間{i}'] if r[f'時間{i}'] else '終日'})" for i in range(1,5) if str(r.get(f'応援者{i}','')).strip() and str(r.get(f'応援者{i}','')).strip()!='nan']
                                cell_text += f"【{r['対象']}】 {r['開始']}~({r['人数']}名)\n " + (" ".join(s_list) if s_list else "(未定)") + "\n" + "-"*15 + "\n"
                            ws.write(d, col, cell_text.strip(), c_fmt)
                st.download_button("📥 ダウンロード", output.getvalue(), f"応援カレンダー_{sel_ex}.xlsx")

else:
    df_raw = fetch_data()
    st.subheader(f"➕ 応援要請の送信")
    with st.expander(f"🔍 {date_str} の申請状況を確認", expanded=True):
        df_p = df_raw[df_raw["日付"] == date_str] if not df_raw.empty else pd.DataFrame()
        if not df_p.empty:
            for _, pr in df_p.iterrows(): st.write(f"✅ **{pr['学部']}** | {pr['対象']} ({pr['開始']}〜)")
        else: st.info("本日の申請はありません。")
    t_s, t_r = st.tabs(["📍 単発", "🗓️ 期間一括"])
    with t_s:
        with st.form("s_f", clear_on_submit=True):
            dept = st.selectbox("学部", ["小学部", "中学部", "高等部"]); target = st.text_input("対象")
            c1, c2, c3 = st.columns(3); st_t = c1.time_input("開始", datetime.time(9, 0)); en_t = c2.time_input("終了", datetime.time(15, 0)); num = c3.number_input("人数", 1, 10, 1)
            memo = st.text_area("理由")
            if st.form_submit_button("送信"):
                p = {"date":date_str, "department":dept, "target":target, "startTime":st_t.strftime("%H:%M"), "endTime":en_t.strftime("%H:%M"), "count":num, "notes":memo}
                if post_to_gas(p): st.success("完了"); st.rerun()
    with t_r:
        with st.form("r_f", clear_on_submit=True):
            sd = st.date_input("開始日"); ed = st.date_input("終了日")
            r_dept = st.selectbox("学部", ["小学部", "中学部", "高等部"], key="rd"); r_target = st.text_input("対象", key="rt")
            c1, c2, c3 = st.columns(3); rs = c1.time_input("開始", datetime.time(9, 0)); re = c2.time_input("終了", datetime.time(15, 0)); rn = c3.number_input("人数", 1, 10, 1)
            rm = st.text_area("理由")
            if st.form_submit_button("一括送信"):
                bulk = []
                curr = sd
                while curr <= ed:
                    if curr.weekday() < 5: bulk.append({"date":curr.strftime("%Y-%m-%d"), "department":r_dept, "target":r_target, "startTime":rs.strftime("%H:%M"), "endTime":re.strftime("%H:%M"), "count":rn, "notes":rm})
                    curr += datetime.timedelta(days=1)
                if post_to_gas({"rows": bulk}): st.success("一括完了"); st.rerun()