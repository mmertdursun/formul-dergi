"""Kaynak sayıları sayilar/*.json dosyalarına derler ve index.json'u günceller."""
import importlib, json, os, sys

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
AYLAR = ["ocak", "subat", "mart", "nisan", "mayis", "haziran", "temmuz", "agustos", "eylul", "ekim", "kasim", "aralik"]

index_yolu = os.path.join(KOK, "index.json")
index = json.load(open(index_yolu, encoding="utf-8"))
kayit = {s["no"]: s for s in index["sayilar"]}

for ad in sorted(os.listdir(os.path.dirname(os.path.abspath(__file__)))):
    if not (ad.startswith("sayi_") and ad.endswith(".py")):
        continue
    veri = importlib.import_module(ad[:-3]).SAYI_VERI
    no = veri["no"]
    dosya = f"2026-{no:02d}-{AYLAR[no-1]}.json"
    with open(os.path.join(KOK, "sayilar", dosya), "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=1)
    eski = kayit.get(no, {})
    kayit[no] = {"no": no, "ad": veri.get("ad", eski.get("ad")), "ad_tr": veri.get("ad_tr", eski.get("ad_tr")), "donem": veri["donem"], "tema": veri["tema"], "acilis": f"2026-{no:02d}-01", "dosya": dosya}
    cumle = sum(len(b.get("s", [])) for bol in veri["bolumler"] for b in bol["bloklar"] if b["t"] in ("p", "kutu", "liste"))
    print(f"{dosya}: {len(veri['bolumler'])} bölüm, {cumle} cümle, {len(veri['quiz'])} soru, {len(veri['bulmacalar'])} bulmaca, {len(veri['terimler'])} terim")

index["sayilar"] = [kayit[k] for k in sorted(kayit)]
index["surum"] = 2
json.dump(index, open(index_yolu, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
