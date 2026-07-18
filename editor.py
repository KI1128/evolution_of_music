import streamlit as st
import pandas as pd
import subprocess

# ページの設定 (広く使う設定に変更)
st.set_page_config(page_title="Music Evolution Editor", layout="wide")
st.title("🎵 The River of Music - Data Editor")

GENRES_CSV = "data/genres.csv"
MILESTONES_CSV = "data/milestones.csv"

@st.cache_data
def load_csv(path):
    return pd.read_csv(path)

menu = st.sidebar.radio("メニュー", ["Genres (ジャンル)", "Milestones (マイルストーン)", "ビルド＆プレビュー"])

if menu == "Genres (ジャンル)":
    st.header("🎸 ジャンルデータの編集")
    
    # 画面を左右に分割（左側を広く：エディタ、右側：プレビュー）
    col_editor, col_preview = st.columns([2, 1.2])
    
    df_genres = load_csv(GENRES_CSV)
    
    with col_editor:
        # エディタ（ここで編集した内容は即座に変数の edited_df に反映される）
        edited_df = st.data_editor(df_genres, num_rows="dynamic", use_container_width=True, height=600)
        
        if st.button("💾 Genres.csvを保存", type="primary"):
            edited_df.to_csv(GENRES_CSV, index=False, encoding="utf-8-sig")
            st.success("ジャンルデータを保存しました！")
            st.cache_data.clear()
            st.rerun()

    with col_preview:
        st.subheader("🔍 コンパクト・プレビュー")
        st.write("選択したジャンルの **親（ルーツ）** と **子（派生先）** の関係、および **カラー** を確認できます。")
        
        genres_list = edited_df['genre'].dropna().tolist()
        if genres_list:
            target_genre = st.selectbox("プレビューするジャンルを選択:", genres_list)
            
            if target_genre:
                # 安全なIDを割り当て（Mermaid描画用）
                safe_id = {g: f"n{i}" for i, g in enumerate(genres_list)}
                
                # ターゲットの親を取得
                target_row = edited_df[edited_df['genre'] == target_genre].iloc[0]
                parents_str = str(target_row['parents']) if pd.notna(target_row['parents']) else ""
                parents = [p.strip() for p in parents_str.split('|') if p.strip()]
                
                # ターゲットの子を取得
                children = []
                for _, r in edited_df.iterrows():
                    if pd.isna(r['genre']): continue
                    p_str = str(r['parents']) if pd.notna(r['parents']) else ""
                    p_list = [p.strip() for p in p_str.split('|') if p.strip()]
                    if target_genre in p_list:
                        children.append(r['genre'])
                
                nodes_to_draw = set([target_genre] + parents + children)
                
                # Mermaid形式のコードを組み立てる
                mermaid_lines = ["graph TD"]
                
                # ノード（箱）と色の定義
                for node in nodes_to_draw:
                    if node not in safe_id: continue
                    node_row = edited_df[edited_df['genre'] == node]
                    color = node_row.iloc[0]['color'] if not node_row.empty and pd.notna(node_row.iloc[0]['color']) else "#555"
                    
                    sid = safe_id[node]
                    # 選択中のジャンルは枠線を白く太くして強調
                    stroke_color = "#ffffff" if node == target_genre else "#222222"
                    stroke_width = "4px" if node == target_genre else "2px"
                    
                    mermaid_lines.append(f'    {sid}["{node}"]')
                    mermaid_lines.append(f'    style {sid} fill:{color},stroke:{stroke_color},stroke-width:{stroke_width},color:#fff')
                
                # エッジ（矢印）の定義
                for p in parents:
                    if p in safe_id:
                        mermaid_lines.append(f'    {safe_id[p]} --> {safe_id[target_genre]}')
                for c in children:
                    if c in safe_id:
                        mermaid_lines.append(f'    {safe_id[target_genre]} --> {safe_id[c]}')
                
                # StreamlitのマークダウンでMermaidを描画
                st.markdown(f"```mermaid\n{chr(10).join(mermaid_lines)}\n```")
                
                st.info("💡 表の色(color)や親(parents)の文字を変更すると、保存前でもこの図にリアルタイムで反映されます。")

elif menu == "Milestones (マイルストーン)":
    st.header("🏆 マイルストーンデータの編集")
    df_milestones = load_csv(MILESTONES_CSV)
    
    edited_df = st.data_editor(df_milestones, num_rows="dynamic", use_container_width=True, height=600)
    
    if st.button("💾 Milestones.csvを保存", type="primary"):
        edited_df.to_csv(MILESTONES_CSV, index=False, encoding="utf-8-sig")
        st.success("マイルストーンデータを保存しました！")
        st.cache_data.clear()
        st.rerun()

elif menu == "ビルド＆プレビュー":
    st.header("🚀 グラフの生成")
    st.write("データを編集したら、ここから新しい画像を生成して最終確認します。")
    
    if st.button("✨ build.py を実行して全体画像を更新", type="primary"):
        with st.spinner("画像を生成中..."):
            result = subprocess.run(["python", "build.py"], capture_output=True, text=True)
            if result.returncode == 0:
                st.success("画像の生成が完了しました！ブラウザで index.html を開いて（F5リロードして）確認してください。")
            else:
                st.error("エラーが発生しました。")
                st.code(result.stderr)