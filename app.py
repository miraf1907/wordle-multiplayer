from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
import random
import markupsafe

# Sözlük dosyamızdan kelimeleri çekiyoruz
from sozluk import KELIME_HAVUZU

app = Flask(__name__)
app.config['SECRET_KEY'] = 'kelime_oyunu_ozel_anahtar'
# SocketIO ayarlarını en stabil hale getirdik
socketio = SocketIO(app, cors_allowed_origins="*", async_mode=None)

ODALAR = {}

@app.route('/')
def ana_sayfa():
    return render_template('index.html')

@socketio.on('oda_kur')
def oda_kur(data):
    try:
        oda_kodu = str(random.randint(1000, 9999))
        # Verinin gelmeme ihtimaline karşı güvenli alım
        uzunluk = int(data.get('uzunluk', 5))
        oyuncu_adi = markupsafe.escape(str(data.get('oyuncu_adi', '')).strip()) or "Oyuncu 1"
        
        # Kelime seçimi (Eğer o uzunlukta kelime yoksa hata vermemesi için koruma)
        havuz = KELIME_HAVUZU.get(uzunluk, ["KALEM"])
        if not havuz: havuz = ["KALEM"]
        gizli_kelime = random.choice(havuz)
        
        ODALAR[oda_kodu] = {
            "kelime": gizli_kelime,
            "uzunluk": uzunluk,
            "oyuncular": {request.sid: oyuncu_adi}, 
            "puanlar": {oyuncu_adi: 0},
            "bilen_sayisi": 0,
            "bitirenler": [] 
        }
        
        join_room(oda_kodu)
        print(f"--- ODA KURULDU: {oda_kodu} | KELİME: {gizli_kelime} ---")
        
        emit('oda_bilgisi', {'oda_kodu': oda_kodu, 'uzunluk': uzunluk}, room=oda_kodu)
        emit('puan_tablosu', ODALAR[oda_kodu]["puanlar"], room=oda_kodu)
    except Exception as e:
        print(f"--- ODA KURMA HATASI: {e} ---")

@socketio.on('odaya_katil')
def odaya_katil(data):
    oda_kodu = str(data.get('oda_kodu'))
    if oda_kodu in ODALAR:
        join_room(oda_kodu)
        oyuncu_adi = markupsafe.escape(str(data.get('oyuncu_adi', '')).strip()) or f"Oyuncu {len(ODALAR[oda_kodu]['oyuncular'])+1}"
        
        # İsim çakışması kontrolü
        while oyuncu_adi in ODALAR[oda_kodu]["puanlar"]:
            oyuncu_adi += "+"

        ODALAR[oda_kodu]["oyuncular"][request.sid] = oyuncu_adi
        ODALAR[oda_kodu]["puanlar"][oyuncu_adi] = 0
        
        emit('oda_bilgisi', {'oda_kodu': oda_kodu, 'uzunluk': ODALAR[oda_kodu]["uzunluk"]})
        emit('puan_tablosu', ODALAR[oda_kodu]["puanlar"], room=oda_kodu)
    else:
        emit('hata', {'mesaj': 'Oda bulunamadı!'})

@socketio.on('tahmin_yap')
def tahmin_yap(data):
    oda_kodu = str(data.get('oda_kodu'))
    tahmin = str(data.get('tahmin', '')).upper()
    satir = data.get('satir')
    sid = request.sid
    
    if oda_kodu not in ODALAR: return

    # Sözlük kontrolü
    if tahmin not in KELIME_HAVUZU.get(len(tahmin), []):
        emit('gecersiz_kelime', {'mesaj': 'Sözlükte bu kelime yok!'})
        return

    gizli_kelime = ODALAR[oda_kodu]["kelime"]
    uzunluk = len(tahmin)
    renkler = ["gri"] * uzunluk
    harf_sayilari = {h: gizli_kelime.count(h) for h in set(gizli_kelime)}

    for i in range(uzunluk):
        if tahmin[i] == gizli_kelime[i]:
            renkler[i] = "yesil"
            harf_sayilari[tahmin[i]] -= 1

    for i in range(uzunluk):
        if renkler[i] == "gri" and tahmin[i] in harf_sayilari and harf_sayilari[tahmin[i]] > 0:
            renkler[i] = "sari"
            harf_sayilari[tahmin[i]] -= 1

    dogru_mu = (tahmin == gizli_kelime)
    oyun_bitti_mi = dogru_mu or (satir == 5)

    emit('tahmin_sonucu', {
        'renkler': renkler, 
        'dogru_mu': dogru_mu,
        'tahmin': tahmin,
        'oyun_bitti_mi': oyun_bitti_mi
    })

    if dogru_mu:
        if sid not in ODALAR[oda_kodu]["bitirenler"]:
            ODALAR[oda_kodu]["bitirenler"].append(sid)
            ODALAR[oda_kodu]["bilen_sayisi"] += 1
            oyuncu_adi = ODALAR[oda_kodu]["oyuncular"][sid]
            ODALAR[oda_kodu]["puanlar"][oyuncu_adi] += 10
            emit('puan_tablosu', ODALAR[oda_kodu]["puanlar"], room=oda_kodu)
            emit('bildin_mesaji', {'mesaj': f"🎉 Tebrikler {oyuncu_adi}! Bildin!"})
    elif satir == 5:
        emit('bildin_mesaji', {'mesaj': f" Hakkın bitti! Kelime: {gizli_kelime}"})

    if len(ODALAR[oda_kodu]["bitirenler"]) == len(ODALAR[oda_kodu]["oyuncular"]):
        emit('tur_bitti', {}, room=oda_kodu)

@socketio.on('yeni_tur')
def yeni_tur(data):
    oda_kodu = str(data.get('oda_kodu'))
    if oda_kodu in ODALAR:
        uzunluk = ODALAR[oda_kodu]["uzunluk"]
        ODALAR[oda_kodu]["kelime"] = random.choice(KELIME_HAVUZU.get(uzunluk, ["KALEM"]))
        ODALAR[oda_kodu]["bilen_sayisi"] = 0
        ODALAR[oda_kodu]["bitirenler"] = []
        emit('yeni_tur_basladi', {}, room=oda_kodu)

@socketio.on('mesaj_gonder')
def mesaj_gonder(data):
    oda_kodu = str(data.get('oda_kodu'))
    mesaj = markupsafe.escape(str(data.get('mesaj', '')))
    if oda_kodu in ODALAR:
        oyuncu_adi = ODALAR[oda_kodu]["oyuncular"].get(request.sid, "Bilinmeyen")
        emit('yeni_mesaj', {'gonderen': oyuncu_adi, 'mesaj': mesaj}, room=oda_kodu)

if __name__ == '__main__':
    socketio.run(app, debug=True)