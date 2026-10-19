# مؤثرات الصوت

## المكتبة الجاهزة: `montage-kit/sfx/` (167 مؤثرًا)

مجلد [`montage-kit/sfx/`](../../montage-kit/sfx/) في جذر المستودع يحتوي 167 ملف WAV جاهزة للاستخدام المباشر في أي برنامج مونتاج، وهو نفسه ما تستخدمه أداة `montage-kit/edit.py`. كلها مولّدة بالكود من الصفر (بلا عينات أو مواد طرف ثالث)، ومشمولة بترخيص CC0 نفسه الموضح في `ASSET-LICENSE.md`. الصيغة: ستيريو، PCM خطي 16-bit، بمعدل 48 kHz.

الأسماء بالإنجليزية تصف الصوت، ومنها على سبيل المثال:

- **انتقالات:** `whoosh-short` و`whoosh-long` و`whoosh-deep` و`swoosh-fast` و`whip` و`swipe`
- **ضربات:** `impact-boom` و`cinematic-hit` و`bass-drop` و`punch` و`slam` و`vine-boom`
- **تصاعد:** `riser-tension` و`riser-short` و`downlifter` و`reverse-cymbal` و`drum-roll`
- **واجهات:** `pop` و`click` و`notification` و`success` و`error` و`subscribe-ding`
- **رقمي وخيال علمي:** `glitch-1` و`static` و`laser` و`power-up` و`portal` و`teleport`
- **ميمز وكرتون:** `airhorn` و`boing` و`bonk` و`sad-trombone` و`ta-da`
- **واقعية:** `camera-shutter` و`typing` و`page-turn` و`cash-register` و`record-scratch`
- **طبول وإيقاع:** `kick` و`snare` و`clap` و`hihat` و`beat-4`
- **أجواء وطبيعة:** `wind` و`rain` و`forest-birds` و`ocean-waves` و`campfire` و`thunder-roll`

للقائمة الكاملة شغّل `ls montage-kit/sfx`. استخدم `whoosh` أو `swoosh` عند القطع، و`impact` أو `bass-drop` عند لحظة الكشف، و`riser` قبل الانتقال، وخفّض مستوى المؤثرات تحت الحوار والموسيقى.

## المؤثرات الخمسة الأساسية (تُولَّد محليًا)

ملفات WAV الخمسة التالية غير مخزنة مسبقًا في المستودع؛ ينشئها `tools/generate_assets.py` محليًا في هذا المجلد. يلزم Python 3، ولا تحتاج العملية إلى حزم إضافية أو اتصال بالإنترنت.

الملفات الناتجة أصلية، أحادية القناة، PCM خطي 16-bit، بمعدل 48 kHz: `whoosh` للانتقال، `riser` للتصعيد قبل القطع، `impact` للكشف أو الضربة، `snap` للقطع الإيقاعي، و`sparkle` للتفاصيل اللامعة.
