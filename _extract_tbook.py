# -*- coding: utf-8 -*-
"""教师用书 69 PDF → 教学环节 episodes 源文本（graphiti 知识库素材）。"""
import fitz, json, os, re, glob
SRC = "../按单元与课次教师用书_文字层可提取"
OUT = "../Think F 教材资产/【数据资产】/教师备课知识库"
os.makedirs(OUT, exist_ok=True)
chunks = []
for f in sorted(glob.glob(f"{SRC}/*.pdf")):
    base = os.path.basename(f)[:-4]
    doc = fitz.open(f)
    for pno in range(len(doc)):
        blocks = doc[pno].get_text("blocks")
        for bi, b in enumerate(blocks):
            if b[6] != 0: continue
            txt = re.sub(r"\s+", " ", b[4]).strip()
            if len(txt) < 30: continue
            # 环节类型启发式
            kind = "内容"
            for pat, k in [(r"Language note", "语言点注释"), (r"Activity idea", "活动设计"),
                           (r"Warmer", "导入活动"), (r"Fast finishers", "快生任务"),
                           (r"Answers?\b", "答案"), (r"Exercise \d", "习题"), (r"RULE", "语法规则"),
                           (r"Grammar rap", "语法说唱"), (r"Extension", "拓展"), (r"Project", "项目"),
                           (r"Test yourself|Test Yourself", "阶段测试"), (r"Workbook", "练习册")]:
                if re.search(pat, txt): kind = k; break
            chunks.append({"id": f"{base}-p{pno+1}-b{bi}", "source_pdf": base, "page": pno+1,
                           "kind": kind, "text": txt})
    doc.close()
    print(base, "✓", flush=True)
json.dump(chunks, open(f"{OUT}/episodes_教师用书.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("总 episodes:", len(chunks))
