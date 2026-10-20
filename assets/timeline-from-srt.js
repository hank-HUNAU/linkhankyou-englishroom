/*
 * timeline-from-srt.js
 * 让篇章播放页直接以 SRT 作为逐句时间轴（句级对齐）数据源，替代内联的 DB.TL 投影。
 * 内联 DB.TL（由 assets/timeline.json 生成）保留为兜底：SRT 缺失/加载失败/解析为空时自动回退，
 * 保证离线、旧部署、p202（无 SRT）等场景仍可正常播放。
 *
 * 用法：在篇章页引擎 <script> 之前引入：
 *   <script src="../assets/timeline-from-srt.js"></script>
 * 引擎 boot() 中：
 *   window.TLF.load(PG, TLx).then(function(t){ TLx = t; run(); });
 *
 * SRT 解析只取每行 cue 的 [start, end]（毫秒精度），顺序即句序，与 SEGS 一一对应。
 */
(function () {
  'use strict';

  function parseSRT(text) {
    var cues = [];
    var raw = String(text).replace(/\r/g, '');
    var blocks = raw.split(/\n\s*\n/);
    var re = /(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})/;
    for (var i = 0; i < blocks.length; i++) {
      var lines = blocks[i].split('\n');
      for (var j = 0; j < lines.length; j++) {
        var m = lines[j].match(re);
        if (m) {
          cues.push([
            (+m[1]) * 3600 + (+m[2]) * 60 + (+m[3]) + (+m[4]) / 1000,
            (+m[5]) * 3600 + (+m[6]) * 60 + (+m[7]) + (+m[8]) / 1000
          ]);
          break;
        }
      }
    }
    return cues;
  }

  // 返回 Promise<[[start,end]...]>；始终 resolve，失败时回退 fallback
  function load(pg, fallback) {
    fallback = fallback || [];
    return new Promise(function (resolve) {
      var resolved = false;
      function done(v) {
        if (resolved) return;
        resolved = true;
        var arr = (Array.isArray(v) && v.length) ? v : fallback;
        resolve(arr);
      }
      var pid = ('00' + pg).slice(-3); // PG 为数字（如 48）→ 文件名 p048.srt（补足 3 位）
      var url = '../assets/subtitles/p' + pid + '.srt';
      try {
        fetch(url)
          .then(function (r) { return r.ok ? r.text() : Promise.reject(); })
          .then(function (t) { var c = parseSRT(t); done(c.length ? c : fallback); })
          .catch(function () { done(fallback); });
      } catch (e) {
        done(fallback);
      }
      // 超时兜底：即使 fetch 卡死也不阻塞播放（1.5s）
      setTimeout(function () { done(fallback); }, 1500);
    });
  }

  window.TLF = { parseSRT: parseSRT, load: load };
})();
