import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import scipy.stats as stats
import os

# フォント設定（同じフォルダ内の日本語フォントを使用）
font_path = "./path_to_japanese_font.ttf"  # フォントのパスを正しく指定
plt.rcParams["font.family"] = font_path

# Streamlit アプリのタイトル
st.title("t検定 Web アプリ")

# CSVテンプレートのダウンロード
st.markdown("### CSVテンプレートのダウンロード")
template_csv = """グループ,値
A,23.5
A,24.1
B,25.3
B,22.8
"""
st.download_button(
    label="CSVテンプレートをダウンロード",
    data=template_csv.encode('utf-8-sig'),
    file_name="template.csv",
    mime="text/csv"
)

# CSVファイルのアップロード
st.sidebar.header("データのアップロード")
uploaded_file = st.sidebar.file_uploader("CSVファイルをアップロード", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write("### アップロードされたデータ")
    st.dataframe(df.head())
    
    # グループの選択
    group_column = st.sidebar.selectbox("グループを示す列を選択", df.columns)
    value_column = st.sidebar.selectbox("数値データの列を選択", [col for col in df.columns if col != group_column])
    
    groups = df[group_column].unique()
    if len(groups) == 2:
        group1 = df[df[group_column] == groups[0]][value_column]
        group2 = df[df[group_column] == groups[1]][value_column]
        
        # t検定の実行
        t_stat, p_value = stats.ttest_ind(group1, group2)
        
        st.subheader("t検定の結果")
        st.write(f"t値: {t_stat:.4f}")
        st.write(f"p値: {p_value:.4f}")
        
        # ヒストグラムの描画
        fig, ax = plt.subplots()
        sns.histplot(group1, label=str(groups[0]), kde=True, color="blue", alpha=0.6, ax=ax)
        sns.histplot(group2, label=str(groups[1]), kde=True, color="red", alpha=0.6, ax=ax)
        ax.set_xlabel("値")
        ax.set_ylabel("頻度")
        ax.legend()
        st.pyplot(fig)
    else:
        st.error("2つのグループを含むデータをアップロードしてください。")