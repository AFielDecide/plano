# -*- coding: utf-8 -*-
"""Artes do A Fiel Decide na identidade v2 (papel e tinta) - a mesma do site.

Gera, nesta pasta:
  card-01..08.png   1080x1080  feed do Instagram, WhatsApp, X
  og-card.png       1080x1080  previa de link do site (copiar pro repo site/)
  avatar-*.png      1080x1080  foto de perfil (Instagram e X, cortada em circulo)
  avatar-*-preview-circular.png  como o avatar fica depois do corte
  banner-x-*.png    1500x500   capa do X

Rodar:  py gera_artes.py
Deterministico: mesmo resultado a cada rodada. As fontes vem de ..\\_fontes
(convertidas das woff2 do site), entao arte e site nunca divergem.

Tokens do handoff do redesign: papel #efece4, tinta #0d0c0b, sem cor de acento
(o acento e a inversao), mosaico de arquibancada no lugar do escudo, sombra dura
sem blur, grao de papel. Nunca usar escudo ou marca oficial do SCCP.
"""
from PIL import Image, ImageDraw, ImageFont
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
FONTES = os.path.join(os.path.dirname(AQUI), "_fontes")

# ---------------------------------------------------------------- tokens
PAPER = (239, 236, 228)
INK = (13, 12, 11)
INK_SOFT = (61, 55, 48)
GRAY = (107, 101, 94)
NUM_GHOST = (196, 191, 182)
ON_DARK = (239, 236, 228)
ON_DARK_MUTE = (156, 150, 141)
ON_DARK_BODY = (181, 175, 166)
RULE_DARK = (58, 53, 47)

SITE = "AFIELDECIDE.GITHUB.IO/SITE"
PERFIS = "@AFIELDECIDE · INSTAGRAM E X"

_cache = {}


def F(nome, size):
    k = (nome, size)
    if k not in _cache:
        _cache[k] = ImageFont.truetype(os.path.join(FONTES, nome + ".ttf"), size)
    return _cache[k]


def display(s):
    return F("archivoblack-400", s)


def body(s, peso=400):
    return F("archivo-%d" % peso, s)


def mono(s, negrito=True):
    return F("courierprime-%d" % (700 if negrito else 400), s)


# ---------------------------------------------------------------- utilidades
def grao(img, passo=8, alpha=26):
    """Grao de papel: pontinhos regulares, quase imperceptiveis de perto."""
    w, h = img.size
    camada = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(camada)
    for y in range(0, h, passo):
        for x in range(0, w, passo):
            d.rectangle([x, y, x + 1, y + 1], fill=(13, 12, 11, alpha))
    return Image.alpha_composite(img.convert("RGBA"), camada)


def mosaico(d, x, y, w, h, listra=34, fg=INK, bg=PAPER, borda=3):
    """Faixa listrada de arquibancada - substitui o escudo, por regra."""
    d.rectangle([x, y, x + w, y + h], fill=bg)
    i = 0
    while i < w:
        d.rectangle([x + i, y, min(x + i + listra, x + w), y + h], fill=fg)
        i += listra * 2
    if borda:
        d.rectangle([x, y, x + w, y + h], outline=fg, width=borda)


def largura(d, s, f, tracking=0.0):
    if not s:
        return 0
    return sum(d.textlength(c, font=f) for c in s) + tracking * (len(s) - 1)


def escreve(d, xy, s, f, fill, tracking=0.0):
    """Char a char, pra aplicar tracking (largo no mono, negativo no display)."""
    x, y = xy
    if tracking == 0:
        d.text((x, y), s, font=f, fill=fill)
        return x + d.textlength(s, font=f)
    for c in s:
        d.text((x, y), c, font=f, fill=fill)
        x += d.textlength(c, font=f) + tracking
    return x


def cap_top(f):
    """Distancia da origem do texto ao topo do 'H' (pra ancorar caixa alta)."""
    return f.getbbox("H")[1]


def cap_h(f):
    b = f.getbbox("H")
    return b[3] - b[1]


def partes(linha):
    """'A GENTE E [[35 MILHOES]].' -> [('A GENTE E ', 0), ('35 MILHOES', 1), ('.', 0)]"""
    out, resto = [], linha
    while "[[" in resto:
        antes, resto = resto.split("[[", 1)
        dentro, resto = resto.split("]]", 1)
        if antes:
            out.append((antes, True and False or False))
            out[-1] = (antes, False)
        out.append((dentro, True))
    if resto:
        out.append((resto, False))
    return out


