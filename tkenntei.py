import streamlit as st
import pandas as pd
import requests
import datetime
import io

# --- 設定 ---
GAS_URL = "https://script.google.com/macros/s/AKfycbzwUck19yBozJgmut0ksH4vqt_Ml1rhDp2O7eO7P0S3dCu2J8YCagsuLhwHCNujWlf3xw/exec"

st.set_page_config(page_title="総合支援部 応援調整ツール", layout="wide", initial_sidebar_state="expanded")

# --- カスタムデザインCSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans JP', sans-serif; background-color: #f1f5f9; }
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 1.5rem; border-radius: 0 0 20px 20px; color: white; text-align: center;
        margin-bottom: 1.5rem; box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    .main-header h1 { color: white !important; font-size: 2rem; border: none !important; margin: 0; }
    .stat-card {
        background: white; padding: 1rem; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        text-align: center; border-top: 6px solid #1e3a8a;
    }
    .stat-val { font-size: 2rem; font-weight: bold; color: #1e3a8a; }
    .req-card {
        background: white; padding: 15px; border-radius: 10px; margin-bottom: 10px;
        border-left: 8px solid #1e3a8a; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .supporter-list {
        background: #f0f9ff; padding: 10px; border-radius: 8px; margin-top: 8px; border: 1px solid #bae6fd;
    }
    .supporter-item { font-size: 0.95rem; color: #0369a1; font-weight: bold; margin-bottom: 4px; }
    .preview-area {
        background: #ffffff; border: 2px solid #3b82f6; border-radius: 12px; padding: 15px; margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 通信関数（タイムアウト対策強化） ---
def fetch_data():
    try:
        # timeoutを30秒に設定し、GASの遅延を許容
        res = requests.get(f"{GAS_URL}?t={datetime.datetime.now().timestamp()}", timeout=30)
        if res.status_code == 200:
            data = res.json()
            if not data: return pd.DataFrame()
            df = pd.DataFrame(data)
            df.columns = [c.strip() for c in df.columns]
            df["人数"] = pd.to_numeric(df["人数"], errors='coerce').fillna(0).astype(int)
            return df
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame() # エラー時は空のDFを返してクラッシュを防ぐ

def post_to_gas(payload):
    try:
        res = requests.post(GAS_URL, json=payload, timeout=60) # 一括登録用に1分待機
        return res.status_code == 200
    except Exception as e:
        st.error(f"送信タイムアウトまたはエラー: {e}")
        return False

# --- UI：ヘッダー ---
st.markdown('<div class="main-header"><h1>🛡️ 総合支援部 応援調整ツール</h1></div>', unsafe_allow_html=True)

# --- UI：サイドバー ---
with st.sidebar:
    st.markdown("### ⚙️ メニュー")
    app_mode = st.radio("表示画面", ["📊 総合支援部（管理・俯瞰）", "➕ 応援依頼（各学部用入力）"])
    st.divider()
    target_date = st.date_input("📅 対象日", datetime.date.today())
    date_str = target_date.strftime("%Y-%m-%d")
    if st.button("🔄 最新情報に更新", use_container_width=True):
        st.rerun()

# --- 1. 総合支援部 モード ---
if app_mode == "📊 総合支援部（管理・俯瞰）":
    df_raw = fetch_data()
    
    if not df_raw.empty and "日付" in df_raw.columns:
        df_today = df_raw[df_raw["日付"] == date_str].copy()
        
        # 統計
        sums = df_today.groupby("学部")["人数"].sum().reindex(["小学部", "中学部", "高等部"], fill_value=0)
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="stat-card" style="border-top-color:#10b981"><small>小学部</small><div class="stat-val">{sums["小学部"]}</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="stat-card" style="border-top-color:#f59e0b"><small>中学部</small><div class="stat-val">{sums["中学部"]}</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="stat-card" style="border-top-color:#3b82f6"><small>高等部</small><div class="stat-val">{sums["高等部"]}</div></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="stat-card"><small>合計</small><div class="stat-val">{sums.sum()}</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        tabs = st.tabs(["🌎 全体俯瞰", "🐥 小学部", "🏃 中学部", "🎓 高等部", "✍️ 応援者割当", "📥 月別Excel出力"])

        def render_cards(data_df):
            if data_df.empty:
                st.info("この条件の要請はありません。")
                return
            for _, row in data_df.sort_values("開始").iterrows():
                color = "#10b981" if row['学部']=="小学部" else "#f59e0b" if row['学部']=="中学部" else "#3b82f6"
                supporters = []
                for i in range(1, 5):
                    n = row.get(f'応援者{i}', '').strip()
                    t = row.get(f'時間{i}', '').strip()
                    if n: supporters.append(f"👤 {n} ({t if t else '終日'})")
                
                supp_html = "".join([f'<div class="supporter-item">{s}</div>' for s in supporters]) if supporters else '<div style="color:#94a3b8">（未定）</div>'
                st.markdown(f"""
                    <div class="req-card" style="border-left-color:{color}">
                        <div style="display:flex; justify-content:space-between; font-weight:bold; color:#1e3a8a;">
                            <span>{row['学部']} | {row['対象']}</span>
                            <span>⏰ {row['開始']} 〜 {row['終了']} (必要:{row['人数']}名)</span>
                        </div>
                        <div style="font-size:0.85rem; color:#64748b; margin: 5px 0;">備考: {row['備考']}</div>
                        <div class="supporter-list">{supp_html}</div>
                    </div>
                """, unsafe_allow_html=True)

        with tabs[0]: render_cards(df_today)
        with tabs[1]: render_cards(df_today[df_today["学部"]=="小学部"])
        with tabs[2]: render_cards(df_today[df_today["学部"]=="中学部"])
        with tabs[3]: render_cards(df_today[df_today["学部"]=="高等部"])

        with tabs[4]: # 割当
            if not df_today.empty:
                df_today['selector'] = df_today['学部'] + " | " + df_today['対象'] + " (" + df_today['開始'] + "~)"
                sel = st.selectbox("更新する要請を選択", df_today['selector'].tolist())
                r = df_today[df_today['selector'] == sel].iloc[0]
                with st.form("assign_form"):
                    ca, cb = st.columns(2)
                    s1 = ca.text_input("応援者1", value=r['応援者1']); t1 = cb.text_input("時間1", value=r['時間1'])
                    s2 = ca.text_input("応援者2", value=r['応援者2']); t2 = cb.text_input("時間2", value=r['時間2'])
                    s3 = ca.text_input("応援者3", value=r['応援者3']); t3 = cb.text_input("時間3", value=r['時間3'])
                    s4 = ca.text_input("応援者4", value=r['応援者4']); t4 = cb.text_input("時間4", value=r['時間4'])
                    if st.form_submit_button("応援担当情報を保存"):
                        p = {"action":"updateSupporters", "date":r['日付'], "department":r['学部'], "target":r['対象'], "startTime":r['開始'], "s1":s1, "t1":t1, "s2":s2, "t2":t2, "s3":s3, "t3":t3, "s4":s4, "t4":t4}
                        if post_to_gas(p): st.success("保存完了"); st.rerun()
            else: st.info("要請がありません。")

        with tabs[5]: # Excel出力
            st.subheader("📥 月間データの書き出し")
            if not df_raw.empty:
                months = sorted(list(set(pd.to_datetime(df_raw["日付"]).dt.strftime("%Y-%m"))), reverse=True)
                sel_m = st.selectbox("出力する月を選択", months)
                df_m = df_raw[pd.to_datetime(df_raw["日付"]).dt.strftime("%Y-%m") == sel_m].copy()
                
                if not df_m.empty:
                    st.dataframe(df_m, hide_index=True, use_container_width=True)
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df_m.to_excel(writer, index=False, sheet_name=f'{sel_m}応援記録')
                    st.download_button(label="📥 Excelファイルを保存", data=output.getvalue(), file_name=f"応援記録_{sel_m}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                else:
                    st.warning("選択した月のデータがありません。")
    else:
        st.warning("スプレッドシートにデータがないか、接続エラーです。")

# --- 2. 各学部 入力モード ---
else:
    df_raw = fetch_data()
    st.subheader(f"➕ 応援依頼の送信")

    # 申請済みプレビュー（ガード処理付き）
    st.markdown('<div class="preview-area"><b>🔍 '+date_str+' の申請済み状況</b>', unsafe_allow_html=True)
    if not df_raw.empty and "日付" in df_raw.columns:
        df_p = df_raw[df_raw["日付"] == date_str]
        if not df_p.empty:
            for _, pr in df_p.iterrows():
                assigned = [pr[f'応援者{i}'] for i in range(1,5) if pr[f'応援者{i}']]
                txt = f"【担当: {' / '.join(assigned)}】" if assigned else "【応援者未定】"
                st.write(f"✅ {pr['学部']} | {pr['対象']} ({pr['開始']}〜{pr['終了']}) {txt}")
        else: st.write("本日の要請はまだありません。")
    else: st.write("申請状況を読み込めませんでした。")
    st.markdown('</div>', unsafe_allow_html=True)

    t_s, t_r = st.tabs(["📍 単発依頼", "🗓️ 期間一括（平日のみ）"])

    with t_s:
        with st.form("single_f", clear_on_submit=True):
            col1, col2 = st.columns(2)
            d_dept = col1.selectbox("学部", ["小学部", "中学部", "高等部"], key="sd")
            d_target = col2.text_input("対象（クラス名・班名）")
            col3, col4, col5 = st.columns(3)
            d_start = col3.time_input("開始時間", datetime.time(9, 0))
            d_end = col4.time_input("終了時間", datetime.time(15, 0))
            d_num = col5.number_input("人数", 1, 10, 1)
            d_memo = st.text_area("詳細理由")
            if st.form_submit_button("📢 応援依頼を送信"):
                p = {"date":date_str, "department":d_dept, "target":d_target, "startTime":d_start.strftime("%H:%M"), "endTime":d_end.strftime("%H:%M"), "count":int(d_num), "notes":d_memo}
                if post_to_gas(p): st.success("送信完了"); st.balloons(); st.rerun()

    with t_r:
        with st.form("range_f", clear_on_submit=True):
            st.info("期間内の「平日」を一括登録します。")
            r1, r2 = st.columns(2)
            s_d = r1.date_input("開始日", datetime.date.today())
            e_d = r2.date_input("終了日", datetime.date.today() + datetime.timedelta(days=5))
            r_dept = st.selectbox("学部", ["小学部", "中学部", "高等部"], key="rd")
            r_target = st.text_input("対象（クラス名・班名）", key="rt")
            c3, c4, c5 = st.columns(3)
            r_start = c3.time_input("開始", datetime.time(9, 0), key="rs")
            r_end = c4.time_input("終了", datetime.time(15, 0), key="re")
            r_num = c5.number_input("人数", 1, 10, 1, key="rn")
            r_memo = st.text_area("詳細理由", key="rm")
            if st.form_submit_button("🗓️ まとめて一括登録"):
                if not r_target: st.error("対象を入力してください")
                else:
                    bulk = []
                    curr = s_d
                    while curr <= e_d:
                        if curr.weekday() < 5:
                            bulk.append({"date":curr.strftime("%Y-%m-%d"), "department":r_dept, "target":r_target, "startTime":r_start.strftime("%H:%M"), "endTime":r_end.strftime("%H:%M"), "count":int(r_num), "notes":r_memo})
                        curr += datetime.timedelta(days=1)
                    if post_to_gas({"rows": bulk}): st.success(f"{len(bulk)}日分の一括登録完了"); st.balloons(); st.rerun()