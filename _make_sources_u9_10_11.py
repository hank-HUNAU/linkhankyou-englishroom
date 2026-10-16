# -*- coding: utf-8 -*-
"""生成 _unit_9/10/11_source.json（模板 _unit_8_source.json）。case2 句子从 txt 拆，case1 用整理好的自然句。"""
import json, re, os

TXT = "词汇诊断/篇章文本_U7_U12"
MAT = r"003 第三版课程材料"

def split_sents(text):
    text = text.replace("’", "'").replace("‘", "'").replace("…", "...")
    out = []
    for para in [p.strip() for p in text.split("\n") if p.strip()]:
        # 缩写保护后按 ". " 切
        prot = para.replace("p.m.", "p§m§").replace("a.m.", "a§m§")
        parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9'“\"1])", prot)
        for p in parts:
            p = p.replace("p§m§", "p.m.").replace("a§m§", "a.m.").strip()
            if p: out.append(p)
    return out

U9 = {"unit": 9, "pages": {
  "p085": {"section": "阅读A", "title": "Kitchen Kids", "type": "case2",
    "audio": "第9单元 第1次课 篇章阅读 音频.mp3",
    "sentences": split_sents(open(os.path.join(TXT, "Unit9_p085_Kitchen Kids.txt"), encoding="utf-8").read().split("\n",1)[1])},
  "p087": {"section": "听力", "title": "Cooking", "type": "case1",
    "audio": "903.mp3",
    "sentences": ["Can we make some sandwiches, Dad?", "Of course you can. No problem.", "Would you like some help?",
      "No, we're okay, thanks.", "Can we use this cheese, Dad?", "No, your mum wants that for the lasagna. Use this cheese.",
      "Okay.", "We need some salad in the sandwiches. Have we got any?", "There's no cucumber, but there are some tomatoes.",
      "Let's have cheese and tomato sandwiches then.", "Cool.", "What are you doing, Dad?",
      "I'm putting some peanut butter on the bread. It's tastier than butter.", "Don't do that.", "Too late.",
      "The thing is, Sally is allergic to nuts.", "Oh no. I'm sorry.", "Never mind. I can eat these.",
      "And you can make some more.", "We can't make any more. We haven't got any more bread.",
      "I know. Can we go for fish and chips, Dad?", "Hmm, okay. Yes, we can.", "Great.", "And can Sally and Max come too?",
      "Yes, of course they can.", "But first, we must clean up this mess.", "Oh, Dad. We're hungry now. Can we do that later?",
      "No, we can't."]},
  "p088": {"section": "阅读B", "title": "In a restaurant", "type": "case1",
    "audio": "905.mp3",
    "sentences": ["Hello. Can I help you?", "Hi, yes. We'd like a table for two, please.", "Here are the menus.", "Thanks.",
      "What would you like to drink?", "I'd like an orange juice.", "And I'd like water, please.", "Great.",
      "Are you ready to order now?", "Yes. I'd like the pizza with salad.", "Any starters?", "No thanks.",
      "Would you like any extra toppings on the pizza? Onion, peppers, or tomatoes?", "Some peppers, please.",
      "And what would you like?", "I'd like the chicken and chips.", "Okay. Is that everything?", "Yes. Thank you.",
      "Would you like a dessert?", "Yes, please. I'd like the fruit salad with vanilla ice cream.", "Me, too.",
      "How are your desserts?", "Great.", "Would you like any more drinks?", "No, thanks. We'd like the bill, please.",
      "Of course.", "Thank you."]},
  "p090": {"section": "口语", "title": "Offering and asking for help", "type": "case1",
    "audio": "Thk2e_BE_L0_SB_Unit_9_p90_t09[公众号happyshare2023].mp3",
    "sentences": ["Wow! What a great smell!", "Thanks, Mum! It's lasagna. It's in the oven and it's almost ready.",
      "Lasagna from the shop?", "No, Mum. It's my lasagna.", "It's got meat, pepper, mushrooms, cheese, onion, everything.",
      "And we can eat it with a bit of salad.", "Oh, right! But we? Who's coming for lunch?",
      "Mark and Chloe. We want to study together this afternoon and have lunch together first.", "That's okay, right?",
      "Of course, Joe. But...", "But what, Mum?", "Well, the thing is, I'd like a nice quiet afternoon.",
      "Oh, don't worry, Mum. After lunch, we plan to study upstairs in my room.", "Oh! It's ready!",
      "Be careful, Joe. It's very hot. Can I help you?",
      "It's okay, Mum. I can just... Oh, no! My lasagna! It's all over the floor!", "Now what?",
      "Well, first, let's clean it all up. And then, do you and your friends want to go to the new sandwich shop?",
      "Not really. But I've got an idea, Mum. We can just have the salad.",
      "Okay. And you and I can make some chocolate-covered bananas so your friends can have some dessert, too.",
      "Thanks, Mum. You're the best!"]},
}}

