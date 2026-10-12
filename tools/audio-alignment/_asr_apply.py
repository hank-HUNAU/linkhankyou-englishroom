# -*- coding: utf-8 -*-
"""把 ASR 轨内公告写回 _alignment.json：inferred→asr、alias→asr(验证)、杂项标注"""
import os, re, json

WORK = os.path.dirname(os.path.abspath(__file__))
asr = json.load(open(os.path.join(WORK, "_asr_tracks.json"), encoding="utf-8"))
alias_asr = json.load(open(os.path.join(WORK, "_asr_alias.json"), encoding="utf-8"))
A = json.load(open(os.path.join(WORK, "_alignment.json"), encoding="utf-8"))

NUMW = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
        "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}
SECW = [("developing speaking", "DEVELOPING SPEAKING"), ("pronunciation", "PRONUNCIATION"),
        ("vocabulary", "VOCABULARY"), ("grammar", "GRAMMAR"), ("reading", "READING"),
        ("listening", "LISTENING"), ("speaking", "SPEAKING"), ("culture", "CULTURE"),
        ("functions", "FUNCTIONS"), ("writing", "WRITING")]

def parse_announce(text):
    t = text.lower()
    for w, n in NUMW.items():
        t = re.sub(r"\b" + w + r"\b", str(n), t)
    sec = None
    for w, s in SECW:
        if re.search(r"\b" + w, t):
            sec = s
            break
    pm = re.search(r"page\s*(\d{2,3})", t)
    em = re.search(r"exercises?\s*(\d{1,2})", t)
    um = re.search(r"unit\s*(\d{1,2})", t)
    return (um.group(1) if um else None,
            int(pm.group(1)) if pm else None,
            sec,
            int(em.group(1)) if em else None)

changed = 0
report = []

def find_row(path):
    for u, d0 in A.items():
        for r0 in d0.get("sb", []) + d0.get("other", []):
            if r0.get("path") == path:
                return u, r0
    return None, None

# ---- A. 27 轨 ASR（inferred + 2 杂项）----
for key, e in asr.items():
    if "error" in e or not e.get("text"):
        continue
    au, ap, asec, aex = parse_announce(e["text"])
    u, r0 = find_row(e["path"])
    if not r0:
        continue
    m = re.search(r"_Unit_([0-9W]+)_p(\d+)_", key)
    fp = int(m.group(2)) if m else None
    ok_page = (ap is None or fp is None or ap == fp)
    if asec and ok_page and r0.get("st") in ("inferred", "exact"):
        r0["st"] = "asr"
        r0["sec"] = asec
        if aex:
            r0["ex"] = str(aex)
        r0["ctx"] = "轨内公告: " + re.sub(r"\s+", " ", e["text"])[:70].strip()
        changed += 1
        report.append((key[:44], "ASR", au, ap, asec, aex))
    elif e.get("tag") == "other":
        r0["note"] = ("轨内公告: " + re.sub(r"\s+", " ", e["text"])[:70].strip()
                      if asec else "自制轨（无公告）｜ASR 内容: " + e["text"][:60].strip())
        report.append((key[:44], "OTH", au, ap, asec, aex))

# ---- B. 12 个改名文件（alias 验证）----
for key, e in alias_asr.items():
    au, ap, asec, aex = parse_announce(e["head"])
    u, r0 = find_row(e["path"])
    if not r0:
        report.append((key[:44], "ALIAS-NOT-IN-ALIGN", au, ap, asec, aex))
        continue
    if asec:
        r0["st"] = "asr"
        r0["sec"] = asec
        if aex:
            r0["ex"] = str(aex)
        r0["ctx"] = "轨内公告: " + re.sub(r"\s+", " ", e["head"])[:70].strip()
        changed += 1
        report.append((key[:44], "ALIAS-OK", au, ap, asec, aex))
    else:
        report.append((key[:44], "ALIAS-NO-ANNOUNCE", None, None, None, None))

json.dump(A, open(os.path.join(WORK, "_alignment.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
for r0 in report:
    print(r0)
print("updated rows:", changed)
