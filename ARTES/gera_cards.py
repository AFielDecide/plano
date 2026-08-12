# -*- coding: utf-8 -*-
"""Gerador dos cards 1080x1080 do kit A Fiel Decide (cards 01-08).

Rodar com:  py gera_cards.py
Regera TODOS os cards na propria pasta ARTES (deterministico — mesmo resultado
sempre que as fontes do Windows nao mudarem). Pra criar card novo, copie um
bloco no fim e ajuste os textos.
"""
from PIL import Image, ImageDraw, ImageFont
import os

W = H = 1080
MARGIN = 92
BG = (11, 11, 12)
INK = (244, 242, 238)
GOLD = (200, 162, 78)
MUTE = (154, 150, 142)
LINE = (38, 38, 42)

FONTS = r"C:\Windows\Fonts"

def pick(*names):
    for n in names:
        p = os.path.join(FONTS, n)
        if os.path.exists(p):
            return p
    raise FileNotFoundError(names)

F_DISPLAY = pick("ARIALNB.TTF", "arialnb.ttf", "impact.ttf", "arialbd.ttf")
F_DISPLAY_IT = pick("ARIALNBI.TTF", "arialnbi.ttf", "ARIALNB.TTF", "impact.ttf", "arialbd.ttf")
F_MONO = pick("consolab.ttf", "consola.ttf", "cour.ttf")
F_MONO_R = pick("consola.ttf", "cour.ttf")

def font(path, size):
    return ImageFont.truetype(path, size)

def text_w(draw, s, f):
    b = draw.textbbox((0, 0), s, font=f)
    return b[2] - b[0]

def fit(draw, s, path, start, max_w):
    size = start
    while size > 30:
        f = font(path, size)
        if text_w(draw, s, f) <= max_w:
            return f
        size -= 4
    return font(path, size)

def tracked(draw, xy, s, f, fill, tracking):
    x, y = xy
    for ch in s:
        draw.text((x, y), ch, font=f, fill=fill)
        b = draw.textbbox((0, 0), ch, font=f)
        x += (b[2] - b[0]) + tracking
    return x

def diamond(draw, cx, cy, s, color, width=4):
    pts = [(cx, cy - s), (cx + s, cy), (cx, cy + s), (cx - s, cy)]
    draw.polygon(pts, outline=color, width=width)
    s2 = int(s * 0.55)
    pts2 = [(cx, cy - s2), (cx + s2, cy), (cx, cy + s2), (cx - s2, cy)]
    draw.polygon(pts2, outline=color, width=2)

def header(draw):
    dy = MARGIN + 18
    diamond(draw, MARGIN + 18, dy, 18, GOLD, 4)
    f = font(F_MONO, 25)
    tracked(draw, (MARGIN + 58, dy - 15), "A FIEL DECIDE", f, INK, 7)
    f2 = font(F_MONO_R, 21)
    tracked(draw, (MARGIN + 58, dy + 46 - 15), "DEMOCRACIA CORINTHIANA DIGITAL", f2, MUTE, 5)

def footer(draw):
    y_line = H - MARGIN - 118
    draw.line([(MARGIN, y_line), (W - MARGIN, y_line)], fill=LINE, width=2)
    f_seal = font(F_MONO, 27)
    tracked(draw, (MARGIN, y_line + 26), "NÃO PEDIMOS PIX. PEDIMOS SUA VOZ.", f_seal, INK, 4)
    f_tag = font(F_DISPLAY, 56)
    s = "#AFIELDECIDE"
    wtag = text_w(draw, s, f_tag)
    draw.text((W - MARGIN - wtag, y_line + 62), s, font=f_tag, fill=GOLD)

def block(draw, lines, y_start, leading=1.02):
    """lines: list of (text, font, color). left-aligned at MARGIN."""
    y = y_start
    for s, f, c in lines:
        draw.text((MARGIN, y), s, font=f, fill=c)
        b = draw.textbbox((MARGIN, y), s, font=f)
        y = y + int((b[3] - b[1]) * leading) + 14
    return y

def new_card():
    img = Image.new("RGB", (W, H), BG)
    return img, ImageDraw.Draw(img)

