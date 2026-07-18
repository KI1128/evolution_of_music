import networkx as nx

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

    pos = {}
    current_y = 0
    BASE_SPACING = 6.0 
    
    for lane_index, lane in enumerate(lanes):
        # 動的データ (milestones) を使って判定
        milestone_count = sum(1 for m in milestones if m["genre"] in lane)
        
        if lane_index > 0:
            current_y += BASE_SPACING + (milestone_count * 0.8)
            
        for genre in lane:
            x_val = warp_time(music_genres[genre]["year"])
            pos[genre] = [x_val, current_y]

    return G, pos