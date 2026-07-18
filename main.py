# main.py
import http.server
import socketserver
import urllib.parse
import webbrowser
import os
import json

from data import load_data, filter_by_genre, CURRENT_YEAR
from layout import calculate_layout
from render import draw_graph

PORT = 8000

class GraphViewerHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        if path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            music_genres, _ = load_data()
            genre_list_js = json.dumps(list(sorted(music_genres.keys())))
            
            html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Music Evolution Viewer</title>
    <style>
        body {{ margin: 0; background-color: #111; overflow: hidden; color: white; font-family: 'Meiryo', sans-serif; }}
        #container {{ width: 100vw; height: 100vh; cursor: grab; }}
        #image {{ transform-origin: 0 0; display: none; user-select: none; -webkit-user-drag: none; }}
        
        #header-title {{ position: absolute; top: 0; width: 100%; text-align: center; padding: 15px 0; font-size: 24px; font-weight: bold; background: linear-gradient(rgba(0,0,0,0.8), transparent); pointer-events: none; z-index: 50; text-shadow: 0 2px 4px #000; }}
        
        #ui {{ position: absolute; top: 60px; left: 20px; background: rgba(0,0,0,0.85); padding: 15px; border-radius: 8px; z-index: 100; box-shadow: 0 4px 10px rgba(0,0,0,0.8); width: 280px; display: flex; flex-direction: column; max-height: calc(100vh - 140px); }}
        #genre-search {{ padding: 8px; background: #222; color: white; border: 1px solid #555; border-radius: 4px; margin-bottom: 10px; font-size: 14px; width: 100%; box-sizing: border-box; }}
        #genre-list {{ overflow-y: auto; display: flex; flex-direction: column; gap: 8px; padding-right: 5px; margin-bottom: 15px; }}
        #genre-list label {{ cursor: pointer; font-size: 13px; display: flex; align-items: center; gap: 8px; }}
        #genre-list label:hover {{ color: #42A5F5; }}
        button {{ padding: 10px; cursor: pointer; background: #1565C0; color: white; border: none; border-radius: 4px; font-weight: bold; font-size: 14px; }}
        button:hover {{ background: #1976D2; }}
        
        #timeline-bar {{ position: absolute; bottom: 0; width: 100%; height: 50px; background: linear-gradient(transparent, rgba(0,0,0,0.9)); z-index: 50; pointer-events: none; overflow: hidden; border-top: 1px solid rgba(255,255,255,0.1); }}
        .timeline-tick {{ position: absolute; bottom: 15px; transform: translateX(-50%); font-size: 14px; font-weight: bold; color: rgba(255,255,255,0.8); text-shadow: 0 1px 3px #000; }}
        .timeline-tick::after {{ content: ''; position: absolute; top: -10px; left: 50%; width: 1px; height: 8px; background: rgba(255,255,255,0.5); }}
        
        #loading {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 24px; font-weight: bold; z-index: 200; display: none; pointer-events: none; text-shadow: 0 2px 4px rgba(0,0,0,0.8); }}
    </style>
</head>
<body>
    <div id="header-title">The Evolution of Music</div>
    
    <div id="ui">
        <label style="margin-bottom: 8px; font-size: 14px; font-weight: bold;">🎵 ジャンルの絞り込み</label>
        <input type="text" id="genre-search" placeholder="ジャンルを検索...">
        <div id="genre-list"></div>
        <button onclick="updateGraph()">描画を更新</button>
    </div>
    
    <div id="loading">🎨 画像を生成中...</div>
    
    <div id="container">
        <img id="image" alt="Graph" draggable="false">
    </div>
    
    <div id="timeline-bar"></div>

    <script>
        const allGenres = {genre_list_js};
        const genreListEl = document.getElementById('genre-list');
        const searchInput = document.getElementById('genre-search');
        
        function renderCheckboxes(filter = '') {{
            genreListEl.innerHTML = '';
            const clearLabel = document.createElement('label');
            clearLabel.innerHTML = `<input type="checkbox" id="check-all" onchange="clearAllChecks()"> <span style="color:#aaa;">(すべて解除 / 全体表示)</span>`;
            genreListEl.appendChild(clearLabel);
            genreListEl.appendChild(document.createElement('hr'));

            allGenres.forEach(g => {{
                if (g.toLowerCase().includes(filter.toLowerCase())) {{
                    const lbl = document.createElement('label');
                    lbl.innerHTML = `<input type="checkbox" class="genre-cb" value="${{g}}"> ${{g}}`;
                    genreListEl.appendChild(lbl);
                }}
            }});
        }}
        
        function clearAllChecks() {{
            document.querySelectorAll('.genre-cb').forEach(cb => cb.checked = false);
            document.getElementById('check-all').checked = false;
        }}

        searchInput.addEventListener('input', (e) => renderCheckboxes(e.target.value));
        renderCheckboxes(); 


        const container = document.getElementById('container');
        const img = document.getElementById('image');
        const loading = document.getElementById('loading');
        let scale = 1, posX = 0, posY = 0;
        let isDragging = false, startX, startY;

        function updateGraph() {{
            loading.style.display = 'block';
            img.style.display = 'none';
            
            const selected = Array.from(document.querySelectorAll('.genre-cb:checked')).map(cb => cb.value);
            const params = new URLSearchParams();
            selected.forEach(g => params.append('genre', g));
            params.append('t', new Date().getTime());
            
            img.onload = function() {{
                loading.style.display = 'none';
                img.style.display = 'block';
                
                // グラフの一番左上がブラウザの左上（タイトルの少し下、UIメニューの横）にぴったり来るように設定
                scale = 1; 
                posX = 500; 
                posY = 80; 
                
                applyTransform();
            }};
            img.src = '/api/graph?' + params.toString();
        }}

        const DISPLAY_YEARS = [1000, 1400, 1600, 1800, 1900, 1930, 1960, 1980, 2000, 2020];
        const CURRENT_YEAR = {CURRENT_YEAR};
        function warp_time(year) {{
            if (year < 1900) return (year - 1400) * 0.4;
            return (1900 - 1400) * 0.4 + (year - 1900) * 2.0;
        }}
        const x_min_val = warp_time(1000) - 10;
        const x_max_val = warp_time(CURRENT_YEAR) + 20;
        
        const timelineBar = document.getElementById('timeline-bar');
        const ticks = [];
        DISPLAY_YEARS.forEach(year => {{
            const el = document.createElement('div');
            el.className = 'timeline-tick';
            el.innerText = year;
            timelineBar.appendChild(el);
            
            const data_x = warp_time(year);
            const percent = (data_x - x_min_val) / (x_max_val - x_min_val);
            const pixel_x = (0.05 + 0.9 * percent) * 2400; 
            ticks.push({{ element: el, px: pixel_x }});
        }});

        function applyTransform() {{
            img.style.transform = `translate(${{posX}}px, ${{posY}}px) scale(${{scale}})`;
            
            ticks.forEach(t => {{
                const screen_x = posX + t.px * scale;
                t.element.style.left = screen_x + 'px';
            }});
        }}

        container.addEventListener('wheel', (e) => {{
            e.preventDefault();
            const xs = (e.clientX - posX) / scale;
            const ys = (e.clientY - posY) / scale;
            const delta = e.deltaY > 0 ? 0.85 : 1.15;
            scale *= delta;
            posX = e.clientX - xs * scale;
            posY = e.clientY - ys * scale;
            applyTransform();
        }});

        container.addEventListener('mousedown', (e) => {{
            if (e.target.closest('#ui')) return;
            e.preventDefault(); 
            isDragging = true;
            startX = e.clientX - posX;
            startY = e.clientY - posY;
            container.style.cursor = 'grabbing';
        }});

        window.addEventListener('mouseup', () => {{
            if (isDragging) {{
                isDragging = false;
                container.style.cursor = 'grab';
            }}
        }});

        window.addEventListener('mousemove', (e) => {{
            if (!isDragging) return;
            e.preventDefault();
            posX = e.clientX - startX;
            posY = e.clientY - startY;
            requestAnimationFrame(applyTransform);
        }});

        updateGraph();
    </script>
</body>
</html>
            """
            self.wfile.write(html.encode('utf-8'))
            
        elif path == '/api/graph':
            query = urllib.parse.parse_qs(parsed_path.query)
            target_genres = query.get('genre', [])
            
            music_genres, milestones = load_data()
            if target_genres:
                music_genres, milestones = filter_by_genre(music_genres, milestones, target_genres)
            
            G, pos = calculate_layout(music_genres, milestones)
            
            temp_filename = "temp_evolution_of_music.svg"
            draw_graph(G, pos, music_genres, milestones, CURRENT_YEAR, temp_filename)
            
            self.send_response(200)
            self.send_header('Content-type', 'image/svg+xml')
            self.end_headers()
            with open(temp_filename, 'rb') as f:
                self.wfile.write(f.read())
        else:
            super().do_GET()

def main():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), GraphViewerHandler) as httpd:
        print("=======================================")
        print(f"🎨 ローカルサーバーを起動しました。")
        print(f"👉 ブラウザで http://localhost:{PORT} を開いてください。")
        print("終了するにはターミナルで Ctrl+C を押してください。")
        print("=======================================")
        
        webbrowser.open(f"http://localhost:{PORT}")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nサーバーを停止しました。")

if __name__ == '__main__':
    main()