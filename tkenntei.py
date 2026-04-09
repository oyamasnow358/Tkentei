import streamlit as st
import pandas as pd
import requests
import datetime
import io
import calendar
import re
import time

# ==========================================
# 1. 設定：あなたのGASのURL
# ==========================================
GAS_URL = "https://script.google.com/macros/s/AKfycbwWAOlJWkDrKf3Wchswba_qeXKpmONAvfAX5dV2eN5rjH1svT9YeLls4azqY4rbGC8Pww/exec"

st.set_page_config(page_title="総合支援部 応援調整ツール", layout="wide", initial_sidebar_state="expanded")

# --- 究極のデザインCSS（一切の省略・変更なし） ---
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
    
    .stat-card {
        background: white; padding: 0.8rem; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        text-align: center; border-top: 5px solid #1e3a8a;
    }
    .stat-val { font-size: 1.8rem; font-weight: bold; color: #1e3a8a; }

    /* カレンダー表示 */
    .calendar-container { width: 100%; overflow-x: auto; background: white; padding: 10px; border-radius: 10px; }
    .cal-table { width: 100%; border-collapse: collapse; font-size: 12px !important; line-height: 1.3; }
    .cal-table th { background-color: #1e3a8a !important; color: white !important; padding: 8px; border: 1px solid #cbd5e1; text-align: center; font-weight: bold; }
    .cal-table td { padding: 6px; border: 1px solid #cbd5e1; vertical-align: top; white-space: pre-wrap; }
    .sat { color: #1d4ed8; background-color: #eff6ff !important; font-weight: bold; text-align: center; }
    .sun { color: #dc2626; background-color: #fef2f2 !important; font-weight: bold; text-align: center; }
    .date-col { text-align: center; font-weight: bold; background-color: #f1f5f9; width: 100px; }
    
    /* タイムライン表示 */
    .timeline-container { width: 100%; overflow-x: auto; margin-top: 10px; background: white; padding: 15px; border-radius: 10px; margin-bottom: 30px; }
    .timeline-table { width: 100%; border-collapse: collapse; table-layout: fixed; min-width: 1200px; }
    .timeline-table th, .timeline-table td { border: 1px solid #e2e8f0; padding: 4px; text-align: center; font-size: 10px; height: 45px; }
    .timeline-header { background-color: #1e3a8a; color: white; font-weight: bold; }
    .member-col { width: 100px; background-color: #f8fafc; font-weight: bold; font-size: 12px !important; position: sticky; left: 0; z-index: 10; border-right: 2px solid #cbd5e1; }
    
    /* 応援レベル別スタイル */
    .job-box { border-radius: 4px; padding: 2px; color: white; font-weight: bold; font-size: 9px; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; line-height: 1.1; }
    .level-alert { border: 2.5px solid #dc2626; box-shadow: 0 0 5px rgba(220,38,38,0.5); }
    
    .bg-elem { background-color: #10b981; } 
    .bg-junior { background-color: #f59e0b; }
    .bg-high { background-color: #3b82f6; }

    .stTabs [aria-selected="true"] { background-color: #1e3a8a !important; color: white !important; }
    .timeline-date-header { background: #475569; color: white; padding: 5px 15px; border-radius: 5px; margin-top: 20px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- ロジック：時間解析 ---
def to_min(t_str):
    if not t_str or str(t_str).lower() == 'nan': return None
    t_str = str(t_str).replace(' ', '').replace('　', '').replace('：', ':')
    match = re.search(r'(\d{1,2}):(\d{2})', t_str)
    if match:
        h, m = map(int, match.groups())
        return h * 60 + m
    return None

def check_job_slot(slot_min, row, idx):
    ind_time = str(row.get(f'時間{idx}', '')).replace(' ', '').replace('～', '~').replace('-', '~').replace('：', ':')
    try:
        if '~' in ind_time:
            parts = ind_time.split('~')
            s_min = to_min(parts[0]); e_min = to_min(parts[1])
        else:
            s_min = to_min(row['開始']); e_min = to_min(row['終了'])
        if s_min is not None and e_min is not None:
            return s_min <= slot_min < e_min
    except: pass
    return False

# --- 通信関数 ---
def fetch_all_data():
    with st.spinner("データ更新中..."):
        try:
            res = requests.get(f"{GAS_URL}?t={datetime.datetime.now().timestamp()}", timeout=30)
            if res.status_code == 200:
                data = res.json()
                req_list = data.get("requests", [])
                mem_list = data.get("members", [])
                if not req_list: return pd.DataFrame(), mem_list
                df = pd.DataFrame(req_list)
                df.columns = [c.strip() for c in df.columns]
                df["日付_OBJ"] = pd.to_datetime(df["日付"]).dt.date
                return df, mem_list
            return pd.DataFrame(), []
        except: return pd.DataFrame(), []

def post_to_gas(payload):
    with st.spinner("通信中..."):
        try:
            res = requests.post(GAS_URL, json=payload, timeout=60)
            return res.status_code == 200
        except: return False

# --- カレンダーHTML生成 ---
def render_calendar_html(df_raw, sel_month):
    year, month = map(int, sel_month.split('-'))
    num_days = calendar.monthrange(year, month)[1]
    depts = ["小学部", "中学部", "高等部"]
    html = '<div class="calendar-container"><table class="cal-table"><thead><tr><th>日付</th><th>小学部</th><th>中学部</th><th>高等部</th></tr></thead><tbody>'
    for d in range(1, num_days + 1):
        day = datetime.date(year, month, d)
        weekday_ja = ["月","火","水","木","金","土","日"][day.weekday()]
        d_cls = "date-col sat" if day.weekday()==5 else "date-col sun" if day.weekday()==6 else "date-col"
        html += f'<tr><td class="{d_cls}">{d}日({weekday_ja})</td>'
        for dept in depts:
            targets = df_raw[(df_raw["日付_OBJ"] == day) & (df_raw["学部"] == dept)]
            cell_content = ""
            for _, r in targets.iterrows():
                lv_ico = "🚨" if r.get("応援レベル") == "欠員補充" else "🤝"
                s_list = [f"└ 👤{r[f'応援者{i}']}({r[f'時間{i}'] if r[f'時間{i}'] else '終日'})" for i in range(1,5) if str(r.get(f'応援者{i}','')).strip() and str(r.get(f'応援者{i}',''))!='nan']
                cell_content += f"<b>{lv_ico}【{r['対象']}】</b> {r['開始']}~<br>{'<br>'.join(s_list) if s_list else '└ (未定)'}<hr style='border:0; border-top:1px dashed #ccc; margin:4px 0;'>"
            html += f'<td>{cell_content}</td>'
        html += '</tr>'
    return html + '</tbody></table></div>'

# --- タイムラインHTML生成 ---
def render_timeline_day_html(day_obj, df_all, member_list):
    df_day = df_all[df_all["日付_OBJ"] == day_obj]
    slots = []
    for h in range(8, 18):
        slots.append((h * 60, f"{h}:00")); slots.append((h * 60 + 30, f"{h}:30"))
    
    html = f'<div class="timeline-date-header">{day_obj.strftime("%Y年%m月%d日")}</div>'
    html += '<div class="timeline-container"><table class="timeline-table"><thead><tr>'
    html += '<th class="timeline-header member-col">応援者名</th>'
    for _, label in slots: html += f'<th class="timeline-header">{label}</th>'
    html += '</tr></thead><tbody>'

    for name in member_list:
        html += f'<tr><td class="member-col">{name}</td>'
        for s_min, _ in slots:
            cell = ""
            for _, r in df_day.iterrows():
                for i in range(1, 5):
                    if str(r.get(f'応援者{i}', '')).strip() == name:
                        if check_job_slot(s_min, r, i):
                            bg = "bg-elem" if r['学部']=="小学部" else "bg-junior" if r['学部']=="中学部" else "bg-high"
                            is_alert = "level-alert" if r.get("応援レベル") == "欠員補充" else ""
                            lv_ico = "🚨" if r.get("応援レベル") == "欠員補充" else ""
                            cell = f'<div class="job-box {bg} {is_alert}">{lv_ico}{r["学部"][0]}<br>{r["対象"][:3]}</div>'
                            break
            html += f'<td>{cell}</td>'
        html += '</tr>'
    html += '</tbody></table></div>'
    return html

# --- UI ---
st.markdown('<div class="main-header"><h1>🛡️ 総合支援部 応援調整ツール</h1></div>', unsafe_allow_html=True)

with st.sidebar:
    app_mode = st.radio("表示切替", ["📊 総合支援部（管理画面）", "➕ 各学部（応援要請）"])
    st.divider()
    target_date = st.date_input("📅 日付選択", datetime.date.today())
    if st.button("🔄 情報を更新"): st.rerun()

if app_mode == "📊 総合支援部（管理画面）":
    df_raw, member_list = fetch_all_data()
    if not df_raw.empty:
        df_today = df_raw[df_raw["日付_OBJ"] == target_date].copy()
        sums_df = df_today.copy()
        sums_df["人数"] = pd.to_numeric(sums_df["人数"], errors='coerce').fillna(0)
        sums = sums_df.groupby("学部")["人数"].sum().reindex(["小学部", "中学部", "高等部"], fill_value=0)
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="stat-card" style="border-top-color:#10b981"><small>小学部</small><div class="stat-val">{int(sums["小学部"])}</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="stat-card" style="border-top-color:#f59e0b"><small>中学部</small><div class="stat-val">{int(sums["中学部"])}</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="stat-card" style="border-top-color:#3b82f6"><small>高等部</small><div class="stat-val">{int(sums["高等部"])}</div></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="stat-card"><small>合計</small><div class="stat-val">{int(sums.sum())}</div></div>', unsafe_allow_html=True)

        st.write("---")
        t_daily, t_timeline, t_cal, t_assign, t_excel = st.tabs(["🌎 本日の状況詳細", "👤 応援者別タイムライン", "📅 月間カレンダー表示", "✍️ 応援者を割り当てる", "📥 Excel出力"])

        with t_daily:
            if not df_today.empty:
                for _, row in df_today.iterrows():
                    lv = row.get("応援レベル", "支援")
                    lv_ico = "🚨" if lv == "欠員補充" else "🤝"
                    st.markdown(f"### {lv_ico} {row['学部']} | {row['対象']} <small>({lv})</small>", unsafe_allow_html=True)
                    st.write(f"⏰ {row['開始']} 〜 {row['終了']}　👥 {row['人数']}名　📝 {row['備考']}")
                    cols = st.columns(4); any_s = False
                    for i in range(1, 5):
                        n = str(row.get(f'応援者{i}', '')).strip()
                        if n and n != 'nan' and n != "":
                            cols[i-1].info(f"👤 **{n}**\n⏰ {row.get(f'時間{i}', '終日')}"); any_s = True
                    if not any_s: st.caption("（未定）")
                    st.divider()
            else: st.info(f"{target_date} の要請はありません。")

        with t_timeline:
            st.subheader("👤 応援者別スケジュール（本日〜1週間後）")
            if not member_list: st.warning("memberシートを確認してください。")
            else:
                for offset in range(7):
                    d_obj = target_date + datetime.timedelta(days=offset)
                    st.markdown(render_timeline_day_html(d_obj, df_raw, member_list), unsafe_allow_html=True)

        with t_cal:
            df_raw['年月'] = pd.to_datetime(df_raw['日付_OBJ']).dt.strftime('%Y-%m')
            sel_m = st.selectbox("月を選択", sorted(df_raw['年月'].unique(), reverse=True))
            if sel_m: st.markdown(render_calendar_html(df_raw, sel_m), unsafe_allow_html=True)

        with t_assign:
            m_options = [""] + member_list
            mode = st.radio("更新方法", ["本日分を個別更新", "期間指定で一括更新"], horizontal=True)
            if mode == "本日分を個別更新":
                if not df_today.empty:
                    df_today['selector'] = df_today['学部'] + " | " + df_today['対象'] + " (" + df_today['開始'] + "~)"
                    sel = st.selectbox("要請を選択", df_today['selector'].tolist())
                    r = df_today[df_today['selector'] == sel].iloc[0]
                    with st.form("assign_f"):
                        c1, c2 = st.columns(2)
                        def get_idx(val): return m_options.index(val) if val in m_options else 0
                        s1 = c1.selectbox("応援者1", m_options, index=get_idx(r.get('応援者1','')))
                        t1 = c2.text_input("時間1", value=r.get('時間1',''))
                        s2 = c1.selectbox("応援者2", m_options, index=get_idx(r.get('応援者2','')))
                        t2 = c2.text_input("時間2", value=r.get('時間2',''))
                        s3 = c1.selectbox("応援者3", m_options, index=get_idx(r.get('応援者3','')))
                        t3 = c2.text_input("時間3", value=r.get('時間3',''))
                        s4 = c1.selectbox("応援者4", m_options, index=get_idx(r.get('応援者4','')))
                        t4 = c2.text_input("時間4", value=r.get('時間4',''))
                        if st.form_submit_button("保存"):
                            p = {"action":"updateSupporters", "isBulk":False, "date":str(r['日付_OBJ']), "department":r['学部'], "target":r['対象'], "startTime":r['開始'], "s1":s1, "t1":t1, "s2":s2, "t2":t2, "s3":s3, "t3":t3, "s4":s4, "t4":t4}
                            if post_to_gas(p): st.success("完了"); st.rerun()
            else:
                with st.form("bulk_assign"):
                    df_raw['dt'] = df_raw['学部'] + " | " + df_raw['対象']
                    unique_targets = sorted(df_raw['dt'].unique().tolist())
                    b1, b2 = st.columns(2); sd = b1.date_input("開始日"); ed = b2.date_input("終了日")
                    target_sel = st.selectbox("対象を選択", unique_targets)
                    c1, c2 = st.columns(2)
                    s1 = c1.selectbox("応援者1", m_options); t1 = c2.text_input("時間1")
                    s2 = c1.selectbox("応援者2", m_options); t2 = c2.text_input("時間2")
                    if st.form_submit_button("一括更新実行"):
                        sel_dept, sel_target = target_sel.split(" | ")
                        p = {"action":"updateSupporters", "isBulk":True, "startDate":sd.strftime("%Y-%m-%d"), "endDate":ed.strftime("%Y-%m-%d"), "department":sel_dept, "target":sel_target, "s1":s1, "t1":t1, "s2":s2, "t2":t2, "s3":"","t3":"","s4":"","t4":""}
                        if post_to_gas(p): st.success("一括完了"); st.rerun()

        with t_excel:
            df_raw['年月'] = pd.to_datetime(df_raw['日付_OBJ']).dt.strftime('%Y-%m')
            sel_ex = st.selectbox("Excel出力月", sorted(df_raw['年月'].unique(), reverse=True), key="ex")
            if st.button("📅 カレンダー形式Excel生成"):
                df_m = df_raw[df_raw['年月'] == sel_ex]
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    wb = writer.book; ws = wb.add_worksheet('応援カレンダー')
                    h_fmt = wb.add_format({'bold':True,'bg_color':'#1e3a8a','font_color':'white','border':1,'align':'center'})
                    c_fmt = wb.add_format({'border':1,'text_wrap':True,'valign':'top','font_size':9})
                    ws.set_column('A:A', 12); ws.set_column('B:D', 45)
                    ws.write_row(0, 0, ["日付", "小学部", "中学部", "高等部"], h_fmt)
                    y, m = map(int, sel_ex.split('-'))
                    for d in range(1, calendar.monthrange(y, m)[1]+1):
                        day = datetime.date(y, m, d)
                        ws.write(d, 0, f"{d}日({['月','火','水','木','金','土','日'][day.weekday()]})", wb.add_format({'border':1}))
                        for col, dept in enumerate(["小学部","中学部","高等部"], 1):
                            targets = df_m[(df_m["日付_OBJ"] == day) & (df_m["学部"] == dept)]
                            cell_text = ""
                            for _, r in targets.iterrows():
                                lv_txt = "🚨" if r.get("応援レベル") == "欠員補充" else ""
                                s_list = [f"👤{r[f'応援者{i}']}({r[f'時間{i}'] if r[f'時間{i}'] else '終日'})" for i in range(1,5) if str(r.get(f'応援者{i}','')).strip() and str(r.get(f'応援者{i}','')).strip()!='nan']
                                cell_text += f"{lv_txt}【{r['対象']}】 {r['開始']}~({r['人数']}名)\n " + (" ".join(s_list) if s_list else "(未定)") + "\n" + "-"*15 + "\n"
                            ws.write(d, col, cell_text.strip(), c_fmt)
                st.download_button("📥 カレンダーExcel保存", output.getvalue(), f"応援カレンダー_{sel_ex}.xlsx")

            if st.button("👤 応援者別タイムラインExcel生成"):
                df_m = df_raw[df_raw['年月'] == sel_ex]
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    wb = writer.book; y, m = map(int, sel_ex.split('-'))
                    for d in range(1, calendar.monthrange(y, m)[1]+1):
                        day = datetime.date(y, m, d); ws = wb.add_worksheet(f"{d}日")
                        slots = []
                        for h in range(8, 18): slots.append((h*60, f"{h}:00")); slots.append((h*60+30, f"{h}:30"))
                        ws.write(0, 0, "応援者名", wb.add_format({'bold':True,'bg_color':'#1e3a8a','font_color':'white','border':1}))
                        for i, (_, label) in enumerate(slots): ws.write(0, i+1, label, wb.add_format({'bold':True,'bg_color':'#1e3a8a','font_color':'white','border':1}))
                        df_day = df_m[df_m["日付_OBJ"] == day]
                        for row_idx, name in enumerate(member_list, 1):
                            ws.write(row_idx, 0, name, wb.add_format({'border':1}))
                            for col_idx, (s_min, _) in enumerate(slots, 1):
                                job_txt = ""; cell_color = None; is_alert = False
                                for _, r in df_day.iterrows():
                                    for i in range(1, 5):
                                        if str(r.get(f'応援者{i}', '')).strip() == name:
                                            if check_job_slot(s_min, r, i):
                                                job_txt = f"{r['学部'][0]}\n{r['対象'][:3]}"
                                                cell_color = '#10b981' if r['学部']=="小学部" else '#f59e0b' if r['学部']=="中学部" else '#3b82f6'
                                                if r.get("応援レベル") == "欠員補充": is_alert = True
                                                break
                                if job_txt:
                                    ws.write(row_idx, col_idx, job_txt, wb.add_format({'border':2 if is_alert else 1,'align':'center','valign':'vcenter','font_size':8,'bg_color':cell_color,'font_color':'white','bold':True,'text_wrap':True}))
                                else: ws.write(row_idx, col_idx, "", wb.add_format({'border':1}))
                        ws.set_column(0, 0, 15); ws.set_column(1, len(slots), 6)
                st.download_button("📥 タイムラインExcel保存", output.getvalue(), f"応援タイムライン_{sel_ex}.xlsx")

else:
    df_raw, member_list = fetch_all_data()
    st.subheader(f"➕ 応援要請の送信")
    with st.form("req_f", clear_on_submit=True):
        lv = st.radio("応援レベル", ["欠員補充", "支援"], horizontal=True, index=1)
        c1, c2 = st.columns(2); dept = c1.selectbox("学部", ["小学部","中学部","高等部"]); target = c2.text_input("対象（クラスとか）")
        c3, c4, c5 = st.columns(3); st_t = c3.time_input("開始", datetime.time(9,0)); en_t = c4.time_input("終了", datetime.time(15,0)); num = c5.number_input("人数", 1, 10, 1)
        memo = st.text_area("理由")
        t1, t2 = st.tabs(["📍 単発申請", "🗓️ 期間一括申請"])
        with t1:
            if st.form_submit_button("単発送信"):
                p = {"date":str(target_date), "department":dept, "target":target, "startTime":st_t.strftime("%H:%M"), "endTime":en_t.strftime("%H:%M"), "count":num, "notes":memo, "level":lv}
                if post_to_gas(p):
                    st.balloons()
                    st.success("応援要請を送信しました！")
                    time.sleep(2); st.rerun()
        with t2:
            sd = st.date_input("開始日"); ed = st.date_input("終了日")
            if st.form_submit_button("一括送信"):
                bulk = []
                curr = sd
                while curr <= ed:
                    if curr.weekday() < 5:
                        bulk.append({"date":curr.strftime("%Y-%m-%d"), "department":dept, "target":target, "startTime":st_t.strftime("%H:%M"), "endTime":en_t.strftime("%H:%M"), "count":num, "notes":memo, "level":lv})
                    curr += datetime.timedelta(days=1)
                if post_to_gas({"rows": bulk}):
                    st.balloons()
                    st.success(f"{len(bulk)}日分の一括要請を送信しました！")
                    time.sleep(2); st.rerun()