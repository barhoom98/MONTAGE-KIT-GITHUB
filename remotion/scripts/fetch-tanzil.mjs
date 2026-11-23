#!/usr/bin/env node
// ينزّل نص القرآن (الرسم العثماني) وبيانات السور من مشروع تنزيل tanzil.net
// ويتحقق منه قبل ما يحفظه. النص بينحفظ حرفياً كما نزل، بدون أي تعديل
// (شروط تنزيل بتمنع تغيير النص).
//
// التشغيل: node scripts/fetch-tanzil.mjs   (من مجلد remotion)
// أو تلقائياً من GitHub Actions: .github/workflows/fetch-tanzil.yml

import { createHash } from "node:crypto";
import { mkdir, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const OUT_DIR = join(dirname(fileURLToPath(import.meta.url)), "..", "public", "quran");

// خيارات التنزيل: رسم عثماني، مع علامات الوقف وعلامة السجدة،
// وبدون علامة الربع (۞) حتى ما تطلع ببداية الآيات على الشاشة.
// ملاحظة: الخيارات عبارة عن checkboxes، فوجود الخيار بالرابط معناه "مفعّل"
// حتى لو قيمته false. عشان نلغي علامة الربع بنحذف rub من الرابط كلياً.
const TEXT_URL =
  "https://tanzil.net/pub/download/index.php?" +
  new URLSearchParams({
    marks: "true",
    sajdah: "true",
    tatweel: "true",
    quranType: "uthmani",
    outType: "txt-2",
    agree: "true",
  });
const META_URL = "https://tanzil.net/res/text/metadata/quran-data.xml";

const TOTAL_AYAT = 6236;
const TOTAL_SURAS = 114;

const fail = (msg) => {
  console.error(`✗ ${msg}`);
  process.exit(1);
};

const get = async (url) => {
  const res = await fetch(url, { headers: { "User-Agent": "montage-kit (tanzil fetch)" } });
  if (!res.ok) fail(`${url} → HTTP ${res.status}`);
  return res.text();
};

const text = await get(TEXT_URL);
const xml = await get(META_URL);

// 1) نص الآيات: كل سطر "سورة|آية|النص"، والأسطر اللي بتبدأ بـ # هي شروط الاستخدام
const verses = new Map();
for (const line of text.split(/\r?\n/)) {
  const m = /^(\d{1,3})\|(\d{1,3})\|(.+)$/.exec(line);
  if (m) verses.set(`${Number(m[1])}:${Number(m[2])}`, m[3]);
}
if (verses.size !== TOTAL_AYAT) {
  fail(`عدد الآيات ${verses.size} بدل ${TOTAL_AYAT}. أول 300 حرف من الرد:\n${text.slice(0, 300)}`);
}
if (!text.includes("Tanzil")) fail("النص نزل بدون شروط الاستخدام تبعت تنزيل، في إشي غلط بالرابط");
if ([...verses.values()].some((v) => v.includes("۞"))) fail("علامة الربع ۞ لسا موجودة بالنص");
const sajdat = [...verses.values()].filter((v) => v.includes("۩")).length;
if (sajdat !== 15) fail(`عدد علامات السجدة ${sajdat} بدل 15`);

// 2) بيانات السور من quran-data.xml
const suras = [];
for (const m of xml.matchAll(/<sura\s+([^>]+?)\/?>/g)) {
  const attrs = Object.fromEntries([...m[1].matchAll(/(\w+)="([^"]*)"/g)].map((a) => [a[1], a[2]]));
  suras.push({
    index: Number(attrs.index),
    ayas: Number(attrs.ayas),
    name: attrs.name,
    tname: attrs.tname,
    ename: attrs.ename,
    type: attrs.type,
  });
}
if (suras.length !== TOTAL_SURAS) fail(`عدد السور ${suras.length} بدل ${TOTAL_SURAS}`);

// 3) تطابق عدد آيات كل سورة بين الملفين
for (const s of suras) {
  for (let a = 1; a <= s.ayas; a++) {
    if (!verses.has(`${s.index}:${a}`)) fail(`الآية ${s.index}:${a} ناقصة من النص`);
  }
  if (verses.has(`${s.index}:${s.ayas + 1}`)) fail(`سورة ${s.index} فيها آيات أكثر من المتوقع`);
}

// 4) الحفظ: النص حرفياً + بيانات السور + ملف المصدر مع البصمة
await mkdir(OUT_DIR, { recursive: true });
await writeFile(join(OUT_DIR, "quran-uthmani.txt"), text);
await writeFile(join(OUT_DIR, "suras.json"), JSON.stringify(suras, null, 1) + "\n");

const sha = createHash("sha256").update(text).digest("hex");
const terms = text
  .split(/\r?\n/)
  .filter((l) => l.startsWith("#"))
  .join("\n");
await writeFile(
  join(OUT_DIR, "SOURCE.md"),
  `# مصدر النص القرآني

- المصدر: مشروع تنزيل (Tanzil Project) — https://tanzil.net
- النوع: الرسم العثماني (Uthmani)، مع علامات الوقف والسجدة، بدون علامة الربع
- رابط التنزيل: ${TEXT_URL}
- بيانات السور: ${META_URL}
- عدد الآيات: ${verses.size} — عدد السور: ${suras.length}
- SHA-256 لملف quran-uthmani.txt: \`${sha}\`

## شروط الاستخدام (كما وردت في الملف)

\`\`\`
${terms}
\`\`\`

لا تعدّل ملف quran-uthmani.txt يدوياً. لتحديثه شغّل \`node scripts/fetch-tanzil.mjs\`
أو شغّل workflow ‏fetch-tanzil من تبويب Actions.
`,
);

console.log(`✓ ${verses.size} آية و${suras.length} سورة — sha256 ${sha.slice(0, 16)}…`);
