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

// --- 🌍 多言語対応（i18n）の設定 ---
let currentLang = 'ja';

const i18n = {
    ja: {
        langBtn: '🌐 English',
        uiHide: '👁️ 検索を非表示',
        uiShow: '🔍 検索を表示',
        searchLabel: '🔍 ジャンル・曲を検索',
        searchPlaceholder: 'ジャンル、曲名、アーティスト...',
        resetView: '🗺️ 全体表示に戻す',
        contactBtn: '💬 お問い合わせ・リクエスト',
        hoverHint: '🖱️ クリックで固定してコピー',
        lockHint: '📌 固定中（テキストをコピーできます。背景をクリックで解除）',
        parentText: '親: ',
        noneText: 'なし',
        otherSongs: '...他 {count} 曲',
        
        modalTitle: '📬 お問い合わせ・リクエスト',
        modalDesc: 'このサイトへのジャンル追加や名盤のリクエストはこちらからお願いします！',
        modalBtnGenre: '🎸 ジャンルの追加・修正をリクエスト',
        modalBtnMilestone: '💿 名盤・マイルストーンをリクエスト',
        modalBtnOther: '📝 その他のお問い合わせ'
    },
    en: {
        langBtn: '🌐 日本語',
        uiHide: '👁️ Hide Search',
        uiShow: '🔍 Show Search',
        searchLabel: '🔍 Search Genres / Songs',
        searchPlaceholder: 'Genre, Title, Artist...',
        resetView: '🗺️ Reset View',
        contactBtn: '💬 Contact & Requests',
        hoverHint: '🖱️ Click to lock & copy',
        lockHint: '📌 Locked (Select text to copy. Click background to unlock)',
        parentText: 'Parent: ',
        noneText: 'None',
        otherSongs: '...and {count} more',

        modalTitle: '📬 Contact & Requests',
        modalDesc: 'Please submit your requests for new genres or albums here!',
        modalBtnGenre: '🎸 Request Genre Addition / Fix',
        modalBtnMilestone: '💿 Request Milestone / Album',
        modalBtnOther: '📝 Other Inquiries'
    }
};

