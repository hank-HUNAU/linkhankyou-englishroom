# -*- coding: utf-8 -*-
"""句级时间轴对齐工具（能量法）。

用法：
  py _align_audio.py dump   <out.json>          从运行中的应用导出"实际生效"的时间轴
  py _align_audio.py check  <timeline.json>     体检：逐条边界打分，输出报告
  py _align_audio.py refine <in.json> <out.json> 只对不合格边界重切，输出修正后的时间轴

判定：边界 ±60ms 内峰值能量 / 全篇峰值。<0.25 正常，0.25~0.50 可疑，>=0.50 切音。
重切：在边界附近搜索静音段（>=80ms），把句尾终点与下句起点一起移到该静音段中点；
      搜索窗内确无静音段的，不动，标记 manual（需人工听）。
"""
import functools
import json
import os
import re
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import numpy as np
from playwright.sync_api import sync_playwright

PORT = 8139
BASE = "http://127.0.0.1:%d" % PORT
ROOT = os.path.dirname(os.path.abspath(__file__))

OK_MAX = 0.25
WARN_MAX = 0.50
MIN_PAUSE = 0.08          # 可用的静音段最短长度
SEARCH = 0.60             # 边界两侧搜索半径
WEIRD_GAP = 2.0           # 句间空档超过这个值 = 结构可疑
MIN_PAUSE_LOOSE = 0.05    # 降级策略：更短的静音也认
SEARCH_LOOSE = 1.00       # 降级策略：更宽的搜索窗
MAX_SHIFT = 0.50          # 单条边界的最大位移；超过就不算"微调"，转人工


def log(*a):
    print(*a, flush=True)
    sys.stdout.flush()


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


ENVELOPE_JS = r"""
async (url) => {
  const resp = await fetch(url);
  const buf = await resp.arrayBuffer();
  const AC = window.OfflineAudioContext || window.webkitOfflineAudioContext;
  const ctx = new AC(1, 1, 44100);
  const audio = await new Promise((res, rej) => {
    const p = ctx.decodeAudioData(buf, res, rej);
    if (p && p.then) p.then(res, rej);
  });
  const ch = audio.getChannelData(0);
  const sr = audio.sampleRate;
  const hop = Math.max(1, Math.round(sr * 0.01));
  const n = Math.floor(ch.length / hop);
  const rms = new Float32Array(n);
  for (let i = 0; i < n; i++) {
    let s = 0;
    const off = i * hop;
    for (let j = 0; j < hop; j++) { const v = ch[off + j]; s += v * v; }
    rms[i] = Math.sqrt(s / hop);
  }
  let peak = 0;
  for (let i = 0; i < n; i++) if (rms[i] > peak) peak = rms[i];
  return { sr, dur: ch.length / sr, hopSec: hop / sr, peak, rms: Array.from(rms) };
}
"""


