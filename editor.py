import streamlit as st
import pandas as pd
import subprocess
import re
import webbrowser  # 💡 ブラウザを開くためのモジュールを追加
import os          # 💡 ファイルの絶対パスを取得するためのモジュールを追加

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
    
    col_editor, col_preview = st.columns([2, 1.2])
    
    df_genres = load_csv(GENRES_CSV)
    genres_list = df_genres['genre'].dropna().tolist()
    
    with col_editor:
        # エラーになっていた ColorColumn をテキスト入力（正規表現チェック付き）に変更
        edited_df = st.data_editor(
            df_genres,
            column_config={
                "color": st.column_config.TextColumn(
                    "color",
                    help="HEXコードを入力。※右側のパネルでカラーパレットから直感的に変更できます！",
                    max_chars=7,
                    validate="^#[0-9a-fA-F]{6}$"
                ),
                "successor": st.column_config.SelectboxColumn(
                    "successor",
                    help="後継（子孫）ジャンルを選択",
                    options=genres_list,
                )
            },
            num_rows="dynamic",
            use_container_width=True,
            height=600
        )
        
        if st.button("💾 Genres.csvを保存", type="primary"):
            edited_df.to_csv(GENRES_CSV, index=False, encoding="utf-8-sig")
            st.success("ジャンルデータを保存しました！")
            st.cache_data.clear()
            st.rerun()

    with col_preview:
        st.subheader("🔍 コンパクト・プレビュー")
        
        if genres_list:
            target_genre = st.selectbox("プレビュー＆詳細編集するジャンル:", genres_list)
            
            if target_genre:
                safe_id = {g: f"n{i}" for i, g in enumerate(genres_list)}
                target_row = edited_df[edited_df['genre'] == target_genre].iloc[0]
                
                # 親の取得
                parents_str = str(target_row['parents']) if pd.notna(target_row['parents']) else ""
                parents = [p.strip() for p in parents_str.split('|') if p.strip()]
                
                # 子の取得
                children = []
                for _, r in edited_df.iterrows():
                    if pd.isna(r['genre']): continue
                    p_str = str(r['parents']) if pd.notna(r['parents']) else ""
                    p_list = [p.strip() for p in p_str.split('|') if p.strip()]
                    if target_genre in p_list:
                        children.append(r['genre'])
                
                # Mermaid描画
                nodes_to_draw = set([target_genre] + parents + children)
                mermaid_lines = ["graph TD"]
                for node in nodes_to_draw:
                    if node not in safe_id: continue
                    node_row = edited_df[edited_df['genre'] == node]
                    color = node_row.iloc[0]['color'] if not node_row.empty and pd.notna(node_row.iloc[0]['color']) else "#555555"
                    
                    sid = safe_id[node]
                    stroke_color = "#ffffff" if node == target_genre else "#222222"
                    stroke_width = "4px" if node == target_genre else "2px"
                    
                    mermaid_lines.append(f'    {sid}["{node}"]')
                    mermaid_lines.append(f'    style {sid} fill:{color},stroke:{stroke_color},stroke-width:{stroke_width},color:#fff')
                
                for p in parents:
                    if p in safe_id:
                        mermaid_lines.append(f'    {safe_id[p]} --> {safe_id[target_genre]}')
                for c in children:
                    if c in safe_id:
                        mermaid_lines.append(f'    {safe_id[target_genre]} --> {safe_id[c]}')
                
                st.markdown(f"```mermaid\n{chr(10).join(mermaid_lines)}\n```")
                
                # ==========================================
                # 💡 詳細編集エリア（親の複数選択 ＆ カラーパレット）
                # ==========================================
                st.divider()
                st.write(f"📝 **{target_genre}** の詳細編集")
                
                # 親ジャンルのマルチセレクト
                current_parents = [p for p in parents if p in genres_list]
                new_parents = st.multiselect("親ジャンル（複数選択可）:", genres_list, default=current_parents)
                
                # カラーパレットの取得と安全なデフォルト値設定
                current_color = str(target_row['color']) if pd.notna(target_row['color']) else "#555555"
                if not re.match(r'^#[0-9a-fA-F]{6}$', current_color):
                    current_color = "#555555"
                
                # カラーピッカーUI
                new_color = st.color_picker("テーマカラーを選択:", current_color)
                
                st.caption("※左の表で未保存の編集がある場合は、先に上の「保存」ボタンを押してください。")
                if st.button("🔄 このジャンルの詳細（親と色）を上書き保存"):
                    # データフレームを書き換えてCSVに保存
                    df_genres.loc[df_genres['genre'] == target_genre, 'parents'] = "|".join(new_parents)
                    df_genres.loc[df_genres['genre'] == target_genre, 'color'] = new_color
                    df_genres.to_csv(GENRES_CSV, index=False, encoding="utf-8-sig")
                    st.success(f"{target_genre} の詳細を更新しました！")
                    st.cache_data.clear()
                    st.rerun()

elif menu == "Milestones (マイルストーン)":
    st.header("🏆 マイルストーンデータの編集")
    
    df_milestones = load_csv(MILESTONES_CSV)
    
    try:
        df_genres = load_csv(GENRES_CSV)
        genres_list = df_genres['genre'].dropna().tolist()
    except:
        genres_list = []
    
    edited_df = st.data_editor(
        df_milestones,
        column_config={
            "genre": st.column_config.SelectboxColumn(
                "genre",
                help="マイルストーンが属するジャンルを選択",
                options=genres_list,
            )
        },
        num_rows="dynamic",
        use_container_width=True,
        height=600
    )
    
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
            result = subprocess.run(
                ["python", "-X", "utf8", "build.py"], 
                capture_output=True, 
                text=True, 
                encoding="utf-8"
            )
            if result.returncode == 0:
                st.success("画像の生成が完了しました！ブラウザでプレビューを開きます...")
                
                # 💡 index.html の絶対パスを取得してブラウザで開く
                html_path = os.path.abspath("index.html")
                webbrowser.open(f"file://{html_path}")
            else:
                st.error("エラーが発生しました。")
                st.code(result.stderr)