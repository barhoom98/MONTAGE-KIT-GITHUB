#!/usr/bin/env node
// بيولّد التعليق الصوتي من ElevenLabs مع توقيت كل حرف، وبيحوّله لترجمة كلمة بكلمة
// بصيغة Remotion (Caption[]) جاهزة لقوالب QuizReel وTipReel وAyahReel.
//
// توليد صوت + ترجمة (بدها ELEVENLABS_API_KEY):
//   node scripts/elevenlabs-captions.mjs --voice VOICE_ID --text scripts/q1.txt --out public/vo/q1
//   ← بيكتب public/vo/q1.mp3 و public/vo/q1.captions.json
//
// تحويل رد محفوظ من الـAPI (with-timestamps) بدون ما نولّد من جديد:
//   node scripts/elevenlabs-captions.mjs --from response.json --out public/vo/q1
//
// خيارات: --model eleven_multilingual_v2   --keep-tashkeel (الافتراضي: الترجمة بدون تشكيل)

import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname } from "node:path";
import { parseArgs } from "node:util";

const { values: a } = parseArgs({
  options: {
    voice: { type: "string" },
    text: { type: "string" },
    from: { type: "string" },
    out: { type: "string" },
    model: { type: "string", default: "eleven_multilingual_v2" },
    "keep-tashkeel": { type: "boolean", default: false },
  },
});

if (!a.out || (!a.from && !(a.voice && a.text))) {
  console.error("الاستخدام: --voice ID --text ملف.txt --out مسار   أو   --from رد.json --out مسار");
  process.exit(1);
}

let response;
if (a.from) {
  response = JSON.parse(await readFile(a.from, "utf8"));
} else {
  const key = process.env.ELEVENLABS_API_KEY;
  if (!key) {
    console.error("حط مفتاح ElevenLabs بمتغير ELEVENLABS_API_KEY");
    process.exit(1);
  }
  const text = (await readFile(a.text, "utf8")).trim();
  const res = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${a.voice}/with-timestamps`, {
    method: "POST",
    headers: { "xi-api-key": key, "Content-Type": "application/json" },
    body: JSON.stringify({ text, model_id: a.model }),
  });
  if (!res.ok) {
    console.error(`ElevenLabs رجّع ${res.status}: ${await res.text()}`);
    process.exit(1);
  }
  response = await res.json();
}

const al = response.alignment ?? response.normalized_alignment;
if (!al?.characters) {
  console.error("الرد ما فيه alignment. لازم يكون من endpoint ‏with-timestamps");
  process.exit(1);
}

// تجميع الحروف لكلمات
const TASHKEEL = /[ً-ْٰـ]/g;
const words = [];
let cur = null;
al.characters.forEach((ch, i) => {
  const start = al.character_start_times_seconds[i];
  const end = al.character_end_times_seconds[i];
  if (/\s/.test(ch)) {
    if (cur) words.push(cur);
    cur = null;
    return;
  }
  if (!cur) cur = { text: "", start, end };
  cur.text += ch;
  cur.end = end;
});
if (cur) words.push(cur);

const captions = words
  .map((w) => ({ ...w, text: a["keep-tashkeel"] ? w.text : w.text.replace(TASHKEEL, "") }))
  .filter((w) => w.text.length > 0)
  .map((w, i) => ({
    text: (i === 0 ? "" : " ") + w.text,
    startMs: Math.round(w.start * 1000),
    endMs: Math.round(w.end * 1000),
    timestampMs: Math.round(((w.start + w.end) / 2) * 1000),
    confidence: null,
  }));

await mkdir(dirname(a.out), { recursive: true });
if (response.audio_base64) await writeFile(`${a.out}.mp3`, Buffer.from(response.audio_base64, "base64"));
await writeFile(`${a.out}.captions.json`, JSON.stringify(captions, null, 1) + "\n");
console.log(`✓ ${captions.length} كلمة → ${a.out}.captions.json${response.audio_base64 ? ` و ${a.out}.mp3` : ""}`);
