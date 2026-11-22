#!/usr/bin/env python3
"""يحسب توقيت سكربت الريل بالعربي ويطلّع ملاحظات.
  python3 beats.py script.txt --target 30
كل سطر = بيت. السرعة الافتراضية 2.6 كلمة/ثانية (حوالي 155 كلمة بالدقيقة)."""
import sys, re, argparse
def secs(line, wps): return max(1.0, len(line.split())/wps)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("input",nargs="?"); ap.add_argument("--target",type=float,default=30); ap.add_argument("--wps",type=float,default=2.6)
    a=ap.parse_args()
    raw=sys.stdin.read() if a.input in (None,"-") else open(a.input,encoding="utf-8").read()
    lines=[l.strip() for l in raw.splitlines() if l.strip()]
    t=0; rows=[]
    for i,l in enumerate(lines):
        d=secs(l,a.wps); rows.append((t,d,l)); t+=d
    words=sum(len(l.split()) for l in lines)
    print(f"ورقة التوقيت · {words} كلمة · ~{t:.1f}ث · الهدف {a.target:.0f}ث\n"+"="*66)
    notes=[]
    for i,(s,d,l) in enumerate(rows):
        tag="هوك" if i==0 else ("ختام" if i==len(rows)-1 else "")
        print(f"  {int(s//60)}:{s%60:04.1f}  {d:4.1f}ث  {tag:4} {l[:50]}")
        if i==0 and d>3: notes.append(f"الهوك {d:.1f}ث. لازم ≤3ث: قصّره.")
        if 0<i and d>4: notes.append(f"البيت {i+1} طويل ({d:.1f}ث). قسّمه أو غيّر اللي على الشاشة.")
    if lines and set(re.findall(r"\w{3,}",lines[0]))&set(re.findall(r"\w{3,}",lines[-1]))==set(): notes.append("ما في لوب: كرّر كلمة من الهوك بآخر سطر عشان الإعادة تنزل حلوة.")
    if abs(t-a.target)>4: notes.append(f"الفرق عن الهدف {t-a.target:+.1f}ث. {'قصّر' if t>a.target else 'زِد أو صوّرها أقصر (الأقصر غالباً أحسن)'}.")
    print("-"*66)
    for n in notes: print("  -",n)
    if not notes: print("  ممتاز: ما في ملاحظات.")
if __name__=="__main__": main()
