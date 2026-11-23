# Remotion templates — rules for producing videos

This folder renders the channels' reels from JSON files. To make videos, write JSON files in `data/<channel>/` and run `npm run batch -- data/<channel>`. Do not edit the templates to change one video's content.

## Files
- Templates: `src/templates/` (QuizReel, AyahReel, TipReel, Cover). Default props for every template live inline in `src/Root.tsx`; a JSON file only needs the fields that differ.
- Channel colours: `src/theme/themes.ts`.
- Voice + word-by-word captions: `npm run captions -- --voice ID --text file.txt --out public/vo/<name>` (needs `ELEVENLABS_API_KEY`).

## Hard rules
- Quran text is never typed, pasted or generated. AyahReel takes only `sura`, `ayaFrom`, `ayaTo`; the text comes from `public/quran/quran-uthmani.txt` (Tanzil). Never edit that file by hand; refresh it with `npm run fetch:quran` or the `fetch-tanzil` workflow.
- Keep the Tanzil credit on screen and add «النص القرآني: مشروع تنزيل tanzil.net» to every Thamarat Aya post description.
- Thamarat Aya lessons must be checked by a qualified person before publishing; leave the placeholder text if no reviewed lesson was given. No music in AyahReel.
- Quizzawi: answer options are always numbered 1 2 3 4, `correct` is 1–4, and the intro uses the channel's existing intro sound (`brand/intro.wav` once the user adds it).
- Nutrition, fitness and accounting facts must be accurate and general; no medical claims ("cures"), no Jordan tax figures unless the user supplies a current source.
- Avoid `#` or `%` next to numbers in Arabic on-screen text (bidi flips them); write «رقم 24».

## Checking work
- `npm run lint` (eslint + tsc) must pass.
- Render a still to check layout: save only the job's `props` object to a temp file, then `npx remotion still QuizReel out/check.png --frame=200 --props=/tmp/props.json`. (A `data/` file wraps props in `{composition, props, cover}`, so it cannot be passed to `--props` directly.)
