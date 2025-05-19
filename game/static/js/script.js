// --- Interactive background animation ---
(function() {
    const canvas = document.getElementById('bg-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let width = window.innerWidth;
    let height = window.innerHeight;
    let mouse = { x: width/2, y: height/2 };
    let bubbles = [];
    const BUBBLE_COUNT = 38;

    function resizeCanvas() {
        width = window.innerWidth;
        height = window.innerHeight;
        canvas.width = width;
        canvas.height = height;
    }
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();

    function randomColor() {
        const colors = [
            'rgba(249,211,66,0.13)', 'rgba(255,99,132,0.13)',
            'rgba(54,162,235,0.13)', 'rgba(255,206,86,0.13)',
            'rgba(75,192,192,0.13)', 'rgba(153,102,255,0.13)'
        ];
        return colors[Math.floor(Math.random() * colors.length)];
    }

    function createBubble() {
        const r = 18 + Math.random() * 32;
        return {
            x: Math.random() * width,
            y: Math.random() * height,
            r,
            dx: (Math.random() - 0.5) * 1.3,
            dy: (Math.random() - 0.5) * 1.3,
            color: randomColor(),
            alpha: 0.6 + Math.random() * 0.3
        };
    }

    function initBubbles() {
        bubbles = [];
        for (let i = 0; i < BUBBLE_COUNT; i++) {
            bubbles.push(createBubble());
        }
    }
    initBubbles();

    canvas.addEventListener('mousemove', function(e) {
        mouse.x = e.clientX;
        mouse.y = e.clientY;
    });

    function animate() {
        ctx.clearRect(0, 0, width, height);
        for (let bubble of bubbles) {
            // Move bubbles
            bubble.x += bubble.dx + (mouse.x - width/2) * 0.0002;
            bubble.y += bubble.dy + (mouse.y - height/2) * 0.0002;
            // Bounce off edges
            if (bubble.x - bubble.r < 0 || bubble.x + bubble.r > width) bubble.dx *= -1;
            if (bubble.y - bubble.r < 0 || bubble.y + bubble.r > height) bubble.dy *= -1;
            // Draw
            ctx.save();
            ctx.globalAlpha = bubble.alpha;
            ctx.beginPath();
            ctx.arc(bubble.x, bubble.y, bubble.r, 0, Math.PI * 2);
            ctx.fillStyle = bubble.color;
            ctx.shadowColor = bubble.color;
            ctx.shadowBlur = 18;
            ctx.fill();
            ctx.restore();
        }
        requestAnimationFrame(animate);
    }
    animate();
    // Re-init bubbles on resize
    window.addEventListener('resize', initBubbles);
})();

const ROWS = 6;
const COLS = 7;
let board = Array.from({ length: ROWS }, () => Array(COLS).fill(0));
let currentPlayer = 1;
let gameOver = false;
const mode = sessionStorage.getItem('mode') || 'ai_vs_human';

function createBoard() {
    const boardDiv = document.getElementById('board');
    boardDiv.innerHTML = '';
    boardDiv.style.display = 'grid';
    boardDiv.style.gridTemplateRows = `repeat(${ROWS}, var(--cell-size))`;
    boardDiv.style.gridTemplateColumns = `repeat(${COLS}, var(--cell-size))`;
    boardDiv.style.gap = `var(--cell-gap)`;

    for (let r = 0; r < ROWS; r++) {
        for (let c = 0; c < COLS; c++) {
            const cell = document.createElement('div');
            cell.classList.add('cell');
            cell.dataset.row = r;
            cell.dataset.col = c;
            cell.style.gridRowStart = r + 1;
            cell.style.gridColumnStart = c + 1;
            cell.onclick = () => { if (mode === 'human_vs_human' || (mode === 'ai_vs_human' && currentPlayer === 1)) handleClick(c); };
            boardDiv.appendChild(cell);
        }
    }
    updateBoard();
}

function updateBoard() {
    for (let r = 0; r < ROWS; r++) {
        for (let c = 0; c < COLS; c++) {
            const cell = document.querySelector(`.cell[data-row='${r}'][data-col='${c}']`);
            cell.classList.remove('player1', 'player2');
            if (board[r][c] === 1) cell.classList.add('player1');
            if (board[r][c] === 2) cell.classList.add('player2');
        }
    }
}

function handleClick(col) {
    if (gameOver) return;
    makeMove(col);
}

function makeMove(col) {
    fetch('/move', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ board, col, current_player: currentPlayer })
    })
    .then(res => res.json())
    .then(data => {
        board = data.board;
        document.getElementById('status').textContent = data.status;
        updateBoard();
        if (data.status) {
            gameOver = true;
            return;
        }
        currentPlayer = data.next_player;
        // Next move if AI turn
        if ((mode === 'ai_vs_human' && currentPlayer === 2) || mode === 'ai_vs_ai') {
            setTimeout(() => makeMove(null), 500);
        }
    });
}

