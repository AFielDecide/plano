# -*- coding: utf-8 -*-
"""Capa da peticao (Change.org) a partir da foto do torcedor com o cartao.

Pega a foto-base (_foto-base-torcedor.png), escreve "A FIEL DECIDE" no cartao
preto respeitando a perspectiva real do objeto, apaga o escudo remanescente do
fundo, corta em 16:9 e monta 3 variacoes.

Rodar com:  py gera_capa_foto.py
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np
import os

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "_foto-base-torcedor.png")
FDIR = os.path.join(BASE, "_fontes")
F_DIS = os.path.join(FDIR, "archivoblack-400.ttf")
F_MON = os.path.join(FDIR, "courierprime-700.ttf")

PAPER = (239, 236, 228)
INK = (13, 12, 11)
GRAY = (107, 101, 94)
DK_MUT = (156, 150, 141)

# cantos do cartao na foto original (medidos na ampliacao 2x)
CARD_QUAD = [(371, 541), (661, 520), (663, 731), (366, 741)]
# escudo deformado na camisa do rapaz a direita
CREST_BOX = (1645, 905, 1820, 1065)
# marca d'agua do Gemini
WM_BOX = (2370, 1520, 2460, 1610)

W, H = 1600, 900


def font(p, s):
    return ImageFont.truetype(p, s)


def tw(d, s, f):
    b = d.textbbox((0, 0), s, font=f)
    return b[2] - b[0]


def fit(d, s, path, start, max_w, floor=12):
    size = start
    while size > floor:
        f = font(path, size)
        if tw(d, s, f) <= max_w:
            return f
        size -= 2
    return font(path, floor)


def tight(d, x, y, s, f, fill):
    b = d.textbbox((0, 0), s, font=f)
    d.text((x - b[0], y - b[1]), s, font=f, fill=fill)
    return y + (b[3] - b[1])


def tracked(d, x, y, s, f, fill, tr):
    b0 = d.textbbox((0, 0), s, font=f)
    cx = x
    for ch in s:
        d.text((cx, y - b0[1]), ch, font=f, fill=fill)
        b = d.textbbox((0, 0), ch, font=f)
        cx += (b[2] - b[0]) + tr if ch != " " else tw(d, " ", f) + tr
    return y + (b0[3] - b0[1])


def tracked_w(d, s, f, tr):
    t = 0
    for ch in s:
        b = d.textbbox((0, 0), ch, font=f)
        t += (b[2] - b[0]) + tr if ch != " " else tw(d, " ", f) + tr
    return t - tr


def mosaic(d, x, y, w, h, block, border, bg, fg):
    d.rectangle([x, y, x + w - 1, y + h - 1], fill=bg, outline=fg, width=border)
    xi, on = x + border, True
    while xi < x + w - border:
        if on:
            d.rectangle([xi, y + border, min(xi + block, x + w - border) - 1,
                         y + h - border - 1], fill=fg)
        xi += block
        on = not on


def find_coeffs(dst, src):
    """coeficientes pra Image.transform PERSPECTIVE (dst -> src)"""
    A, B = [], []
    for (xd, yd), (xs, ys) in zip(dst, src):
        A.append([xd, yd, 1, 0, 0, 0, -xs * xd, -xs * yd])
        A.append([0, 0, 0, xd, yd, 1, -ys * xd, -ys * yd])
        B += [xs, ys]
    return np.linalg.solve(np.array(A, dtype=float), np.array(B, dtype=float))


# ---------------------------------------------------------------- arte do cartao
def arte_cartao(cw=620, ch=430):
    """desenha o cartao 'A FIEL DECIDE' num retangulo reto (RGBA)"""
    card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    pad = 52
    inner = cw - pad * 2

    f_big = fit(d, "DECIDE", F_DIS, 108, inner)
    f_mon = font(F_MON, 26)
    mos_h = 20
    bloco = mos_h + 30 + 78 + 12 + 78 + 26 + 26          # estimativa
    y = (ch - bloco) // 2

    mosaic(d, pad, y, 190, mos_h, 16, 2, (0, 0, 0, 0), PAPER + (255,))
    y += mos_h + 30
    y = tight(d, pad, y, "A FIEL", f_big, PAPER + (255,))
    y = tight(d, pad, y + 12, "DECIDE", f_big, PAPER + (255,))
    tracked(d, pad, y + 26, "VOTO DO TORCEDOR", f_mon, (200, 196, 188, 235), 4)
    return card


def aplica_cartao(foto):
    """cola a arte do cartao na foto respeitando a perspectiva"""
    card = arte_cartao()
    cw, ch = card.size
    src = [(0, 0), (cw, 0), (cw, ch), (0, ch)]
    coeffs = find_coeffs(CARD_QUAD, src)
    warped = card.transform(foto.size, Image.PERSPECTIVE, coeffs,
                            Image.BICUBIC)
    warped = warped.filter(ImageFilter.GaussianBlur(0.7))   # casa com o foco
    a = warped.getchannel("A").point(lambda v: int(v * 0.93))
    warped.putalpha(a)
    out = foto.copy()
    out.alpha_composite(warped)
    return out


def apaga_regiao(foto, box, blur=16, escurece=0.55, feather=22):
    """derrete uma regiao (escudo / marca d'agua) sem deixar borda dura"""
    x0, y0, x1, y1 = box
    pad = feather * 2
    reg = (max(0, x0 - pad), max(0, y0 - pad),
           min(foto.size[0], x1 + pad), min(foto.size[1], y1 + pad))
    crop = foto.crop(reg)
    fixed = crop.filter(ImageFilter.GaussianBlur(blur))
    fixed = ImageEnhance.Brightness(fixed).enhance(escurece)
    mask = Image.new("L", (reg[2] - reg[0], reg[3] - reg[1]), 0)
    ImageDraw.Draw(mask).ellipse(
        [x0 - reg[0], y0 - reg[1], x1 - reg[0], y1 - reg[1]], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(feather))
    out = foto.copy()
    out.paste(Image.composite(fixed, crop, mask), reg)
    return out


def corta_169(foto, top_ratio=0.16):
    """corta 16:9 tirando mais do rodape que do topo, e reduz pra 1600x900"""
    fw, fh = foto.size
    alvo_h = int(fw * 9 / 16)
    corte = fh - alvo_h
    top = int(corte * top_ratio)
    return foto.crop((0, top, fw, top + alvo_h)).resize((W, H), Image.LANCZOS)


def barra(img, manchete="A FIEL QUER VOTAR"):
    """tarja inferior tinta com manchete + assinatura"""
    d = ImageDraw.Draw(img)
    bh = 136
    y = H - bh
    d.rectangle([0, y, W, H], fill=INK)
    mosaic(d, 0, y - 14, W, 14, 26, 3, INK, PAPER)
    f = font(F_DIS, 54)
    tight(d, 60, y + 28, manchete, f, PAPER)
    fm = font(F_MON, 21)
    s = "#AFIELDECIDE"
    tracked(d, W - 60 - tracked_w(d, s, fm, 4), y + 34, s, fm, PAPER, 4)
    s2 = "AFIELDECIDE.GITHUB.IO/SITE"
    fm2 = font(F_MON, 16)
    tracked(d, W - 60 - tracked_w(d, s2, fm2, 3), y + 80, s2, fm2, DK_MUT, 3)
    return img


# =============================================================== pipeline
foto = Image.open(SRC).convert("RGBA")
foto = aplica_cartao(foto)
foto = apaga_regiao(foto, CREST_BOX, blur=18, escurece=0.5, feather=26)
foto = apaga_regiao(foto, WM_BOX, blur=10, escurece=0.9, feather=18)
base = corta_169(foto).convert("RGB")

# V1 — foto limpa, so o cartao fala
base.save(os.path.join(BASE, "capa-foto-1-limpa.png"))

# V2 — foto + tarja com a manchete
barra(base.copy()).save(os.path.join(BASE, "capa-foto-2-tarja.png"))

# V3 — preto e branco (casa com o site) + tarja  >>> ESCOLHIDA PELO ALLAN
pb = ImageEnhance.Contrast(base.convert("L")).enhance(1.18).convert("RGB")
v3 = barra(pb)
v3.save(os.path.join(BASE, "capa-foto-3-pb.png"))
v3.save(os.path.join(BASE, "capa-peticao-FINAL.png"))

print("OK - 3 capas + capa-peticao-FINAL.png geradas em", BASE)
