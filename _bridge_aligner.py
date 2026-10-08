#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
_bridge_aligner.py —— 桥接 audio-aligner-v4.0.0 的对齐内核，与现网时间轴全量比对。

现网权威时间轴是 assets/timeline.json（12 篇 / 312 句），它由「人工核查 + 能量法」
产出；本脚本用另一个项目 audio-aligner-v4.0.0 的对齐内核（faster-whisper 词级
时间戳 + difflib.SequenceMatcher 词序列匹配 + 可选静音吸附）独立算一遍，再逐句比对。

注意两者的关系：它们用的是同一代方法（都是 Whisper 词级时间戳 + 序列匹配），
所以这是**实现层面的交叉验证**，不是方法论层面的第三方仲裁。两者一致的点可以
放心采信，矛盾的点仍需人耳或 CTC（方案 A）定案。

用法
----
    python _bridge_aligner.py                  # 纯词级对齐比对，秒级，不解码音频
    python _bridge_aligner.py --silence        # 追加静音吸附（需解码 12 篇 mp3）
    python _bridge_aligner.py --page p067      # 只看一篇
    python _bridge_aligner.py --tol 0.20       # 静音吸附容差（默认 0.15s）
    python _bridge_aligner.py --conf 0.8       # 低置信阈值（默认 0.8）

产出
----
    _bridge_bounds.json   逐句结果（现网值 / 对齐值 / 静音吸附值 / 偏差 / 置信度）
    _bridge_report.md     人类可读报告：低置信句、偏差 >0.3s 清单、首句（报幕）核对