def _pads(tam):
    """Folga do bloco invertido: horizontal e vertical."""
    return int(tam * 0.07), int(tam * 0.06)


def leading_auto(linhas):
    """Entrelinha: apertada por padrao, mais folgada quando ha bloco invertido
    (o retangulo precisa caber sem invadir a linha de cima) e mais ainda quando
    o trecho invertido tem acento alto, tipo MILHOES."""
    invertidos = [t for l in linhas for t, inv in partes(l) if inv]
    if not invertidos:
        return 0.88
    alto = any(c in "ÁÂÃÀÉÊÍÓÔÕÚÜ" for t in invertidos for c in t)
    return 1.04 if alto else 0.96


def largura_linha(d, linha, f, tracking, tam):
    pad_x, _ = _pads(tam)
    total = 0
    for i, (txt, inv) in enumerate(partes(linha)):
        total += largura(d, txt, f, tracking) + (tracking if i else 0)
        if inv:
            total += pad_x * 2
    return total


def manchete(d, x, y_topo, linhas, tam, fill, inv_bg, inv_fg, leading=None):
    """Caixa alta com [[trecho]] em bloco invertido. Devolve o y do fim do texto."""
    if leading is None:
        leading = leading_auto(linhas)
    f = display(tam)
    tracking = -0.028 * tam
    pad_x, pad_y = _pads(tam)
    ch = cap_h(f)
    # referencia fixa de altura do bloco: cabe til e cedilha em qualquer linha
    ref = f.getbbox("HÕÇ")
    passo = int(tam * leading)
    y = y_topo
    for linha in linhas:
        cx = x
        origem_y = y - cap_top(f)
        for i, (txt, inv) in enumerate(partes(linha)):
            w = largura(d, txt, f, tracking)
            if inv:
                d.rectangle([cx, origem_y + ref[1] - pad_y,
                             cx + w + pad_x * 2, origem_y + ref[3] + pad_y],
                            fill=inv_bg)
                escreve(d, (cx + pad_x, origem_y), txt, f, inv_fg, tracking)
                cx += w + pad_x * 2 + tracking
            else:
                escreve(d, (cx, origem_y), txt, f, fill, tracking)
                cx += w + tracking
        y += passo
    return y - passo + ch


def alt_manchete(linhas, tam, leading=None):
    if leading is None:
        leading = leading_auto(linhas)
    return int(tam * leading) * (len(linhas) - 1) + cap_h(display(tam))


def linhas_paragrafo(d, texto, f, max_w):
    palavras, linha, out = texto.split(" "), [], []
    for p in palavras:
        teste = linha + [p]
        if d.textlength(" ".join(teste).replace("**", ""), font=f) <= max_w:
            linha = teste
        else:
            out.append(" ".join(linha))
            linha = [p]
    if linha:
        out.append(" ".join(linha))
    return out


def paragrafo(d, x, y, texto, f, fill, max_w, leading=1.5, negrito_f=None):
    passo = int(f.size * leading)
    for l in linhas_paragrafo(d, texto, f, max_w):
        cx = x
        for i, pedaco in enumerate(l.split("**")):
            if not pedaco:
                continue
            usa = negrito_f if (i % 2 == 1 and negrito_f) else f
            d.text((cx, y), pedaco, font=usa, fill=fill)
            cx += d.textlength(pedaco, font=usa)
        y += passo
    return y


def selo(img, texto, centro_xy, escuro=True, angulo=-6, tam=25):
    """Carimbo rotacionado, tipo 'Copia livre - reproduza'. centro_xy = centro da peca."""
    f = mono(tam)
    tr = tam * 0.16
    d0 = ImageDraw.Draw(img)
    w = int(largura(d0, texto, f, tr)) + 52
    h = int(tam * 2.5)
    peca = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dp = ImageDraw.Draw(peca)
    bg, fg = (INK, ON_DARK) if escuro else (PAPER, INK)
    dp.rectangle([0, 0, w - 1, h - 1], fill=bg, outline=INK if not escuro else ON_DARK, width=3)
    escreve(dp, (26, (h - tam * 1.4) / 2), texto, f, fg, tr)
    peca = peca.rotate(angulo, resample=Image.BICUBIC, expand=True)
    img.alpha_composite(peca, (int(centro_xy[0] - peca.width / 2),
                               int(centro_xy[1] - peca.height / 2)))
    return peca.size


