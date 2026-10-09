# 桥接比对报告 · audio-aligner-v4.0.0 vs 现网 timeline.json

生成方式：`python _bridge_aligner.py`（容差 0.15s，低置信阈值 0.8）

> 两者是同代方法（Whisper 词级时间戳 + 序列匹配），这是**实现层面的交叉验证**，不是方法论仲裁。一致的点可采信，矛盾的点仍需人耳或 CTC 定案。

## 总览

- 比对句数：**312**（12 篇）
- 低置信句（confidence < 0.8）：**0**
- 系统偏移：Δstart 中位数 **+0.079s**、Δend 中位数 **-0.262s**（已剥离，以下均为去偏移后的值）
- 真分歧 > 0.3s 的句：**191**

## 按篇汇总（先看这张表定位问题篇）

| 篇 | 句数 | Δstart 中位数 | 去偏移后 >0.3s | 最大真分歧 | 争议句 |
|---|---|---|---|---|---|
| p066 | 27 | +0.953 | 22 | -1.870 | #10 |
| p067 | 19 | -0.202 | 9 | -0.729 | #2 |
| p069 | 21 | -0.060 | 3 | -0.823 | #11 |
| p070 | 23 | -0.264 | 14 | -1.644 | #14 |
| p072 | 15 | +0.128 | 2 | +0.364 | #5 |
| p073 | 27 | +0.485 | 19 | +4.551 | #21 |
| p110 | 28 | +0.095 | 18 | +1.066 | #22 |
| p111 | 24 | -0.025 | 12 | +1.298 | #0 |
| p113 | 42 | +0.189 | 15 | -2.144 | #27 |
| p114 | 33 | -0.024 | 14 | +1.684 | #18 |
| p117 | 30 | +0.182 | 20 | +1.848 | #20 |
| p202 | 23 | +0.560 | 17 | +2.019 | #17 |

> 整篇中位数明显偏离 0、且分歧句占比高 → 多半是**句切分口径错了**（漏句/多句/对白），不是边界微调能修的，要重切。p073 就是这一型。

## 一、首句核对（报幕相关）

| 篇 | 现网 start | 对齐 start | Δ | 置信 | 文本 |
|---|---|---|---|---|---|
| p066 | 12.142 | 12.12 | -0.022 | 1.0 | A slam dunk and the crowds cheer! |
| p067 | 9.678 | 9.44 | -0.238 | 1.0 | Nikolai Kutsenko, from Ukraine, can do a… |
| p069 | 8.121 | 8.12 | -0.001 | 1.0 | Hi, Julia. It's me, Mike. |
| p070 | 10.197 | 9.5 | -0.697 | 1.0 | It's 15th February at Greece Athena High… |
| p072 | 8.760 | 8.62 | -0.14 | 1.0 | Right! Have we got everything? Tennis ra… |
| p073 | 11.095 | 10.9 | -0.195 | 1.0 | Oh, hello. It's you. Sorry, I'm not feel… |
| p110 | 8.835 | 9.2 | 0.365 | 1.0 | Our lives move very fast today, especial… |
| p111 | 5.313 | 6.69 | 1.377 | 1.0 | A lot of big cities, like London, have g… |
| p113 | 8.410 | 8.86 | 0.45 | 1.0 | Good morning. |
| p114 | 7.159 | 6.97 | -0.189 | 1.0 | My favourite journey. We all love going … |
| p117 | 7.403 | 7.37 | -0.033 | 1.0 | Transport around the world. |
| p202 | 10.975 | 11.54 | 0.565 | 1.0 | People use different types of transport … |

## 二、真分歧 Top 30（按 |Δstart| 排序，已剥离系统偏移）

