import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os

# 日本語フォントの設定（同じフォルダにあるフォントを使用）
font_path = "./your_font.ttf"  # 必要に応じて修正してください
plt.rcParams['font.family'] = font_path

# Streamlit アプリのタイトル
st.title("t検定 Web アプリ")

# 説明を追加
st.markdown("""
### t検定とは？
- **t検定** は、2つのグループの平均値が統計的に異なるかを検定する方法です。
- 例えば、「薬を飲んだグループ」と「飲まなかったグループ」の成績を比較する場合に使われます。
- 検定の結果、p値が **0.05未満** であれば「有意差あり」と判断できます。
""")

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
            
            ax.set_xlabel("値")
            ax.set_ylabel("頻度")
            ax.set_title("t検定の比較結果")
            ax.legend()
            
            st.pyplot(fig)
            
            # 検定の解釈を追加
            st.markdown("""
            ### 結果の解釈
            - **t値** が大きいほど、2つのグループの平均が異なる可能性が高い。
            - **p値** が **0.05未満** の場合、2つのグループに統計的な差があると判断。
            - **p値が0.05以上** の場合、「偶然の誤差による差」と考えられる。
            """)