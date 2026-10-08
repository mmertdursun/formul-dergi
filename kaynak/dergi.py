"""Formül dergi sayılarını JSON'a çeviren küçük yardımcılar.

Her sayı kaynak/sayi_XX.py içinde bu fonksiyonlarla yazılır,
`python3 kaynak/derle.py` ile sayilar/*.json üretilir.

Blok türleri (app'teki okuyucu bunları tanır):
  p       paragraf: cümle çiftleri [[en, tr], ...]
  h       ara başlık: [en, tr]
  kutu    renkli kutu: stil (bilgi | ipucu | sinif | soru), baslik [en, tr], cümleler
  formul  ortada duran formül satırı
  liste   madde işaretli cümle çiftleri
  terimler  "Math English" kutusu: [[en, tr], ...]
  tablo   basliklar [...], satirlar [[...], ...]
Cümle içinde **kalın** yazılan kelimeler vurgulu terim olarak gösterilir.
"""


def P(*cumleler):
    return {"t": "p", "s": [list(c) for c in cumleler]}


def H(en, tr):
    return {"t": "h", "s": [en, tr]}


def KUTU(stil, en, tr, *cumleler):
    return {"t": "kutu", "stil": stil, "baslik": [en, tr], "s": [list(c) for c in cumleler]}


def FORMUL(metin):
    return {"t": "formul", "m": metin}


def LISTE(*cumleler):
    return {"t": "liste", "s": [list(c) for c in cumleler]}


def TERIMLER(*ciftler):
    return {"t": "terimler", "items": [list(c) for c in ciftler]}


def TABLO(basliklar, *satirlar):
    return {"t": "tablo", "basliklar": list(basliklar), "satirlar": [list(s) for s in satirlar]}


def PORTRE(url, ad, yillar, aciklama_en, aciklama_tr, kaynak):
    """Küçük fotoğraflı kişi kartı."""
    return {"t": "portre", "url": url, "ad": ad, "yillar": yillar,
            "s": [[aciklama_en, aciklama_tr]], "kaynak": kaynak}


def BOLUM(id, ikon, renk, en, tr, *bloklar):
    return {"id": id, "ikon": ikon, "renk": renk, "baslik": en, "baslik_tr": tr, "bloklar": list(bloklar)}


def SORU(en, tr, secenekler, dogru, aciklama_en, aciklama_tr):
    return {"soru": en, "soru_tr": tr, "secenekler": list(secenekler), "dogru": dogru,
            "aciklama": aciklama_en, "aciklama_tr": aciklama_tr}


def ANAGRAM(karisik, cevap, ipucu_en, ipucu_tr):
    return {"tip": "anagram", "karisik": karisik, "cevap": cevap, "ipucu": ipucu_en, "ipucu_tr": ipucu_tr}


def ESLESTIR(baslik_en, baslik_tr, *ciftler):
    return {"tip": "eslestir", "baslik": baslik_en, "baslik_tr": baslik_tr, "ciftler": [list(c) for c in ciftler]}


def MANTIK(baslik_en, baslik_tr, soru_en, soru_tr, cevap_en, cevap_tr):
    return {"tip": "mantik", "baslik": baslik_en, "baslik_tr": baslik_tr, "soru": soru_en, "soru_tr": soru_tr,
            "cevap": cevap_en, "cevap_tr": cevap_tr}


def tum_terimler(bolumler):
    """Sayıdaki tüm Math English terimlerini (Kelime Yağmuru seti için) toplar."""
    gorulen, liste = set(), []
    for b in bolumler:
        for blok in b["bloklar"]:
            if blok["t"] == "terimler":
                for en, tr in blok["items"]:
                    if en.lower() not in gorulen:
                        gorulen.add(en.lower())
                        liste.append([en, tr])
    return liste


def SAYI(no, donem, donem_en, tema, tema_en, kapak, bolumler, quiz, bulmacalar, ad=None, ad_tr=None):
    return {
        "format": 2,
        "no": no,
        "ad": ad,
        "ad_tr": ad_tr,
        "donem": donem,
        "donem_en": donem_en,
        "tema": tema,
        "tema_en": tema_en,
        "kapak": kapak,
        "bolumler": bolumler,
        "quiz": quiz,
        "bulmacalar": bulmacalar,
        "terimler": tum_terimler(bolumler),
    }
