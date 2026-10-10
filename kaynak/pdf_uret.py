"""Öğretmen sürümü PDF'leri üretir: docs/ogretmen/<sayı>.pdf

Her sayının İngilizce metni, cümle cümle Türkçesi, sorular ve cevap anahtarıyla
yazdırılabilir bir A4 dosyası. Kullanım: python3 kaynak/pdf_uret.py
"""
import html
import json
import os
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CIKTI = os.path.join(KOK, "docs", "ogretmen")
FONT = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("Govde", FONT + "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("Govde-B", FONT + "DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Govde-I", FONT + "DejaVuSans-Oblique.ttf"))
pdfmetrics.registerFont(TTFont("Govde-BI", FONT + "DejaVuSans-BoldOblique.ttf"))
pdfmetrics.registerFont(TTFont("Baslik", FONT + "DejaVuSerif-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Mono", FONT + "DejaVuSansMono.ttf"))
pdfmetrics.registerFontFamily("Govde", normal="Govde", bold="Govde-B", italic="Govde-I", boldItalic="Govde-BI")

MUREKKEP = colors.HexColor("#1F2430")
GRI = colors.HexColor("#5B6170")


def stiller(renk):
    r = colors.HexColor(renk)
    return {
        "kapak": ParagraphStyle("kapak", fontName="Baslik", fontSize=30, leading=34, textColor=r),
        "kapak_alt": ParagraphStyle("kapak_alt", fontName="Govde", fontSize=12, leading=16, textColor=GRI),
        "bolum": ParagraphStyle("bolum", fontName="Baslik", fontSize=17, leading=21, textColor=r, spaceBefore=6, spaceAfter=2),
        "bolum_tr": ParagraphStyle("bolum_tr", fontName="Govde-I", fontSize=10.5, leading=14, textColor=GRI, spaceAfter=8),
        "h": ParagraphStyle("h", fontName="Govde-B", fontSize=12, leading=16, textColor=MUREKKEP, spaceBefore=8, spaceAfter=1),
        "h_tr": ParagraphStyle("h_tr", fontName="Govde-I", fontSize=9.5, leading=12, textColor=GRI, spaceAfter=4),
        "en": ParagraphStyle("en", fontName="Govde", fontSize=10.5, leading=15, textColor=MUREKKEP, spaceAfter=2),
        "tr": ParagraphStyle("tr", fontName="Govde-I", fontSize=9, leading=12.5, textColor=GRI, spaceAfter=7, leftIndent=8),
        "formul": ParagraphStyle("formul", fontName="Mono", fontSize=11, leading=16, alignment=TA_CENTER, spaceBefore=4, spaceAfter=6),
        "kutu_b": ParagraphStyle("kutu_b", fontName="Govde-B", fontSize=10.5, leading=14, textColor=r),
        "kucuk": ParagraphStyle("kucuk", fontName="Govde", fontSize=8.5, leading=11, textColor=GRI),
        "hucre": ParagraphStyle("hucre", fontName="Govde", fontSize=9, leading=12),
    }


def md(metin):
    """**kalın** > <b>, HTML karakterlerini kaçır."""
    m = html.escape(metin, quote=False)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", m)


def cumle_ciftleri(ciftler, s, madde=False):
    """İngilizce paragraf, altında cümle cümle Türkçe."""
    on = "• " if madde else ""
    if madde:
        out = []
        for en, tr in ciftler:
            out.append(Paragraph(on + md(en), s["en"]))
            out.append(Paragraph(md(tr), s["tr"]))
        return out
    en = " ".join(md(c[0]) for c in ciftler)
    tr = " ".join(md(c[1]) for c in ciftler)
    return [Paragraph(en, s["en"]), Paragraph(tr, s["tr"])]


def blok(b, s, renk):
    t = b["t"]
    if t == "p":
        return cumle_ciftleri(b["s"], s)
    if t == "h":
        return [Paragraph(md(b["s"][0]), s["h"]), Paragraph(md(b["s"][1]), s["h_tr"])]
    if t == "formul":
        return [Paragraph(html.escape(b["m"]), s["formul"])]
    if t == "liste":
        return cumle_ciftleri(b["s"], s, madde=True)
    if t == "kutu":
        ic = [Paragraph(f"{md(b['baslik'][0])} · <i>{md(b['baslik'][1])}</i>", s["kutu_b"]), Spacer(1, 3)]
        ic += cumle_ciftleri(b["s"], s, madde=True)
        tablo = Table([[ic]], colWidths=[170 * mm])
        tablo.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(renk).clone(alpha=0.07)),
            ("LINEBEFORE", (0, 0), (0, -1), 2.5, colors.HexColor(renk)),
            ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        return [Spacer(1, 3), tablo, Spacer(1, 6)]
    if t == "terimler":
        satir = [[Paragraph(md(en), s["hucre"]), Paragraph(f"<i>{md(tr)}</i>", s["hucre"])] for en, tr in b["items"]]
        tablo = Table(satir, colWidths=[70 * mm, 100 * mm])
        tablo.setStyle(TableStyle([
            ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#D6D9E0")),
            ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        return [Spacer(1, 4), Paragraph("Words to know · <i>Bilinmesi gereken kelimeler</i>", s["kutu_b"]), Spacer(1, 2), tablo, Spacer(1, 8)]
    if t == "tablo":
        veri = [[Paragraph(f"<b>{md(h)}</b>", s["hucre"]) for h in b["basliklar"]]]
        veri += [[Paragraph(md(str(x)), s["hucre"]) for x in sat] for sat in b["satirlar"]]
        tablo = Table(veri, colWidths=[170 * mm / len(b["basliklar"])] * len(b["basliklar"]))
        tablo.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C9CDD6")),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF0F4")),
        ]))
        return [Spacer(1, 4), tablo, Spacer(1, 8)]
    if t == "portre":
        out = [Paragraph(f"<b>{md(b['ad'])}</b> ({md(b['yillar'])})", s["h"])]
        out += cumle_ciftleri(b["s"], s)
        out.append(Paragraph(md(b["kaynak"]), s["kucuk"]))
        return out
    return []


