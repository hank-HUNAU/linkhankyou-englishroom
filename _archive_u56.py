# -*- coding: utf-8 -*-
"""U5/U6 归档正典三件套：01_正文篇章 (mp3+句级数据json+txt原文) + 02_词汇数据"""
import io, sys, os, json, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ARCH = r'E:/04 少儿原版课程/03 Think 0 课程制作/Codex 学习中心/Think F 教材资产'
REPO = os.path.join(ARCH, 'github在线推送')
tl = json.load(open(os.path.join(REPO, 'assets', 'timeline.json'), encoding='utf-8'))
be = json.load(open(os.path.join(REPO, '_book_extra.json'), encoding='utf-8'))

META = {
    48: ('U5', 'U5_FreeTime', 'u5_p048_robotics_club', '阅读A', 'Robotics Club is cool!', 'Unit5_p48_Robotics Club is cool!.txt'),
    51: ('U5', 'U5_FreeTime', 'u5_p051_favourite_technology', '听力', 'Favourite technology', 'Unit5_p51_Favourite technology.txt'),
    52: ('U5', 'U5_FreeTime', 'u5_p052_tech_break', '阅读B', 'Do you need a tech break?', 'Unit5_p52_Do you need a tech break?.txt'),
    54: ('U5', 'U5_FreeTime', 'u5_p054_school_concert', '口语', 'The school concert', 'Unit5_p54_The school concert.txt'),
    56: ('U6', 'U6_BestFriends', 'u6_p056_real_friend', '阅读A', 'A real friend', 'Unit6_p56_A real friend.txt'),
    59: ('U6', 'U6_BestFriends', 'u6_p059_present_annie', '听力', 'A present for Annie', 'Unit6_p59_A present for Annie.txt'),
    60: ('U6', 'U6_BestFriends', 'u6_p060_new_teacher', '口语对话', 'The new teacher', 'Unit6_p60_The new teacher.txt'),
    63: ('U6', 'U6_BestFriends', 'u6_p063_welcoming_people', '文化', 'Welcoming people around the world', 'Unit6_p63_Welcoming people around the world.txt'),
}
for pg, (u, folder, pkey, typ, title, txtname) in META.items():
    d1 = os.path.join(ARCH, folder, '01_正文篇章')
    d2 = os.path.join(ARCH, folder, '02_词汇数据')
    os.makedirs(d1, exist_ok=True); os.makedirs(d2, exist_ok=True)
    p3 = '%03d' % pg
    # 1) mp3
    shutil.copy2(os.path.join(REPO, 'assets', 'p%s.mp3' % p3), os.path.join(d1, 'p%s.mp3' % p3))
    # 2) 句级数据 json
    k = 'p' + p3
    sents = tl[k]
    txt = '\n'.join(' '.join(p) for p in be['book'][str(pg)]['arts'])
    j = {
        'unit': u, 'passage_key': pkey, 'page': 'p' + p3, 'title': title, 'type': typ,
        'n_sent': len(sents), 'duration_s': sents[-1]['end_s'],
        'source': 'github在线推送/assets/timeline.json（句级音频对齐，2026-10-19 U5/U6 标准化）；原文教师用书文字层 + 书后资源 Audioscript',
        'sentences': [{'i': o['i'], 'start_s': o['start_s'], 'end_s': o['end_s'], 'text': o['text']} for o in sents]
    }
    json.dump(j, open(os.path.join(d1, '句级数据_p%s.json' % p3), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    # 3) txt 原文
    open(os.path.join(d1, txtname), 'w', encoding='utf-8').write(txt + '\n')
    # 4) 02_词汇数据：主题词汇 json 副本
    src = os.path.join(ARCH, '00_主题词汇', 'theme_u%s.json' % u[1])
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(d2, 'theme_u%s.json' % u[1]))
    print('p%s → %s 归档完成（%d 句）' % (p3, folder, len(sents)))
print('U5/U6 归档三件套完成')