function toggleLanguage() {
    currentLang = currentLang === 'ja' ? 'en' : 'ja';
    const t = i18n[currentLang];

    // UIのテキストを書き換え
    document.getElementById('lang-toggle-btn').innerText = t.langBtn;
    document.getElementById('contact-btn').innerText = t.contactBtn;
    
    const uiBtn = document.getElementById('toggle-ui-btn');
    if (document.getElementById('ui').style.display === 'none') {
        uiBtn.innerText = t.uiShow;
    } else {
        uiBtn.innerText = t.uiHide;
    }

    document.querySelector('#ui label').innerText = t.searchLabel;
    document.getElementById('genre-search').placeholder = t.searchPlaceholder;
    document.querySelector('#ui button[onclick="resetView()"]').innerText = t.resetView;
    
    // モーダル内のテキストを書き換え
    document.getElementById('modal-title').innerText = t.modalTitle;
    document.getElementById('modal-desc').innerText = t.modalDesc;
    document.getElementById('modal-btn-genre').innerText = t.modalBtnGenre;
    document.getElementById('modal-btn-milestone').innerText = t.modalBtnMilestone;
    document.getElementById('modal-btn-other').innerText = t.modalBtnOther;
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
let isTooltipLocked = false;
let clickStartX, clickStartY;

container.addEventListener('wheel', (e) => {
    e.preventDefault();
    cancelAnimationFrame(animationFrame); 
    const xs = (e.clientX - posX) / scale;
    const ys = (e.clientY - posY) / scale;
    const delta = e.deltaY > 0 ? 0.85 : 1.15;
    scale *= delta;
    posX = e.clientX - xs * scale;
    posY = e.clientY - ys * scale;
    applyTransform();
});

container.addEventListener('mousedown', (e) => {
    // UIやツールチップ内をクリックした場合はドラッグを無効化
    if (e.target.closest('#ui') || e.target.closest('#tooltip')) return;
    e.preventDefault();
    cancelAnimationFrame(animationFrame);
    isDragging = true;
    startX = e.clientX - posX;
    startY = e.clientY - posY;
    
    // クリック判定用に座標を保存
    clickStartX = e.clientX;
    clickStartY = e.clientY;
    container.style.cursor = 'grabbing';
});

window.addEventListener('mouseup', (e) => {
    if (isDragging) {
        isDragging = false;
        container.style.cursor = 'grab';
        
        // クリック判定（マウスがほぼ動いていない場合）
        const dist = Math.hypot(e.clientX - clickStartX, e.clientY - clickStartY);
        if (dist < 5 && tooltip.style.display === 'block' && !isTooltipLocked) {
            // ツールチップをロック（固定）する
            isTooltipLocked = true;
            tooltip.style.border = '2px solid #42A5F5';
            tooltip.innerHTML = `<div style="font-size:12px; color:#42A5F5; margin-bottom:10px; border-bottom:1px solid #555; padding-bottom:5px;">${i18n[currentLang].lockHint}</div>` + tooltip.innerHTML;
            return;
        }
    }
    
    // ロック中に背景（ツールチップ外）をクリックしたら解除
    if (isTooltipLocked && !e.target.closest('#tooltip')) {
        isTooltipLocked = false;
        tooltip.style.display = 'none';
        tooltip.style.border = '1px solid #555';
    }
});

window.addEventListener('mousemove', (e) => {
    // ロック中はマウスが動いてもツールチップを更新しない
    if (isTooltipLocked) return;

    // === 1. ツールチップのホバー判定 ===
    const imageX = (e.clientX - posX) / scale;
    const imageY = (e.clientY - posY) / scale;
    
    let hoveredGenre = null;
    let minDistance = HOVER_RADIUS;

    for (const [genre, data] of Object.entries(genreCoordinates)) {
        const dx = imageX - data.x;
        const dy = imageY - data.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        
        if (dist < minDistance) {
            minDistance = dist;
            hoveredGenre = genre;
        }
    }

    let hoveredMilestones = [];
    if (typeof milestoneCoordinates !== 'undefined') {
        milestoneCoordinates.forEach(m => {
            const dx = imageX - m.x;
            const dy = imageY - m.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            
            if (dist < HOVER_RADIUS) {
                hoveredMilestones.push(m);
            }
        });
    }

    if ((hoveredGenre || hoveredMilestones.length > 0) && !isDragging) {
        let tooltipHTML = '';
        const t = i18n[currentLang]; // 現在の言語辞書を取得
        
        tooltipHTML += `<div style="font-size: 11px; color: #81D4FA; margin-bottom: 8px; text-align: right; border-bottom: 1px dashed #555; padding-bottom: 4px;">${t.hoverHint}</div>`;

        if (hoveredGenre) {
            const parents = genreCoordinates[hoveredGenre].parents;
            const parentText = parents && parents.length > 0 ? parents.join(', ') : t.noneText;
            tooltipHTML += `<strong>🎵 ${hoveredGenre}</strong><br><span style="font-size:12px; color:#aaa;">${t.parentText}${parentText}</span>`;
        }

        if (hoveredMilestones.length > 0) {
            if (hoveredGenre) tooltipHTML += '<hr style="border-top: 1px solid #555; margin: 10px 0;">';
            
            tooltipHTML += '<div style="display: flex; flex-wrap: wrap; gap: 10px; max-width: 900px;">';
            hoveredMilestones.forEach(m => {
                tooltipHTML += `
                    <div style="flex: 1 1 200px; background: #222; padding: 8px; border-radius: 4px; border: 1px solid #444;">
                        <strong>💿 ${m.work}</strong><br>
                        <span style="font-size:12px; color:#ccc;">${m.artist} (${m.year})</span><br>
                        <span style="font-size:11px; color:#888;">${m.genre}</span>
                    </div>
                `;
            });
            tooltipHTML += '</div>';
        }

        tooltip.innerHTML = tooltipHTML;
        tooltip.style.display = 'block';
        
        // 初期の表示位置（はみ出しを考慮する前の仮置き）
        let tipX = e.clientX + 15;
        let tipY = e.clientY + 15;
        tooltip.style.left = tipX + 'px';
        tooltip.style.top = tipY + 'px';
        container.style.cursor = 'pointer';

        // ツールチップが画面外にはみ出ないように描画直後に位置を補正
        requestAnimationFrame(() => {
            const rect = tooltip.getBoundingClientRect();
            if (rect.right > window.innerWidth) {
                tooltip.style.left = Math.max(10, window.innerWidth - rect.width - 15) + 'px';
            }
            if (rect.bottom > window.innerHeight) {
                tooltip.style.top = Math.max(10, window.innerHeight - rect.height - 15) + 'px';
            }
        });

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

// --- お問い合わせモーダルの開閉処理 ---
function openContactModal(e) {
    e.preventDefault();
    document.getElementById('contact-modal').style.display = 'flex';
}

function closeContactModal() {
    document.getElementById('contact-modal').style.display = 'none';
}

// モーダルの外側をクリックしても閉じるようにする機能
window.addEventListener('click', (e) => {
    const modal = document.getElementById('contact-modal');
    if (e.target === modal) {
        modal.style.display = 'none';
    }
});