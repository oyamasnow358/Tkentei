import streamlit as st
import pandas as pd
import requests
import datetime
import io

# --- 必須ライブラリチェック ---
try:
    import openpyxl
except ImportError:
    st.error("ライブラリ 'openpyxl' が見つかりません。'pip install openpyxl' を実行してください。")

# --- 設定 ---
GAS_URL = "https://script.google.com/macros/s/AKfycbxNZkAWgYliW9i_UJyBNs3kjF4Zi3PGKlD3n95c1_NQY6uRy33i9InflnUQaUFs7YlT/exec"

st.set_page_config(page_title="総合支援部 応援調整ツール", layout="wide", initial_sidebar_state="expanded")

# --- デザインCSS ---
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
        background: white; padding: 15px; border-radius: 10px; margin-bottom: 10px;
        border-left: 10px solid #1e3a8a; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .supporter-list {
        background: #f0f9ff; padding: 10px; border-radius: 8px; margin-top: 8px; border: 1px solid #bae6fd;
    }
    .supporter-item { font-size: 0.95rem; color: #0369a1; font-weight: bold; margin-bottom: 4px; }
    .preview-area {
        background: white; border: 1px solid #e2e8f0; border-radius: 10px; padding: 15px; margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- データ取得・送信関数 ---
def fetch_data():
    try:
        res = requests.get(f"{GAS_URL}?t={datetime.datetime.now().timestamp()}", timeout=10)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            if not df.empty:
                df.columns = [c.strip() for c in df.columns]
                df["人数"] = pd.to_numeric(df["人数"], errors='coerce').fillna(0).astype(int)
                return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"データ取得失敗: {e}")
        return pd.DataFrame()

def post_to_gas(payload):
    try:
        res = requests.post(GAS_URL, json=payload, timeout=15)
        return res.status_code == 200
    except Exception as e:
        st.error(f"送信失敗: {e}")
        return False

# --- メインヘッダー ---
st.markdown('<div class="main-header"><h1>🛡️ 総合支援部 応援調整ツール</h1></div>', unsafe_allow_html=True)

# --- サイドバー ---
with st.sidebar:
    st.markdown("### ⚙️ メニュー")
    app_mode = st.radio("表示画面切替", ["📊 総合支援部（管理・俯瞰）", "➕ 応援依頼（各学部用入力）"])
    st.divider()
    target_date = st.date_input("📅 対象日選択", datetime.date.today())
    date_str = target_date.strftime("%Y-%m-%d")
    st.write(f"**選択日:** {target_date.strftime('%Y/%m/%d')}")
    st.divider()
    if st.button("🔄 画面情報を更新する", use_container_width=True):
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
        t_all, t_e, t_m, t_h, t_assign, t_excel = st.tabs(["🌎 全体俯瞰", "🐥 小学部", "🏃 中学部", "🎓 高等部", "✍️ 応援者割当", "📥 Excel出力"])

        def render_cards(data_df):
            if data_df.empty:
                st.info("応援要請はありません。")
                return
            for _, row in data_df.sort_values("開始").iterrows():
                color = "#10b981" if row['学部']=="小学部" else "#f59e0b" if row['学部']=="中学部" else "#3b82f6"
                supporters = []
                for i in range(1, 5):
                    name = row.get(f'応援者{i}', '').strip()
                    time = row.get(f'時間{i}', '').strip()
                    if name: supporters.append(f"👤 {name} ({time if time else '終日'})")
                
                supporter_html = "".join([f'<div class="supporter-item">{s}</div>' for s in supporters]) if supporters else '<div style="color:#94a3b8">（未定）</div>'
                
                st.markdown(f"""
                    <div class="req-card" style="border-left-color:{color}">
                        <div style="display:flex; justify-content:space-between; font-weight:bold; color:#1e3a8a;">
                            <span>{row['学部']} | {row['対象']}</span>
                            <span>⏰ {row['開始']} 〜 {row['終了']} (必要:{row['人数']}名)</span>
                        </div>
                        <div style="font-size:0.85rem; color:#64748b; margin: 5px 0;">📝 {row['備考']}</div>
                        <div class="supporter-list">
                            <div style="font-size:0.75rem; color:#64748b; margin-bottom:4px; font-weight:bold;">【応援担当者】</div>
                            {supporter_html}
                        </div>
                    </div>
                """, unsafe_allow_html=True)

        with t_all: render_cards(df_today)
        with t_e: render_cards(df_today[df_today["学部"]=="小学部"])
        with t_m: render_cards(df_today[df_today["学部"]=="中学部"])
        with t_h: render_cards(df_today[df_today["学部"]=="高等部"])

        with t_assign:
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
                        if post_to_gas(p): st.success("保存しました！"); st.rerun()
            else: st.info("要請がありません。")

        with t_excel:
            st.subheader("📊 月間集計エクセル出力")
            months = sorted(list(set(pd.to_datetime(df_raw["日付"]).dt.strftime("%Y-%m"))), reverse=True)
            sel_m = st.selectbox("対象月を選択", months)
            df_m = df_raw[pd.to_datetime(df_raw["日付"]).dt.strftime("%Y-%m") == sel_m].copy()
            st.dataframe(df_m, hide_index=True, use_container_width=True)
            
            output = io.BytesIO()
            try:
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_m.to_excel(writer, index=False, sheet_name='応援状況一覧')
                st.download_button(label="📥 Excelをダウンロード", data=output.getvalue(), file_name=f"応援集計_{sel_m}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            except Exception as e:
                st.error(f"Excel生成エラー: {e}")

    else: st.warning("データが見つかりません。")

# --- 2. 各学部 入力モード ---
else:
    df_raw = fetch_data()
    st.subheader(f"➕ 応援依頼の送信")

    # 1. 申請済みプレビュー（これが非常に重要）
    st.markdown('<div class="preview-area"><b>🔍 本日（'+date_str+'）の申請済み状況</b>', unsafe_allow_html=True)
    df_p = df_raw[df_raw["日付"] == date_str]
    if not df_p.empty:
        for _, pr in df_p.iterrows():
            s_assigned = [pr[f'応援者{i}'] for i in range(1,5) if pr[f'応援者{i}']]
            s_txt = f"【担当: {' / '.join(s_assigned)}】" if s_assigned else "【応援者未定】"
            st.write(f"✅ {pr['学部']} | {pr['対象']} ({pr['開始']}〜{pr['終了']}) {s_txt}")
    else: st.write("まだ本日の要請はありません。")
    st.markdown('</div>', unsafe_allow_html=True)

    tab_single, tab_range = st.tabs(["📍 単発（1日のみ）", "🗓️ 期間（まとめて一括）"])

    with tab_single:
        with st.form("single_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            d_dept = col1.selectbox("依頼元の学部", ["小学部", "中学部", "高等部"], key="sd")
            d_target = col2.text_input("対象（クラス・班名）", placeholder="例: 1年2組 / 木工班")
            col3, col4, col5 = st.columns(3)
            d_start = col3.time_input("開始時間", datetime.time(9, 0), key="ss")
            d_end = col4.time_input("終了時間", datetime.time(15, 0), key="se")
            d_num = col5.number_input("人数", 1, 10, 1, key="sn")
            d_memo = st.text_area("詳細理由", placeholder="担任不在のため見守り補助希望")
            if st.form_submit_button("📢 応援依頼を送信"):
                p = {"date":date_str, "department":d_dept, "target":d_target, "startTime":d_start.strftime("%H:%M"), "endTime":d_end.strftime("%H:%M"), "count":int(d_num), "notes":d_memo}
                if post_to_gas(p): st.success("送信完了しました！"); st.balloons(); st.rerun()

    with tab_range:
        with st.form("range_form", clear_on_submit=True):
            st.info("指定期間内の「平日のみ」自動で毎日登録します。")
            r_col1, r_col2 = st.columns(2)
            start_d = r_col1.date_input("開始日", datetime.date.today())
            end_d = r_col2.date_input("終了日", datetime.date.today() + datetime.timedelta(days=5))
            
            r_d1, r_d2 = st.columns(2)
            r_dept = r_d1.selectbox("学部", ["小学部", "中学部", "高等部"], key="rd")
            r_target = r_d2.text_input("対象（クラス・班名）", key="rt")
            r_d3, r_d4, r_d5 = st.columns(3)
            r_start = r_d3.time_input("開始", datetime.time(9, 0), key="rs")
            r_end = r_d4.time_input("終了", datetime.time(15, 0), key="re")
            r_num = r_d5.number_input("人数", 1, 10, 1, key="rn")
            r_memo = st.text_area("詳細理由", key="rm")
            
            if st.form_submit_button("🗓️ 期間内の平日をすべて一括登録"):
                if not r_target: st.error("対象を入力してください")
                else:
                    bulk_rows = []
                    curr = start_d
                    while curr <= end_d:
                        if curr.weekday() < 5: # 土日除外
                            bulk_rows.append({"date":curr.strftime("%Y-%m-%d"), "department":r_dept, "target":r_target, "startTime":r_start.strftime("%H:%M"), "endTime":r_end.strftime("%H:%M"), "count":int(r_num), "notes":r_memo})
                        curr += datetime.timedelta(days=1)
                    if post_to_gas({"rows": bulk_rows}):
                        st.success(f"{len(bulk_rows)}日分の一括登録が完了しました！")
                        st.balloons(); st.rerun()