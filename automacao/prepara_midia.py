#!/usr/bin/env python
"""Converte os cards para JPEG, que e o unico formato de imagem que a API do
Instagram aceita.

    py prepara_midia.py

Le `ARTES/v2-papel-e-tinta/card-*.png` e escreve `automacao/midia/card-*.jpg`.
Os JPEG ficam versionados de proposito: o Instagram nao recebe arquivo, ele
baixa a imagem de um endereco publico, e o endereco publico aqui e o proprio
repositorio no GitHub.

Nao mexe nos PNG originais, que continuam sendo a arte de referencia.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parent
ORIGEM = RAIZ.parent / "ARTES" / "v2-papel-e-tinta"
DESTINO = RAIZ / "midia"

QUALIDADE = 92  # alto o bastante para nao sujar tipografia em fundo de papel


def converte(origem: Path, destino: Path) -> tuple[int, int]:
    imagem = Image.open(origem)
    if imagem.mode != "RGB":
        imagem = imagem.convert("RGB")
    destino.parent.mkdir(parents=True, exist_ok=True)
    imagem.save(destino, "JPEG", quality=QUALIDADE, optimize=True, progressive=True)
    return imagem.size


def main() -> int:
    if not ORIGEM.exists():
        print(f"  ERRO: nao achei as artes em {ORIGEM}")
        return 1

    cards = sorted(ORIGEM.glob("card-*.png"))
    if not cards:
        print(f"  Nenhum card-*.png em {ORIGEM}")
        return 1

    print(f"\n  {len(cards)} card(s) de {ORIGEM}\n")
    for card in cards:
        saida = DESTINO / f"{card.stem}.jpg"
        largura, altura = converte(card, saida)
        antes = card.stat().st_size / 1024
        depois = saida.stat().st_size / 1024
        print(
            f"  {card.name:<28} -> {saida.name:<28} "
            f"{largura}x{altura}  {antes:.0f} KB -> {depois:.0f} KB"
        )

    print(
        "\n  Agora commite a pasta midia/ e envie ao GitHub. So depois de estar\n"
        "  publica no repositorio o Instagram consegue baixar a imagem.\n"
        "  Confira com: py publicar.py --checar --online\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
