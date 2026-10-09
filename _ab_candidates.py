#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成「多候选起点」人耳定案页。

用途：当 Whisper 的词级起点不可信（常落在上一词的尾音里，如 p067#3、p069#5），
      不再盲信对齐值，而是给同一句话多个候选起点，由人耳点选「第一个干净词」的那一档。

用法：
  python _ab_candidates.py --spec '{"p069":{"5":[26.24,26.50,26.60,26.70,26.90]},
                                    "p072":{"1":[13.75,13.95,14.20,14.45],
                                            "4":[31.87,32.00,32.20,32.45]}}'

输出：_ab_cand_p069.html / _ab_cand_p072.html（已加入 .gitignore）
"""
import json
import argparse
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
W = json.load(open(os.path.join(ROOT, "_whisper_all_words.json")))
TL = json.load(open(os.path.join(ROOT, "assets", "timeline.json")))

# 各页音质备注（节选自 _match_source / ffprobe 结论）
AUDIO_NOTE = {
    "p066": "本页音质 32kbps/22050Hz 单声道（压缩噪明显），结论打折",
    "p067": "本页音质 128kbps/44.1kHz 立体声（干净）",
    "p069": "本页音质 128kbps/44.1kHz 立体声（干净）",
    "p070": "本页音质 128kbps/44.1kHz 立体声（干净）",
    "p072": "本页音质 128kbps/44.1kHz 立体声（干净）",
    "p073": "本页音质 32kbps/22050Hz 单声道（压缩噪明显），结论打折",
    "p110": "本页音质 64kbps（一般）",
    "p202": "本页音质 32kbps/22050Hz 单声道（压缩噪明显），结论打折",
}


def word_at(page, t):
    """返回时刻 t 所在或其后最近的一个 whisper 词（用于给候选起点标注『会听到什么』。"""
    words = W[page]
    cur = None
    for (ws, we, wrd) in words:
        if ws <= t <= we:
            return wrd, ws, we
        if ws > t:
            if cur is None or ws < cur[1]:
                cur = (wrd, ws, we)
    return (cur[0] if cur else "—", cur[1] if cur else None, cur[2] if cur else None)


def build(page, cands):
    tl = {s["i"]: s for s in TL[page]}
    rows = []
    for si, cand_list in cands.items():
        si = int(si)
        t = tl[si]
        cur = t["start_s"]
        words = t["text"].split()
        head = words[0].strip(".,!?;:'\"") if words else ""
        txt = t["text"].replace(head, "<b>%s</b>" % head, 1) if head else t["text"]
        btns = []
        # 现网（当前值）红钮
        w, _, _ = word_at(page, cur)
        btns.append(
            '<button class="cur" onclick="playFrom(%s)">现网 %.2f ▸ %s</button>'
            % (cur, cur, w)
        )
        # 候选起点
        for c in cand_list:
            w, _, _ = word_at(page, c)
            cls = "cand"
            btns.append(
                '<button class="%s" onclick="playFrom(%s)">候选 %.2f ▸ %s</button>'
                % (cls, c, c, w)
            )
        rows.append(
            '<tr><td class="sid">#%s</td><td class="txt">%s</td>'
            '<td class="btns">%s</td></tr>'
            % (si, txt, "".join(btns))
        )
    note = AUDIO_NOTE.get(page, "")
    html = """<!doctype html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>多候选起点 · %s</title>
<style>
* { box-sizing: border-box; }
body { font-family: -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;
       background:#f5f6f8; color:#222; margin:0; padding:18px; }
h1 { font-size:19px; margin:0 0 4px; }
.note { color:#b8860b; background:#fff7e0; border:1px solid #f0d488;
        padding:6px 10px; border-radius:6px; font-size:13px; margin:8px 0 14px; }
table { border-collapse:collapse; width:100%%; background:#fff;
        border-radius:8px; overflow:hidden; box-shadow:0 1px 3px rgba(0,0,0,.08); }
td { border-bottom:1px solid #eee; padding:10px 12px; vertical-align:top; }
tr:last-child td { border-bottom:none; }
.sid { font-weight:700; white-space:nowrap; color:#1565c0; width:42px; }
.txt { font-size:15px; line-height:1.5; }
.txt b { color:#c62828; background:#ffe9e9; padding:0 3px; border-radius:3px; }
.btns { display:flex; flex-wrap:wrap; gap:6px; }
button { font-size:13px; border:none; border-radius:6px; padding:7px 11px;
         cursor:pointer; background:#e8eef7; color:#1565c0; transition:.12s; }
button:hover { filter:brightness(.96); }
.cur { background:#fde7e7; color:#c62828; font-weight:600; }
.cand { background:#e6f4ea; color:#1b7a3d; }
.player { position:sticky; top:0; background:#fff; padding:10px 12px;
          border-radius:8px; box-shadow:0 1px 4px rgba(0,0,0,.1); margin-bottom:12px;
          display:flex; align-items:center; gap:12px; z-index:5; }
.player audio { flex:1; }
.hint { font-size:12px; color:#666; }
.ok { color:#1b7a3d; font-weight:700; }
</style></head><body>
<div class="player">
  <span class="hint">点按钮即从此刻播放：</span>
  <audio id="a" src="assets/%s.mp3" preload="auto" controls></audio>
  <label class="hint"><input type="checkbox" id="only" checked> 只听 1.6s</label>
</div>
<h1>多候选起点 · %s</h1>
<div class="note">%s</div>
<table>%s</table>
<div class="note" style="margin-top:14px">
  听法：点「候选 X.XX ▸ 词」按钮，听它落下的第一个词是不是本句标黄的首词。
  若仍带上一句尾音 → 选更靠后的候选；若已截掉本句首词 → 选更靠前的。
  选定后把该候选时间告诉我，我据此改 timeline.json。
</div>
<script>
const a=document.getElementById('a'), only=document.getElementById('only');
let timer=null;
function playFrom(t){
  clearTimeout(timer);
  a.currentTime=t;
  const p=a.play();
  if(p&&p.catch) p.catch(()=>{});
  if(only.checked){ timer=setTimeout(()=>a.pause(), 1600); }
}
a.addEventListener('pause',()=>clearTimeout(timer));
</script>
</body></html>""" % (page, page, page, note, "\n".join(rows))
    out = os.path.join(ROOT, "_ab_cand_%s.html" % page)
    open(out, "w", encoding="utf-8").write(html)
    print("[ok] 生成", out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True, help="JSON: {page:{sent:[cand_starts...]}}")
    a = ap.parse_args()
    spec = json.loads(a.spec)
    for page, cands in spec.items():
        build(page, cands)


if __name__ == "__main__":
    main()
