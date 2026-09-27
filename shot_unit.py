# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright
URL='file:///C:/Users/Thinkpad/AppData/Roaming/TRAE%20SOLO%20CN/ModularData/ai-agent/work-mode-projects/6a963ac655852a745b9b5a45/xueersi-diancan-%E5%8E%9F%E5%9E%8B/%E5%AD%A6%E7%94%9F%E7%AB%AF.html'
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':1300})
    pg.goto(URL); pg.wait_for_timeout(500)
    pg.click('#shelf .book[data-k="7"]'); pg.wait_for_timeout(700)
    pg.screenshot(path='学生端_单元页.png'); b.close()
print('done')