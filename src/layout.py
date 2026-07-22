import networkx as nx
import math
from datetime import datetime

def warp_time(year):
    if year < 1900:
        return (year - 1400) * 0.4
    else:
        return (1900 - 1400) * 0.4 + (year - 1900) * 2.0

def calculate_layout(music_genres, milestones):
    G = nx.Graph()
    for genre, data in music_genres.items():
        G.add_node(genre, year=data["year"], volume=data["volume"])
        for parent in data["parents"]:
            if parent in music_genres: 
                G.add_edge(parent, genre)
    
    lanes = []
    assigned = set()
    sorted_by_year = sorted(music_genres.keys(), key=lambda g: music_genres[g]["year"])
    
    for genre in sorted_by_year:
        if genre in assigned:
            continue
        
        current_lane = []
        current = genre
        while current:
            current_lane.append(current)
            assigned.add(current)
            successor = music_genres[current].get("successor")
            if successor and successor in music_genres and successor not in assigned:
                current = successor
            else:
                current = None
                
        lanes.append(current_lane)
        
    def lane_sort_key(lane):
        return min(music_genres[g]["year"] for g in lane)
        
    lanes.sort(key=lane_sort_key, reverse=True)

    CURRENT_YEAR = datetime.now().year
    pos = {}
    current_y = 0
    BASE_SPACING = 2.0
    
    for lane_index, lane in enumerate(lanes):
        # そのレーン（系譜）に含まれるマイルストーンの総数
        milestone_count = sum(1 for m in milestones if m["genre"] in lane)
        
        if lane_index > 0:
            # 1. レーンの期間（開始年〜終了年）を算出
            lane_start = min(music_genres[g]["year"] for g in lane)
            lane_end = lane_start
            for g in lane:
                if music_genres[g].get("end_year"):
                    lane_end = max(lane_end, music_genres[g]["end_year"])
                else:
                    lane_end = max(lane_end, CURRENT_YEAR)
            
            # ゼロ除算防止＆最低期間として10年を担保
            duration = max(10, lane_end - lane_start) 
            
            # 2. 密度（10年あたりの作品数）を算出
            density = (milestone_count / duration) * 10 
            
            # 3. 必要な縦幅（スペース）をハイブリッドで計算
            # (A) 作品数の平方根（緩やかに増加） + (B) 密度に応じた広がり
            extra_space = (math.sqrt(milestone_count) * 2) + (density * 4)
            
            # 極端に広がりすぎないよう、最大15.0でキャップ（上限）を設ける
            # extra_space = min(extra_space, 15.0) 
            
            # 以前の (milestone_count * 0.8) から置き換え
            current_y += BASE_SPACING + extra_space
            
        for genre in lane:
            x_val = warp_time(music_genres[genre]["year"])
            pos[genre] = [x_val, current_y]

    return G, pos