import streamlit as st
import pandas as pd
import requests
import datetime

# --- 1. アプリ設定 ---
GAS_URL = "https://script.google.com/macros/s/AKfycbxms40qgOEVxYAMJCXa-zU5IJDcpX2cSBhgzKaYxId_8TtQeuz_EUYIQS6eGpZ0CAyh0g/exec"

st.set_page_config(page_title="総合支援部 応援調整ツール", layout="wide", initial_sidebar_state="expanded")

# --- 2. 究極のカスタムデザインCSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans JP', sans-serif; background-color: #f4f7f9; }
    
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 2rem; border-radius: 0 0 25px 25px; color: white; text-align: center;
        margin-bottom: 2rem; box-shadow: 0 10px 20px rgba(0,0,0,0.15);
    }
    .main-header h1 { color: white !important; font-size: 2.5rem; margin-bottom: 0.5rem; border: none; }
    
    .stat-card {
        background: white; padding: 1.5rem; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        text-align: center; border-top: 8px solid #1e3a8a;
    }
    .stat-val { font-size: 2.8rem; font-weight: bold; color: #1e3a8a; }
    .stat-label { font-size: 1.1rem; color: #64748b; font-weight: bold; }
    
    .supporter-box {
        background-color: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px;
        padding: 8px; margin-bottom: 5px; font-size: 0.9rem; color: #0369a1;
    }
    
    .stButton>button {
        width: 100%; border-radius: 12px; height: 3.5rem; 
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        color: white; font-weight: bold; font-size: 1.1rem; border: none; transition: 0.3s;
    }
    .stTabs [aria-selected="true"] { background-color: #1e3a8a !important; color: white !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. データ操作ロジック ---
def fetch_data():
    try:
        # キャッシュを回避するためにタイムスタンプを付与
        res = requests.get(f"{GAS_URL}?t={datetime.datetime.now().timestamp()}")
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            if not df.empty:
                df.columns = [c.strip() for c in df.columns]
                # 人数を計算用に数値化
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

# --- 4. メインヘッダー表示 ---
st.markdown("""
    <div class="main-header">
        <h1>🛡️ 総合支援部 応援調整ツール</h1>
        <p>特別支援学校：本日（および未来）の教育活動を支える司令塔</p>
    </div>
    """, unsafe_allow_html=True)

# --- 5. サイドバー ---
with st.sidebar:
    st.markdown("### ⚙️ システム設定")
    app_mode = st.radio("画面切り替え", ["📊 総合支援部（管理・俯瞰）", "➕ 応援依頼を入力（各学部）"])
    st.divider()
    target_date = st.date_input("📅 調整対象日", datetime.date.today())
    date_str = target_date.strftime("%Y-%m-%d")
    st.info(f"対象日: {target_date.strftime('%Y/%m/%d')}")

# --- 6. 総合支援部 モード ---
if app_mode == "📊 総合支援部（管理・俯瞰）":
    df_raw = fetch_data()
    
    if not df_raw.empty and "日付" in df_raw.columns:
        # 選択された日付のデータのみ抽出
        df = df_raw[df_raw["日付"] == date_str].copy()
        
        # サマリーカード表示
        sum_e = int(df[df["学部"]=="小学部"]["人数"].sum())
        sum_m = int(df[df["学部"]=="中学部"]["人数"].sum())
        sum_h = int(df[df["学部"]=="高等部"]["人数"].sum())
        
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f'<div class="stat-card" style="border-top-color:#10b981"><div class="stat-label">小学部</div><div class="stat-val">{sum_e}</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="stat-card" style="border-top-color:#f59e0b"><div class="stat-label">中学部</div><div class="stat-val">{sum_m}</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="stat-card" style="border-top-color:#3b82f6"><div class="stat-label">高等部</div><div class="stat-val">{sum_h}</div></div>', unsafe_allow_html=True)
        with c4: st.markdown(f'<div class="stat-card" style="border-top-color:#6366f1"><div class="stat-label">全体合計</div><div class="stat-val">{sum_e+sum_m+sum_h}</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # タブ切り替え
        tab_view, tab_assign = st.tabs(["🌎 応援状況を一括表示", "✍️ 応援者を割り当てる"])

        with tab_view:
            if not df.empty:
                # 応援者1〜4、時間1〜4をすべて結合して表示するロジック
                def combine_supporters(row):
                    s_list = []
                    for i in range(1, 5):
                        name = row.get(f'応援者{i}', '').strip()
                        time = row.get(f'時間{i}', '').strip()
                        if name:
                            s_list.append(f"👤 {name} ({time if time else '終日'})")
                    return "\n".join(s_list) if s_list else "（未定）"

                view_df = df.copy()
                view_df["応援担当者割り当て"] = view_df.apply(combine_supporters, axis=1)
                
                # 表示用にテーブル化
                st.subheader(f"📋 {target_date.strftime('%m/%d')} の応援要請リスト")
                st.table(view_df.sort_values("開始")[["学部", "対象", "開始", "終了", "人数", "応援担当者割り当て", "備考"]])
            else:
                st.info(f"{date_str} の応援要請はありません。")

        with tab_assign:
            st.subheader("応援者の詳細割り当て")
            if not df.empty:
                # どの要請を編集するか選択
                df['selector'] = df['学部'] + " | " + df['対象'] + " (" + df['開始'] + "~)"
                target_label = st.selectbox("編集する要請を選んでください", df['selector'].tolist())
                target_row = df[df['selector'] == target_label].iloc[0]

                with st.form("edit_supporters_form"):
                    st.info(f"【対象要請】 {target_label}")
                    
                    # 4人分の名前と時間を入力するグリッド
                    col_a, col_b = st.columns(2)
                    s1 = col_a.text_input("応援者1 氏名", value=target_row.get('応援者1', ''))
                    t1 = col_b.text_input("時間1 (例 9:15-10:00)", value=target_row.get('時間1', ''))
                    
                    col_c, col_d = st.columns(2)
                    s2 = col_c.text_input("応援者2 氏名", value=target_row.get('応援者2', ''))
                    t2 = col_d.text_input("時間2", value=target_row.get('時間2', ''))
                    
                    col_e, col_f = st.columns(2)
                    s3 = col_e.text_input("応援者3 氏名", value=target_row.get('応援者3', ''))
                    t3 = col_f.text_input("時間3", value=target_row.get('時間3', ''))
                    
                    col_g, col_h = st.columns(2)
                    s4 = col_g.text_input("応援者4 氏名", value=target_row.get('応援者4', ''))
                    t4 = col_h.text_input("時間4", value=target_row.get('時間4', ''))
                    
                    if st.form_submit_button("応援担当情報を確定して保存"):
                        update_payload = {
                            "action": "updateSupporters",
                            "date": target_row['日付'],
                            "department": target_row['学部'],
                            "target": target_row['対象'],
                            "startTime": target_row['開始'],
                            "s1": s1, "t1": t1, "s2": s2, "t2": t2,
                            "s3": s3, "t3": t3, "s4": s4, "t4": t4
                        }
                        if post_to_gas(update_payload):
                            st.success("スプレッドシートを更新しました。")
                            st.rerun()
                        else:
                            st.error("更新に失敗しました。")
            else:
                st.write("対象となる要請がありません。")

# --- 7. 各学部 入力モード ---
else:
    st.subheader(f"➕ {target_date.strftime('%m月%d日')} の新規応援依頼")
    with st.container():
        with st.form("new_request_form", clear_on_submit=True):
            f_col1, f_col2 = st.columns(2)
            req_dept = f_col1.selectbox("自分の学部", ["小学部", "中学部", "高等部"])
            req_target = f_col2.text_input("対象（クラス・作業班・学年など）", placeholder="例: 1年1組 / 農耕班")
            
            f_col3, f_col4, f_col5 = st.columns(3)
            req_start = f_col3.time_input("開始", datetime.time(9, 0))
            req_end = f_col4.time_input("終了", datetime.time(15, 0))
            req_num = f_col5.number_input("必要な人数", 1, 10, 1)
            
            req_notes = st.text_area("詳細・備考", placeholder="例: 急な欠員のため、見守り補助をお願いします。")
            
            if st.form_submit_button("📢 応援要請を送信する"):
                if not req_target:
                    st.error("「対象」を入力してください。")
                else:
                    new_payload = {
                        "date": date_str,
                        "department": req_dept,
                        "target": req_target,
                        "startTime": req_start.strftime("%H:%M"),
                        "endTime": req_end.strftime("%H:%M"),
                        "count": int(req_num),
                        "notes": req_notes
                    }
                    if post_to_gas(new_payload):
                        st.success(f"要請を送信しました。対象日: {date_str}")
                        st.balloons()
                    else:
                        st.error("送信に失敗しました。")

# 更新ボタン（共通）
st.sidebar.write("---")
if st.sidebar.button("🔄 最新の情報に更新"):
    st.rerun()