const socket = io();

let currentRow = 0;
let currentTile = 0;
let currentGuess = [];
let wordLength = 5;
let currentRoom = null;
let isGameOver = false;

function showMessage(text) {
    document.getElementById('modal-message').innerHTML = text; 
    document.getElementById('custom-modal').style.display = 'flex';
}

function fireConfetti() {
    confetti({
        particleCount: 150,
        spread: 80,
        origin: { y: 0.6 },
        colors: ['#538d4e', '#b59f3b', '#ffffff'] 
    });
}

document.addEventListener('DOMContentLoaded', () => {
    createBoard();

    document.getElementById('modal-close-btn').addEventListener('click', () => {
        document.getElementById('custom-modal').style.display = 'none';
    });

    document.getElementById('create-room').addEventListener('click', () => {
        const length = parseInt(document.getElementById('word-length').value);
        const playerName = document.getElementById('player-name').value;
        socket.emit('oda_kur', { uzunluk: length, oyuncu_adi: playerName });
    });

    document.getElementById('join-room').addEventListener('click', () => {
        const code = document.getElementById('room-input').value;
        const playerName = document.getElementById('player-name').value;
        if (code) {
            socket.emit('odaya_katil', { oda_kodu: code, oyuncu_adi: playerName });
        }
    });

    document.getElementById('next-round').addEventListener('click', () => {
        if (currentRoom) {
            socket.emit('yeni_tur', { oda_kodu: currentRoom });
        }
    });

    document.getElementById('send-btn').addEventListener('click', () => {
        const chatInput = document.getElementById('chat-input');
        const msg = chatInput.value.trim();
        if (msg && currentRoom) {
            socket.emit('mesaj_gonder', { oda_kodu: currentRoom, mesaj: msg });
            chatInput.value = ''; 
        }
    });

    document.getElementById('chat-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') document.getElementById('send-btn').click();
    });

    socket.on('oda_bilgisi', (data) => {
        currentRoom = data.oda_kodu;
        wordLength = data.uzunluk;
        document.getElementById('room-display').innerHTML = `Oda: <span style="color:#b59f3b">${currentRoom}</span> (${wordLength} Harf)`;
        document.getElementById('next-round').style.display = 'none';
        document.getElementById('scoreboard').style.display = 'block';
        document.getElementById('chat-container').style.display = 'flex';
        resetGame();
        createBoard();
    });

    socket.on('yeni_mesaj', (data) => {
        const chatBox = document.getElementById('chat-messages');
        const msgDiv = document.createElement('div');
        msgDiv.innerHTML = `<span class="sender">${data.gonderen}:</span> ${data.mesaj}`;
        chatBox.appendChild(msgDiv);
        chatBox.scrollTop = chatBox.scrollHeight; 
    });

    socket.on('tur_bitti', () => {
        document.getElementById('next-round').style.display = 'inline-block';
    });

    socket.on('yeni_tur_basladi', () => {
        document.getElementById('next-round').style.display = 'none';
        resetGame();
        createBoard();
        showMessage("<i class='fas fa-info-circle'></i> Yeni tur başladı! İyi şanslar.");
    });

    socket.on('puan_tablosu', (puanlar) => {
        const scoreList = document.getElementById('score-list');
        scoreList.innerHTML = '';
        
        const siraliPuanlar = Object.entries(puanlar).sort((a, b) => b[1] - a[1]);

        siraliPuanlar.forEach(([oyuncu, puan], index) => {
            const li = document.createElement('li');
            let madalya = "";
            if(index === 0 && puan > 0) madalya = "🥇 ";
            else if(index === 1 && puan > 0) madalya = "🥈 ";
            
            li.innerHTML = `${madalya}<b>${oyuncu}</b>: ${puan} Puan`;
            scoreList.appendChild(li);
        });
    });

    socket.on('gecersiz_kelime', (data) => {
        const row = document.querySelectorAll('.row')[currentRow];
        row.classList.add('shake');
        setTimeout(() => row.classList.remove('shake'), 500);
        showMessage("<i class='fas fa-exclamation-triangle' style='color:#b59f3b'></i> " + data.mesaj);
    });

    socket.on('tahmin_sonucu', (data) => {
        const row = document.querySelectorAll('.row')[currentRow];
        const renkler = data.renkler;
        const tahminHarfleri = data.tahmin.split('');
        
        if (data.oyun_bitti_mi) {
            isGameOver = true;
        }

        tahminHarfleri.forEach((harf, index) => {
            const box = row.children[index];
            setTimeout(() => {
                box.classList.add('flip');
                setTimeout(() => {
                    box.classList.add(renkler[index]);
                    const keyButton = document.querySelector(`.key[data-key="${harf}"]`);
                    if (keyButton && !keyButton.classList.contains('yesil')) {
                        keyButton.classList.remove('sari', 'gri');
                        keyButton.classList.add(renkler[index]);
                    }
                }, 250);
            }, index * 100);
        });

        setTimeout(() => {
            if (data.dogru_mu) {
                fireConfetti(); 
            }
            currentRow++;
            currentTile = 0;
            currentGuess = [];
        }, (wordLength * 100) + 500);
    });

    socket.on('bildin_mesaji', (data) => {
        setTimeout(() => {
            showMessage(data.mesaj);
        }, (wordLength * 100) + 600);
    });

    socket.on('hata', (data) => {
        showMessage("<i class='fas fa-times-circle' style='color:red'></i> " + data.mesaj);
    });

    const keys = document.querySelectorAll('.key');
    keys.forEach(key => {
        key.addEventListener('click', () => handleInput(key.getAttribute('data-key')));
    });

    document.addEventListener('keydown', (e) => {
        if (e.target.tagName === 'INPUT') return;
        if (document.getElementById('custom-modal').style.display === 'flex') {
            if (e.key === 'Enter') document.getElementById('modal-close-btn').click(); 
            return; 
        }

        let key = e.key.toUpperCase();
        if (key === 'BACKSPACE') handleInput('BACKSPACE');
        else if (key === 'ENTER') handleInput('ENTER');
        else if (/^[A-ZÇĞİÖŞÜ]$/.test(key)) {
            if (e.key === 'i') key = 'İ';
            handleInput(key);
        }
    });
});