def mono_que_cabe(d, texto, max_w, tam_ini=23, tracking_em=0.14):
    tam = tam_ini
    while tam > 14 and largura(d, texto, mono(tam, False), tam * tracking_em) > max_w:
        tam -= 1
    return mono(tam, False), tam * tracking_em


# ---------------------------------------------------------------- card 1080
W = H = 1080
M = 78
CONT = W - 2 * M


def card(nome, kicker, linhas, lead=None, fonte=None, escuro=False, carimbo=None):
    bg = INK if escuro else PAPER
    fg = ON_DARK if escuro else INK
    mute = ON_DARK_MUTE if escuro else GRAY
    corpo_cor = ON_DARK_BODY if escuro else INK_SOFT
    inv_bg, inv_fg = (ON_DARK, INK) if escuro else (INK, PAPER)

    img = Image.new("RGBA", (W, H), bg)
    d = ImageDraw.Draw(img)

    # ---- topo: marca + kicker
    y = M
    mosaico(d, M, y + 2, 42, 22, listra=7, fg=fg, bg=bg, borda=2)
    escreve(d, (M + 60, y - 3), "A FIEL DECIDE", mono(26), fg, 26 * 0.16)
    y += 44
    f_kick, tr_kick = mono_que_cabe(d, kicker.upper(), CONT)
    escreve(d, (M, y), kicker.upper(), f_kick, mute, tr_kick)
    topo_livre = y + 78

    # ---- rodape: regua + perfis + endereco + hashtag
    y_rodape = H - M - 58
    d.line([(M, y_rodape - 34), (W - M, y_rodape - 34)],
           fill=RULE_DARK if escuro else NUM_GHOST, width=3)
    escreve(d, (M, y_rodape), PERFIS, mono(21), fg, 21 * 0.14)
    escreve(d, (M, y_rodape + 30), SITE, mono(21, negrito=False), mute, 21 * 0.14)
    f_tag = display(38)
    tag = "#AFIELDECIDE"
    escreve(d, (W - M - largura(d, tag, f_tag, -1.2), y_rodape + 2), tag, f_tag, fg, -1.2)
    base_livre = y_rodape - 78
    if carimbo:
        base_livre -= 96

    # ---- bloco central: manchete + mosaico + lead (+ fonte), centralizado no vao
    vao = base_livre - topo_livre
    f_lead, f_lead_b = body(34), body(34, 600)
    alt_lead = 0
    if lead:
        alt_lead = 34 + len(linhas_paragrafo(d, lead, f_lead, CONT)) * int(34 * 1.5)
    alt_fonte = 40 if fonte else 0
    alt_mosaico = 36 + 40

    tam = 196
    while tam > 44:
        f = display(tam)
        tr = -0.028 * tam
        cabe_largura = all(largura_linha(d, l, f, tr, tam) <= CONT for l in linhas)
        alt_total = alt_manchete(linhas, tam) + alt_mosaico + alt_lead + alt_fonte
        if cabe_largura and alt_total <= vao:
            break
        tam -= 2

    y0 = topo_livre + max(0, (vao - (alt_manchete(linhas, tam) + alt_mosaico +
                                     alt_lead + alt_fonte)) // 2)
    y_fim = manchete(d, M, y0, linhas, tam, fg, inv_bg, inv_fg)
    y_fim += 40
    mosaico(d, M, y_fim, CONT, 36, listra=34, fg=fg, bg=bg, borda=3)
    y_fim += 36
    if lead:
        y_fim = paragrafo(d, M, y_fim + 34, lead, f_lead, corpo_cor, CONT, negrito_f=f_lead_b)
    if fonte:
        escreve(d, (M, y_fim + 10), fonte.upper(), mono(20, negrito=False), mute, 20 * 0.12)

    if carimbo:
        selo(img, carimbo, (W - M - 190, H - M - 152), escuro=not escuro)

    img = grao(img, alpha=30 if not escuro else 16)
    p = os.path.join(AQUI, nome + ".png")
    img.convert("RGB").save(p, optimize=True)
    print("%-34s %5.0f KB" % (nome + ".png", os.path.getsize(p) / 1024))


# ---------------------------------------------------------------- avatar
def avatar(nome, palavra="FIEL", escuro=True, duas_linhas=False):
    """Foto de perfil. Precisa ler a 40px: poucas letras, o maior possivel.

    A largura util nao e a do quadrado inscrito, e a corda do circulo na altura
    do bloco - por isso o texto pode ser bem maior do que parece."""
    S = 1080
    R = S / 2 * 0.94                # raio util (folga pra borda do corte)
    bg = INK if escuro else PAPER
    fg = ON_DARK if escuro else INK
    img = Image.new("RGBA", (S, S), bg)
    d = ImageDraw.Draw(img)

    linhas = ["A FIEL", "DECIDE."] if duas_linhas else [palavra]
    respiro = 44 if not duas_linhas else 38
    alt_mosaico = 34

    tam = 520 if not duas_linhas else 300
    while tam > 60:
        f = display(tam)
        tr = -0.03 * tam
        alt_bloco = alt_manchete(linhas, tam, leading=0.86) + respiro + alt_mosaico
        # corda do circulo na borda do bloco: onde ele e mais estreito
        meia = alt_bloco / 2
        util = 2 * (R ** 2 - meia ** 2) ** 0.5 if meia < R else 0
        if util > 0 and all(largura(d, l, f, tr) <= util for l in linhas):
            break
        tam -= 4

    alt_txt = alt_manchete(linhas, tam, leading=0.86)
    largura_txt = max(largura(d, l, display(tam), -0.03 * tam) for l in linhas)
    x0 = int((S - largura_txt) / 2)
    y = (S - (alt_txt + respiro + alt_mosaico)) // 2
    y_fim = manchete(d, x0, y, linhas, tam, fg, fg, bg, leading=0.86)
    mosaico(d, x0, y_fim + respiro, int(largura_txt), alt_mosaico,
            listra=int(largura_txt / 21), fg=fg, bg=bg, borda=3)

    img = grao(img, alpha=26 if not escuro else 14)
    p = os.path.join(AQUI, nome + ".png")
    img.convert("RGB").save(p, optimize=True)

    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, S - 1, S - 1], fill=255)
    prev = Image.new("RGB", (S, S), (146, 146, 146))
    prev.paste(img.convert("RGB"), (0, 0), mask)
    prev.save(os.path.join(AQUI, nome + "-preview-circular.png"), optimize=True)
    print("%-34s %5.0f KB  (+ preview circular)" % (nome + ".png",
                                                    os.path.getsize(p) / 1024))


