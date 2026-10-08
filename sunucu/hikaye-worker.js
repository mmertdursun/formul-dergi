// Formül · Hikâye sunucusu (Cloudflare Worker)
// App seçilen kelimeleri ve istenen uzunluğu gönderir, Worker Gemini'ye yazdırır.
// Gemini anahtarı yalnızca burada, GEMINI_API_KEY gizli değişkeninde durur.
//
// Gerekli değişkenler (Settings > Variables and Secrets):
//   GEMINI_API_KEY  (Secret)  Google AI Studio anahtarı
//   APP_TOKEN       (Secret)  App'in gönderdiği ortak anahtar: formul-2026-hikaye
//   MODEL           (Text, isteğe bağlı)  varsayılan gemini-2.5-flash

const MODELLER = ["gemini-2.5-flash", "gemini-flash-latest", "gemini-2.0-flash"];

export default {
  async fetch(istek, env) {
    if (istek.method === "OPTIONS") return cevap({}, 204);
    if (istek.method !== "POST") return cevap({ hata: "POST bekleniyor" }, 405);
    if (env.APP_TOKEN && istek.headers.get("x-formul-token") !== env.APP_TOKEN) {
      return cevap({ hata: "yetkisiz" }, 401);
    }

    let govde;
    try { govde = await istek.json(); } catch { return cevap({ hata: "geçersiz JSON" }, 400); }

    const kelimeler = (Array.isArray(govde.kelimeler) ? govde.kelimeler : [])
      .map((k) => String(k).trim()).filter(Boolean).slice(0, 15);
    const uzunluk = Math.min(500, Math.max(60, parseInt(govde.uzunluk, 10) || 150));
    const seviye = ["A2", "B1", "B2", "C1"].includes(govde.seviye) ? govde.seviye : "B1";
    if (kelimeler.length === 0) return cevap({ hata: "en az bir kelime seçin" }, 400);

    const modeller = env.MODEL ? [env.MODEL, ...MODELLER] : MODELLER;
    let sonHata = "";
    for (let deneme = 0; deneme < 2; deneme++) {
      for (const model of modeller) {
        try {
          const hikaye = await yaz(env.GEMINI_API_KEY, model, kelimeler, uzunluk, seviye);
          const sayi = kelimeSay(hikaye);
          // Hedefin %25'inden fazla saparsa bir kez daha dene
          if (deneme === 0 && Math.abs(sayi - uzunluk) > uzunluk * 0.25) { sonHata = `uzunluk ${sayi}`; break; }
          return cevap({ ...hikaye, kelime_sayisi: sayi, model });
        } catch (e) {
          sonHata = String(e.message || e);
          if (!/404|not found|not supported/i.test(sonHata)) break;
        }
      }
    }
    return cevap({ hata: "Hikâye yazılamadı", ayrinti: sonHata }, 502);
  },
};

async function yaz(anahtar, model, kelimeler, uzunluk, seviye) {
  const yonerge = `Write an original, engaging short story in English for a Turkish learner of English at CEFR ${seviye} level.
The story must be about ${uzunluk} words long (stay within 10% of ${uzunluk}).
It must naturally use ALL of these target words or phrases at least once: ${kelimeler.join(", ")}.
Every time a target word (or a natural inflected form of it) appears, wrap it in double asterisks like **word**.
Split the story into 2-6 paragraphs and every paragraph into sentences.
For every sentence give a natural, faithful Turkish translation, and wrap the Turkish equivalent of each target word in ** too.
Also give a short title in English and Turkish.
Keep the content friendly and suitable for all ages. Do not use semicolons.`;

  const r = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`, {
    method: "POST",
    headers: { "content-type": "application/json", "x-goog-api-key": anahtar },
    body: JSON.stringify({
      contents: [{ role: "user", parts: [{ text: yonerge }] }],
      generationConfig: {
        temperature: 0.9,
        responseMimeType: "application/json",
        responseSchema: {
          type: "OBJECT",
          properties: {
            baslik_en: { type: "STRING" },
            baslik_tr: { type: "STRING" },
            paragraflar: {
              type: "ARRAY",
              items: {
                type: "ARRAY",
                items: {
                  type: "OBJECT",
                  properties: { en: { type: "STRING" }, tr: { type: "STRING" } },
                  required: ["en", "tr"],
                },
              },
            },
          },
          required: ["baslik_en", "baslik_tr", "paragraflar"],
        },
      },
    }),
  });
  if (!r.ok) throw new Error(`${r.status} ${(await r.text()).slice(0, 200)}`);
  const veri = await r.json();
  const metin = veri?.candidates?.[0]?.content?.parts?.map((p) => p.text || "").join("") || "";
  const j = JSON.parse(metin);
  return {
    baslik: [j.baslik_en, j.baslik_tr],
    paragraflar: j.paragraflar
      .map((p) => p.filter((c) => c.en).map((c) => [c.en, c.tr || ""]))
      .filter((p) => p.length),
  };
}

function kelimeSay(h) {
  return h.paragraflar.flat().map((c) => c[0].replace(/\*\*/g, "").split(/\s+/).filter(Boolean).length)
    .reduce((a, b) => a + b, 0);
}

function cevap(veri, durum = 200) {
  return new Response(durum === 204 ? null : JSON.stringify(veri), {
    status: durum,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "access-control-allow-origin": "*",
      "access-control-allow-headers": "content-type, x-formul-token",
      "access-control-allow-methods": "POST, OPTIONS",
    },
  });
}