class Audio:
    def __init__(self, env):
        self.rms = np.asarray(env["rms"], dtype=np.float64)
        self.hop = env["hopSec"]
        self.dur = env["dur"]
        self.peak = env["peak"] or 1.0
        self.thr = max(self.peak * 0.02,
                       float(np.percentile(self.rms, 20)) * 0.15, 1e-4)
        self._pauses = None

    def ratio_at(self, t, win=0.06):
        lo = max(0, int((t - win) / self.hop))
        hi = min(len(self.rms), int((t + win) / self.hop) + 1)
        seg = self.rms[lo:hi]
        return float(seg.max()) / self.peak if len(seg) else 0.0

    @property
    def pauses(self):
        if self._pauses is None:
            act = self.rms > self.thr
            segs, i, n = [], 0, len(act)
            while i < n:
                if act[i]:
                    j = i
                    while j < n and act[j]:
                        j += 1
                    segs.append((i, j))
                    i = j
                else:
                    i += 1
            out = []
            for k in range(len(segs) - 1):
                gs, ge = segs[k][1] * self.hop, segs[k + 1][0] * self.hop
                if ge - gs >= MIN_PAUSE:
                    out.append((gs, ge))
            self._pauses = out
        return self._pauses

    def best_pause(self, lo, hi):
        """在 [lo,hi] 内找最宽的静音段，返回其中点。"""
        cand = [p for p in self.pauses if p[0] >= lo and p[1] <= hi]
        if not cand:
            return None
        p = max(cand, key=lambda x: x[1] - x[0])
        return (p[0] + p[1]) / 2

    def pauses_min(self, min_len):
        act = self.rms > self.thr
        segs, i, n = [], 0, len(act)
        while i < n:
            if act[i]:
                j = i
                while j < n and act[j]:
                    j += 1
                segs.append((i, j))
                i = j
            else:
                i += 1
        out = []
        for k in range(len(segs) - 1):
            gs, ge = segs[k][1] * self.hop, segs[k + 1][0] * self.hop
            if ge - gs >= min_len:
                out.append((gs, ge))
        return out

    def best_pause_between(self, lo, hi, min_len):
        cand = [p for p in self.pauses_min(min_len) if p[0] >= lo and p[1] <= hi]
        if not cand:
            return None
        p = max(cand, key=lambda x: x[1] - x[0])
        return (p[0] + p[1]) / 2

    def quietest(self, lo, hi):
        """窗口内最安静的时刻（用于没有真正静音段时的降级）。"""
        i0, i1 = max(0, int(lo / self.hop)), min(len(self.rms), int(hi / self.hop) + 1)
        if i1 <= i0:
            return None, 1.0
        seg = self.rms[i0:i1]
        j = int(np.argmin(seg))
        return (i0 + j) * self.hop, float(seg[j]) / self.peak


def verdict(ratio):
    return "ok" if ratio < OK_MAX else ("warn" if ratio < WARN_MAX else "bad")


def load_timeline(path):
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    out = {}
    for k, v in raw.items():
        m = re.search(r"(\d+)", str(k))
        pid = str(int(m.group(1)))
        segs = v["tl"] if isinstance(v, dict) and "tl" in v else v
        if isinstance(segs[0], list):
            out[pid] = [[float(p[0]), float(p[1])] for p in segs]
        else:
            out[pid] = [[float(p["start_s"]), float(p["end_s"])] for p in segs]
    return out


def serve():
    h = functools.partial(Quiet, directory=ROOT)
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()


def open_app(pw):
    b = pw.chromium.launch()
    pg = b.new_page()
    pg.goto(BASE + "/index.html?pg=67", wait_until="domcontentloaded")
    pg.wait_for_timeout(1000)
    return b, pg


def cmd_dump(out_path):
    serve()
    with sync_playwright() as pw:
        b, pg = open_app(pw)
        data = pg.evaluate("""()=>{
            const TL = window.DB.TL, BOOK = window.BOOK || {};
            const o = {};
            for (const k of Object.keys(TL)) {
                o['p' + String(k).padStart(3, '0')] = {
                    audio: BOOK[k] ? BOOK[k].audio : null,
                    title: BOOK[k] ? BOOK[k].title : null,
                    sents: BOOK[k] ? BOOK[k].arts.flat() : null,
                    tl: TL[k]
                };
            }
            return o;
        }""")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        log("已导出 %d 篇到 %s" % (len(data), out_path))
        b.close()


def measure(pg, tl_by_page, audio_of):
    result = {}
    for pid, tl in tl_by_page.items():
        audio = audio_of.get(pid)
        if not audio:
            log("  p%s 无音频，跳过" % pid)
            continue
        env = pg.evaluate(ENVELOPE_JS, "/" + audio)
        au = Audio(env)
        rows = []
        for k in range(len(tl) - 1):
            e, s = tl[k][1], tl[k + 1][0]
            re_, rs_ = au.ratio_at(e), au.ratio_at(s)
            w = max(re_, rs_)
            rows.append({"k": k, "end": e, "start": s, "re": re_, "rs": rs_,
                         "worst": w, "verdict": verdict(w),
                         "gap": s - e})
        result[pid] = {"dur": au.dur, "rows": rows, "audio": audio}
    return result


