#!/usr/bin/env python3
"""يقيّم هوكات الريلز العربية (٠–١٠٠). الاستخدام:
  python3 hookscore.py hooks.txt       # هوك بكل سطر
  python3 hookscore.py --hook "سطر"
بدون شبكة وبدون مكتبات."""
import re, sys, argparse

GREET = ["أهلا","اهلا","مرحبا","مرحباً","السلام عليكم","هلا","اليوم رح احكي","اليوم رح أحكي","اليوم بدي احكي","اليوم بدي أحكي","في هالفيديو","في هذا الفيديو","صباح الخير","مساء الخير"]
CLICHE = ["ما رح تصدق","لن تصدق","شي ما حدا بيحكيلك","اضغط","لا تنسى اللايك","اشترك"]
ADDRESS = ["انت","إنت","أنت","اتحداك","أتحداك","معك","صاحبك","إلك","الك","بتقدر","جاوب","ركّز","ركز","خمّن","خمن","اكتب"]
STAKES = ["غلط","يغلطوا","بيغلطوا","خسرت","سر","مستحيل","أصعب","اصعب","وقت","ثواني","ثانية","ثواني","ممنوع","فقط","واحد","وحدة","عكس","مختلف","ما حدا","٩٩","99","أسرع","قبل ما"]
NUM = re.compile(r"[0-9٠-٩]+")

def score(h):
    w = h.split(); n = len(w)
    first3 = " ".join(w[:3])
    r = {}
    # 1) frontload: claim/number/tension in the first 3 words
    r["الواجهة"] = 100 if (NUM.search(first3) or any(s in first3 for s in STAKES+ADDRESS)) else 45
    # 2) specificity: numbers/concrete
    r["التحديد"] = 100 if len(NUM.findall(h)) >= 1 else 60
    # 3) address: talks to the viewer
    r["الخطاب"] = 100 if any(a in h for a in ADDRESS) else 55
    # 4) stakes / tension
    c = sum(1 for s in STAKES if s in h)
    r["التوتر"] = min(100, 50 + 25*c)
    # 5) length (spoken in <=3s ~ <=8 words)
    r["الطول"] = 100 if n <= 8 else (80 if n <= 11 else (50 if n <= 15 else 20))
    base = sum(r.values())/len(r)
    deal = None
    for g in GREET:
        if h.strip().startswith(g) or g in h[:25]:
            deal = f"ترحيب/مقدمة: «{g}». ما حدا إجا الفيد ليتسلّم عليه."; base = min(base, 15); break
    if not deal:
        for c_ in CLICHE:
            if c_ in h: deal = f"كليشيه: «{c_}»."; base = min(base, 40); break
    return round(base,1), r, deal, n

def label(s): return "قوي" if s >= 75 else ("مقبول" if s >= 55 else "ضعيف")

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("input", nargs="?"); ap.add_argument("--hook")
    a = ap.parse_args()
    if a.hook: hooks=[a.hook]
    else:
        raw = sys.stdin.read() if a.input in (None,"-") else open(a.input,encoding="utf-8").read()
        hooks=[l.strip() for l in raw.splitlines() if l.strip()]
    res = sorted(((score(h),h) for h in hooks), key=lambda x:-x[0][0])
    print("ترتيب الهوكات\n"+"="*60)
    for i,((s,r,d,n),h) in enumerate(res):
        weak = min(r, key=r.get)
        print(f"{'->' if i==0 else '  '} {s:5.1f} {label(s)}  {h}\n       أضعف نقطة: {weak} ({r[weak]})  ·  {n} كلمة")
        if d: print(f"       مشكلة قاتلة: {d}")
    if res and res[0][0][0] < 50: print("\nأحسن هوك تحت 50. ما عندك هوك لسا، التعديل ما رح يصلحه.")

if __name__ == "__main__": main()
