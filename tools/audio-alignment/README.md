# 音频对齐工具链（ASR / TB 三重证据）

本目录从上一任 WorkBuddy 工作区（`C:\Users\Thinkpad\WorkBuddy\2026-10-08-22-28-29`）
交接而来，于 2026-10-12 入库。负责把**教师用书栏目标题 ↔ 官方 CD 198 轨音频**做精确对齐，
产出的最终成果是 `_alignment.json`（轨 → 单元/课次/栏目/练习号），
以及 `../reports/` 下的一组可点击对照表 HTML。

## 数据文件（成果，可追溯）

| 文件 | 内容 |
|---|---|
| `_alignment.json` | **最终对齐结果**：198 轨 → 单元/课次/栏目/练习号（`st` = exact/alias/inferred/asr） |
| `_tb_refs.json` | 67 册教师用书文本层解析出的「课次 → 轨号引用」 |
| `_durations.json` | 198 轨时长（`_match_source.py` 同款时长指纹） |
| `_asr_tracks.json` | 27 轨的 faster-whisper 转写（含轨内公告文本） |
| `_asr_alias.json` | 12 个改名/别名文件的公告验证结果 |
| `_tb_cache/` | 67 份教师用书 PDF 提取出的文本缓存（pypdf，可重算） |
| `_tb_u7l1.txt` | Unit 7 第 1 次课文本样例 |

## 脚本流水线

```
_build_alignment.py          教师用书文本层轨号解析 → _alignment.json（89 轨精确 + 12 别名 + 25 推断）
    ↓
_asr_tracks.py               faster-whisper 转写 25 个推断轨 → _asr_tracks.json（轨内公告）
_asr_alias.py                12 个改名文件 ASR 验证 → _asr_alias.json
    ↓
_asr_apply.py                把 ASR 公告写回 _alignment.json（inferred→asr，三重证据互锁）
_asr_match.py                ASR 转写 × TB 练习块匹配（辅助核验）
    ↓
_make_html.py                栏目标题与音频对照表.html
_make_lesson_map.py          教师用书逐课标题-音频对应表.html
_make_report.py              站点与数据接入需求报告.html
_make_repo_list.py           GitHub 仓库清单.html
```

## 环境依赖

- **Python venv**：仓库根 `.venv-align/`（`torch` / `torchaudio` / `soundfile` / `faster-whisper` / `PyAV`）。
  `_asr_tracks.py` / `_asr_alias.py` 依赖 `faster_whisper`，用
  `..\.venv-align\Scripts\python.exe _asr_tracks.py` 跑。
- **素材库**：脚本里 `base = r"E:\04 少儿原版课程\03 Think 0 课程制作\003 第三版课程材料"`，
  指向官方 CD 音频与教师用书 PDF。这是环境事实，不是仓库内容；换机器需改这一处。

## 说明

- 所有路径已从上一任的硬编码 `C:\Users\Thinkpad\WorkBuddy\...` 改为脚本自身目录
  （`os.path.dirname(os.path.abspath(__file__))`），整目录搬移后仍可复算。
- `_asr_tracks.py` / `_asr_alias.py` 的转写结果已经固化在对应 JSON 里，日常无需重跑。
- 产出 HTML 统一写进仓库根的 `reports/`。
