# -*- coding: utf-8 -*-
"""Genera las imagenes de la app (assets/hero.png y assets/logo.png) con Pillow.

    ~/PyxisEffects/.venv/bin/python tools/make_assets.py

Cabecera: degradado oscuro con rejilla, un grafo de nodos enlazados con brillo y una onda de audio (karaoke).
"""
import math
import os
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
VIOLET, CYAN, PINK = (124, 92, 255), (56, 217, 245), (236, 72, 153)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def gradient(w, h):
    img = Image.new("RGB", (w, h))
    px = img.load()
    c0, c1, c2 = (10, 10, 24), (28, 18, 64), (14, 40, 78)
    for y in range(h):
        for x in range(w):
            t = x / w * 0.65 + y / h * 0.35
            px[x, y] = lerp(c0, c1, t * 2) if t < 0.5 else lerp(c1, c2, (t - 0.5) * 2)
    return img


def glow(layer, radius, strength=1.0):
    blur = layer.filter(ImageFilter.GaussianBlur(radius))
    return ImageChops.add(layer, blur.point(lambda v: min(255, int(v * strength))))


def hero(w=1600, h=520):
    base = gradient(w, h).convert("RGBA")
    grid = Image.new("RGBA", (w, h), (0, 0, 0, 0))                # la rejilla va en su capa: asi el alpha se mezcla de verdad
    gd = ImageDraw.Draw(grid)
    for x in range(0, w, 40):
        gd.line([(x, 0), (x, h)], fill=(255, 255, 255, 10))
    for y in range(0, h, 40):
        gd.line([(0, y), (w, y)], fill=(255, 255, 255, 10))
    base = Image.alpha_composite(base, grid)

    rnd = random.Random(7)
    # onda de audio (barras) a lo largo de la parte baja
    bars = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bars)
    n = 96
    for i in range(n):
        x = int(i * w / n) + 6
        amp = (math.sin(i * 0.33) * 0.5 + 0.5) * 0.6 + rnd.random() * 0.4
        bh = int(24 + amp * 120)
        col = lerp(CYAN, VIOLET, i / n) + (190,)
        bd.rounded_rectangle([x, h - 28 - bh, x + 8, h - 28], radius=4, fill=col)
    base = Image.alpha_composite(base, glow(bars, 10, 0.9))
    base = Image.alpha_composite(base, bars)

    # grafo de nodos: tarjetas redondeadas unidas por curvas
    nodes = [(930, 90, VIOLET), (1160, 40, CYAN), (1160, 190, PINK), (1390, 110, VIOLET), (1030, 250, CYAN)]
    links = [(0, 1), (0, 2), (1, 3), (2, 3), (0, 4), (4, 2)]
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    for a, b in links:
        (x1, y1, c1), (x2, y2, c2) = nodes[a], nodes[b]
        x1 += 150
        pts = []
        for k in range(41):
            t = k / 40
            bx = (1 - t) ** 3 * x1 + 3 * (1 - t) ** 2 * t * (x1 + 90) + 3 * (1 - t) * t ** 2 * (x2 - 90) + t ** 3 * x2
            by = (1 - t) ** 3 * (y1 + 36) + 3 * (1 - t) ** 2 * t * (y1 + 36) + 3 * (1 - t) * t ** 2 * (y2 + 36) + t ** 3 * (y2 + 36)
            pts.append((bx, by))
        ld.line(pts, fill=lerp(c1, c2, 0.5) + (230,), width=4, joint="curve")
    base = Image.alpha_composite(base, glow(lay, 8, 1.2))
    base = Image.alpha_composite(base, lay)
    card = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    for x, y, c in nodes:
        cd.rounded_rectangle([x, y, x + 150, y + 72], radius=14, fill=(20, 20, 40, 235), outline=c + (255,), width=3)
        cd.rounded_rectangle([x, y, x + 150, y + 24], radius=14, fill=c + (255,))
        cd.rectangle([x, y + 14, x + 150, y + 24], fill=c + (255,))
        cd.ellipse([x - 8, y + 42, x + 8, y + 58], fill=(20, 20, 40, 255), outline=c + (255,), width=3)
        cd.ellipse([x + 142, y + 42, x + 158, y + 58], fill=c + (255,))
        cd.rounded_rectangle([x + 22, y + 44, x + 112, y + 52], radius=4, fill=(255, 255, 255, 60))
    base = Image.alpha_composite(base, glow(card, 14, 0.6))
    base = Image.alpha_composite(base, card)

    # vineta
    vig = Image.new("L", (w, h), 0)
    ImageDraw.Draw(vig).ellipse([-w * 0.2, -h * 0.5, w * 1.2, h * 1.5], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(90))
    dark = Image.new("RGBA", (w, h), (6, 6, 16, 255))
    base = Image.composite(base, dark, vig)
    return base.convert("RGB")


def logo(size=256):
    s = size * 4
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i in range(s):                                          # cuadrado redondeado con degradado diagonal
        pass
    grad = Image.new("RGBA", (s, s))
    gp = grad.load()
    for y in range(s):
        for x in range(s):
            gp[x, y] = lerp(VIOLET, CYAN, (x + y) / (2 * s)) + (255,)
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, s - 1, s - 1], radius=int(s * 0.23), fill=255)
    img = Image.composite(grad, img, mask)
    d = ImageDraw.Draw(img)
    w = int(s * 0.07)
    nodes = [(0.30, 0.34), (0.70, 0.34), (0.50, 0.70)]          # tres nodos unidos = grafo
    px = [(int(x * s), int(y * s)) for x, y in nodes]
    for a, b in ((0, 1), (1, 2), (2, 0)):
        d.line([px[a], px[b]], fill=(255, 255, 255, 235), width=w)
    r = int(s * 0.085)
    for x, y in px:
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, 255))
        d.ellipse([x - r // 2, y - r // 2, x + r // 2, y + r // 2], fill=lerp(VIOLET, CYAN, 0.5) + (255,))
    return img.resize((size, size), Image.LANCZOS)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    hero().save(os.path.join(OUT, "hero.png"), optimize=True)
    logo().save(os.path.join(OUT, "logo.png"), optimize=True)
    print("assets generados en", OUT)
