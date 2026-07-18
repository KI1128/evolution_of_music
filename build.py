# build.py
import os
import json
from src.data import load_data, CURRENT_YEAR
from src.layout import calculate_layout, warp_time
from src.render import draw_graph

def main():
    print("🎨 データの読み込みとレイアウト計算を開始します...")
    music_genres, milestones = load_data()
    
    # レイアウトの計算
    G, pos = calculate_layout(music_genres, milestones)
    
    output_filename = "music_tree_optimized.svg"
    
    print("⏳ グラフを描画しています（数秒〜数十秒かかります）...")
    draw_graph(G, pos, music_genres, milestones, CURRENT_YEAR, output_filename)
    
    # ====================================================
    # 🌟 ここから追加：フロントエンド用の座標データを計算して出力
    # ====================================================
    print("🗺️ 検索ジャンプ用の座標データを生成しています...")
    
    # グラフのX軸とY軸の範囲（render.pyと同じ計算）
    x_min_val = warp_time(1000) - 10
    x_max_val = warp_time(CURRENT_YEAR) + 20
    max_y = max(p[1] for p in pos.values()) if pos else 0
    y_min_val = -3
    y_max_val = max_y + 3

    # キャンバスサイズと余白（render.pyと同じ計算）
    canvas_height = max(3, max_y * 0.35)
    width_px = 2400
    height_px = canvas_height * 100

    top_margin_inch = 0.5
    bottom_margin_inch = 0.5
    top_adjust = 1.0 - (top_margin_inch / canvas_height)
    bottom_adjust = bottom_margin_inch / canvas_height
    
    plot_height_px = height_px * (top_adjust - bottom_adjust)
    top_margin_px = height_px * (1.0 - top_adjust)

    coords = {}
    for genre, (x, y) in pos.items():
        # X座標のピクセル換算
        x_pct = (x - x_min_val) / (x_max_val - x_min_val)
        px_x = width_px * 0.05 + x_pct * (width_px * 0.90)
        
        # Y座標のピクセル換算（MatplotlibとSVGの上下反転を考慮）
        y_pct = (y - y_min_val) / (y_max_val - y_min_val)
        px_y = top_margin_px + (1.0 - y_pct) * plot_height_px
        
        coords[genre] = {"x": round(px_x, 2), "y": round(px_y, 2)}

    # JSファイルとして保存
    with open("coordinates.js", "w", encoding="utf-8") as f:
        f.write(f"const imageConfig = {{ width: {width_px}, height: {height_px} }};\n")
        f.write(f"const genreCoordinates = {json.dumps(coords, ensure_ascii=False)};\n")
    
    # ====================================================

    # svgo による圧縮（あれば）
    try:
        print("🗜️ svgo によるSVGの圧縮を試みます...")
        os.system(f"npx svgo {output_filename} -o {output_filename}")
    except Exception:
        pass
        
    print(f"\n🎉 完了しました！ '{output_filename}' と 'coordinates.js' が生成されました。")

if __name__ == '__main__':
    main()