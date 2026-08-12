# -*- coding: utf-8 -*-
"""Converte as woff2 do site (site/fonts/) em .ttf pro Pillow desenhar os cards.

Usa exatamente as mesmas fontes do site, entao card e site nunca divergem.
Rodar:  py converte_fontes.py
"""
from fontTools.ttLib import TTFont
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.abspath(os.path.join(AQUI, "..", "..", "projeto corinthians", "site", "fonts"))
if not os.path.isdir(SRC):
    SRC = os.path.abspath(os.path.join(AQUI, "..", "..", "site", "fonts"))

ARQUIVOS = [
    "archivoblack-400", "archivo-400", "archivo-500", "archivo-600",
    "courierprime-400", "courierprime-700",
]

# Acentos e simbolos que os cards usam de verdade.
TESTE = "ÁÂÃÀÉÊÍÓÔÕÚÇáâãàéêíóôõúç~×·—“”"

for nome in ARQUIVOS:
    origem = os.path.join(SRC, nome + ".woff2")
    destino = os.path.join(AQUI, nome + ".ttf")
    f = TTFont(origem)
    f.flavor = None
    f.save(destino)
    cmap = f.getBestCmap()
    faltando = [c for c in TESTE if ord(c) not in cmap]
    kb = os.path.getsize(destino) / 1024
    print(f"{nome}.ttf  {kb:5.1f} KB  faltando: {''.join(faltando) or 'nada'}")
