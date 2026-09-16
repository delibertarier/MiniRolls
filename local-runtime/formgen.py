#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
FORMS=ROOT/"forms"; BIN=ROOT/"bin"
LIST_TARGETS={"ROLS6005","ROLS6013","ROLS6023"}

def parse(name):
    path=FORMS/f"{name}.LAY"
    if not path.exists(): raise SystemExit(f"Missing form: {path}")
    d={"fields":[],"menus":[],"actions":[]}
    for line in path.read_text().splitlines():
        if not line.strip(): continue
        k,*rest=line.split(" ",1); val=rest[0] if rest else ""
        if k=="TITLE": d["title"]=val
        elif k=="FIELD": d["fields"].append(val.split("|"))
        elif k=="MENU": d["menus"].append(val.split("|"))
        elif k=="ACTION": d["actions"].append(val.split("|"))
    return d

def validate():
    errors=[]
    for path in FORMS.glob("*.LAY"):
        for row in parse(path.stem)["menus"]:
            target=row[2]
            if target in ("BACK","EXIT"): continue
            if not (FORMS/f"{target}.LAY").exists():
                errors.append(f"{path.name}: missing {target}.LAY")
    if errors: raise SystemExit("Form configuration errors:\n- "+"\n- ".join(errors))

def box(title,rows):
    width=max([len(title)]+[len(x) for x in rows]+[42])+4
    print("\n+"+"-"*(width-2)+"+")
    print("| "+title.ljust(width-4)+" |")
    print("+"+"-"*(width-2)+"+")
    for r in rows: print("| "+r.ljust(width-4)+" |")
    print("+"+"-"*(width-2)+"+")

def execute(name,values=None):
    exe=BIN/f"ui-{name}"
    if not exe.exists(): raise SystemExit(f"Missing executable: {exe}")
    data="" if values is None else "\n".join(values)+"\n"
    r=subprocess.run([str(exe)],input=data,text=True,cwd=ROOT,capture_output=True)
    if r.stdout.strip(): print("\n"+r.stdout.rstrip())
    if r.stderr.strip(): print(r.stderr.rstrip(),file=sys.stderr)
    if r.returncode: raise SystemExit(f"{name} failed: {r.returncode}")
    input("\nPress Enter to continue...")

def form(name):
    d=parse(name)
    box(d.get("title",name),
        [f"{label:<18} [ {'_'*min(int(length),30)} ]"
         for _,label,_,length in d["fields"]])
    values=[]
    for field,label,typ,length in d["fields"]:
        while True:
            v=input(f"{label}: ").strip()
            if typ=="NUMERIC" and (not v.isdigit() or len(v)>int(length)):
                print(f"Enter up to {length} digits."); continue
            values.append(v); break
    execute(name,values)

def menu(name):
    while True:
        d=parse(name)
        box(d.get("title",name),[f"{k}. {label}" for k,label,t in d["menus"]])
        c=input("Choice: ").strip().upper()
        m=next((x for x in d["menus"] if x[0].upper()==c),None)
        if not m: continue
        target=m[2]
        if target in ("BACK","EXIT"): return target
        if target in LIST_TARGETS:
            execute(target); continue
        td=parse(target)
        if td["menus"]: menu(target)
        else: form(target)

if __name__=="__main__":
    validate()
    while True:
        if menu("ROLS0001")=="EXIT": break
