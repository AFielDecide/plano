# -*- coding: utf-8 -*-
"""Capas 1600x900 para o abaixo-assinado do Change.org (A Fiel Decide).

Identidade v2 do site (papel envelhecido + tinta, sem cor de acento, mosaico
de arquibancada no lugar do escudo). Tokens copiados de site/styles.css.

Rodar com:  py gera_capa_peticao.py
Gera 3 variacoes (A, B, C) na propria pasta ARTES. Cada bloco de conteudo e
renderizado duas vezes: a 1a passada mede a altura, a 2a desenha centralizado
na area util (evita texto grudado no rodape ou sobra de ar embaixo).
"""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1600, 900
M = 96                      # margem lateral

PAPER  = (239, 236, 228)    # --paper
INK    = (13, 12, 11)       # --ink
GRAY   = (107, 101, 94)     # --gray
SHADOW = (151, 146, 138)    # --shadow-on-paper
DK_MUT = (156, 150, 141)    # --on-dark-mute
DK_SHD = (85, 80, 74)       # --shadow-on-dark

BASE  = os.path.dirname(os.path.abspath(__file__))
FDIR  = os.path.join(BASE, "_fontes")
F_DIS = os.path.join(FDIR, "archivoblack-400.ttf")
F_B6  = os.path.join(FDIR, "archivo-600.ttf")
F_MON = os.path.join(FDIR, "courierprime-700.ttf")

MAXW = W - 2 * M
OUT = BASE


def font(path, size):
    return ImageFont.truetype(path, size)


def tw(d, s, f):
    b = d.textbbox((0, 0), s, font=f)
    return b[2] - b[0]


def fit(d, s, path, start, max_w, floor=24):
    size = start
    while size > floor:
        f = font(path, size)
        if tw(d, s, f) <= max_w:
            return f
        size -= 2
    return font(path, floor)


def tight(d, x, y, s, f, fill):
    """desenha com o topo REAL do glifo em y; devolve o y da base real"""
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
    total = 0
    for ch in s:
        b = d.textbbox((0, 0), ch, font=f)
        total += (b[2] - b[0]) + tr if ch != " " else tw(d, " ", f) + tr
    return total - tr


def mosaic(d, x, y, w, h, block=30, border=3, bg=PAPER, fg=INK):
    d.rectangle([x, y, x + w - 1, y + h - 1], fill=bg, outline=fg, width=border)
    xi, on = x + border, True
    while xi < x + w - border:
        if on:
            d.rectangle([xi, y + border, min(xi + block, x + w - border) - 1,
                         y + h - border - 1], fill=fg)
        xi += block
        on = not on