def uret(veri, dosya_adi):
    renk = veri["kapak"]["renkler"][0]
    s = stiller(renk)
    hikaye = []
    hikaye.append(Paragraph("Matematik Molası · Öğretmen sürümü", s["kapak_alt"]))
    hikaye.append(Spacer(1, 4))
    hikaye.append(Paragraph(md(veri.get("ad") or veri["donem"]), s["kapak"]))
    hikaye.append(Paragraph(f"{md(veri.get('ad_tr', ''))} · No. {veri['no']} · {md(veri['donem'])}", s["kapak_alt"]))
    hikaye.append(Paragraph(f"Tema: {md(veri['tema'])}", s["kapak_alt"]))
    hikaye.append(Spacer(1, 6))
    hikaye.append(Paragraph(
        "Bu dosyada İngilizce metnin her paragrafının altında Türkçesi yer alır. "
        "Sorular ve bulmacalar en sonda, cevap anahtarıyla birlikte verilmiştir. "
        "Sınıfta çoğaltılarak serbestçe kullanılabilir.", s["kucuk"]))
    hikaye.append(Spacer(1, 10))

    for bol in veri["bolumler"]:
        baslik = [Paragraph(md(bol["baslik"]), stiller(bol.get("renk", renk))["bolum"]),
                  Paragraph(md(bol["baslik_tr"]), s["bolum_tr"])]
        icerik = []
        for b in bol["bloklar"]:
            icerik += blok(b, s, bol.get("renk", renk))
        hikaye.append(KeepTogether(baslik + icerik[:2]))
        hikaye += icerik[2:]
        hikaye.append(Spacer(1, 10))

    # Sorular (öğrenci sayfası) ve cevap anahtarı
    hikaye.append(PageBreak())
    hikaye.append(Paragraph("Quiz · <i>Sorular</i>", s["bolum"]))
    harfler = "ABCDEFGH"
    for i, q in enumerate(veri.get("quiz", []), 1):
        sec = "   ".join(f"{harfler[j]}) {md(x)}" for j, x in enumerate(q["secenekler"]))
        hikaye.append(KeepTogether([
            Paragraph(f"<b>{i}.</b> {md(q['soru'])}", s["en"]),
            Paragraph(md(q["soru_tr"]), s["tr"]),
            Paragraph(sec, s["en"]), Spacer(1, 6)]))

    bulmacalar = veri.get("bulmacalar", [])
    if bulmacalar:
        hikaye.append(Spacer(1, 6))
        hikaye.append(Paragraph("Puzzles · <i>Bulmacalar</i>", s["bolum"]))
        for i, z in enumerate(bulmacalar, 1):
            if z["tip"] == "anagram":
                hikaye.append(Paragraph(f"<b>{i}.</b> Anagram: <b>{md(z['karisik'])}</b> · {md(z['ipucu'])}", s["en"]))
                hikaye.append(Paragraph(md(z["ipucu_tr"]), s["tr"]))
            elif z["tip"] == "eslestir":
                sol = [c[0] for c in z["ciftler"]]
                sag = sorted(c[1] for c in z["ciftler"])
                satir = [[Paragraph(f"{j+1}. {md(a)}", s["hucre"]), Paragraph(f"{harfler[j]}) {md(b)}", s["hucre"])]
                         for j, (a, b) in enumerate(zip(sol, sag))]
                hikaye.append(Paragraph(f"<b>{i}.</b> {md(z['baslik'])} · <i>{md(z['baslik_tr'])}</i>", s["en"]))
                t = Table(satir, colWidths=[85 * mm, 85 * mm])
                hikaye += [t, Spacer(1, 8)]
            elif z["tip"] == "mantik":
                hikaye.append(Paragraph(f"<b>{i}. {md(z['baslik'])}</b> · <i>{md(z['baslik_tr'])}</i>", s["en"]))
                hikaye.append(Paragraph(md(z["soru"]), s["en"]))
                hikaye.append(Paragraph(md(z["soru_tr"]), s["tr"]))

    hikaye.append(PageBreak())
    hikaye.append(Paragraph("Answer key · <i>Cevap anahtarı</i>", s["bolum"]))
    for i, q in enumerate(veri.get("quiz", []), 1):
        hikaye.append(Paragraph(f"<b>{i}. {harfler[q['dogru']]}</b> · {md(q['aciklama'])}", s["en"]))
        hikaye.append(Paragraph(md(q["aciklama_tr"]), s["tr"]))
    for i, z in enumerate(bulmacalar, 1):
        if z["tip"] == "anagram":
            hikaye.append(Paragraph(f"<b>{i}.</b> {md(z['cevap'])}", s["en"]))
        elif z["tip"] == "eslestir":
            sag = sorted(c[1] for c in z["ciftler"])
            eslesme = ", ".join(f"{j+1}-{harfler[sag.index(c[1])]}" for j, c in enumerate(z["ciftler"]))
            hikaye.append(Paragraph(f"<b>{i}.</b> {eslesme}", s["en"]))
        elif z["tip"] == "mantik":
            hikaye.append(Paragraph(f"<b>{i}.</b> {md(z['cevap'])}", s["en"]))
            hikaye.append(Paragraph(md(z["cevap_tr"]), s["tr"]))

    def sayfa(canvas, doc):
        canvas.saveState()
        canvas.setFont("Govde", 8)
        canvas.setFillColor(GRI)
        canvas.drawString(20 * mm, 12 * mm, f"Formül · Matematik Molası No. {veri['no']} · {veri['donem']}")
        canvas.drawRightString(190 * mm, 12 * mm, str(doc.page))
        canvas.restoreState()

    os.makedirs(CIKTI, exist_ok=True)
    yol = os.path.join(CIKTI, dosya_adi.replace(".json", ".pdf"))
    doc = SimpleDocTemplate(yol, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm,
                            bottomMargin=20 * mm, title=f"Matematik Molası No. {veri['no']} - Öğretmen sürümü",
                            author="Formül")
    doc.build(hikaye, onFirstPage=sayfa, onLaterPages=sayfa)
    return yol