function handleInput(letter) {
    if (!currentRoom) {
        showMessage("Lütfen önce bir odaya katılın veya oda kurun!");
        return;
    }
    if (isGameOver) return; 

    if (letter === 'BACKSPACE') deleteLetter();
    else if (letter === 'ENTER') checkGuess();
    else addLetter(letter);
}

function addLetter(letter) {
    if (currentTile < wordLength && currentRow < 6) {
        const row = document.querySelectorAll('.row')[currentRow];
        row.children[currentTile].textContent = letter;
        currentGuess.push(letter);
        currentTile++;
    }
}

function deleteLetter() {
    if (currentTile > 0) {
        currentTile--;
        const row = document.querySelectorAll('.row')[currentRow];
        row.children[currentTile].textContent = '';
        currentGuess.pop();
    }
}

function checkGuess() {
    if (currentTile < wordLength) {
        const row = document.querySelectorAll('.row')[currentRow];
        row.classList.add('shake');
        setTimeout(() => row.classList.remove('shake'), 500);
        return;
    }
    const guessString = currentGuess.join('');
    socket.emit('tahmin_yap', { oda_kodu: currentRoom, tahmin: guessString, satir: currentRow });
}

// DÜZELTİLEN KISIM BURASI: Kutu boyutlarını ve sütun sayısını geri getirdik
function createBoard() {
    const board = document.getElementById('game-board');
    board.innerHTML = '';
    for (let i = 0; i < 6; i++) {
        const row = document.createElement('div');
        row.className = 'row';
        
        // Sütun sayısını kelime uzunluğuna göre ayarlıyoruz (5 harfse 5 sütun)
        row.style.gridTemplateColumns = `repeat(${wordLength}, 1fr)`;
        
        for (let j = 0; j < wordLength; j++) {
            const box = document.createElement('div');
            box.className = 'box';
            
            // Kutucuk boyutlarını kelime uzunluğuna göre daraltıp genişletiyoruz
            let size = wordLength === 7 ? '45px' : (wordLength === 6 ? '50px' : '55px');
            box.style.width = size;
            box.style.height = size;
            
            row.appendChild(box);
        }
        board.appendChild(row);
    }
}

function resetGame() {
    currentRow = 0; 
    currentTile = 0; 
    currentGuess = [];
    isGameOver = false; 
    document.querySelectorAll('.key').forEach(k => k.classList.remove('yesil', 'sari', 'gri'));
}