MAXW = W - 2 * MARGIN
OUT = os.path.dirname(os.path.abspath(__file__))

# ---------- CARD 1 ----------
img, d = new_card()
header(d)
l1 = fit(d, "~4 MIL DECIDEM", F_DISPLAY, 150, MAXW)
l2 = fit(d, "O CORINTHIANS.", F_DISPLAY, 150, MAXW)
l3 = font(F_DISPLAY, 84)
l4 = fit(d, "35 MILHÕES.", F_DISPLAY, 205, MAXW)
y = block(d, [
    ("~4 MIL DECIDEM", l1, INK),
    ("O CORINTHIANS.", l2, INK),
], 260)
y = block(d, [("A GENTE É", l3, MUTE)], y + 30)
block(d, [("35 MILHÕES.", l4, GOLD)], y + 6)
footer(d)
img.save(os.path.join(OUT, "card-01-4mil.png"))

# ---------- CARD 2 ----------
img, d = new_card()
header(d)
f_a = fit(d, "O SAFIEL TRAZ", F_DISPLAY, 132, MAXW)
f_b = fit(d, "O CAPITAL.", F_DISPLAY, 132, MAXW)
f_c = fit(d, "A FIEL TRAZ", F_DISPLAY, 132, MAXW)
f_d = fit(d, "O MANDATO.", F_DISPLAY, 188, MAXW)
y = block(d, [
    ("O SAFIEL TRAZ", f_a, MUTE),
    ("O CAPITAL.", f_b, INK),
], 265)
block(d, [
    ("A FIEL TRAZ", f_c, MUTE),
    ("O MANDATO.", f_d, GOLD),
], y + 44)
footer(d)
img.save(os.path.join(OUT, "card-02-tese.png"))

# ---------- CARD 3 ----------
img, d = new_card()
header(d)
f_a = fit(d, "AQUI NÃO TEM", F_DISPLAY, 148, MAXW)
f_b = fit(d, "LÍDER. NEM DONO.", F_DISPLAY, 148, MAXW)
f_c = fit(d, "NEM SALVADOR.", F_DISPLAY, 148, MAXW)
y = block(d, [
    ("AQUI NÃO TEM", f_a, INK),
    ("LÍDER. NEM DONO.", f_b, INK),
    ("NEM SALVADOR.", f_c, INK),
], 255)
f_sub = font(F_DISPLAY, 66)
block(d, [("QUEM ENTRA", f_sub, GOLD), ("VIRA CO-DONO DA MISSÃO.", f_sub, GOLD)], y + 40)
footer(d)
img.save(os.path.join(OUT, "card-03-semlider.png"))

# ---------- CARD 4 ----------
img, d = new_card()
header(d)
f_q = fit(d, "MAS SEMPRE COM", F_DISPLAY_IT, 124, MAXW)
f_dem = fit(d, "DEMOCRACIA.\"", F_DISPLAY_IT, 150, MAXW)
y = block(d, [
    ("\"GANHAR", f_q, INK),
    ("OU PERDER,", f_q, INK),
    ("MAS SEMPRE COM", f_q, INK),
    ("DEMOCRACIA.\"", f_dem, GOLD),
], 240)
f_src = font(F_MONO_R, 26)
tracked(d, (MARGIN, y + 46), "FAIXA DA FIEL · MORUMBI · DEZ/1983", f_src, MUTE, 4)
d.text((MARGIN, y + 112), "ESTÁ NA HORA DE VOLTAR A MANDAR.", font=fit(d, "ESTÁ NA HORA DE VOLTAR A MANDAR.", F_DISPLAY, 62, MAXW), fill=INK)
footer(d)
img.save(os.path.join(OUT, "card-04-faixa1983.png"))