| 篇 | 句 | 现网 start | 对齐 start | Δstart* | Δend* | 文本 |
|---|---|---|---|---|---|---|
| p073 | #21 | 106.270 | 110.900 | +4.551 | -0.119 | Tyler has a geography test tomorrow … |
| p073 | #5 | 42.663 | 46.860 | +4.118 | -0.046 | Because I have a geography test tomo… |
| p073 | #6 | 53.628 | 56.940 | +3.233 | -0.312 | I can't play tennis with Tyler. |
| p073 | #13 | 82.168 | 84.980 | +2.733 | -1.613 | It's Tyler! |
| p073 | #25 | 134.988 | 137.340 | +2.273 | +8.819 | Just relax. |
| p113 | #27 | 77.125 | 75.060 | -2.144 | -0.859 | That's £19.90. |
| p202 | #17 | 148.682 | 150.780 | +2.019 | -0.932 | This strange form of transportation … |
| p066 | #10 | 65.531 | 63.740 | -1.870 | +0.564 | But here in Laos they don't play vol… |
| p117 | #20 | 108.833 | 110.760 | +1.848 | -0.050 | Ankara's cable car is cheaper than o… |
| p066 | #21 | 135.746 | 137.620 | +1.795 | -0.301 | Do you know squash? |
| p073 | #26 | 155.500 | 157.280 | +1.701 | -0.079 | See you next time! |
| p114 | #18 | 93.497 | 95.260 | +1.684 | +0.009 | What's my favourite journey? |
| p066 | #22 | 140.196 | 141.920 | +1.645 | -0.265 | Lots of people like playing it. |
| p070 | #14 | 103.145 | 101.580 | -1.644 | -0.433 | The team wins, and Jason is a real h… |
| p066 | #17 | 108.638 | 110.360 | +1.643 | -0.555 | Bowling uses a different kind of bal… |
| p073 | #1 | 17.340 | 19.000 | +1.581 | +0.056 | Why? This is why. And I have a geogr… |
| p070 | #11 | 77.633 | 76.200 | -1.512 | -0.064 | But suddenly he hits a 3-point baske… |
| p066 | #4 | 38.188 | 39.760 | +1.493 | -0.002 | Ball sports are very popular. |
| p066 | #20 | 129.970 | 131.480 | +1.431 | +0.090 | Young and old people can play this g… |
| p066 | #19 | 121.140 | 122.600 | +1.381 | +0.052 | You roll it and try to knock over th… |
| p073 | #4 | 37.914 | 39.320 | +1.327 | +0.485 | But that's not the only problem. |
| p070 | #22 | 142.340 | 143.720 | +1.301 | -0.104 | He travels across the US to help get… |
| p111 | #0 | 5.313 | 6.690 | +1.298 | -0.029 | A lot of big cities, like London, ha… |
| p066 | #5 | 43.765 | 42.560 | -1.284 | -0.065 | For example, football. |
| p073 | #23 | 123.539 | 124.860 | +1.242 | +0.002 | See, stay positive. |
| p066 | #7 | 50.206 | 51.500 | +1.215 | +0.118 | That's almost four billion people. |
| p117 | #27 | 150.907 | 152.180 | +1.194 | -0.025 | It is a safe and comfortable way to … |
| p066 | #6 | 46.015 | 47.280 | +1.186 | +0.116 | Half of the world loves football. |
| p073 | #12 | 78.392 | 79.620 | +1.149 | +0.218 | Or can I? |
| p066 | #2 | 23.097 | 24.260 | +1.084 | +0.040 | All over the world, people love watc… |

完整 312 句数据在 `_bridge_bounds.json`（含 `adj_start` / `adj_end` 字段）。

## 三、抽样取证：争议处到底谁对

对 Top 6 争议句，直接列出 Whisper 原始词流。判据很简单：**句首第一个词的时间戳**就是该句真正的起点。若现网值落在空档里或处在第一个词之后，说明现网把句首词切掉了。

**p073 #21** —— Δstart +4.551（现网 106.270 / 对齐 110.900）

- 课文：Tyler has a geography test tomorrow too, and Tyler's great at geograph
- 句首词应为：`Tyler`
- 该段词流：soon`105.80` just`109.70` you`110.50` and`110.72` tyler`110.90`
- 判定：对齐值落在句首词上，现网值落在其后 → **现网切掉了句首词**

**p073 #5** —— Δstart +4.118（现网 42.663 / 对齐 46.860）

- 课文：Because I have a geography test tomorrow, I can't do all the things I 
- 句首词应为：`Because`
- 该段词流：because`46.86` i`47.64` have`47.86` a`48.04` geography`48.18`
- 判定：对齐值落在句首词上，现网值落在其后 → **现网切掉了句首词**

**p073 #6** —— Δstart +3.233（现网 53.628 / 对齐 56.940）

- 课文：I can't play tennis with Tyler.
- 句首词应为：`I`
- 该段词流：i`56.94` can't`57.62` play`57.98` tennis`58.16`
- 判定：对齐值落在句首词上，现网值落在其后 → **现网切掉了句首词**

**p073 #13** —— Δstart +2.733（现网 82.168 / 对齐 84.980）

- 课文：It's Tyler!
- 句首词应为：`It's`
- 该段词流：it's`84.98` tyler`86.38`
- 判定：对齐值落在句首词上，现网值落在其后 → **现网切掉了句首词**

**p073 #25** —— Δstart +2.273（现网 134.988 / 对齐 137.340）

- 课文：Just relax.
- 句首词应为：`Just`
- 该段词流：just`137.34` you`138.06` and`138.32` tyler`138.48`
- 判定：对齐值落在句首词上，现网值落在其后 → **现网切掉了句首词**

**p113 #27** —— Δstart -2.144（现网 77.125 / 对齐 75.060）

- 课文：That's £19.90.
- 句首词应为：`That's`
- 该段词流：that's`75.06` 19`75.54` 90`76.06` right`77.64`
- 判定：对齐值落在句首词上，现网值落在其后 → **现网切掉了句首词**

## 四、低置信句（对齐不可信，优先人工听）

无。