def liste_sayfasi():
    """Liste, açılış tarihi gelen sayıları index2.json'dan okuyup kendisi gösterir."""
    sayfa = """<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Matematik Molası · Öğretmen PDF'leri</title>
<link rel="stylesheet" href="../stil.css">
</head>
<body>
<main>
  <h1>Öğretmen PDF'leri</h1>
  <p>Her sayının İngilizce metni, paragraf paragraf Türkçesi, soruları ve cevap anahtarı. Sınıfta çoğaltarak kullanabilirsiniz. Yeni sayı ayın ilk günü eklenir.</p>
  <ul id="liste"><li>Yükleniyor…</li></ul>
</main>
<script>
fetch('https://raw.githubusercontent.com/mmertdursun/formul-dergi/main/index2.json')
  .then(r => r.json())
  .then(j => {
    const bugun = new Date().toISOString().slice(0, 10);
    const ul = document.getElementById('liste');
    ul.innerHTML = '';
    j.sayilar.filter(s => s.dosya.endsWith('.json') && s.acilis <= bugun)
      .sort((a, b) => b.no - a.no)
      .forEach(s => {
        const li = document.createElement('li');
        const a = document.createElement('a');
        a.href = s.dosya.replace('.json', '.pdf');
        a.textContent = 'No. ' + s.no + ' · ' + s.donem + ' · ' + (s.ad || '');
        li.appendChild(a);
        if (s.ad_tr) li.append(' ' + s.ad_tr);
        ul.appendChild(li);
      });
  })
  .catch(() => { document.getElementById('liste').innerHTML = '<li>Liste yüklenemedi.</li>'; });
</script>
</body>
</html>
"""
    open(os.path.join(CIKTI, "index.html"), "w", encoding="utf-8").write(sayfa)


if __name__ == "__main__":
    index = json.load(open(os.path.join(KOK, "index2.json"), encoding="utf-8"))
    for kayit in index["sayilar"]:
        dosya = kayit["dosya"]
        if not dosya.endswith(".json"):
            continue
        veri = json.load(open(os.path.join(KOK, "sayilar", dosya), encoding="utf-8"))
        print(uret(veri, dosya))
    liste_sayfasi()
