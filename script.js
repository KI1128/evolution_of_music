const container = document.getElementById('container');
const img = document.getElementById('image');
const searchInput = document.getElementById('genre-search');
const genreListEl = document.getElementById('genre-list');

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
    if (!isDragging) return;
    e.preventDefault();
    posX = e.clientX - startX;
    posY = e.clientY - startY;
    requestAnimationFrame(applyTransform);
});