# ---------- CARD 5 ----------
img, d = new_card()
header(d)
f_a = fit(d, "ENTROU E FEZ HISTÓRIA.", F_DISPLAY, 92, MAXW)
f_b = fit(d, "A FAIXA NA ARENA.", F_DISPLAY, 92, MAXW)
f_c = fit(d, "NÃO VÃO BARRAR", F_DISPLAY, 118, MAXW)
f_c2 = fit(d, "A URNA.", F_DISPLAY, 118, MAXW)
y = block(d, [
    ("EM 83, A FAIXA", f_a, INK),
    ("ENTROU E FEZ HISTÓRIA.", f_a, INK),
], 218)
y = block(d, [
    ("EM 26, BARRARAM", f_b, MUTE),
    ("A FAIXA NA ARENA.", f_b, MUTE),
], y + 20)
block(d, [
    ("NÃO VÃO BARRAR", f_c, GOLD),
    ("A URNA.", f_c2, GOLD),
], y + 26)
footer(d)
img.save(os.path.join(OUT, "card-05-faixabarrada.png"))

# ---------- CARD 6 ----------
img, d = new_card()
header(d)
f_a = fit(d, "CASAGRANDE VOTOU.", F_DISPLAY, 96, MAXW)
f_sub = font(F_MONO_R, 28)
f_g = fit(d, "MEMPHIS, VEM SER", F_DISPLAY, 110, MAXW)
f_g2 = fit(d, "SÓCRATES.", F_DISPLAY, 146, MAXW)
y = block(d, [
    ("SÓCRATES VOTOU.", f_a, INK),
    ("WLADIMIR VOTOU.", f_a, INK),
    ("CASAGRANDE VOTOU.", f_a, INK),
], 215)
x_end = tracked(d, (MARGIN, y + 20), "ELENCO DE 2026, A CAMISA CHAMA:", f_sub, MUTE, 3)
block(d, [
    ("MEMPHIS, VEM SER", f_g, GOLD),
    ("SÓCRATES.", f_g2, GOLD),
], y + 78)
footer(d)
img.save(os.path.join(OUT, "card-06-chamado.png"))

# ---------- CARD 7 — junta 3, já é núcleo (playbook) ----------
img, d = new_card()
header(d)
f_a = fit(d, "JUNTA 3,", F_DISPLAY, 170, MAXW)
f_b = fit(d, "JÁ É NÚCLEO.", F_DISPLAY, 170, MAXW)
f_sub = font(F_DISPLAY, 60)
f_c = fit(d, "O MANUAL É ABERTO. ABRE O SEU.", F_DISPLAY, 62, MAXW)
y = block(d, [
    ("JUNTA 3,", f_a, INK),
    ("JÁ É NÚCLEO.", f_b, GOLD),
], 245)
y = block(d, [
    ("NA QUEBRADA, NA ORGANIZADA,", f_sub, MUTE),
    ("NA FACUL, NO GRUPO DO ZAP.", f_sub, MUTE),
], y + 34)
block(d, [("O MANUAL É ABERTO. ABRE O SEU.", f_c, INK)], y + 26)
footer(d)
img.save(os.path.join(OUT, "card-07-nucleo.png"))

# ---------- CARD 8 — zelador rotativo, anti-cartola (playbook) ----------
img, d = new_card()
header(d)
f_a = fit(d, "NÚCLEO NÃO TEM", F_DISPLAY, 128, MAXW)
f_b = fit(d, "PRESIDENTE.", F_DISPLAY, 170, MAXW)
f_c = fit(d, "TEM ZELADOR.", F_DISPLAY, 122, MAXW)
f_d = fit(d, "E TROCA TODO MÊS.", F_DISPLAY, 122, MAXW)
f_e = fit(d, "NINGUÉM CRIA RAIZ NO CARGO.", F_DISPLAY, 58, MAXW)
y = block(d, [
    ("NÚCLEO NÃO TEM", f_a, INK),
    ("PRESIDENTE.", f_b, INK),
], 235)
y = block(d, [("TEM ZELADOR.", f_c, GOLD)], y + 34)
y = block(d, [("E TROCA TODO MÊS.", f_d, GOLD)], y + 14)
block(d, [("NINGUÉM CRIA RAIZ NO CARGO.", f_e, MUTE)], y + 26)
footer(d)
img.save(os.path.join(OUT, "card-08-zelador.png"))

print("OK — 8 cards gerados em", OUT)
