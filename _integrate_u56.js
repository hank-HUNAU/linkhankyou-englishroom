// U5/U6 集成：_book_extra.json +8 篇 / index.html UNITS live + PASSAGES 卡
const fs = require('fs');

// ── 1) book_extra：U5/U6 8 篇（arts 按原文段落分组） ──
const be = JSON.parse(fs.readFileSync('_book_extra.json', 'utf8'));
const A5 = '第5单元/第5单元 音频/', A6 = '第6单元/第6单元 音频/';
be.book['48'] = { u: 'Unit 5', audio: '../assets/p048.mp3', title: 'Robotics Club is cool!', arts: [
  ["Our school has a Robotics Club and it's brilliant. I know this because I go to it! So, what is a Robotics Club? Easy – it's a club for building robots and I love robots."],
  ["Mr Thomas is the club leader. He thinks of things for us to do and helps us build our robots. He's really cool and very kind. He never gets angry with us. He teaches Music (not Design and Technology!), but he just loves everything to do with computers."],
  ["We often make our own robots, but we sometimes watch videos of other robots on the internet. When our robot is ready, we use computer programs to make it do things."],
  ["Every year there is a competition for schools all over the country. I feel really excited when we show our robots to students from other schools. We never win, but that's not important. The other students like watching our robot move. It feels great."],
  ["I love Robotics Club. It's a great place to meet new people. You make so many friends and not just with people from school. Robotics Club is for everyone."],
  ["We meet in the school hall every Monday at lunchtime and every Thursday after school. Come and see us – we're always happy to see new people!"]
] };
be.book['51'] = { u: 'Unit 5', audio: '../assets/p051.mp3', title: 'Favourite technology', arts: [
  ["My favourite piece of technology is my phone. I love it. I use it for so many things. I use it to text my friends. I use it to play games. I sometimes use it to help me with my homework. I use it for lots of things, but I don't use it in class."],
  ["I love my virtual reality headset. It's so cool. I feel that I'm really in the game. I don't play games on my TV because they don't feel as real. The headset is very easy to wear, and it never hurts my head. The only problem is that the games are very expensive."],
  ["My tablet is brilliant. It was my birthday present this year. What a great present. It's very thin and it doesn't feel heavy, but it's got a big screen, so it's great for watching films and playing games. My mum and dad always want to use it, so I have a special place to put it where they can't find it."],
  ["My favourite things are my headphones. I love music. I listen to it all the time. My mum often wants the radio on, but we don't like the same kind of music. With my headphones, it's no problem. I listen to cool music, and she listens to the old music that she likes."]
] };
be.book['52'] = { u: 'Unit 5', audio: '../assets/p052.mp3', title: 'Do you need a tech break?', arts: [
  ["How many hours do you look at a TV, phone, tablet or computer every day?", "Do you check your phone before school?", "Do you worry when your phone or tablet has no power?", "Do you watch TV before you do your homework?", "Does your family ever say that you use your phone too much?"],
  ["5 to 9 – No, you don't need a break! You use it well.", "10 to 12 – You're not too bad, but be careful!", "13 to 15 – Yes, you do. You need a break from tech! Do something different!"]
] };
be.book['54'] = { u: 'Unit 5', audio: '../assets/p054.mp3', title: 'The school concert', arts: [
  ["Hey, Liz. What's wrong?", "I've got a cold.", "So? Everyone gets a cold sometimes. What's the problem?", "The problem? The problem is, there's the school concert tomorrow. And I'm the singer!", "I'm sure you can still sing.", "No way, Claudio! Listen to my voice!", "She's right. This really is a problem. Oh, Liz, I'm sorry.", "Don't worry, Liz. We're here to help you.", "How, Claudio?", "I don't know!", "Just a minute. I've got an idea. Lucy, you can sing, can't you?", "A little, Liz. But I can't sing with a band.", "Oh, come on, Lucy. You can do it. You're a great singer.", "OK, I'll do it for you, Liz. But this is crazy! OK, what are the songs?", "I'll tell you later. You're the best, Lucy!"]
] };
be.book['56'] = { u: 'Unit 6', audio: '../assets/p056.mp3', title: 'A real friend', arts: [
  ["Julia is 11. She has got curly, brown hair, brown eyes and a big smile. She's got a lot of friends at school. All her classmates like her."],
  ["At lunchtime, Julia always goes to the school canteen and buys her lunch. Her friend, Jack, doesn't buy any food. He just drinks a glass of water. Jack does this every day, and Julia is worried."],
  ["One day, she asks Jack, 'Are you hungry?' 'Yes,' says Jack. 'But you don't eat at school,' says Julia. 'I haven't got any money for lunch,' says Jack. 'My dad hasn't got a job and my mum's ill. They've got lots of problems. But don't worry about me – I'm OK.'"],
  ["Julia thinks about this. At home, she's got a big glass jar. It's full of coins. She wants to buy an electric scooter one day. That night, Julia opens the jar, takes the coins and puts them into a bag. Her mum sees her. 'Why are you doing that?' she asks."],
  ["'My friend Jack hasn't got any lunch money and I've got some money here. This is for him.' 'That's very kind of you,' says her mum. She feels happy that her daughter wants to do this."],
  ["The next day, Julia and her mum go and see her teacher. They tell her about Jack and Julia gives her the money. 'This is for Jack's lunch. Now, he can have lunch every day,' she says. Julia hasn't got an electric scooter, but she's got a happy friend – Jack!"]
] };
be.book['59'] = { u: 'Unit 6', audio: '../assets/p059.mp3', title: 'A present for Annie', arts: [
  ["Hello, can I help?", "Yes. Have you got anything I can give to my best friend? It's a present.", "Yes, we've got a lot of things. Is it for a girl or a boy?", "It's for a girl, for my friend, Annie.", "OK. I've got this lovely little yellow rose. Yellow's a happy colour. It's a lovely present for a girl. It's got a necklace with it.", "Have you got any little animals?", "Yes, we've got a little silver dolphin or a dog. They both show friendship.", "Oh, I love the dolphin, and Annie likes dolphins, too. They're her favourite animal. But she's got a dog. It's just like this one.", "Hmm. So maybe the dog or the dolphin. I've got one more to show you. It's really beautiful.", "Oh, it's a heart. And it's in two pieces. That's clever.", "Yes. You wear one piece and your friend, Annie, wears the other.", "Oh, that's so cool. I like that idea, but I still prefer the dolphin. How much is it?", "It's £15.", "That's OK. Can I have the dolphin, then?", "Of course. And do you want the necklace too?", "No. Annie's got a nice silver necklace. She doesn't need another one.", "OK, then. That's £15. I've got a little bag you can put it in.", "Oh, that's great. Thank you.", "I hope she likes it."]
] };
be.book['60'] = { u: 'Unit 6', audio: '../assets/p060.mp3', title: 'The new teacher', arts: [
  ["Hi, Oliver. Good to see you.", "Hi, Ellie. You look happy. How's it going? How's your first day back at school?", "Not too bad, thanks. We've got this great new teacher. You'd really like him.", "Really? Lucky you. What does he teach?", "Science.", "But you don't like Science.", "I do now. This new teacher's very funny. He makes us all laugh and he makes Science fun. And I understand everything. It's great.", "Really? What does this new teacher look like?", "Well, he's quite tall and he's slim. He's got brown eyes and he wears glasses. He's got short curly hair. It's red like yours.", "He's got red hair?", "Yes, like yours but your hair is straight and his is curly.", "Has he got a beard?", "Yes, he's got a short beard.", "And has he got a moustache?", "Yes … Oh, and he likes sport. He plays rugby and he likes football. He goes to football matches at the weekends with his son. His son's the same age as us.", "Really? And his favourite team is Manchester City.", "Yes, it is. How do you know?", "Is this him walking towards us now?", "Yes, it is.", "That's my dad.", "No way! You're kidding!"]
] };
be.book['63'] = { u: 'Unit 6', audio: '../assets/p063.mp3', title: 'Welcoming people around the world', arts: [
  ["How do you say hello to someone you know? Do you smile? Do you touch the other person? Here are some ideas for travellers. This is how people in different countries welcome each other. Do you do different things in your country?"],
  ["In many countries in Asia, people bow their heads when they meet each other. This shows respect. In India, Nepal and Bangladesh, people bring their hands together in front of their heart and say 'Namaste'."],
  ["When you greet a grandmother or grandfather or another older person in Turkey, you kiss their right hand and then place it on your forehead. They do this in the Philippines, too."],
  ["The Maori people in New Zealand rub noses together when they meet. This is called the 'hongi'."],
  ["In Malaysia, you put your hand on your heart and nod your head. Sometimes you also take the person's hands in your hands first."],
  ["In Western countries, many people shake hands when they meet. Sometimes they just smile and say something like 'Hello!' or 'Hi!' In the US and in other countries, some people like using a 'fist bump' to greet another person. Both people make a fist, push their arm forward slowly and touch each other's fists."],
  ["In many countries around the world, friends kiss each other on the cheek. In some countries they kiss one cheek, in others they kiss both cheeks and in some they kiss cheeks three times."]
] };
fs.writeFileSync('_book_extra.json', JSON.stringify(be, null, 1) + '\n');
console.log('book_extra:', Object.keys(be.book).length, '篇（+8）');

