# data.py
import csv
from datetime import datetime

CURRENT_YEAR = datetime.now().year
DISPLAY_YEARS = [1000, 1400, 1600, 1800, 1900, 1930, 1960, 1980, 2000, 2020]

def load_data(genres_csv="data/genres.csv", milestones_csv="data/milestones.csv"):
    music_genres = {}
    with open(genres_csv, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            genre = row['genre']
            music_genres[genre] = {
                "year": int(row['year']),
                "parents": row['parents'].split('|') if row['parents'] else [],
                "volume": int(row['volume']),
                "color": row['color'],
            }
            if row.get('successor'):
                music_genres[genre]['successor'] = row['successor']
            if row.get('end_year'):
                music_genres[genre]['end_year'] = int(float(row['end_year']))
                
    milestones = []
    with open(milestones_csv, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            milestones.append({
                "year": int(row['year']),
                "genre": row['genre'],
                "artist": row['artist'],
                "work": row['work']
            })
            
    return music_genres, milestones

def get_descendants(genre, children_map):
    descendants = set()
    def dfs(current):
        for child in children_map.get(current, []):
            if child not in descendants:
                descendants.add(child)
                dfs(child)
    dfs(genre)
    return descendants

def get_ancestors(genre, parents_map):
    ancestors = set()
    def dfs(current):
        for parent in parents_map.get(current, []):
            if parent not in ancestors:
                ancestors.add(parent)
                dfs(parent)
    dfs(genre)
    return ancestors

# 複数選択（リスト）に対応
def filter_by_genre(music_genres, milestones, target_genres):
    if not target_genres:
        return music_genres, milestones

    parents_map = {g: d["parents"] for g, d in music_genres.items()}
    children_map = {g: [] for g in music_genres}
    for g, d in music_genres.items():
        for p in d["parents"]:
            if p in children_map:
                children_map[p].append(g)

    # 選択されたすべてのジャンルとその系譜を結合
    related_genres = set()
    for tg in target_genres:
        if tg in music_genres:
            related_genres.add(tg)
            related_genres.update(get_ancestors(tg, parents_map))
            related_genres.update(get_descendants(tg, children_map))

    if not related_genres:
        return music_genres, milestones

    filtered_genres = {g: d for g, d in music_genres.items() if g in related_genres}
    
    for g in filtered_genres:
        filtered_genres[g]["parents"] = [p for p in filtered_genres[g]["parents"] if p in filtered_genres]

    filtered_milestones = [m for m in milestones if m["genre"] in filtered_genres]
    return filtered_genres, filtered_milestones