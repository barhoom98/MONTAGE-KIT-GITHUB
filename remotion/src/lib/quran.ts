import { staticFile } from "remotion";

// قراءة نص القرآن من ملفات تنزيل (public/quran). النص ما بينكتب يدوي أبداً:
// القالب بياخذ رقم السورة والآية وبيسحب النص حرفياً من الملف.

export type Sura = { index: number; ayas: number; name: string; tname: string; ename: string; type: string };
export type Ayah = { sura: number; aya: number; text: string; basmala: boolean };

let cache: Promise<{ verses: Map<string, string>; suras: Sura[] }> | null = null;

const loadQuran = () => {
  cache ??= (async () => {
    const [txtRes, surasRes] = await Promise.all([
      fetch(staticFile("quran/quran-uthmani.txt")),
      fetch(staticFile("quran/suras.json")),
    ]);
    if (!txtRes.ok || !surasRes.ok) {
      throw new Error("ملفات القرآن مش موجودة بـ public/quran. شغّل: node scripts/fetch-tanzil.mjs");
    }
    const verses = new Map<string, string>();
    for (const line of (await txtRes.text()).split(/\r?\n/)) {
      const m = /^(\d+)\|(\d+)\|(.+)$/.exec(line);
      if (m) verses.set(`${Number(m[1])}:${Number(m[2])}`, m[3]);
    }
    return { verses, suras: (await surasRes.json()) as Sura[] };
  })();
  return cache;
};

// تنزيل بيحط البسملة بأول آية من كل سورة (ما عدا الفاتحة والتوبة).
// بنفصلها لسطر لحال للعرض بس، والنص نفسه ما بيتغير.
export const getAyat = async (sura: number, from: number, to: number) => {
  const { verses, suras } = await loadQuran();
  const info = suras.find((s) => s.index === sura);
  if (!info) throw new Error(`رقم السورة ${sura} غلط (من 1 لـ 114)`);
  if (from < 1 || to < from || to > info.ayas) {
    throw new Error(`سورة ${info.name} فيها ${info.ayas} آية، والمدى ${from}–${to} غلط`);
  }
  const basmalaText = verses.get("1:1")!;
  const ayat: Ayah[] = [];
  for (let aya = from; aya <= to; aya++) {
    const text = verses.get(`${sura}:${aya}`)!;
    const hasBasmala = aya === 1 && sura !== 1 && sura !== 9 && text.startsWith(`${basmalaText} `);
    ayat.push({
      sura,
      aya,
      text: hasBasmala ? text.slice(basmalaText.length + 1) : text,
      basmala: hasBasmala,
    });
  }
  return { sura: info, ayat, basmalaText };
};

const AR_DIGITS = "٠١٢٣٤٥٦٧٨٩";
export const toArabicDigits = (n: number) => String(n).replace(/\d/g, (d) => AR_DIGITS[Number(d)]);

// مسار ملف التلاوة بنفس ترتيب مستودع thamarat-aya-audio (وEveryAyah): SSSAAA.mp3
export const recitationPath = (base: string, reciter: string, sura: number, aya: number) =>
  `${base.replace(/\/+$/, "")}/${reciter}/${String(sura).padStart(3, "0")}${String(aya).padStart(3, "0")}.mp3`;
