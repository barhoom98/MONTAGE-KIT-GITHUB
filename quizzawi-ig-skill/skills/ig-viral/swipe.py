#!/usr/bin/env python3
"""يرتّب الريلز حسب مضاعف المشاهدات مقارنة بمتوسط الحساب نفسه.
  python3 swipe.py captured.tsv [--out ~/.claude/instagram/swipe.md]
أعمدة TSV (بدون عنوان): حساب <tab> متابعين <tab> متوسط_مشاهدات_الحساب <tab> مشاهدات_الريل <tab> الهوك <tab> الصيغة(اختياري)"""
import sys, argparse, os
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("input"); ap.add_argument("--out"); a=ap.parse_args()
    rows=[]
    for l in open(a.input,encoding="utf-8"):
        p=l.rstrip("\n").split("\t")
        if len(p)<5: continue
        try: acc,fol,med,views=p[0],int(p[1]),float(p[2]),float(p[3])
        except ValueError: continue
        rows.append((views/med if med else 0,acc,fol,views,p[4],p[5] if len(p)>5 else ""))
    rows.sort(reverse=True)
    out=["# ملف الاقتباس (swipe)\n","| مضاعف | الحساب | المتابعين | المشاهدات | الهوك | الصيغة |","|---|---|---|---|---|---|"]
    for m,acc,fol,v,h,f in rows:
        flag="🔥 إشارة" if m>=3 else ("عادي" if m<1.5 else "")
        out.append(f"| {m:.1f}x {flag} | {acc} | {fol:,} | {v:,.0f} | {h} | {f} |")
    txt="\n".join(out); print(txt)
    if a.out:
        p=os.path.expanduser(a.out); os.makedirs(os.path.dirname(p),exist_ok=True); open(p,"w",encoding="utf-8").write(txt+"\n"); print("\nكُتب:",p)
if __name__=="__main__": main()
