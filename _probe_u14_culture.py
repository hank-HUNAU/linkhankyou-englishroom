import fitz, warnings, os, re
warnings.filterwarnings("ignore")
BASE = r"E:\04 少儿原版课程\03 Think 0 课程制作\003 第三版课程材料"
LESSON = r"E:\04 少儿原版课程\03 Think 0 课程制作\Codex 学习中心\按单元与课次教师用书_文字层可提取"
for u in (1, 2, 3, 4):
    f = os.path.join(BASE, f"第{u}单元", f"L{u}_教师用书.pdf")
    d = fitz.open(f)
    t = "".join(p.get_text() for p in d)
    d.close()
    lines = [l.strip() for l in t.split("\n") if l.strip()]
    print(f"===== U{u} 整册 TB：culture 命中 =====")
    hits = [(i, l) for i, l in enumerate(lines) if "ulture" in l or "CULTURE" in l]
    for i, l in hits[:8]:
        print(f"  [{i}] {l[:70]}")
        ctx = " / ".join(x[:36] for x in lines[max(0, i - 1):i + 3])
        print(f"       上下文: {ctx[:150]}")
    if not hits:
        print("  （无）")
    # 单元结构页（Objectives 附近罗列各板块）
    print(f"  --- U{u} 板块标题全列 ---")
    secs = [l for l in lines if re.fullmatch(r"(READING|LISTENING|SPEAKING|WRITING|GRAMMAR|VOCABULARY|CULTURE|FUNCTIONS|PROJECT|REVIEW|VALUES|LIFE|WATCH|WORDWISE)", l)]
    print("   ", secs)