// --- Dynamic background color for player turn ---
function setPlayerBg(player) {
    document.body.classList.remove('player1-bg', 'player2-bg');
    if (player === 1) {
        document.body.classList.add('player1-bg');
    } else if (player === 2) {
        document.body.classList.add('player2-bg');
    }
}

// --- Winner background color ---
function setWinnerBg(player) {
    document.body.classList.remove('winner1-bg', 'winner2-bg', 'player1-bg', 'player2-bg');
    if (player === 1) {
        document.body.classList.add('winner1-bg');
    } else if (player === 2) {
        document.body.classList.add('winner2-bg');
    }
}

// For menu: reset background on load
if (window.location.pathname === '/' || window.location.pathname === '/menu') {
    document.body.classList.remove('player1-bg', 'player2-bg');
}

// For game: update background on turn change
if (window.location.pathname === '/game') {
    // Try to detect current player from status or board (requires cooperation from game logic)
    function updateGameBg() {
        // Try to read from a global variable or DOM, fallback to player 1
        let current = 1;
        if (window.currentPlayer) current = window.currentPlayer;
        else {
            // Try to read from DOM
            const status = document.getElementById('status');
            if (status && status.textContent.includes('Player 2')) current = 2;
        }
        setPlayerBg(current);
    }
    // Hook into your JS game logic if possible:
    if (typeof window.setCurrentPlayer === 'function') {
        const origSetCurrentPlayer = window.setCurrentPlayer;
        window.setCurrentPlayer = function(player) {
            origSetCurrentPlayer(player);
            setPlayerBg(player);
        };
    }
    // Fallback: observe status changes
    const status = document.getElementById('status');
    if (status) {
        const observer = new MutationObserver(updateGameBg);
        observer.observe(status, { childList: true, subtree: true });
    }
    updateGameBg();

    function setGameBg() {
        document.body.classList.remove('winner1-bg', 'winner2-bg');
        document.body.classList.add('game-bg');
    }
    // On load and on play again
    setGameBg();
    const playAgainBtn = document.querySelector('.controls .primary');
    if (playAgainBtn) {
        playAgainBtn.addEventListener('click', setGameBg);
    }
    // On win, remove game-bg and add winner-bg
    function checkWinnerBg() {
        const status = document.getElementById('status');
        if (!status) return;
        if (/Player 1.*wins|فاز اللاعب 1/i.test(status.textContent)) {
            document.body.classList.remove('game-bg');
            setWinnerBg(1);
        } else if (/Player 2.*wins|فاز اللاعب 2/i.test(status.textContent)) {
            document.body.classList.remove('game-bg');
            setWinnerBg(2);
        }
    }
    // Observe status changes for win
    if (status) {
        const observer = new MutationObserver(checkWinnerBg);
        observer.observe(status, { childList: true, subtree: true });
    }
    // Also call on load
    checkWinnerBg();
}

window.onload = () => {
    createBoard();
    // Kickoff AI if needed
    if (mode === 'ai_vs_ai' || (mode === 'ai_vs_human' && currentPlayer === 2)) {
        setTimeout(() => makeMove(null), 500);
    }
};