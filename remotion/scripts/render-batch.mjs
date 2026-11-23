#!/usr/bin/env node
// رندر دفعة كاملة: كل ملف JSON بمجلد = فيديو واحد (وغلاف إذا بدك).
// بعد الرندر بيوحّد علو الصوت على -14 LUFS عشان كل الفيديوهات تطلع بنفس المستوى.
//
//   node scripts/render-batch.mjs data/quizzawi
//   node scripts/render-batch.mjs data/quizzawi --force          (يعيد حتى الموجود)
//   node scripts/render-batch.mjs data/quizzawi -- --concurrency=4  (خيارات إضافية لـ remotion)
//
// شكل ملف JSON:
//   { "composition": "QuizReel", "props": { ... }, "cover": { "title": "...", "badge": "..." } }
// الناتج بـ out/<اسم المجلد>/<اسم الملف>.mp4 و <اسم الملف>-cover.png

import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { basename, join, resolve } from "node:path";
import { tmpdir } from "node:os";

const args = process.argv.slice(2);
const dashIndex = args.indexOf("--");
const extra = dashIndex >= 0 ? args.slice(dashIndex + 1) : [];
const own = dashIndex >= 0 ? args.slice(0, dashIndex) : args;
const force = own.includes("--force");
const dir = own.find((x) => !x.startsWith("--"));

if (!dir || !existsSync(dir)) {
  console.error("الاستخدام: node scripts/render-batch.mjs data/<مجلد القناة>");
  process.exit(1);
}

const run = (cmd, cmdArgs) => {
  const r = spawnSync(cmd, cmdArgs, { stdio: "inherit", shell: process.platform === "win32" });
  if (r.status !== 0) throw new Error(`فشل: ${cmd} ${cmdArgs.join(" ")}`);
};

const outDir = join("out", basename(resolve(dir)));
mkdirSync(outDir, { recursive: true });

console.log("• تجهيز البندل…");
run("npx", ["remotion", "bundle", "--log=error"]);

const files = readdirSync(dir).filter((f) => f.endsWith(".json")).sort();
let done = 0;
for (const file of files) {
  const name = file.replace(/\.json$/, "");
  const job = JSON.parse(readFileSync(join(dir, file), "utf8"));
  const final = join(outDir, `${name}.mp4`);
  if (existsSync(final) && !force) {
    console.log(`↷ ${name} موجود، تخطيته`);
    continue;
  }
  console.log(`▶ ${name} (${job.composition})`);
  const propsFile = join(tmpdir(), `props-${name}.json`);
  writeFileSync(propsFile, JSON.stringify(job.props ?? {}));
  const raw = join(outDir, `${name}.raw.mp4`);
  run("npx", ["remotion", "render", "build", job.composition, raw, `--props=${propsFile}`, "--log=error", ...extra]);

  // توحيد علو الصوت: -14 LUFS وذروة -1.5 dBTP، والفيديو بدون إعادة ترميز
  run("npx", [
    "remotion", "ffmpeg", "-y", "-v", "error", "-i", raw,
    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", final,
  ]);
  rmSync(raw);

  if (job.cover) {
    const coverProps = join(tmpdir(), `cover-${name}.json`);
    writeFileSync(coverProps, JSON.stringify({ channel: job.props?.channel, ...job.cover }));
    run("npx", ["remotion", "still", "build", "Cover", join(outDir, `${name}-cover.png`), `--props=${coverProps}`, "--log=error", ...extra]);
  }
  done++;
}
console.log(`✓ خلصت ${done} فيديو → ${outDir}`);