U10 = {"unit": 10, "pages": {
  "p092": {"section": "阅读A", "title": "She was the first woman in space", "type": "case2",
    "audio": "Thk2e_BE_L0_SB_Unit_10_p92_t01[公众号happyshare2023].mp3",
    "sentences": split_sents(open(os.path.join(TXT, "Unit10_p092_She was the first woman in space.txt"), encoding="utf-8").read().split("\n",1)[1])},
  "p095": {"section": "听力", "title": "A prize-giving at school", "type": "case1",
    "audio": "Thk2e_BE_L0_SB_Unit_10_p95_t03[公众号happyshare2023].mp3",
    "sentences": ["Hi Will, how are you? Are you better?", "Yes, thanks. I was ill yesterday and the day before but I'm okay now.",
      "Good, I'm pleased.", "So yesterday was the prize-giving at school, right? Was it good?",
      "No, it wasn't. Well, not really. There weren't many parents there.",
      "Oh really? There were lots last year. Were all the teachers there?",
      "Of course! The teachers can't choose, can they?",
      "No, and neither can the kids. Anyway, who were the big winners this year?",
      "Well, the best student of the year for the whole school was Sandra Hammond.",
      "Sandra? Was she the best student last year too?",
      "No, she wasn't. It was her brother Tom. This year, Tom was the best sports person in the school.",
      "Oh, the Hammonds! They always win everything! Boring!",
      "I know, but it's okay. They're leaving at the end of term, so next year, who knows? Maybe you!",
      "You're joking of course. I'm never the best at anything.",
      "Well, anyway, guess who the best science student was?", "No idea. Andy Clarkson?", "No, me!",
      "You? Really? Well done! That's fantastic! I'm proud of you. Was the prize something nice?",
      "Yes, it was. A book about science. I really want to read it.", "Good for you, Alice. Well done. Thanks, Will."]},
  "p096": {"section": "阅读B", "title": "Sports achievers", "type": "case1",
    "audio": "Thk2e_BE_L0_SB_Unit_10_p96_t05[公众号happyshare2023].mp3",
  },
}}

U10["pages"]["p096"] = {"section": "阅读B", "title": "Sports achievers", "type": "case1",
  "audio": "Thk2e_BE_L0_SB_Unit_10_p96_t05[公众号happyshare2023].mp3",
  "sentences": [
    "Yesterday, I was online and I learned about a woman called Amy who walked all around the UK to get money for charity and in winter when there was rain and snow. Do you know any other amazing stories like that?",
    "How about Dee Caffari? She sailed around the world non-stop three times. That's right, three times. Imagine the wind and the rain. Fantastic, eh? Jenny.",
    "OK, well, there's a boy called Jordan Romero from the US. He climbed Mount Everest when he was 13 years old. It's really cold up there, but he managed to get to the top. Only 13. Now that's an achievement. Sam.",
    "My friend Corey Armstrong decided to run a marathon when he was 16. He finished in just over four hours. He enjoyed it a lot, so then he decided to do the marathon in Death Valley in the US. It's so hot there, often more than 40 degrees Celsius. This time he was slower, almost five hours, but I still think it's fantastic. 42 kilometres when it's over 40 degrees. I think he almost died. Martha.",
    "Before 1926, a lot of women tried to swim the cold water of the English Channel from England to France, but they all failed. But in 1926, Gertrude Ederle, an Olympic gold medal swimmer, arrived on an English beach after 14 hours and 31 minutes. She returned to her home in New York a hero. How about that? Mark."]}