def cmd_check(path):
    tl_map = load_timeline(path)
    serve()
    with sync_playwright() as pw:
        b, pg = open_app(pw)
        amap = pg.evaluate("""()=>{const B=window.BOOK||{},o={};
            for(const k of Object.keys(window.DB.TL)) o[k]=B[k]?B[k].audio:null;
            return o;}""")
        audio_of = {str(int(re.search(r"(\d+)", str(k)).group(1))): v for k, v in amap.items()}
        res = measure(pg, tl_map, audio_of)
        b.close()
    tot = bad = warn = weird = 0
    for pid, r in res.items():
        rows = r["rows"]
        tot += len(rows)
        bad += sum(1 for x in rows if x["verdict"] == "bad")
        warn += sum(1 for x in rows if x["verdict"] == "warn")
        weird += sum(1 for x in rows if x["gap"] > WEIRD_GAP)
        log("p%-4s 边界 %2d  切音 %d  可疑 %d  正常 %d%s"
            % (pid, len(rows), sum(1 for x in rows if x["verdict"] == "bad"),
               sum(1 for x in rows if x["verdict"] == "warn"),
               sum(1 for x in rows if x["verdict"] == "ok"),
               "   ⚠异常空档 %d" % sum(1 for x in rows if x["gap"] > WEIRD_GAP) if any(
                   x["gap"] > WEIRD_GAP for x in rows) else ""))
    log("合计 边界 %d  切音 %d  可疑 %d  正常 %d  异常空档 %d"
        % (tot, bad, warn, tot - bad - warn, weird))
    side = os.path.splitext(path)[0] + ".rows.json"
    with open(side, "w", encoding="utf-8") as f:
        json.dump({pid: {"audio": r["audio"], "dur": r["dur"], "rows": r["rows"]}
                   for pid, r in res.items()}, f, ensure_ascii=False, indent=1)
    log("逐条明细 → %s" % side)
    return res


