"""Erzeugt die App-Icons (nur einmalig nötig; braucht Pillow)."""
from PIL import Image, ImageDraw

INK = (14, 20, 32)
AMBER = (232, 178, 58)
TEAL = (63, 184, 175)


def rounded_bar(d, x, y, w, h, r, color):
    d.rounded_rectangle([x, y, x + w, y + h], radius=r, fill=color)


def make(size, pad_ratio=0.0):
    img = Image.new("RGB", (size, size), INK)
    d = ImageDraw.Draw(img)
    # Sicherheitszone für maskable: Inhalt zentriert
    inset = int(size * pad_ratio)
    area = size - 2 * inset
    # 4 aufsteigende Balken (Quoten/Statistik-Motiv)
    heights = [0.42, 0.60, 0.80, 1.00]
    colors = [AMBER, AMBER, AMBER, TEAL]
    n = len(heights)
    band_w = area * 0.62
    gap = band_w * 0.10
    bw = (band_w - gap * (n - 1)) / n
    base_y = inset + area * 0.80
    x0 = inset + (area - band_w) / 2
    r = max(2, int(bw * 0.22))
    for i, (hf, col) in enumerate(zip(heights, colors)):
        bh = area * 0.58 * hf
        x = x0 + i * (bw + gap)
        rounded_bar(d, x, base_y - bh, bw, bh, r, col)
    # Grundlinie
    d.rounded_rectangle([x0, base_y + area * 0.02, x0 + band_w, base_y + area * 0.05],
                        radius=int(area * 0.015), fill=(40, 50, 74))
    return img


# Standard-Icons (Inhalt mit etwas Rand -> auch als any/apple-touch gut)
make(512, 0.16).save("web/icons/icon-512.png")
make(512, 0.16).resize((192, 192), Image.LANCZOS).save("web/icons/icon-192.png")
make(512, 0.16).resize((180, 180), Image.LANCZOS).save("web/icons/icon-180.png")
# Maskable: enger zentriert (Sicherheitszone), Vollbild-Hintergrund
make(512, 0.26).save("web/icons/icon-512-maskable.png")
print("Icons erzeugt:", *__import__("os").listdir("web/icons"))