"""

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ALIGNER_HOME = r"D:\Trae Project\audio-aligner-v4.0.0"

TIMELINE = os.path.join(HERE, "assets", "timeline.json")
WORDS = os.path.join(HERE, "_whisper_all_words.json")
OUT_JSON = os.path.join(HERE, "_bridge_bounds.json")
OUT_MD = os.path.join(HERE, "_bridge_report.md")


def load_aligner():
    """导入隔壁项目的对齐内核。"""
    if not os.path.isdir(ALIGNER_HOME):
        sys.exit("找不到对齐项目：%s" % ALIGNER_HOME)
    sys.path.insert(0, ALIGNER_HOME)
    import aligner  # noqa: E402
    return aligner


def make_light_aligner(mod, silence_cfg):
    """构造一个不解码音频的轻量实例。

    AudioTextAligner.__init__ 会用 pydub 读整个 mp3，只为拿 duration；而
    duration 只在「没有词级时间戳」的兜底分支里才用到。我们有词级时间戳，
    所以可以绕过解码，让纯对齐路径保持在秒级。
    """
    a = mod.AudioTextAligner.__new__(mod.AudioTextAligner)
    a.filepath = None
    a.language = "en"
    a.model_size = "small"
    a.silence_config = silence_cfg
    a.audio = None
    a.duration = 0.0
    a._audio_samples = None
    a._sample_rate = None
    a._silence_detector = None
    return a


def run(args):
    mod = load_aligner()

    tl = json.load(open(TIMELINE, encoding="utf-8"))
    words_raw = json.load(open(WORDS, encoding="utf-8"))

    silence_cfg = {
        "enabled": args.silence,
        "min_silence_duration": 0.3,
        "silence_threshold_db": -40,
        "boundary_tolerance": args.tol,
    }

    pages = [args.page] if args.page else sorted(tl.keys())
    out = {}

    for page in pages:
        sents = tl.get(page)
        raw_words = words_raw.get(page)
        if not sents:
            print("[skip] %s 不在 timeline.json" % page)
            continue
        if not raw_words:
            print("[skip] %s 没有词级时间戳" % page)
            continue

        words = [{"text": w[2], "start": w[0], "end": w[1]} for w in raw_words]
        sentences = [s["text"] for s in sents]

        light = make_light_aligner(mod, silence_cfg)
        aligned = light._align_sentences_with_word_timestamps(sentences, words)

        silenced = None
        if args.silence:
            mp3 = os.path.join(HERE, "assets", page + ".mp3")
            if not os.path.isfile(mp3):
                print("[warn] %s 缺音频，跳过静音吸附" % page)
            else:
                from pydub import AudioSegment  # noqa: E402

                det = mod.SilenceDetector(
                    AudioSegment.from_file(mp3),
                    min_silence_duration=silence_cfg["min_silence_duration"],
                    silence_threshold_db=silence_cfg["silence_threshold_db"],
                    boundary_tolerance=silence_cfg["boundary_tolerance"],
                )
                det.detect_silence_intervals()
                silenced = det.validate_and_adjust_boundaries(aligned)

        rows = []
        for i, cur in enumerate(sents):
            al = aligned[i] if i < len(aligned) else None
            sil = silenced[i] if silenced and i < len(silenced) else None
            rows.append(
                {
                    "i": cur.get("i", i),
                    "text": cur["text"],
                    "cur_start": round(cur["start_s"], 3),
                    "cur_end": round(cur["end_s"], 3),
                    "al_start": round(al["start"], 3) if al else None,
                    "al_end": round(al["end"], 3) if al else None,
                    "sil_start": round(sil["start"], 3) if sil else None,
                    "sil_end": round(sil["end"], 3) if sil else None,
                    "confidence": al["confidence"] if al else None,
                    "d_start": round(al["start"] - cur["start_s"], 3) if al else None,
                    "d_end": round(al["end"] - cur["end_s"], 3) if al else None,
                }
            )
        out[page] = rows
        print(
            "[ok] %s %d 句 / %d 词级时间戳%s"
            % (page, len(rows), len(words), " + 静音吸附" if silenced else "")
        )

    json.dump(out, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return out, args


def med(xs):
    xs = sorted(xs)
    n = len(xs)
    if not n:
        return 0.0
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def build_report(out, args, words_raw=None):
    lines = []
    lines.append("# 桥接比对报告 · audio-aligner-v4.0.0 vs 现网 timeline.json")
    lines.append("")
    lines.append(
        "生成方式：`python _bridge_aligner.py%s`（容差 %ss，低置信阈值 %s）"
        % (" --silence" if args.silence else "", args.tol, args.conf)
    )
    lines.append("")
    lines.append(
        "> 两者是同代方法（Whisper 词级时间戳 + 序列匹配），这是**实现层面的交叉验证**，"
        "不是方法论仲裁。一致的点可采信，矛盾的点仍需人耳或 CTC 定案。"
    )
    lines.append("")

    rows_all = [(p, r) for p in sorted(out) for r in out[p]]
    total = len(rows_all)

    # 系统偏移：Whisper 的词 end 系统性偏早（约 -0.26s），start 略偏晚（约 +0.12s）。
    # 先看整体中位数，把系统偏移剥掉，剩下的才是真分歧。
    bias_s = med([r["d_start"] for _, r in rows_all if r["d_start"] is not None])
    bias_e = med([r["d_end"] for _, r in rows_all if r["d_end"] is not None])

    for _, r in rows_all:
        r["adj_start"] = round(r["d_start"] - bias_s, 3) if r["d_start"] is not None else None
        r["adj_end"] = round(r["d_end"] - bias_e, 3) if r["d_end"] is not None else None

    low_conf = [(p, r) for p, r in rows_all if r["confidence"] is not None and r["confidence"] < args.conf]
    big_delta = [
        (p, r)
        for p, r in rows_all
        if r["adj_start"] is not None and (abs(r["adj_start"]) > 0.3 or abs(r["adj_end"]) > 0.3)
    ]
    heads = [(p, r) for p, r in rows_all if r["i"] == 0]

    lines.append("## 总览")
    lines.append("")
    lines.append("- 比对句数：**%d**（12 篇）" % total)
    lines.append("- 低置信句（confidence < %s）：**%d**" % (args.conf, len(low_conf)))
    lines.append(
        "- 系统偏移：Δstart 中位数 **%+.3fs**、Δend 中位数 **%+.3fs**（已剥离，以下均为去偏移后的值）"
        % (bias_s, bias_e)
    )
    lines.append("- 真分歧 > 0.3s 的句：**%d**" % len(big_delta))
    lines.append("")

    lines.append("## 按篇汇总（先看这张表定位问题篇）")
    lines.append("")
    lines.append("| 篇 | 句数 | Δstart 中位数 | 去偏移后 >0.3s | 最大真分歧 | 争议句 |")
    lines.append("|---|---|---|---|---|---|")
    for page in sorted(out):
        rows = out[page]
        ds = [r["adj_start"] for r in rows if r["adj_start"] is not None]
        if not ds:
            continue
        worst = max(rows, key=lambda r: abs(r["adj_start"] or 0))
        nbad = sum(1 for v in ds if abs(v) > 0.3)
        lines.append(
            "| %s | %d | %+.3f | %d | %+.3f | #%s |"
            % (page, len(rows), med([r["d_start"] for r in rows]), nbad, worst["adj_start"], worst["i"])
        )
    lines.append("")
    lines.append(
        "> 整篇中位数明显偏离 0、且分歧句占比高 → 多半是**句切分口径错了**（漏句/多句/对白），"
        "不是边界微调能修的，要重切。p073 就是这一型。"
    )
    lines.append("")

    lines.append("## 一、首句核对（报幕相关）")
    lines.append("")
    lines.append("| 篇 | 现网 start | 对齐 start | Δ | 置信 | 文本 |")
    lines.append("|---|---|---|---|---|---|")
    for page, r in heads:
        lines.append(
            "| %s | %.3f | %s | %s | %s | %s |"
            % (
                page,
                r["cur_start"],
                r["al_start"],
                r["d_start"],
                r["confidence"],
                (r["text"][:40] + "…") if len(r["text"]) > 40 else r["text"],
            )
        )
    lines.append("")

    lines.append("## 二、真分歧 Top 30（按 |Δstart| 排序，已剥离系统偏移）")
    lines.append("")
    lines.append("| 篇 | 句 | 现网 start | 对齐 start | Δstart* | Δend* | 文本 |")
    lines.append("|---|---|---|---|---|---|---|")
    for page, r in sorted(rows_all, key=lambda x: -abs(x[1]["adj_start"] or 0))[:30]:
        lines.append(
            "| %s | #%s | %.3f | %.3f | %+.3f | %+.3f | %s |"
            % (
                page,
                r["i"],
                r["cur_start"],
                r["al_start"],
                r["adj_start"],
                r["adj_end"],
                (r["text"][:36] + "…") if len(r["text"]) > 36 else r["text"],
            )
        )
    lines.append("")
    lines.append("完整 %d 句数据在 `_bridge_bounds.json`（含 `adj_start` / `adj_end` 字段）。" % total)
    lines.append("")

    if words_raw:
        lines.append("## 三、抽样取证：争议处到底谁对")
        lines.append("")
        lines.append(
            "对 Top 6 争议句，直接列出 Whisper 原始词流。判据很简单："
            "**句首第一个词的时间戳**就是该句真正的起点。若现网值落在空档里或处在"
            "第一个词之后，说明现网把句首词切掉了。"
        )
        lines.append("")
        for page, r in sorted(rows_all, key=lambda x: -abs(x[1]["adj_start"] or 0))[:6]:
            lo = min(r["cur_start"], r["al_start"]) - 0.5
            hi = max(r["cur_start"], r["al_start"]) + 1.6
            flow = " ".join(
                "%s`%.2f`" % (w[2], w[0])
                for w in words_raw.get(page, [])
                if lo <= w[0] <= hi
            )
            first_word = (r["text"].split() or [""])[0]
            lines.append("**%s #%s** —— Δstart %+.3f（现网 %.3f / 对齐 %.3f）" % (page, r["i"], r["adj_start"], r["cur_start"], r["al_start"]))
            lines.append("")
            lines.append("- 课文：%s" % r["text"][:70])
            lines.append("- 句首词应为：`%s`" % first_word)
            lines.append("- 该段词流：%s" % (flow or "（空档，无词）"))
            lines.append(
                "- 判定：%s"
                % (
                    "对齐值落在句首词上，现网值落在其后 → **现网切掉了句首词**"
                    if abs(r["al_start"] - r["cur_start"]) > 0.3
                    else "两者一致"
                )
            )
            lines.append("")
    lines.append("## 四、低置信句（对齐不可信，优先人工听）")
    lines.append("")
    if not low_conf:
        lines.append("无。")
    else:
        lines.append("| 篇 | 句 | 置信 | Δstart | Δend | 文本 |")
        lines.append("|---|---|---|---|---|---|")
        for page, r in sorted(low_conf, key=lambda x: x[1]["confidence"]):
            lines.append(
                "| %s | #%s | %.2f | %+.3f | %+.3f | %s |"
                % (
                    page,
                    r["i"],
                    r["confidence"],
                    r["d_start"],
                    r["d_end"],
                    (r["text"][:36] + "…") if len(r["text"]) > 36 else r["text"],
                )
            )
    lines.append("")

    if args.silence:
        lines.append("## 五、静音吸附的效果")
        lines.append("")
        moved = [
            (p, r)
            for p in sorted(out)
            for r in out[p]
            if r["sil_start"] is not None
            and (r["sil_start"] != r["al_start"] or r["sil_end"] != r["al_end"])
        ]
        lines.append("- 被吸附移动的边界：**%d** 处" % len(moved))
        lines.append("")
        if moved:
            lines.append("| 篇 | 句 | 对齐 | 吸附后 | Δ（吸附-现网） |")
            lines.append("|---|---|---|---|---|")
            for page, r in moved[:40]:
                lines.append(
                    "| %s | #%s | %.3f–%.3f | %.3f–%.3f | %+.3f / %+.3f |"
                    % (
                        page,
                        r["i"],
                        r["al_start"],
                        r["al_end"],
                        r["sil_start"],
                        r["sil_end"],
                        r["sil_start"] - r["cur_start"],
                        r["sil_end"] - r["cur_end"],
                    )
                )
            if len(moved) > 40:
                lines.append("")
                lines.append("（仅列前 40 处，完整数据在 `_bridge_bounds.json`）")
        lines.append("")

    open(OUT_MD, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    # adj_* 是在上面算出来的，run() 里那次 dump 还没有，这里补写一次
    json.dump(out, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return total, len(low_conf), len(big_delta)


AB_TPL = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>A/B 试听 · %(page)s</title>
<style>
 body{font-family:-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;background:#f7f8fa;color:#1a1d21;
      margin:0;padding:24px;line-height:1.6}
 .wrap{max-width:900px;margin:0 auto}
 h1{font-size:19px;margin:0 0 4px}
 .sub{color:#6b7280;font-size:13px;margin-bottom:18px}
 .tip{background:#fff8e6;border:1px solid #f0d69a;border-radius:8px;padding:12px 14px;font-size:13px;margin-bottom:20px}
 .tip b{color:#8a5a00}
 table{width:100%%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden;
       box-shadow:0 1px 3px rgba(0,0,0,.08)}
 th,td{padding:10px 12px;text-align:left;border-bottom:1px solid #eef0f3;font-size:13px;vertical-align:middle}
 th{background:#f1f3f6;font-weight:600;color:#4b5563}
 tr.ctrl td{background:#f0fdf4}
 tr.forced td{background:#eff6ff}
 .tag{display:inline-block;font-size:11px;padding:1px 6px;border-radius:4px;background:#fee2e2;color:#b91c1c}
 .tag.ok{background:#dcfce7;color:#15803d}
 .tag.ed{background:#dbeafe;color:#1d4ed8}
 .txt{color:#374151}
 .txt b{background:#fff3b0;padding:0 2px}
 button{border:1px solid #d1d5db;background:#fff;border-radius:6px;padding:5px 10px;font-size:12px;
        cursor:pointer;margin-right:6px;color:#374151}
 button:hover{background:#f3f4f6}
 button.play{background:#2563eb;border-color:#2563eb;color:#fff}
 button.play:hover{background:#1d4ed8}
 button.cur{background:#dc2626;border-color:#dc2626;color:#fff}
 button.cur:hover{background:#b91c1c}
 .ts{font-variant-numeric:tabular-nums;font-size:12px;color:#6b7280}
 .now{position:sticky;bottom:0;background:#1a1d21;color:#fff;padding:10px 14px;border-radius:8px;
      margin-top:16px;font-size:13px;font-variant-numeric:tabular-nums}
 .now span{color:#fbbf24}
</style></head><body><div class="wrap">
<h1>A/B 试听 · %(page)s —— 现网起点 vs 词级对齐起点</h1>
<div class="sub">数据来自 <code>_bridge_report.md</code>。共 %(n)s 句：%(ndis)s 句争议 + %(nctl)s 句对照。</div>
%(note)s
<div class="tip">
<b>怎么听：</b>每行有三个按钮。先点 <b>红「现网」</b>，再点 <b>蓝「对齐」</b>，或点 <b>「连听」</b>自动
先红后蓝。判据只有一条：<b>听到的第一个词是不是课文句首那个词（黄色高亮）</b>。
如果红按钮听起来是从句中某个词开始的、或者带上前一个词的尾巴，就是现网切错了。<br>
对照行（绿底）是两种方法一致的句子，用来确认这套听法本身靠谱——如果连对照行都听着别扭，
说明是音量/耳机问题而不是数据问题。
</div>
<table>
<tr><th>句</th><th>课文（句首词高亮）</th><th>Δstart</th><th>试听</th></tr>
%(rows)s
</table>
<div class="now" id="now">就绪。音频：<code>assets/%(page)s.mp3</code></div>
<audio id="au" src="assets/%(page)s.mp3" preload="auto"></audio>
<script>
var AU=document.getElementById('au'), NOW=document.getElementById('now'), TIMER=null;
var PAD=0.4, LEN=2.4;
function fmt(s){return s.toFixed(2)+'s';}
function playOne(t0,label){
  clearTimeout(TIMER);
  var t=Math.max(0,t0-PAD), end=t0+LEN;
  AU.pause(); AU.currentTime=t;
  AU.play();
  NOW.innerHTML='正在播放 <span>'+label+'</span>：从 '+fmt(t)+' 起（起点 '+fmt(t0)+'）';
  AU.ontimeupdate=function(){ if(AU.currentTime>=end){ AU.pause(); AU.ontimeupdate=null;
    NOW.innerHTML='<span>'+label+'</span> 播完（'+fmt(t0)+' → '+fmt(end)+'）'; } };
}
function playAB(c,a,i){
  clearTimeout(TIMER);
  playOne(c,'#'+i+' 现网 '+fmt(c));
  var dur=(LEN+PAD)*1000;
  TIMER=setTimeout(function(){
    AU.pause();
    TIMER=setTimeout(function(){ playOne(a,'#'+i+' 对齐 '+fmt(a)); }, 600);
  }, dur);
  NOW.innerHTML='连听 <span>#'+i+'</span>：先红后蓝';
}
</script>
</div></body></html>
"""