# ---------------------------------------------------------------- banner do X
def banner_x(nome, escuro=False):
    """1500x500. O avatar do X cobre o canto inferior esquerdo: nada critico ali."""
    BW, BH = 1500, 500
    bg = INK if escuro else PAPER
    fg = ON_DARK if escuro else INK
    mute = ON_DARK_MUTE if escuro else GRAY
    inv_bg, inv_fg = (ON_DARK, INK) if escuro else (INK, PAPER)

    img = Image.new("RGBA", (BW, BH), bg)
    d = ImageDraw.Draw(img)
    MB = 58
    base_mosaico = 30

    # esquerda: a marca, terminando acima da zona do avatar
    linhas = ["A FIEL", "DECIDE."]
    tam = 132
    y0 = 62
    manchete(d, MB, y0, linhas, tam, fg, inv_bg, inv_fg, leading=0.86)
    # abaixo da marca fica a zona coberta pelo avatar do X: nada escrito ali

    # direita: tese + mantra, centralizados na altura util
    xd = 700
    largura_dir = BW - xd - MB
    f_t = display(52)
    tr = -0.028 * 52
    pad_x, pad_y = _pads(52)
    ct = cap_h(f_t)
    ref = f_t.getbbox("HÕÇ")
    passo = int(52 * 0.98)

    bloco = ["O SAFIEL TRAZ", "O CAPITAL.", "A FIEL TRAZ", "O [[MANDATO]]."]
    alt_bloco = passo * (len(bloco) - 1) + ct + 42 + 30 + 34
    ytop = (BH - base_mosaico - alt_bloco) // 2 + 10
    y_fim = manchete(d, xd, ytop, bloco, 52, fg, inv_bg, inv_fg, leading=0.98)

    escreve(d, (xd, y_fim + 42), "1 PESSOA = 1 VOTO · A URNA É DE VIDRO",
            mono(22), mute, 22 * 0.16)
    escreve(d, (xd, y_fim + 42 + 34), "NÃO PEDIMOS SEU PIX. PEDIMOS SUA VOZ.",
            mono(22), fg, 22 * 0.16)
    f_end = mono(21)
    escreve(d, (BW - MB - largura(d, SITE, f_end, 21 * 0.14), BH - base_mosaico - 44),
            SITE, f_end, mute, 21 * 0.14)

    mosaico(d, 0, BH - base_mosaico, BW, base_mosaico, listra=34, fg=fg, bg=bg, borda=0)
    d.line([(0, BH - base_mosaico - 3), (BW, BH - base_mosaico - 3)], fill=fg, width=3)

    img = grao(img, alpha=30 if not escuro else 16)
    p = os.path.join(AQUI, nome + ".png")
    img.convert("RGB").save(p, optimize=True)
    print("%-34s %5.0f KB" % (nome + ".png", os.path.getsize(p) / 1024))


