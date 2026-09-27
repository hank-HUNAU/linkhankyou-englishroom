# -*- coding: utf-8 -*-
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
lines = open(r'C:\Users\Thinkpad\AppData\Roaming\TRAE SOLO CN\ModularData\ai-agent\work-mode-projects\6a963ac655852a745b9b5a45\xueersi-diancan-原型\index.html', encoding='utf-8').read().split('\n')
pats = ['function initDB', 'function onPick', 'function switchDir', 'var DB', 'MAP_BOOKS', 'function render(pg)', 'function unitOf', 'function meta', 'function boot', 'function openHome', 'var TL', '.mp3', 'sentence_audio', 'function playSentence', 'new SpeechSynthesisUtterance', 'playbackRate', 'function jump', 'function highlightAt', 'audio[']
for i, l in enumerate(lines, 1):
    for p in pats:
        if p in l:
            print(f'{i:5d} | {p:28s} | {l.strip()[:150]}')
            break