U11 = {"unit": 11, "pages": {
  "p102": {"section": "阅读A", "title": "Dolphins to the rescue", "type": "case2",
    "audio": "Thk2e_BE_L0_SB_Unit_11_p102_t01[公众号happyshare2023].mp3",
    "sentences": split_sents(open(os.path.join(TXT, "Unit11_p102_Dolphins to the rescue.txt"), encoding="utf-8").read().split("\n",1)[1])},
  "p105": {"section": "听力", "title": "Josh's holiday", "type": "case1",
    "audio": "Thk2e_BE_L0_SB_Unit_11_p105_t02[公众号happyshare2023].mp3",
    "sentences": ["Hey Josh, did you have a good holiday?", "Hi Mandy, yes it was great.", "Where did you go?",
      "The Pantanal, it's in the east of Brazil. It's a really big wetland.", "Oh right, so why did you go there?",
      "Because there are amazing animals and birds there.", "We all love animals in my family, especially my dad.",
      "He's a bird watcher.", "Really? I didn't know that.", "Yes, he loves birds.", "So are you a big bird watcher too?",
      "Well I like them and we saw some really beautiful parrots and toucans, but I prefer the other animals.",
      "Did you see anything special?", "Yes, loads of stuff.", "There were lots of Cayman.", "Cayman? What are they?",
      "They're like small crocodiles.", "Cool, what else did you see?",
      "We saw an anaconda, you know one of those really big snakes, and then one night we heard a jaguar but we didn't see it.",
      "Wow, were you scared?", "No, it was exciting, especially because it was so near our tent.",
      "Tent? Did you go camping?", "Yes, but just for a few nights. Most of the time we were in small hotels.",
      "So how did you travel around? Did you have a guide?", "Yes, we did.", "His name was Sergio.",
      "He knew where to find all the animals.", "Did he speak English?",
      "Yes, he did. His English was good which was lucky because no one in my family can speak Portuguese.",
      "It sounds like you had a great time.", "We did. It was fantastic."]},
  "p106": {"section": "阅读B", "title": "Extinct animals", "type": "case2",
    "audio": "Thk2e_BE_L0_SB_Unit_11_p106_t05[公众号happyshare2023].mp3",
    "sentences": split_sents(open(os.path.join(TXT, "Unit11_p106_Extinct animals.txt"), encoding="utf-8").read().split("\n",1)[1])},
  "p108": {"section": "口语", "title": "Sequencing a story", "type": "case1",
    "audio": "Thk2e_BE_L0_SB_Unit_11_p108_t07[公众号happyshare2023].mp3",
    "sentences": ["Hey Nathan, how are you? Did you have a good weekend?", "Yes, thanks. It was really good on Saturday.",
      "Oh, why? What did you do?", "In the morning, I went to town with Harry. We went to the ice cream shop.",
      "Harry jumped out of the front of the car and stopped with her hand.", 
      "Well, we walked out of the shop with her books when she saw her friend.",
      "Oh no! What happened next?", "Well, first, let's see..."]},
}}

for spec in (U9, U10, U11):
    fn = "_unit_%d_source.json" % spec["unit"]
    json.dump(spec, open(fn, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    tot = sum(len(p["sentences"]) for p in spec["pages"].values())
    print(fn, "→", len(spec["pages"]), "篇", tot, "句")
    for pk, p in spec["pages"].items():
        print("  %s %s %s %d句 audio=%s" % (pk, p["section"], p["title"], len(p["sentences"]), p["audio"][:40]))
