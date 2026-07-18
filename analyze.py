from data import load_data, get_ancestors
from collections import defaultdict

def main():
    print("データを読み込み中...")
    music_genres, milestones = load_data()
    
    print("=== 🎵 音楽ジャンル データ構造解析レポート ===\n")

    print("■ 0. マイルストーン年代別解析（25年単位）")
    counts = defaultdict(int)
    for m in milestones:
        year = m.get("year")
        if year:
            period_start = (year // 25) * 25
            counts[period_start] += 1
            
    print(f"  {'年代':<15} | {'作品数'}")
    print("  " + "-" * 25)
    
    total = 0
    for start_year in sorted(counts.keys()):
        count = counts[start_year]
        total += count
        end_year = start_year + 24
        print(f"  {start_year} - {end_year} | {count}作品")
        
    print("  " + "-" * 25)
    print(f"  合計: {total}作品\n")

    print("■ 1. マイルストーン不足警告（0〜1曲のジャンル）")
    milestone_counts = defaultdict(int)
    for m in milestones:
        genre = m.get("genre")
        if genre in music_genres:
            milestone_counts[genre] += 1
    
    empty_genres = []
    for genre in music_genres.keys():
        if milestone_counts[genre] <= 1:
            empty_genres.append((genre, milestone_counts[genre]))
    
    if empty_genres:
        for g, count in sorted(empty_genres, key=lambda x: x[1]):
            print(f"  - {g}: {count}作品")
    else:
        print("  ✅ 全ジャンルに十分なマイルストーンが設定されています！")
    print()

    print("■ 2. 派生不足警告（巨大ジャンルなのに子ジャンルがない行き止まり）")
    children_map = defaultdict(list)
    for g, data in music_genres.items():
        for p in data.get("parents", []):
            children_map[p].append(g)
            
    dead_end_majors = []
    for genre, data in music_genres.items():
        if data.get("volume", 0) >= 80 and len(children_map[genre]) == 0:
            if not data.get("successor"): 
                dead_end_majors.append(genre)
                
    if dead_end_majors:
        for g in dead_end_majors:
            print(f"  - {g} (Volume: {music_genres[g]['volume']}) -> 派生先なし")
    else:
        print("  ✅ 主要ジャンルからの派生は健全です！")
    print()

    print("■ 3. 親子関係の重複警告（A→B→C なのに A→C も直接繋いでしまっている箇所）")
    parents_map = {g: data.get("parents", []) for g, data in music_genres.items()}
    redundant_found = False
    
    for child, parents in parents_map.items():
        for p1 in parents:
            for p2 in parents:
                if p1 == p2: continue
                p2_ancestors = get_ancestors(p2, parents_map)
                if p1 in p2_ancestors:
                    print(f"  ⚠️ '{child}' の親設定に重複あり:")
                    print(f"     直接の親として '{p1}' が設定されていますが、")
                    print(f"     別の親 '{p2}' のルーツを辿ると既に '{p1}' が含まれています。")
                    print(f"     【解決策】 '{child}' の parents から '{p1}' を削除してください。\n")
                    redundant_found = True
                    
    if not redundant_found:
        print("  ✅ 冗長な親子関係はありません！美しいツリー構造です。")
        
    print("===================================================")

if __name__ == "__main__":
    main()