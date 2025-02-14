import streamlit as st
import pandas as pd
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.font_manager as fm

# 日本語フォントの設定（フォントは同じフォルダ内のものを使用）
font_path = "ipaexg.ttf"  # フォントのファイル名を正しく指定
font_prop = fm.FontProperties(fname=font_path)
plt.rcParams["font.family"] = font_prop.get_name()

# Streamlit アプリのタイトル
st.title("t検定 Web アプリ")

# 説明の追加
st.markdown("""
### 📌 t検定とは？
t検定は **2つのグループの平均値に有意な差があるか** を検定する方法です。  
例えば、「薬を飲んだグループ」と「飲まなかったグループ」で血圧に違いがあるかを調べるときに使います。

### 📊 このアプリの使い方
1. CSVファイルをアップロードする（2つのグループのデータを用意）
2. 比較する2つのグループの列を選択する
3. t検定の結果を確認する（p値が **0.05未満** なら「統計的に有意な差がある」と判断）
""")

# CSVテンプレートのダウンロード
st.markdown("### 📥 CSVテンプレートのダウンロード")
template_csv = """グループ1,グループ2
55,60
62,58
53,65
61,59
66,63
"""
st.download_button(
    label="CSVテンプレートをダウンロード",
    data=template_csv.encode('utf-8-sig'),
    file_name="t_test_template.csv",
    mime="text/csv"
)

# CSVファイルのアップロード
st.sidebar.header("データのアップロード")
uploaded_file = st.sidebar.file_uploader("CSVファイルをアップロード", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write("### アップロードされたデータ")
    st.dataframe(df.head())
    
    # グループと数値データの選択
    group_col = st.sidebar.selectbox("グループを表す列を選択", df.columns)
    value_col = st.sidebar.selectbox("比較する数値データの列を選択", df.columns)
    
    if group_col and value_col:
        groups = df[group_col].unique()
        if len(groups) != 2:
            st.error("t検定は2つのグループのみ比較できます。グループ数を確認してください。")
        else:
            group1 = df[df[group_col] == groups[0]][value_col].dropna()
            group2 = df[df[group_col] == groups[1]][value_col].dropna()
            
            # t検定の実行
            t_stat, p_value = stats.ttest_ind(group1, group2)
            
            # 結果の表示
            st.subheader("t検定の結果")
            st.write(f"t値: {t_stat:.4f}")
            st.write(f"p値: {p_value:.4f}")
            
            if p_value < 0.05:
                st.success("この結果は統計的に有意です (p < 0.05)！")
            else:
                st.info("統計的に有意な差はありません (p ≥ 0.05)")
            
            # ヒストグラムの描画
            fig, ax = plt.subplots()
            sns.histplot(group1, label=f'{groups[0]}', color='blue', kde=True, ax=ax)
            sns.histplot(group2, label=f'{groups[1]}', color='red', kde=True, ax=ax)
            
            ax.set_xlabel("値", fontproperties=font_prop)
            ax.set_ylabel("頻度", fontproperties=font_prop)
            ax.set_title("t検定の比較結果", fontproperties=font_prop)
            ax.legend()
            
            st.pyplot(fig)
            
            # 検定の解釈を追加
            st.markdown("""
            ### 結果の解釈
            - **t値** が大きいほど、2つのグループの平均が異なる可能性が高い。
            - **p値** が **0.05未満** の場合、2つのグループに統計的な差があると判断。
            - **p値が0.05以上** の場合、「偶然の誤差による差」と考えられる。
            """)