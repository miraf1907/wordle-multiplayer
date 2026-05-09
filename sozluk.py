import requests
import random

# Gerçek ve çalışan bir Türkçe kelime listesi URL'si
URL = "https://raw.githubusercontent.com/mertemin/turkish-word-list/master/words.txt"

def kelimeleri_getir():
    try:
        print("--- SOZLUK BAGLANTISI KURULUYOR ---")
        response = requests.get(URL, timeout=10)
        
        # YENİ VE EN KRİTİK SATIR: Eğer sayfa bulunamazsa (404 vb) anında hata ver (Gizlice okumasın)
        response.raise_for_status() 
        
        satirlar = response.text.splitlines()
        havuz = {5: [], 6: [], 7: []}
        
        for kelime in satirlar:
            kelime = kelime.strip()
            kelime = kelime.replace('i', 'İ').upper()
            uzunluk = len(kelime)
            
            if uzunluk in [5, 6, 7]:
                if all(c in "ABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ" for c in kelime):
                    havuz[uzunluk].append(kelime)
        
        toplam = len(havuz[5]) + len(havuz[6]) + len(havuz[7])
        
        # Eğer bir terslik olur da yine 1-2 kelime gelirse iptal et
        if toplam < 100:
            raise ValueError("Yeterli kelime bulunamadı, site boş dönmüş olabilir.")
            
        print(f"--- BASARILI: {toplam} KELIME YUKLENDI ---")
        return havuz
        
    except Exception as e:
        print(f"--- HATA YAKALANDI: {e} ---")
        print("--- İNTERNET SÖZLÜĞÜ ÇÖKTÜ: BÜYÜK YEDEK LİSTE DEVREYE GİRİYOR! ---")
        
        # İnternet kopsa bile oyunun aslanlar gibi çalışmasını sağlayacak devasa yerel yedek havuz
        return {
            5: ["ARABA", "SELAM", "MASAL", "KALEM", "KİTAP", "BİLGİ", "SEVGİ", "ÇİÇEK", "BULUT", 
                "GÜNEŞ", "KAVUN", "KABAK", "BAHAR", "ŞEHİR", "SOKAK", "DUVAR", "TABAK", "ÇANTA", 
                "ELMAS", "FİDAN", "GİZEM", "IRMAK", "KABLO", "LİMON", "NOHUT", "ORMAN", "PAMUK", 
                "ROMAN", "TAVUK", "UZMAN", "YILAN", "ZEBRA", "MÜZİK", "RESİM", "DENİZ", "ÇOCUK", 
                "AKŞAM", "SABAH", "MEYVE", "SEBZE", "SAKAL", "KAŞIK", "ÇATAL", "BIÇAK", "DEMİR"],
            6: ["BARDAK", "KLAVYE", "SÖZLÜK", "GÖZLÜK", "YAPRAK", "BAYRAK", "ÇAKMAK", "FİNCAN",
                "GÖMLEK", "HEYKEL", "LASTİK", "MANTAR", "OTOBÜS", "PEYNİR", "TOPRAK", "ZEYTİN",
                "YOĞURT", "YASTIK", "YAPBOZ", "CÜZDAN", "DEFTER", "BÜLBÜL", "CENNET", "ŞAMPUAN"],
            7: ["YAZILIM", "PROGRAM", "ANAHTAR", "KUTUCUK", "KARINCA", "KELEBEK", "PENCERE", 
                "MAKARNA", "TELEFON", "YAKAMOZ", "GÖRÜNTÜ", "OYUNCAK", "KAMYON", "FABRİKA", 
                "ŞEMSİYE", "ASANSÖR", "ÇAMAŞIR", "TÜRKİYE", "İSTANBUL", "BİSİKLET", "DONDURMA"]
        }

KELIME_HAVUZU = kelimeleri_getir()