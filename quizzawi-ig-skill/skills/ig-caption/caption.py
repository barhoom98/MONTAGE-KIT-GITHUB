#!/usr/bin/env python3
"""يفحص كابشن إنستغرام/يوتيوب شورتس.
  python3 caption.py caption.txt [--yt]      # --yt: حد 100 حرف مع الهاشتاقات، بدون إيموجي، لازم #Shorts
بيعرض أول 125 حرف (اللي بيشوفه المتصفح قبل «المزيد»)."""
import sys, re, argparse
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿\U0001F000-\U0001F2FF]")
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("input",nargs="?"); ap.add_argument("--yt",action="store_true")
    a=ap.parse_args(); raw=(sys.stdin.read() if a.input in (None,"-") else open(a.input,encoding="utf-8").read()).strip()
    tags=re.findall(r"#\S+",raw); n=len(raw)
    print("اللي بيشوفه الفيد قبل «المزيد»:\n+"+"-"*54+"+")
    vis=raw[:125].replace("\n"," ")
    for i in range(0,len(vis),52): print("| "+vis[i:i+52])
    print("+"+"-"*44+" ... المزيد +")
    print(f"\nالطول: {n} حرف · هاشتاقات: {len(tags)}")
    notes=[]
    if n>125 and not re.search(r"[؟?!.:،]",raw[:125]): notes.append("الجملة الأولى ما بتخلص قبل 125 حرف: ارجع صياغتها.")
    if len(tags)>5: notes.append("هاشتاقات كثيرة (>5). 3–5 كفاية.")
    if a.yt:
        if n>100: notes.append(f"يوتيوب: {n} حرف، الحد 100 مع الهاشتاقات.")
        if EMOJI.search(raw): notes.append("يوتيوب: شيل الإيموجي.")
        if "#shorts" not in raw.lower(): notes.append("يوتيوب: ضيف #Shorts.")
    print("\nالملاحظات:"); [print("  -",x) for x in notes]
    if not notes: print("  ممتاز.")
if __name__=="__main__": main()
