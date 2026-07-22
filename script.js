const container = document.getElementById('container');
const img = document.getElementById('image');
const searchInput = document.getElementById('genre-search');
const genreListEl = document.getElementById('genre-list');
const tooltip = document.getElementById('tooltip');
const HOVER_RADIUS = 40; // 反応する半径（ピクセル）

const CURRENT_YEAR = new Date().getFullYear();
const DISPLAY_YEARS = [1000, 1400, 1600, 1800, 1900, 1930, 1960, 1980, 2000, 2020];

function warp_time(year) {
    if (year < 1900) return (year - 1400) * 0.4;
    return (1900 - 1400) * 0.4 + (year - 1900) * 2.0;
}

const x_min_val = warp_time(1000) - 10;
const x_max_val = warp_time(CURRENT_YEAR) + 20;

const timelineBar = document.getElementById('timeline-bar');
const ticks = [];

let scale = 0.5, posX = 0, posY = 0;
let isDragging = false, startX, startY;
let animationFrame;

function toggleUI() {
    const ui = document.getElementById('ui');
    const btn = document.getElementById('toggle-ui-btn');
    if (ui.style.display === 'none') {
        ui.style.display = 'flex';
        btn.innerText = '👁️ 検索を非表示';
    } else {
        ui.style.display = 'none';
        btn.innerText = '🔍 検索を表示';
    }
}

// --- 1. ジャンルリストの描画 ---
function renderList(filter = '') {
    genreListEl.innerHTML = '';
    const lowerFilter = filter.toLowerCase();

    // 1. ジャンルの検索と描画
    const genres = Object.keys(genreCoordinates).sort();
    genres.forEach(g => {
        if (g.toLowerCase().includes(lowerFilter)) {
            const el = document.createElement('div');
            el.className = 'genre-item';
            el.innerText = `🎵 ${g}`; // アイコンで区別
            el.onclick = () => jumpToPosition(genreCoordinates[g].x, genreCoordinates[g].y);
            genreListEl.appendChild(el);
        }
    });

    // 2. マイルストーンの検索と描画
    if (typeof milestoneCoordinates !== 'undefined') {
        milestoneCoordinates.forEach(m => {
            // 曲名・アーティスト名・年・ジャンル名のどれにでもヒットするようにする
            const searchTarget = `${m.work} ${m.artist} ${m.year} ${m.genre}`.toLowerCase();
            if (searchTarget.includes(lowerFilter)) {
                const el = document.createElement('div');
                el.className = 'genre-item';
                el.innerText = `💿 ${m.work} / ${m.artist} (${m.year})`; // アイコンで区別
                el.onclick = () => jumpToPosition(m.x, m.y);
                genreListEl.appendChild(el);
            }
        });
    }
}
searchInput.addEventListener('input', (e) => renderList(e.target.value));
renderList();

// --- 2. 画像の変形を適用 ---
function applyTransform() {
    img.style.transform = `translate(${posX}px, ${posY}px) scale(${scale})`;
    
    ticks.forEach(t => {
        const screen_x = posX + t.px * scale;
        t.element.style.left = screen_x + 'px';
    });
}

// --- 3. アニメーション（ジャンプ機能） ---
function animateTo(targetX, targetY, targetScale) {
    cancelAnimationFrame(animationFrame);
    const duration = 1000; // アニメーションの長さ（ミリ秒）
    const startTime = performance.now();
    const initX = posX, initY = posY, initScale = scale;

    function step(currentTime) {
        let progress = (currentTime - startTime) / duration;
        if (progress > 1) progress = 1;

        // スムーズなイージング（徐々に減速）
        const ease = 1 - Math.pow(1 - progress, 3);

        posX = initX + (targetX - initX) * ease;
        posY = initY + (targetY - initY) * ease;
        scale = initScale + (targetScale - initScale) * ease;

        applyTransform();

        if (progress < 1) {
            animationFrame = requestAnimationFrame(step);
        }
    }
    animationFrame = requestAnimationFrame(step);
}