def seal(text, angle=-5, bg=PAPER, fg=INK, size=28, pad=(24, 15), tr=5):
    """carimbo retangular rotacionado (RGBA, pronto pra colar)"""
    f = font(F_MON, size)
    dt = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    w = tracked_w(dt, text, f, tr) + pad[0] * 2
    b = dt.textbbox((0, 0), text, font=f)
    h = (b[3] - b[1]) + pad[1] * 2
    lay = Image.new("RGBA", (int(w) + 20, int(h) + 20), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    dl.rectangle([8, 8, w + 8, h + 8], fill=bg + (255,), outline=fg + (255,), width=3)
    tracked(dl, 8 + pad[0], 8 + pad[1], text, f, fg, tr)
    return lay.rotate(angle, expand=True, resample=Image.BICUBIC)


def grain(img, dot=INK, alpha=0.09, step=5):
    ov = img.copy()
    d = ImageDraw.Draw(ov)
    for y in range(0, H, step):
        for x in range(0, W, step):
            d.point((x, y), fill=dot)
    return Image.blend(img, ov, alpha)


def centered(render, top, bottom):
    """roda o bloco em branco pra medir, devolve o y0 que centraliza na area"""
    probe = Image.new("RGB", (W, H), PAPER)
    hgt = render(ImageDraw.Draw(probe), 0, None) - 0
    return top + max(0, (bottom - top - hgt)) // 2


# =========================================================================
# A — MANCHETE: "A FIEL QUER VOTAR."  (papel, jornal/zine)
# =========================================================================
def bloco_A(d, y0, img):
    y = tracked(d, M, y0, "MOVIMENTO DA TORCIDA  ·  SEM CAIXA  ·  SEM DONO",
                font(F_MON, 23), GRAY, 5)
    f1 = fit(d, "A FIEL QUER", F_DIS, 196, MAXW)
    f2 = fit(d, "VOTAR.", F_DIS, 272, MAXW)
    y = tight(d, M, y + 44, "A FIEL QUER", f1, INK)
    y = tight(d, M, y + 16, "VOTAR.", f2, INK)
    fb = font(F_B6, 36)
    ys = y + 48
    y1 = tight(d, M, ys, "Voz e voto do torcedor no Corinthians.", fb, INK)
    y2 = tight(d, M, y1 + 14, "Assinar é um voto, não um cheque.", fb, GRAY)
    if img is not None:
        sl = seal("NÃO É PIX. É VOTO.", angle=-5)
        img.paste(sl, (W - M - sl.size[0] + 8, ys - 26), sl)
    return y2


img = Image.new("RGB", (W, H), PAPER)
d = ImageDraw.Draw(img)
mosaic(d, 0, 0, W, 30, block=32)
mosaic(d, 0, H - 128, W, 22, block=26)
fh = font(F_DIS, 46)
tight(d, M, H - 84, "#AFIELDECIDE", fh, INK)
fm = font(F_MON, 22)
s = "AFIELDECIDE.GITHUB.IO/SITE"
tracked(d, W - M - tracked_w(d, s, fm, 4), H - 70, s, fm, GRAY, 4)
bloco_A(d, centered(lambda dd, yy, ii: bloco_A(dd, yy, ii), 46, H - 140), img)
img = grain(img)
img.save(os.path.join(OUT, "capa-peticao-A-manchete.png"))

# =========================================================================
# B — NÚMEROS: "~4 MIL DECIDEM / A GENTE É 35 MILHÕES"  (tinta, invertida)
# =========================================================================
def bloco_B(d, y0, img):
    y = tracked(d, M, y0, "PETIÇÃO PÚBLICA  ·  CONSELHO DELIBERATIVO  ·  CORI  ·  PRESIDÊNCIA",
                font(F_MON, 21), DK_MUT, 4)
    f1 = fit(d, "~4 MIL DECIDEM", F_DIS, 132, MAXW)
    y = tight(d, M, y + 48, "~4 MIL DECIDEM", f1, PAPER)
    y = tight(d, M, y + 14, "O CORINTHIANS.", f1, PAPER)
    y = tight(d, M, y + 40, "A GENTE É", font(F_DIS, 58), DK_MUT)
    f3 = fit(d, "35 MILHÕES.", F_DIS, 178, MAXW)
    y = tight(d, M, y + 18, "35 MILHÕES.", f3, PAPER)
    fs = font(F_DIS, 50)
    bw = tw(d, "A FIEL QUER VOTAR", fs) + 64
    bh, by = 92, y + 52
    d.rectangle([M + 9, by + 9, M + bw + 9, by + bh + 9], fill=DK_SHD)
    d.rectangle([M, by, M + bw, by + bh], fill=PAPER)
    tight(d, M + 32, by + 25, "A FIEL QUER VOTAR", fs, INK)
    return by + bh


img = Image.new("RGB", (W, H), INK)
d = ImageDraw.Draw(img)
mosaic(d, 0, 0, W, 30, block=32, bg=INK, fg=PAPER)
fm = font(F_MON, 22)
tracked(d, M, H - 62, "#AFIELDECIDE  ·  AFIELDECIDE.GITHUB.IO/SITE", fm, DK_MUT, 4)
bloco_B(d, centered(lambda dd, yy, ii: bloco_B(dd, yy, ii), 46, H - 108), img)
img = grain(img, dot=PAPER, alpha=0.07)
img.save(os.path.join(OUT, "capa-peticao-B-numeros.png"))

# =========================================================================
# C — FAIXA 83: "NÃO VÃO BARRAR A URNA."  (papel, histórico)
# =========================================================================
def bloco_C(d, y0, img):
    y = tracked(d, M, y0, "1983 — DEMOCRACIA CORINTHIANA  ·  2026 — A FIEL DECIDE",
                font(F_MON, 23), GRAY, 5)
    fa = font(F_DIS, 56)
    y = tight(d, M, y + 44, "EM 83, A FAIXA ENTROU E FEZ HISTÓRIA.", fa, GRAY)
    y = tight(d, M, y + 16, "EM 26, BARRARAM A FAIXA NA ARENA.", fa, GRAY)
    f1 = fit(d, "NÃO VÃO BARRAR", F_DIS, 182, MAXW)
    y = tight(d, M, y + 52, "NÃO VÃO BARRAR", f1, INK)
    y = tight(d, M, y + 16, "A URNA.", f1, INK)
    fb = font(F_B6, 36)
    ys = y + 50
    y = tight(d, M, ys, "Voz e voto do torcedor no Corinthians.", fb, INK)
    if img is not None:
        sl = seal("NÃO É PIX. É VOTO.", angle=-5)
        img.paste(sl, (W - M - sl.size[0] + 8, ys - 30), sl)
    return y


img = Image.new("RGB", (W, H), PAPER)
d = ImageDraw.Draw(img)
mosaic(d, 0, 0, W, 30, block=32)
mosaic(d, 0, H - 128, W, 22, block=26)
fh = font(F_DIS, 46)
tight(d, M, H - 84, "A FIEL QUER VOTAR", fh, INK)
fm = font(F_MON, 22)
s = "#AFIELDECIDE"
tracked(d, W - M - tracked_w(d, s, fm, 4), H - 70, s, fm, GRAY, 4)
bloco_C(d, centered(lambda dd, yy, ii: bloco_C(dd, yy, ii), 46, H - 140), img)
img = grain(img)
img.save(os.path.join(OUT, "capa-peticao-C-faixa83.png"))

print("OK - 3 capas 1600x900 geradas em", OUT)