def probe_audio(page):
    """探测 assets/pXXX.mp3 的编码参数，用于判断听感是否可信。"""
    ffprobe = os.path.join(ALIGNER_HOME, "ffmpeg", "ffprobe.exe")
    mp3 = os.path.join(HERE, "assets", page + ".mp3")
    if not (os.path.isfile(ffprobe) and os.path.isfile(mp3)):
        return None
    try:
        import subprocess

        r = subprocess.run(
            [ffprobe, "-v", "error", "-show_entries", "stream=sample_rate,channels",
             "-show_entries", "format=duration,bit_rate", "-of", "json", mp3],
            capture_output=True, timeout=30,
        )
        d = json.loads(r.stdout.decode("utf-8", "replace"))
        st = (d.get("streams") or [{}])[0]
        fm = d.get("format") or {}
        return {
            "sr": int(st.get("sample_rate", 0)),
            "ch": int(st.get("channels", 0)),
            "kbps": int(fm.get("bit_rate", 0)) // 1000,
        }
    except Exception:
        return None


def quality_note(page):
    m = probe_audio(page)
    if not m:
        return ""
    good = m["kbps"] >= 128 and m["sr"] >= 44100
    if good:
        return (
            '<div class="tip" style="background:#f0fdf4;border-color:#bbf7d0">'
            "<b>本页音质：%(sr)d Hz / %(ch)d 声道 / %(kbps)d kbps</b> —— 原始质量，"
            "听感应当清晰。若这里也觉得嘈杂，那问题在耳机或播放器，不在数据。"
            "</div>" % m
        )
    return (
        '<div class="tip" style="background:#fef2f2;border-color:#fecaca">'
        "<b>⚠️ 本页音质偏低：%(sr)d Hz / %(ch)d 声道 / %(kbps)d kbps</b>"
        "（正常篇是 44100Hz 立体声 128kbps）。低码率会同时干扰能量法和 Whisper 时间戳，"
        "<b>本页的 A/B 判断只能作为参考</b>，别据此下最终结论。"
        "</div>" % m
    )