// ── 2) index.html：UNITS live + PASSAGES ──
let h = fs.readFileSync('index.html', 'utf8');
h = h.replace("{ key:'5',  n:5,  title:'Free time',       sub:'休闲时光',    h:350, live:false }", "{ key:'5',  n:5,  title:'Free time',       sub:'休闲时光',    h:350, live:true  }");
h = h.replace("{ key:'6',  n:6,  title:'Best friends',     sub:'最佳伙伴',    h:0,   live:false }", "{ key:'6',  n:6,  title:'Best friends',     sub:'最佳伙伴',    h:275, live:true  }");
const cards = {
  "5": [{ key:'u5_48', p:'48', kind:'阅读 A', title:'Robotics Club is cool!', intro:'机器人社团快讯', demo:false }, { key:'u5_51', p:'51', kind:'听力', title:'Favourite technology', intro:'四个青少年的最爱科技', demo:false }, { key:'u5_52', p:'52', kind:'阅读 B', title:'Do you need a tech break?', intro:'科技休息小测验', demo:false }, { key:'u5_54', p:'54', kind:'口语对话', title:'The school concert', intro:'校园音乐会救场', demo:false }],
  "6": [{ key:'u6_56', p:'56', kind:'阅读 A', title:'A real friend', intro:'真心朋友朱莉娅', demo:false }, { key:'u6_59', p:'59', kind:'听力', title:'A present for Annie', intro:'给安妮挑礼物', demo:false }, { key:'u6_60', p:'60', kind:'口语对话', title:'The new teacher', intro:'新来的老师长什么样', demo:false }, { key:'u6_63', p:'63', kind:'文化', title:'Welcoming people around the world', intro:'世界各地的问候方式', demo:false }]
};
for (const u of ['5', '6']) {
  const marker = 'Object.assign(PASSAGES, { "' + u + '":';
  if (h.includes(marker)) { console.log('PASSAGES', u, '已存在，跳过'); continue; }
  const anchor = 'var K = ';
  h = h.replace(anchor, 'Object.assign(PASSAGES, ' + JSON.stringify({ [u]: cards[u] }).replace(/"/g, "'") + ' });\n\n' + anchor);
}
fs.writeFileSync('index.html', h);
console.log('index.html: UNITS U5/U6 live + PASSAGES 卡完成');
// 校验
console.log('U5 卡:', h.includes("u5_48"), '| U6 卡:', h.includes("u6_63"), '| live5:', !h.includes("title:'Free time',       sub:'休闲时光',    h:350, live:false"));
