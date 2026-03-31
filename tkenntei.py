import streamlit as st
import pandas as pd
import requests
import datetime

# --- 設定 ---
GAS_URL = "https://script.google.com/macros/s/AKfycbx8zdcF31wtnoD6sS7QcDHSvWh9NMV5zvR-3W1mUsOErcAU8b4Xgz_2M2iyFM3xfjdbmw/exec"

# ページ設定
st.set_page_config(page_title="総合支援部 応援調整ツール", layout="wide", initial_sidebar_state="expanded")

# --- 究極のカスタムCSS（デザインの肝） ---
st.markdown("""
    <style>
    /* 全体の背景とフォント */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans JP', sans-serif; background-color: #f0f2f5; }
    
    /* ヘッダーデザイン */
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 2rem;
        border-radius: 0 0 20px 20px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .main-header h1 { font-size: 2.2rem; margin-bottom: 0.5rem; color: white !important; border: none !important; }
    
    /* 統計カードのデザイン */
    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-top: 8px solid #1e3a8a;
        text-align: center;
        transition: transform 0.2s;
    }
    .stat-card:hover { transform: translateY(-5px); }
    .stat-val { font-size: 2.5rem; font-weight: bold; color: #1e3a8a; }
    .stat-label { font-size: 1rem; color: #64748b; font-weight: bold; }
    
    /* 学部別カラー表示 */
    .elem { border-top-color: #10b981 !important; } /* 緑 */
    .mid { border-top-color: #f59e0b !important; }  /* オレンジ */
    .high { border-top-color: #3b82f6 !important; } /* 青 */
    .total { border-top-color: #6366f1 !important; } /* 紫 */

    /* タブのデザイン */
    .stTabs [data-baseweb="tab-list"] { background-color: transparent; gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: white; border-radius: 10px 10px 0 0; 
        padding: 10px 20px; font-weight: bold; border: 1px solid #e2e8f0;
    }
    .stTabs [aria-selected="true"] { background-color: #1e3a8a !important; color: white !important; }

    /* 入力フォームの装飾 */
    .stForm { background: white; padding: 2rem; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); border: none; }
    
    /* ボタン */
    .stButton>button {
        width: 100%; border-radius: 12px; height: 3.5rem; 
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        color: white; font-weight: bold; font-size: 1.1rem; border: none; transition: 0.3s;
    }
    .stButton>button:hover { opacity: 0.9; transform: scale(1.02); }
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
    except:
        return pd.DataFrame()

# --- タイトルヘッダー ---
st.markdown("""
    <div class="main-header">
        <h1>🛡️ 総合支援部 応援調整ツール</h1>
        <p>特別支援学校の円滑な教育活動のために</p>
    </div>
    """, unsafe_allow_html=True)

# --- サイドバー構成 ---
with st.sidebar:
    st.markdown("### 🛠️ 操作パネル")
    app_mode = st.radio("表示モードを選択", ["📊 総合支援部（管理画面）", "➕ 各学部（応援依頼入力）"])
    st.divider()
    target_date = st.date_input("📅 調整対象日", datetime.date.today())
    date_str = target_date.strftime("%Y-%m-%d")
    st.info(f"現在、{target_date.strftime('%m月%d日')} のデータを操作しています。")

# --- メインコンテンツ ---

if app_mode == "📊 総合支援部（管理画面）":
    df_raw = fetch_data()
    
    if not df_raw.empty and "日付" in df_raw.columns:
        df = df_raw[df_raw["日付"] == date_str].copy()
        
        # 1. 統計カード（scoreboard）
        sum_e = int(df[df["学部"]=="小学部"]["人数"].sum())
        sum_m = int(df[df["学部"]=="中学部"]["人数"].sum())
        sum_h = int(df[df["学部"]=="高等部"]["人数"].sum())
        total = sum_e + sum_m + sum_h

        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f'<div class="stat-card elem"><div class="stat-label">小学部 要員</div><div class="stat-val">{sum_e}</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="stat-card mid"><div class="stat-label">中学部 要員</div><div class="stat-val">{sum_m}</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="stat-card high"><div class="stat-label">高等部 要員</div><div class="stat-val">{sum_h}</div></div>', unsafe_allow_html=True)
        with c4: st.markdown(f'<div class="stat-card total"><div class="stat-label">全学部 合計</div><div class="stat-val">{total}</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 2. 詳細表示エリア
        st.subheader("📋 応援要請・タイムライン詳細")
        tab_all, tab_e, tab_m, tab_h = st.tabs(["🌎 全学部一括 ", "🐥 小学部", "🏃 中学部", "🎓 高等部"])
        
        with tab_all:
            if not df.empty:
                # 時間順に並べて見やすく
                st.dataframe(df.sort_values("開始")[["学部", "対象", "開始", "終了", "人数", "備考"]], 
                             use_container_width=True, hide_index=True)
            else:
                st.info("本日の応援要請はありません。")
                
        with tab_e: st.dataframe(df[df["学部"]=="小学部"][["対象", "開始", "終了", "人数", "備考"]], use_container_width=True, hide_index=True)
        with tab_m: st.dataframe(df[df["学部"]=="中学部"][["対象", "開始", "終了", "人数", "備考"]], use_container_width=True, hide_index=True)
        with tab_h: st.dataframe(df[df["学部"]=="高等部"][["対象", "開始", "終了", "人数", "備考"]], use_container_width=True, hide_index=True)
        
    else:
        st.warning("データがありません。スプレッドシートを確認してください。")

    if st.button("🔄 最新の情報に更新（8:30 最終確認用）"):
        st.rerun()

else:
    # 応援依頼入力画面
    st.subheader(f"➕ {target_date.strftime('%m月%d日')} の応援依頼")
    with st.form("input_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        dept = col1.selectbox("依頼元の学部", ["小学部", "中学部", "高等部"])
        target = col2.text_input("場所・対象（クラス・作業班名）", placeholder="例: 1年2組 / 陶芸班")
        
        col3, col4, col5 = st.columns(3)
        s_time = col3.time_input("開始", datetime.time(9, 0))
        e_time = col4.time_input("終了", datetime.time(15, 0))
        num = col5.number_input("必要人数", 1, 10, 1)
        
        notes = st.text_area("具体的な理由・備考", placeholder="例: 急な欠員のため、見守りをお願いします。")
        
        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("📢 応援要請を送信する")
        
        if submitted:
            if not target:
                st.error("「対象」を入力してください。")
            else:
                payload = {
                    "date": date_str, "department": dept, "target": target,
                    "startTime": s_time.strftime("%H:%M"), "endTime": e_time.strftime("%H:%M"),
                    "count": num, "notes": notes
                }
                if requests.post(GAS_URL, json=payload).status_code == 200:
                    st.success("送信完了しました。総合支援部で確認されます。")
                    st.balloons()
                else:
                    st.error("送信エラー。ネットワークを確認してください。")