def build_ab_page(out, page, topn=8, nctl=2, show=None):
    rows = [r for r in out[page] if r.get("adj_start") is not None]
    if not rows:
        print("[warn] %s 没有可比对的句子" % page)
        return None

    # --show：强制列出的句子（刚改过的、想复听的），排在最前面
    show_ids = set()
    if show:
        for x in show.split(","):
            x = x.strip()
            if x.isdigit():
                show_ids.add(int(x))
    forced = [r for r in rows if r["i"] in show_ids]

    dis = [r for r in sorted(rows, key=lambda r: -abs(r["adj_start"])) if r["i"] not in show_ids][:topn]
    ctl = sorted(rows, key=lambda r: abs(r["adj_start"]))[:nctl]
    ctl = [r for r in ctl if abs(r["adj_start"]) < 0.15 and r["i"] not in show_ids][:nctl]

    trs = []
    for r in forced:
        words = r["text"].split()
        head = words[0].strip(".,!?;:'\"") if words else ""
        txt = r["text"].replace(head, "<b>%s</b>" % head, 1)
        trs.append(
            '<tr class="forced"><td>#%s <span class="tag ed">已改</span></td>'
            '<td class="txt">%s</td><td class="ts">%+.3f</td>'
            '<td><button class="cur" onclick="playOne(%f,\'#%s 现值\')">现值 %.2f</button>'
            '<button class="play" onclick="playOne(%f,\'#%s 对齐\')">对齐 %.2f</button>'
            '<button onclick="playAB(%f,%f,%s)">连听 ▶▶</button></td></tr>'
            % (r["i"], txt, r["adj_start"], r["cur_start"], r["i"], r["cur_start"],
               r["al_start"], r["i"], r["al_start"], r["cur_start"], r["al_start"], r["i"])
        )
    for r in dis:
        words = r["text"].split()
        head = words[0].strip(".,!?;:'\"") if words else ""
        txt = r["text"].replace(head, "<b>%s</b>" % head, 1)
        trs.append(
            '<tr><td>#%s</td><td class="txt">%s</td><td class="ts">%+.3f</td>'
            '<td><button class="cur" onclick="playOne(%f,\'#%s 现网\')">现网 %.2f</button>'
            '<button class="play" onclick="playOne(%f,\'#%s 对齐\')">对齐 %.2f</button>'
            '<button onclick="playAB(%f,%f,%s)">连听 ▶▶</button></td></tr>'
            % (r["i"], txt, r["adj_start"], r["cur_start"], r["i"], r["cur_start"],
               r["al_start"], r["i"], r["al_start"], r["cur_start"], r["al_start"], r["i"])
        )
    for r in ctl:
        words = r["text"].split()
        head = words[0].strip(".,!?;:'\"") if words else ""
        txt = r["text"].replace(head, "<b>%s</b>" % head, 1)
        trs.append(
            '<tr class="ctrl"><td>#%s <span class="tag ok">对照</span></td>'
            '<td class="txt">%s</td><td class="ts">%+.3f</td>'
            '<td><button class="cur" onclick="playOne(%f,\'#%s 现网\')">现网 %.2f</button>'
            '<button class="play" onclick="playOne(%f,\'#%s 对齐\')">对齐 %.2f</button>'
            '<button onclick="playAB(%f,%f,%s)">连听 ▶▶</button></td></tr>'
            % (r["i"], txt, r["adj_start"], r["cur_start"], r["i"], r["cur_start"],
               r["al_start"], r["i"], r["al_start"], r["cur_start"], r["al_start"], r["i"])
        )

    html = AB_TPL % {
        "page": page,
        "rows": "\n".join(trs),
        "n": len(dis) + len(ctl),
        "ndis": len(dis),
        "nctl": len(ctl),
        "note": quality_note(page),
    }
    path = os.path.join(HERE, "_ab_%s.html" % page)
    open(path, "w", encoding="utf-8").write(html)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--silence", action="store_true", help="追加静音吸附（需解码音频）")
    ap.add_argument("--page", help="只跑一篇，如 p067")
    ap.add_argument("--tol", type=float, default=0.15, help="静音吸附容差（秒）")
    ap.add_argument("--conf", type=float, default=0.8, help="低置信阈值")
    ap.add_argument("--ab", help="生成 A/B 试听页，指定篇号如 p066（需先跑过该篇）")
    ap.add_argument("--show", help="试听页强制列出指定句，如 3 或 2,3（用于复听刚改过的句）")
    args = ap.parse_args()

    out, args = run(args)
    words_raw = json.load(open(WORDS, encoding="utf-8"))
    total, low, big = build_report(out, args, words_raw)
    print("\n完成：%d 句，低置信 %d，偏差>0.3s %d" % (total, low, big))
    print("  -> %s" % OUT_JSON)
    print("  -> %s" % OUT_MD)

    if args.ab:
        # 放在 build_report 之后：adj_start 是那里算出来的
        # 支持逗号分隔一次出多篇，如 --ab p066,p067
        for pg in [x.strip() for x in args.ab.split(",") if x.strip()]:
            p = build_ab_page(out, pg, show=args.show)
            if p:
                print("  -> %s" % p)
        print("     双击打开，戴耳机点「连听 ▶▶」即可；每页顶部标了该篇的码率")


if __name__ == "__main__":
    main()