# ---------------------------------------------------------------- as pecas
if __name__ == "__main__":
    card("card-01-4mil",
         "O Placar Aberto · números que o clube já divulga",
         ["~4 MIL DECIDEM", "O CORINTHIANS.", "A GENTE É", "[[35 MILHÕES]]."],
         lead="Um time fundado por operários, governado de portão fechado — "
              "e a nossa própria casa penhorada por dívida. **A crise não é só "
              "de dinheiro: é de poder.**",
         fonte="Fontes: MeuTimão (sócios aptos, 2023) · Exame / Poder360")

    card("card-02-tese",
         "A tese · por que a gente completa o SAFiel",
         ["O SAFIEL TRAZ", "O CAPITAL.", "A FIEL TRAZ", "O [[MANDATO]]."],
         lead="A legitimidade popular não ameaça a reforma: **ela destrava a "
              "reforma.** Capital sem mandato empaca no Parque São Jorge.")

    card("card-03-semlider",
         "A cláusula · o que separa este movimento dos que falharam",
         ["AQUI NÃO", "TEM LÍDER.", "NEM DONO.", "NEM SALVADOR."],
         lead="Quem recebe este manifesto e fica **vira co-dono da missão**, com "
              "o mesmo peso de todos. Todo salvador vira, mais cedo ou mais tarde, "
              "um novo cartola.",
         escuro=True)

    card("card-04-faixa1983",
         "Faixa da Fiel · Morumbi · dez/1983",
         ["“GANHAR OU", "PERDER, MAS", "SEMPRE COM", "DEMOCRACIA.”"],
         lead="A Democracia Corinthiana foi feita por **jogadores que decidiam "
              "tudo no voto**, em plena ditadura, com o próprio emprego em jogo.",
         escuro=True)

    card("card-05-faixabarrada",
         "2026 · censura na nossa própria casa",
         ["BARRARAM", "A FAIXA.", "NÃO VÃO", "BARRAR [[A URNA]]."],
         lead="Em 83 a faixa entrou em campo. Em 2026, barraram a faixa de protesto "
              "da Fiel na porta da Arena. **O voto ninguém barra.**")

    card("card-06-chamado",
         "Aos herdeiros da camisa",
         ["MEMPHIS,", "VEM SER", "SÓCRATES."],
         lead="Sócrates jogou com “eu quero votar pra presidente” nas costas. Hoje "
              "não custa nem isso: **empresta a voz.** Uma frase, um story — a Fiel "
              "faz o resto.",
         escuro=True)

    card("card-07-nucleo",
         "A rede · como participar de verdade",
         ["3 PESSOAS", "JÁ É [[NÚCLEO]]."],
         lead="1 é opinião. 2 é resenha. **3 é núcleo.** Abra o seu na quebrada, na "
              "organizada ou no grupo do zap — o manual é aberto e ninguém precisa "
              "pedir licença.",
         carimbo="Manual aberto")

    card("card-08-zelador",
         "Os papéis do núcleo · rodízio mensal",
         ["O ZELADOR", "CUIDA.", "[[NÃO MANDA]]."],
         lead="Três papéis que giram todo mês e **nenhum presidente**. Mantenedor é "
              "zelador temporário, não dono: as chaves são de no mínimo três pessoas.",
         carimbo="Cópia livre")

    card("og-card",
         "Democracia Corinthiana Digital · movimento independente da Fiel",
         ["~4 MIL DECIDEM", "O CORINTHIANS.", "A GENTE É", "[[35 MILHÕES]]."],
         lead="Voto aberto, contas na mesa, urna de vidro auditável. **Não pedimos "
              "seu Pix. Pedimos sua voz.**")

    avatar("avatar-01-fiel-tinta", palavra="FIEL", escuro=True)
    avatar("avatar-02-fiel-papel", palavra="FIEL", escuro=False)
    avatar("avatar-03-completo-tinta", escuro=True, duas_linhas=True)
    avatar("avatar-04-completo-papel", escuro=False, duas_linhas=True)
    banner_x("banner-x-01-papel", escuro=False)
    banner_x("banner-x-02-tinta", escuro=True)
