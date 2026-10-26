# TH!NK PWA 图标生成：品牌渐变(#10B981→#7C3AED) + 白色 T 字标
# 产出 assets/icon-192.png / icon-512.png / icon-maskable-512.png / apple-touch-icon.png
from PIL import Image, ImageDraw, ImageFont
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(OUT, exist_ok=True)
G1, G2 = (16, 185, 129), (124, 58, 237)     # #10B981 → #7C3AED

def grad(size):
    im = Image.new("RGB", (size, size))
    d = ImageDraw.Draw(im)
    for y in range(size):
        for_x = y / max(1, size - 1)
        # 对角渐变：左下绿 → 右上紫
        for x in range(0, size, max(1, size // 96)):
            t = min(1.0, (x / max(1, size - 1) * 0.55 + for_x * 0.45))
            c = tuple(int(G1[i] + (G2[i] - G1[i]) * t) for i in range(3))
            d.line([(x, y), (min(size, x + max(1, size // 96)), y)], fill=c)
    return im

def font(size, px):
    for p in (r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\segoeuib.ttf"):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, px)
            except Exception:
                pass
    return ImageFont.load_default()

def make(size, name, radius_ratio=0.22, pad_ratio=0.0):
    im = grad(size).convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=int(size * radius_ratio), fill=255)
    im.putalpha(mask)
    # 字标：T + 感叹号点（TH!NK 的 ! 意象）
    d = ImageDraw.Draw(im)
    pad = int(size * pad_ratio)
    box = size - pad * 2
    fx = font(size, int(box * 0.62))
    txt = "T"
    bb = d.textbbox((0, 0), txt, font=fx)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    tx = pad + (box - tw) / 2 - bb[0]
    ty = pad + (box - th) / 2 - bb[1] - int(box * 0.04)
    d.text((tx, ty), txt, font=fx, fill=(255, 255, 255, 255))
    # 感叹号圆点（右上）
    r = int(box * 0.075)
    cx, cy = pad + box * 0.78, pad + box * 0.26
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, 235))
    im.save(os.path.join(OUT, name), "PNG")
    return name, size

print("生成:", make(192, "icon-192.png"),
      make(512, "icon-512.png"),
      make(512, "icon-maskable-512.png", radius_ratio=0.5, pad_ratio=0.14),
      make(180, "apple-touch-icon.png", radius_ratio=0.0))