function jumpToPosition(targetX, targetY) {
    const targetScale = 2.0; // ズームインの強さ
    const screenW = window.innerWidth;
    const screenH = window.innerHeight;

    const targetPosX = (screenW / 2) - (targetX * targetScale);
    const targetPosY = (screenH / 2) - (targetY * targetScale);

    animateTo(targetPosX, targetPosY, targetScale);
}

function resetView() {
    // 初期状態（全体が見える位置）に戻す
    animateTo(50, 50, 0.4);
}

// 初期表示位置
img.onload = () => {
    // 💡 ここに追加：Pythonが計算した「本来のピクセルサイズ」をブラウザに強制する
    img.style.width = imageConfig.width + 'px';
    img.style.height = imageConfig.height + 'px';

    resetView();
};

// --- 4. マウス操作（ホイールズームとドラッグ） ---
container.addEventListener('wheel', (e) => {
    e.preventDefault();
    cancelAnimationFrame(animationFrame); // 手動操作中はアニメを止める
    const xs = (e.clientX - posX) / scale;
    const ys = (e.clientY - posY) / scale;
    const delta = e.deltaY > 0 ? 0.85 : 1.15;
    scale *= delta;
    posX = e.clientX - xs * scale;
    posY = e.clientY - ys * scale;
    applyTransform();
});

container.addEventListener('mousedown', (e) => {
    if (e.target.closest('#ui')) return;
    e.preventDefault();
    cancelAnimationFrame(animationFrame);
    isDragging = true;
    startX = e.clientX - posX;
    startY = e.clientY - posY;
    container.style.cursor = 'grabbing';
});

window.addEventListener('mouseup', () => {
    if (isDragging) {
        isDragging = false;
        container.style.cursor = 'grab';
    }
});

window.addEventListener('mousemove', (e) => {
    // === 1. ツールチップのホバー判定 ===
    // 画面上のマウス座標から、画像内の元のピクセル座標を逆算する
    const imageX = (e.clientX - posX) / scale;
    const imageY = (e.clientY - posY) / scale;
    
    let hoveredGenre = null;
    let minDistance = HOVER_RADIUS;

    // 全ジャンルの座標と距離をピタゴラスの定理で計算して、最も近いものを探す
    for (const [genre, data] of Object.entries(genreCoordinates)) {
        const dx = imageX - data.x;
        const dy = imageY - data.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        
        if (dist < minDistance) {
            minDistance = dist;
            hoveredGenre = genre;
        }
    }

    // 近くにジャンルがあり、かつ画面をドラッグ中でない場合ツールチップを表示
    if (hoveredGenre && !isDragging) {
        const parents = genreCoordinates[hoveredGenre].parents;
        const parentText = parents && parents.length > 0 ? parents.join(', ') : 'なし';
        
        tooltip.innerHTML = `<strong>🎵 ${hoveredGenre}</strong><br><span style="font-size:12px; color:#aaa;">親: ${parentText}</span>`;
        tooltip.style.display = 'block';
        tooltip.style.left = (e.clientX + 15) + 'px';
        tooltip.style.top = (e.clientY + 15) + 'px';
        container.style.cursor = 'pointer';
    } else {
        tooltip.style.display = 'none';
        container.style.cursor = isDragging ? 'grabbing' : 'grab';
    }

    // === 2. 画面のドラッグ移動処理 ===
    if (isDragging) {
        e.preventDefault();
        posX = e.clientX - startX;
        posY = e.clientY - startY;
        requestAnimationFrame(applyTransform);
    }
});

// DOM読み込み時に年代の目盛り(div)を作成
window.addEventListener('DOMContentLoaded', () => {
    DISPLAY_YEARS.forEach(year => {
        const el = document.createElement('div');
        el.className = 'timeline-tick';
        el.innerText = year;
        timelineBar.appendChild(el);
        
        const data_x = warp_time(year);
        const percent = (data_x - x_min_val) / (x_max_val - x_min_val);
        // coordinates.js の imageConfig.width を使用
        const pixel_x = (0.05 + 0.9 * percent) * imageConfig.width; 
        ticks.push({ element: el, px: pixel_x });
    });
});