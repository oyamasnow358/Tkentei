import streamlit as st
import pandas as pd
import requests
import datetime



# --- 設定 ---
GAS_URL = "https://script.google.com/macros/s/AKfycbw8OIWeRd4mdtCArE-xtMOmFr04w6y4sNvX1F-erj2RW8GWX8bLaNDr4Xn06hlMqqfzpA/exec"

st.set_page_config(page_title="総合支援部 応援調整ツール", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans JP', sans-serif; background-color: #f0f4f8; }

    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 2rem; border-radius: 0 0 24px 24px; text-align: center;
        margin-bottom: 2rem; box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    .main-header h1 { color: white !important; font-size: 2.2rem; margin: 0; border: none !important; }
    .main-header p { color: rgba(255,255,255,0.85); margin: 0.5rem 0 0; font-size: 1rem; }

    .stat-card {
        background: white; padding: 1.2rem; border-radius: 14px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.07); text-align: center;
        border-top: 7px solid #1e3a8a; margin-bottom: 1rem;
    }
    .stat-val { font-size: 2.4rem; font-weight: bold; color: #1e3a8a; line-height: 1.2; }
    .stat-label { font-size: 0.95rem; color: #64748b; font-weight: bold; margin-top: 4px; }

    .req-card {
        background: white; padding: 1.2rem 1.5rem; border-radius: 14px;
        margin-bottom: 1rem; border-left: 10px solid #3b82f6;
        box-shadow: 0 3px 8px rgba(0,0,0,0.07);
    }
    .req-title { font-size: 1.15rem; font-weight: bold; color: #1e3a8a; margin: 0; }
    .req-meta { color: #64748b; font-size: 0.9rem; margin-top: 4px; }
    .supporter-box {
        background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px;
        padding: 8px 12px; margin-top: 10px;
    }
    .supporter-header { font-size: 0.8rem; color: #94a3b8; font-weight: bold; margin-bottom: 6px; }
    .supporter-item {
        font-size: 1rem; color: #0369a1; font-weight: bold;
        padding: 4px 0; border-bottom: 1px dashed #e0f2fe;
    }
    .supporter-item:last-child { border-bottom: none; }
    .undecided { color: #94a3b8; font-style: italic; font-size: 0.9rem; }

    .stTabs [data-baseweb="tab-list"] { gap: 8px; background: transparent; }
    .stTabs [data-baseweb="tab"] {
        background: white; border-radius: 8px 8px 0 0;
        padding: 8px 18px; font-weight: bold; border: 1px solid #e2e8f0;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1e3a8a !important; color: white !important;
    }

    .stButton > button {
        width: 100%; border-radius: 10px; height: 3.2rem;
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        color: white; font-weight: bold; font-size: 1rem; border: none;
    }
    </style>
""", unsafe_allow_html=True)


# ============================================================
# データ取得・送信
# ============================================================

def fetch_data():
    try:
        res = requests.get(f"{GAS_URL}?t={datetime.datetime.now().timestamp()}", timeout=10)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            if not df.empty:
                df.columns = [c.strip() for c in df.columns]
                df["人数"] = pd.to_numeric(df["人数"], errors="coerce").fillna(0).astype(int)
                # 応援者・時間列が存在しない場合に空文字で補完
                for i in range(1, 5):
                    for col in [f"応援者{i}", f"時間{i}"]:
                        if col not in df.columns:
                            df[col] = ""
                        else:
                            df[col] = df[col].fillna("").astype(str)
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"データ取得エラー: {e}")
        return pd.DataFrame()

def post_to_gas(payload):
    try:
        res = requests.post(GAS_URL, json=payload, timeout=10)
        return res.status_code == 200
    except:
        return False


# ============================================================
# 応援者表示コンポーネント（ここが核心）
# ============================================================

def show_supporters_native(row):
    """
    st.write を使って応援者1〜4を確実に縦に並べて表示する。
    HTMLに頼らないため、省略・非表示が起こらない。
    """
    items = []
    for i in range(1, 5):
        name = str(row.get(f"応援者{i}", "")).strip()
        time = str(row.get(f"時間{i}", "")).strip()
        if name:
            label = f"👤 {name}"
            if time:
                label += f"　（{time}）"
            items.append(label)

    if items:
        for item in items:
            st.write(item)
    else:
        st.caption("（未定）")


def render_request_cards(data_df):
    """
    応援要請を1件ずつカードとして表示。
    応援者はst.writeで縦に並べることで省略なし表示を保証。
    """
    if data_df.empty:
        st.info("該当する応援要請はありません。")
        return

    DEPT_COLOR = {"小学部": "#10b981", "中学部": "#f59e0b", "高等部": "#3b82f6"}

    for _, row in data_df.sort_values("開始").iterrows():
        color = DEPT_COLOR.get(row["学部"], "#6366f1")

        # カードの枠をHTMLで描く（中身はStreamlitネイティブ）
        st.markdown(f"""
            <div class="req-card" style="border-left-color:{color};">
                <p class="req-title">
                    <span style="background:{color}; color:white; padding:2px 10px; border-radius:5px; font-size:0.8rem;">{row['学部']}</span>
                    　{row['対象']}　<span style="font-size:0.95rem; color:#64748b;">（必要: {row['人数']}名）</span>
                </p>
                <p class="req-meta">⏰ {row['開始']} 〜 {row['終了']}　｜　備考: {row['備考']}</p>
                <div class="supporter-box">
                    <div class="supporter-header">▼ 応援担当者</div>
            </div></div>
        """, unsafe_allow_html=True)

        # ↑ HTMLカードの「中」にはStreamlit要素を入れられないため、
        # カードの「直後」にst.writeで応援者を表示する。
        # 視覚的に近接させることで一体感を出す。
        with st.container():
            cols = st.columns([0.05, 0.95])
            with cols[1]:
                items = []
                for i in range(1, 5):
                    name = str(row.get(f"応援者{i}", "")).strip()
                    time = str(row.get(f"時間{i}", "")).strip()
                    if name:
                        items.append(f"👤 **{name}**　{time}")
                if items:
                    for item in items:
                        st.write(item)
                else:
                    st.caption("（未定）")
        st.divider()


# ============================================================
# ヘッダー
# ============================================================

st.markdown("""
    <div class="main-header">
        <h1>🛡️ 総合支援部 応援調整ツール</h1>
        <p>全学部の状況を俯瞰し、最適な人員配置を支援する司令塔</p>
    </div>
""", unsafe_allow_html=True)


# ============================================================
# サイドバー
# ============================================================

with st.sidebar:
    st.markdown("### ⚙️ メニュー")
    app_mode = st.radio("画面切替", ["📊 総合支援部（管理画面）", "➕ 各学部（応援依頼入力）"])
    st.divider()
    target_date = st.date_input("📅 対象日", datetime.date.today())
    date_str = target_date.strftime("%Y-%m-%d")
    st.info(f"選択日: {target_date.strftime('%Y/%m/%d')}")
    st.divider()
    if st.button("🔄 最新情報に更新"):
        st.rerun()


# ============================================================
# 総合支援部 管理画面
# ============================================================

if app_mode == "📊 総合支援部（管理画面）":
    df_raw = fetch_data()

    if df_raw.empty or "日付" not in df_raw.columns:
        st.warning("データがありません。スプレッドシートとGAS URLを確認してください。")
        st.stop()

    df = df_raw[df_raw["日付"] == date_str].copy()

    # --- 統計カード ---
    sums = df.groupby("学部")["人数"].sum().reindex(["小学部", "中学部", "高等部"], fill_value=0)
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="stat-card" style="border-top-color:#10b981"><div class="stat-label">小学部 必要数</div><div class="stat-val">{sums["小学部"]}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="stat-card" style="border-top-color:#f59e0b"><div class="stat-label">中学部 必要数</div><div class="stat-val">{sums["中学部"]}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="stat-card" style="border-top-color:#3b82f6"><div class="stat-label">高等部 必要数</div><div class="stat-val">{sums["高等部"]}</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="stat-card" style="border-top-color:#6366f1"><div class="stat-label">全体合計</div><div class="stat-val">{int(sums.sum())}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- タブ ---
    tab_all, tab_e, tab_m, tab_h, tab_assign = st.tabs([
        "🌎 全体俯瞰", "🐥 小学部", "🏃 中学部", "🎓 高等部", "✍️ 応援者を割り当てる"
    ])

    with tab_all:
        st.subheader(f"📋 {target_date.strftime('%m/%d')} 全体タイムライン")
        render_request_cards(df)

    with tab_e:
        st.subheader("🐥 小学部 詳細")
        render_request_cards(df[df["学部"] == "小学部"])

    with tab_m:
        st.subheader("🏃 中学部 詳細")
        render_request_cards(df[df["学部"] == "中学部"])

    with tab_h:
        st.subheader("🎓 高等部 詳細")
        render_request_cards(df[df["学部"] == "高等部"])

    with tab_assign:
        st.subheader("✍️ 応援者の割り当て入力")
        if df.empty:
            st.info("この日の応援要請はありません。")
        else:
            df["selector"] = df["学部"] + " ｜ " + df["対象"] + "（" + df["開始"] + "〜）"
            selected_label = st.selectbox("編集する要請を選択してください", df["selector"].tolist())
            target_row = df[df["selector"] == selected_label].iloc[0]

            st.info(f"📍 編集対象：{selected_label}")

            with st.form("assignment_form"):
                st.markdown("#### 応援者と担当時間を入力")
                col_a, col_b = st.columns(2)

                s1 = col_a.text_input("応援者1 氏名", value=target_row.get("応援者1", ""))
                t1 = col_b.text_input("時間1（例: 9:00〜10:30）", value=target_row.get("時間1", ""))

                s2 = col_a.text_input("応援者2 氏名", value=target_row.get("応援者2", ""))
                t2 = col_b.text_input("時間2", value=target_row.get("時間2", ""))

                s3 = col_a.text_input("応援者3 氏名", value=target_row.get("応援者3", ""))
                t3 = col_b.text_input("時間3", value=target_row.get("時間3", ""))

                s4 = col_a.text_input("応援者4 氏名", value=target_row.get("応援者4", ""))
                t4 = col_b.text_input("時間4", value=target_row.get("時間4", ""))

                if st.form_submit_button("💾 この内容でスプレッドシートに保存する"):
                    payload = {
                        "action": "updateSupporters",
                        "date":       str(target_row["日付"]),
                        "department": str(target_row["学部"]),
                        "target":     str(target_row["対象"]),
                        "startTime":  str(target_row["開始"]),
                        "s1": s1, "t1": t1,
                        "s2": s2, "t2": t2,
                        "s3": s3, "t3": t3,
                        "s4": s4, "t4": t4,
                    }
                    if post_to_gas(payload):
                        st.success("✅ スプレッドシートを更新しました！")
                        st.rerun()
                    else:
                        st.error("❌ 更新に失敗しました。GAS URLとネットワークを確認してください。")


# ============================================================
# 各学部 応援依頼入力画面
# ============================================================

else:
    st.subheader(f"➕ {target_date.strftime('%m月%d日')} の新規応援依頼")

    with st.form("req_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        d_in = col1.selectbox("依頼元の学部", ["小学部", "中学部", "高等部"])
        t_in = col2.text_input("対象（クラス・作業班・場所）", placeholder="例: 1年1組 / 農耕班")

        col3, col4, col5 = st.columns(3)
        s_in = col3.time_input("開始時間", datetime.time(9, 0))
        e_in = col4.time_input("終了時間", datetime.time(15, 0))
        n_in = col5.number_input("必要人数", min_value=1, max_value=10, value=1)

        m_in = st.text_area("詳細・備考（理由など）", placeholder="例: 担任が急な病欠のため補助をお願いします。")

        if st.form_submit_button("📢 応援要請を送信する"):
            if not t_in:
                st.error("「対象」を入力してください。")
            else:
                payload = {
                    "date":        date_str,
                    "department":  d_in,
                    "target":      t_in,
                    "startTime":   s_in.strftime("%H:%M"),
                    "endTime":     e_in.strftime("%H:%M"),
                    "count":       int(n_in),
                    "notes":       m_in,
                }
                if post_to_gas(payload):
                    st.success("✅ 送信完了しました。総合支援部で確認されます。")
                    st.balloons()
                else:
                    st.error("❌ 送信に失敗しました。ネットワークを確認してください。")
