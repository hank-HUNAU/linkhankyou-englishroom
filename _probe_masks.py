import fitz, warnings, os
warnings.filterwarnings("ignore")
LESSON = r"E:\04 少儿原版课程\03 Think 0 课程制作\Codex 学习中心\按单元与课次教师用书_文字层可提取"
# 1) U2 第4次课 TB：masks 文章全文
f = os.path.join(LESSON, "Unit 2 第4次课_教师用书.pdf")
d = fitz.open(f)
t = "".join(p.get_text() for p in d)
d.close()
lines = [l.strip() for l in t.split("\n") if l.strip()]
i = next(j for j, l in enumerate(lines) if "Masks from around the world" in l)
print("=== U2 masks 文章区（从标题起 40 行）===")
for x in lines[i:i+40]:
    print("   ", x[:72])
