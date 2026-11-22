# سكيلات إنستغرام بالعربي (Quizzawi)

ثمانية سكيلات لـ Claude بتساعد بإدارة حساب ريلز عربي بلهجة أردنية: هوكات مقيّمة، توقيت سكربت، كابشن، تحليل أداء، اقتباس صيغ، خطة أسبوعية، ردود، وفاحص لهجة.
**مجانية (MIT)، بدون API key، وما بتنشر شي: إنت بتنشر.**

## التثبيت
```bash
git clone <رابط-الريبو> quizzawi-ig-skill
cp -r quizzawi-ig-skill/skills/ig-* ~/.claude/skills/
mkdir -p ~/.claude/instagram && cp quizzawi-ig-skill/templates/voice.md ~/.claude/instagram/voice.md
```
بعدها عبّي `voice.md` (أو ابعت 3 ريلز لـ Claude: «اكتب voice.md منها»).

## السكيلات
| الأمر | شو بيعمل |
|---|---|
| `/ig-reel` | فكرة ← 3 هوكات (من 12 صيغة) مقيّمة + سكربت + ورقة توقيت |
| `/ig-caption` | الكابشن مفحوص (أول 125 حرف، ويوتيوب ≤100 حرف بدون إيموجي + #Shorts) |
| `/ig-viral` | بيرتّب ريلز المجال حسب مضاعف المشاهدات وبيكتب ملف اقتباس |
| `/ig-audit` | تحليل أداء ريلزك من أرقام بتلصقها |
| `/ig-plan` | خطة أسبوع (13:00 عمّان، تنويع الأنواع) |
| `/ig-profile` | تقييم البروفايل من 100 |
| `/ig-reply` | ردود على التعليقات والدايركت |
| `/ig-lahja` | فاحص اللهجة الأردنية لنصوص الفويس |

## الأدوات اللي بتشتغل (بدون شبكة ولا مكتبات)
```bash
python3 skills/ig-reel/hookscore.py hooks.txt
python3 skills/ig-reel/beats.py script.txt --target 30
python3 skills/ig-caption/caption.py caption.txt --yt
python3 skills/ig-viral/swipe.py captured.tsv
python3 skills/ig-lahja/lahja.py text.txt
```

## شو ما بيعمل
- **ما بيربط حسابك مع إنستغرام.** التحليل على أرقام بتلصقها.
- **ما بيسحب ولا بيطلب باسوورد.** البحث بمتصفحك إنت.
- فاحص اللهجة بيلقط الأغلب، والحكم الأخير لسمعك.
الفكرة مستوحاة من مشروع MIT مشابه بالإنجليزي، والنص والكود هون مكتوبين من الصفر بالعربي.
