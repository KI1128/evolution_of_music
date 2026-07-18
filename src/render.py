# render.py
import matplotlib.pyplot as plt
import numpy as np
from src.layout import warp_time

plt.rcParams['font.family'] = ['Meiryo', 'Yu Gothic', 'MS Gothic', 'sans-serif']
plt.rcParams['svg.fonttype'] = 'none'

def draw_graph(G, pos, music_genres, milestones, current_year, output_file="evolution_of_music.svg"):
    max_y = max(p[1] for p in pos.values()) if pos else 0
    canvas_height = max(3, max_y * 0.35)

    fig, ax = plt.subplots(figsize=(24, canvas_height), dpi=100)
    fig.patch.set_facecolor('#111111')
    ax.set_facecolor('#111111')

    # ブラウザのUI軸と完璧に連動させるため、描画エリアの余白を固定値に設定
    top_margin_inch = 0.5
    bottom_margin_inch = 0.5
    top_adjust = 1.0 - (top_margin_inch / canvas_height)
    bottom_adjust = bottom_margin_inch / canvas_height
    
    fig.subplots_adjust(left=0.05, right=0.95, top=top_adjust, bottom=bottom_adjust)
    
    x_min_val = warp_time(1000) - 10
    x_max_val = warp_time(current_year) + 20
    ax.set_xlim(x_min_val, x_max_val)
    ax.set_ylim(-3, max_y + 3)

    # 1. エッジの描画
    for child, data in music_genres.items():
        cy = pos[child][1]
        child_year = data["year"]
        cx = warp_time(child_year)
        for parent in data["parents"]:
            py = pos[parent][1]
            parent_year = music_genres[parent]["year"]
            curve_start_year = max(parent_year, child_year - 15)
            px = warp_time(curve_start_year)
            xs = np.linspace(px, cx, 50)
            if cx != px:
                t = (xs - px) / (cx - px)
                ys = py + (cy - py) * t * t * (3.0 - 2.0 * t) 
            else:
                ys = np.linspace(py, cy, 50) 
            ax.plot(xs, ys, color=music_genres[parent]["color"], alpha=0.4, linewidth=3, zorder=1)

    # 2. 動的ストリーム（帯）の描画
    for node in G.nodes():
        start_year = music_genres[node]["year"]
        start_x = warp_time(start_year)
        
        successor = music_genres[node].get("successor")
        end_year_val = music_genres[node].get("end_year")
        
        if successor and successor in music_genres:
            end_x = warp_time(music_genres[successor]["year"])
        elif end_year_val:
            end_x = warp_time(end_year_val)
        else:
            end_x = warp_time(current_year)
            
        end_x = max(end_x, start_x + 0.1)

        y = pos[node][1]
        node_color = music_genres[node]["color"]
        
        xs = np.linspace(start_x, end_x, 150)
        base_thickness = music_genres[node]["volume"] * 0.0015
        thicknesses = np.full_like(xs, base_thickness)

        genre_mstones = [m for m in milestones if m["genre"] == node]
        for m in genre_mstones:
            mx = warp_time(m["year"])
            bump = base_thickness * 2.0 * np.exp(-((xs - mx)**2) / 30)
            thicknesses += bump

        if successor or end_year_val:
            fade = np.linspace(1.0, 0.05, len(xs))
        else:
            fade = np.linspace(1.0, 0.4, len(xs))
            
        thicknesses = thicknesses * fade

        y_upper = y + thicknesses
        y_lower = y - thicknesses

        ax.fill_between(xs, y_lower, y_upper, color=node_color, alpha=0.85, zorder=2, edgecolor='none')
        ax.scatter(start_x, y, color='white', s=40, zorder=5, edgecolors=node_color, linewidths=1.5)
        ax.text(start_x, y + 0.3, f"{node}", color='white', fontsize=8, ha='left', va='bottom', weight='bold')

    # 3. マイルストーン（全体での衝突回避処理）
    all_labels = []
    
    for genre in music_genres.keys():
        if genre not in pos: continue
        base_y = pos[genre][1]
        for m in [m for m in milestones if m["genre"] == genre]:
            x = warp_time(m["year"])
            text = f"{m['year']} - {m['work']}\n({m['artist']})"
            all_labels.append({"x": x, "y": base_y - 0.8, "text": text, "genre_y": base_y, "genre_color": music_genres[genre]["color"]})
            ax.scatter(x, base_y, color='white', s=50, marker='o', edgecolors=music_genres[genre]["color"], linewidths=2, zorder=10)

    for _ in range(30): 
        for i in range(len(all_labels)):
            for j in range(i + 1, len(all_labels)):
                l1, l2 = all_labels[i], all_labels[j]
                dx = abs(l1["x"] - l2["x"])
                if dx < 25.0: 
                    dy = abs(l1["y"] - l2["y"])
                    if dy < 1.0: 
                        if l1["y"] < l2["y"]:
                            l1["y"] -= 0.15
                        else:
                            l2["y"] -= 0.15

    for lbl in all_labels:
        ax.plot([lbl["x"], lbl["x"]+0.4], [lbl["genre_y"], lbl["y"]], 
                color='white', alpha=0.3, linewidth=1.0, linestyle=':', zorder=9)
        ax.text(lbl["x"] + 0.5, lbl["y"], lbl["text"], color='white', fontsize=4, ha='left', va='top', zorder=11,
                bbox=dict(facecolor='#111111', alpha=0.8, edgecolor='none', pad=1.0))

    # タイトルや軸などを非表示にし、純粋なグラフデータだけにする
    ax.axis('off')

    # bbox_inches='tight'を外すことで余白計算を完全に固定
    plt.savefig(output_file, dpi=100, facecolor='#111111')
    plt.close()