def cmd_refine(src, dst):
    tl_map = load_timeline(src)
    serve()
    with sync_playwright() as pw:
        b, pg = open_app(pw)
        amap = pg.evaluate("""()=>{const B=window.BOOK||{},o={};
            for(const k of Object.keys(window.DB.TL)) o[k]=B[k]?B[k].audio:null;
            return o;}""")
        res = measure(pg, tl_map, {str(k): v for k, v in amap.items()})
        changed = []
        manual = []
        for pid, tl in tl_map.items():
            r = res.get(pid)
            if not r:
                continue
            env = pg.evaluate(ENVELOPE_JS, "/" + r["audio"])
            au = Audio(env)
            for x in r["rows"]:
                if x["verdict"] == "ok":
                    continue
                k = x["k"]
                lo = max(tl[k][1] - SEARCH, tl[k][0])
                hi = min(tl[k + 1][0] + SEARCH, tl[k + 1][1])
                if hi <= lo:
                    lo, hi = x["end"] - SEARCH, x["start"] + SEARCH
                t = au.best_pause(lo, hi)
                how = "静音段"
                if t is None:
                    t = au.best_pause_between(x["end"] - SEARCH_LOOSE,
                                              x["start"] + SEARCH_LOOSE, MIN_PAUSE_LOOSE)
                    how = "短静音"
                if t is None:
                    t, e_ratio = au.quietest(x["end"] - SEARCH_LOOSE,
                                             x["start"] + SEARCH_LOOSE)
                    if t is None or e_ratio >= 0.5 * x["worst"]:
                        manual.append((pid, k, x))
                        continue
                    how = "能量低谷(%.2f)" % e_ratio
                old = (tl[k][1], tl[k + 1][0])
                # 两个端点都不许被挪太远，否则不是"微调"
                if abs(t - old[0]) > MAX_SHIFT or abs(t - old[1]) > MAX_SHIFT:
                    manual.append((pid, k, x))
                    continue
                tl[k][1] = round(t, 3)
                tl[k + 1][0] = round(t, 3)
                # 整个表必须保持严格递增（含首句）
                if not all(tl[i][0] < tl[i][1] for i in range(len(tl))) or \
                   not all(tl[i][1] <= tl[i + 1][1] for i in range(len(tl) - 1)):
                    tl[k][1] = old[0]
                    tl[k + 1][0] = old[1]
                    manual.append((pid, k, x))
                    continue
                if k > 0 and tl[k - 1][1] > tl[k][0]:
                    tl[k][1] = old[0]
                    tl[k + 1][0] = old[1]
                    manual.append((pid, k, x))
                    continue
                changed.append((pid, k, old, t, x, how))
        b.close()

    # 归一化：源数据里有若干 5~80ms 的相邻重叠，统一把前句终点压到后句起点
    for pid, tl in tl_map.items():
        for i in range(len(tl) - 1):
            if tl[i][1] > tl[i + 1][0]:
                tl[i][1] = round(tl[i + 1][0], 3)

    out = {}
    for pid, tl in tl_map.items():
        out["p%s" % pid.zfill(3)] = [{"i": i, "start_s": p[0], "end_s": p[1]} for i, p in enumerate(tl)]
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    log("")
    log("=" * 70)
    log("重切 %d 条，无法自动修复 %d 条" % (len(changed), len(manual)))
    for pid, k, old, t, x, how in changed:
        log("  p%s #%-2d  %.3f/%.3f  ->  %.3f   (原能量 %.2f/%.2f, %s)"
            % (pid, k, old[0], old[1], t, x["re"], x["rs"], how))
    for pid, k, x in manual:
        log("  p%s #%-2d  %.3f/%.3f  原能量 %.2f/%.2f  —— 搜索窗内无静音段，需人工"
            % (pid, k, x["end"], x["start"], x["re"], x["rs"]))
    log("已写入 %s" % dst)


def norm_text(s):
    s = re.sub(r"[\u2018\u2019]", "'", str(s))
    s = re.sub(r"[\u201C\u201D]", '"', s)
    return re.sub(r"\s+", " ", s).strip()


def cmd_cmp(src):
    """比对某份 timeline 的文本与应用的句子文本。"""
    with open(src, encoding="utf-8") as f:
        raw = json.load(f)
    serve()
    with sync_playwright() as pw:
        b, pg = open_app(pw)
        sents = pg.evaluate("""()=>{const o={};
            for(const k of Object.keys(window.DB.TL)) o[k]=window.BOOK[k].arts.flat();
            return o;}""")
        b.close()
    for k, v in raw.items():
        pid = str(int(re.search(r"(\d+)", k).group(1)))
        segs = v["tl"] if isinstance(v, dict) and "tl" in v else v
        texts = [norm_text(p["text"]) for p in segs] if not isinstance(segs[0], list) else None
        app = sents.get(pid) or []
        log("%-6s 应用 %d 句 / 该表 %d 句" % (k, len(app), len(segs)))
        if texts is None:
            log("       该表无文本字段，跳过文本比对")
            continue
        diff = [i for i in range(min(len(app), len(texts))) if norm_text(app[i]) != texts[i]]
        log("       文本不一致 %d 条 %s" % (len(diff), diff[:8]))
        for i in diff[:3]:
            log("         #%d 应用: %s" % (i, app[i][:60]))
            log("             该表: %s" % texts[i][:60])


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        log(__doc__)
    elif args[0] == "dump":
        cmd_dump(args[1])
    elif args[0] == "check":
        cmd_check(args[1])
    elif args[0] == "refine":
        cmd_refine(args[1], args[2])
    elif args[0] == "cmp":
        cmd_cmp(args[1])
