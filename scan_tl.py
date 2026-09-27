# -*- coding: utf-8 -*-
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
s = open(r'C:\Users\Thinkpad\AppData\Roaming\TRAE SOLO CN\ModularData\ai-agent\work-mode-projects\6a963ac655852a745b9b5a45\xueersi-diancan-原型\index.html', encoding='utf-8').read()
need = ['66','67','69','70','72','73','110','111','113','114','117']
# DB.TL 定义首部
m = re.search(r'var DB=\{"TL":\{', s)
head = s[m.start():m.start()+2000]
print('DB.TL 头部片段:')
print(head[:900])
print('---')
# 找所有 DB.TL["NN"]= 赋值
dbtl = re.findall(r'DB\.TL\["(\d+)"\]', s)
print('显式 DB.TL[".."] 赋值页面:', sorted(set(dbtl)))
print('缺失(需确认):', [x for x in need if x not in set(dbtl)])