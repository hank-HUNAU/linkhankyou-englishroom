# -*- coding: utf-8 -*-
"""听力 6 篇交叉 ASR 验证：small(beam5) + base(beam5) 对比现行文本，输出逐句差异报告"""
import io, sys, os, json, re, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
os.environ.setdefault("HF_HUB_OFFLINE", "1")
ROOT = os.path.dirname(os.path.abspath(__file__))
from faster_whisper import WhisperModel

def unit_of(pg):
    return 12 if pg in (110, 111, 113, 114, 117, 202) else 7 if pg <= 73 else 8 if pg <= 80 else 9 if pg <= 90 else 10 if pg <= 99 else 11

be = json.load(open(os.path.join(ROOT, '_book_extra.json'), encoding='utf-8'))

def arts_of(pg):
    if str(pg) in be['book']:
        return [s for p in be['book'][str(pg)]['arts'] for s in p]
    for f in glob.glob(os.path.join(ROOT, '篇章页', '复习_%03d_*.html' % pg)):
        h = open(f, encoding='utf-8').read()
        marker = '%d:{u:"Unit ' % pg
        i = h.find(marker)
        a = h.find('arts:[', i)
        d = 0; inS = None
        for k in range(a + 5, len(h)):
            c = h[k]
            if inS:
                if c == '\\': continue
                elif c == inS: inS = None
            else:
                if c in '"\'': inS = c
                elif c == '[': d += 1
                elif c == ']':
                    d -= 1
                    if d == 0: return [s for p in json.loads(h[a + 5:k + 1]) for s in p]
    return []

def norm_words(t):
    return re.sub(r"[^a-z0-9'\s]", ' ', t.lower()).split()

MODELS = {}
def get_model(size):
    if size not in MODELS:
        MODELS[size] = WhisperModel(size, device='cpu', compute_type='int8')
    return MODELS[size]

REPORT = {}
for pg in [69, 77, 87, 95, 105, 113]:
    sents = arts_of(pg)
    cur = ' '.join(sents)
    aw = norm_words(cur)
    asr = {}
    for size in ('small', 'base'):
        try:
            model = get_model(size)
            segs, _ = model.transcribe(os.path.join(ROOT, 'assets', 'p%03d.mp3' % pg),
                                       language='en', word_timestamps=True, beam_size=5, temperature=0.0,
                                       vad_filter=False, condition_on_previous_text=False)
            words = []
            for s in segs:
                for w in s.words:
                    words.append((w.start, w.end, w.word))
            asr[size] = words
        except Exception as e:
            print('  [warn] %s 模型转写失败: %s' % (size, e))
            asr[size] = []
    # 词序列（去噪音标记）
    def wseq(ws):
        return [re.sub(r"[^a-z0-9']", '', w[2].lower()) for w in ws if re.sub(r"[^a-z0-9']", '', w[2].lower())]
    sa, sb = wseq(asr['small']), wseq(asr['base'])
    # 双模型一致集合
    setA, setB = set(sa), set(sb)
    both = setA & setB
    # 现文有而双模型都没有的词（候选误听）
    curSet = set(aw)
    suspicious = sorted(curSet - both)
    # PDF 片段验证（练习引用句）：从教师用书全文找现文句子的完全包含
    import fitz
    PDFBASE = r'E:/04 少儿原版课程/03 Think 0 课程制作/Codex 学习中心/按单元与课次教师用书_文字层可提取'
    u = unit_of(pg)
    pdfw = set()
    for f in glob.glob(os.path.join(PDFBASE, 'Unit %d 第*课_教师用书.pdf' % u)):
        doc = fitz.open(f)
        for p in doc: pdfw |= set(norm_words(p.get_text()))
    verified = [s for s in sents if len(norm_words(s)) >= 3 and set(norm_words(s)) <= pdfw]
    REPORT[pg] = {'suspicious': suspicious, 'n_sents': len(sents), 'pdf_verified_sents': len(verified)}
    print('p%03d: %d句 | 现文词数 %d | 双模型一致词 %d | 候选误听 %d: %s | PDF片段整句验证 %d/%d'
          % (pg, len(sents), len(aw), len(both), len(suspicious), ' '.join(suspicious[:25]), len(verified), len(sents)))

json.dump(REPORT, open(os.path.join(ROOT, '_listen_cross_report.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
