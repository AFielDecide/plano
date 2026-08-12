#!/usr/bin/env python
"""Publicador da fila do A Fiel Decide.

Nada aqui publica sozinho. Sao quatro modos, do mais seguro para o menos:

    py publicar.py                    lista a fila e o que ja foi publicado
    py publicar.py --checar           confere tudo que da para conferir sem publicar
    py publicar.py --ensaio <id>      mostra exatamente o que iria ao ar
    py publicar.py --publicar <id>    publica, depois de voce digitar o id de novo

Nao existe atalho para pular a confirmacao, e isso e de proposito: publicar e
irreversivel e em nome de um movimento que nao e de uma pessoa so. Se algum dia
fizer sentido publicar sem alguem olhando, essa e uma decisao nova, tomada em
aberto, e nao um parametro escondido.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import tomllib
from datetime import datetime, timezone
from pathlib import Path

import redes

RAIZ = Path(__file__).resolve().parent
FILA = RAIZ / "posts-aprovados.toml"
REGISTRO = RAIZ / "registro-publicacoes.json"
ARTES = RAIZ.parent / "ARTES" / "v2-papel-e-tinta"

# Limites de produto das duas redes para conta comum. Ficam aqui como padrao
# ajustavel: se a rede mudar a regra, mude no `.env` sem mexer no codigo.
LIMITE_X_PADRAO = 280
LIMITE_IG_PADRAO = 2200


# ---------------------------------------------------------------------------
# leitura da fila e do registro
# ---------------------------------------------------------------------------


def carrega_fila() -> dict:
    if not FILA.exists():
        sair(f"Nao achei a fila em {FILA}")
    with FILA.open("rb") as arquivo:
        return tomllib.load(arquivo)


def carrega_registro() -> list[dict]:
    if not REGISTRO.exists():
        return []
    return json.loads(REGISTRO.read_text(encoding="utf-8"))


def anota_registro(entrada: dict) -> None:
    """Grava o comprovante da publicacao. Este arquivo e a memoria do que ja
    foi ao ar: sem ele, nada impede publicar a mesma peca duas vezes."""
    registro = carrega_registro()
    registro.append(entrada)
    REGISTRO.write_text(
        json.dumps(registro, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def acha_post(fila: dict, identificador: str) -> dict:
    for post in fila.get("post", []):
        if post.get("id") == identificador:
            return post
    sair(f"Nao existe post com id `{identificador}` na fila.")


def ja_publicado(identificador: str) -> dict | None:
    for entrada in carrega_registro():
        if entrada.get("id") == identificador:
            return entrada
    return None


def sair(mensagem: str, codigo: int = 1):
    print(f"\n  ERRO: {mensagem}\n", file=sys.stderr)
    raise SystemExit(codigo)


def agora() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# apoio
# ---------------------------------------------------------------------------


def mensagens_do_post(post: dict) -> list[dict]:
    """Um post virou sempre uma lista: fio do X tem varias mensagens, o resto
    tem uma. Assim o resto do codigo trata os dois casos igual."""
    if post.get("tipo") == "fio":
        return [
            {"texto": m["texto"].strip(), "arte": m.get("arte")}
            for m in post.get("mensagem", [])
        ]
    return [{"texto": post.get("texto", "").strip(), "arte": post.get("arte")}]


def caminho_arte(nome: str) -> Path:
    return ARTES / nome


def url_da_arte(nome: str, base: str) -> str:
    """O Instagram nao aceita upload de arquivo: ele baixa a imagem de um
    endereco publico, e so em JPEG. Por isso apontamos para o JPEG gerado
    pelo `prepara_midia.py`."""
    return f"{base.rstrip('/')}/{Path(nome).stem}.jpg"


def limite_da_rede(rede: str, env: dict) -> int:
    if rede == "x":
        return int(env.get("X_LIMITE_CARACTERES", LIMITE_X_PADRAO) or LIMITE_X_PADRAO)
    return int(env.get("IG_LIMITE_CARACTERES", LIMITE_IG_PADRAO) or LIMITE_IG_PADRAO)


def env_opcional() -> dict:
    """Le o `.env` se existir. Os modos de leitura funcionam sem ele."""
    try:
        return redes.le_env()
    except FileNotFoundError:
        return {}


# ---------------------------------------------------------------------------
# modo: listar
# ---------------------------------------------------------------------------


def modo_listar(fila: dict) -> int:
    registro = {e["id"]: e for e in carrega_registro()}
    print(f"\n  FILA: {fila['fila']['nome']}")
    if fila["fila"].get("observacao"):
        print(f"  {fila['fila']['observacao']}")
    print()
    print(f"  {'DATA':<12} {'REDE':<10} {'ID':<24} {'APROVADO':<9} SITUACAO")
    print(f"  {'-'*12} {'-'*10} {'-'*24} {'-'*9} {'-'*30}")
    for post in fila.get("post", []):
        publicado = registro.get(post["id"])
        if publicado:
            situacao = f"publicado em {publicado['quando'][:16]}"
        elif post.get("condicao"):
            situacao = "na fila (tem condicao — leia o TOML)"
        else:
            situacao = "na fila"
        print(
            f"  {post.get('data_sugerida', '-'):<12} "
            f"{post['rede']:<10} {post['id']:<24} "
            f"{('sim' if post.get('aprovado') else 'NAO'):<9} {situacao}"
        )
    print(
        "\n  Para aprovar um post, troque `aprovado = false` por `true` "
        "no posts-aprovados.toml.\n"
    )
    return 0


# ---------------------------------------------------------------------------
# modo: checar
# ---------------------------------------------------------------------------


def modo_checar(fila: dict, online: bool) -> int:
    env = env_opcional()
    problemas: list[str] = []
    avisos: list[str] = []

    print("\n  CONFERENCIA DA FILA\n")

    # 1. credenciais
    print("  Credenciais no .env")
    if not env:
        avisos.append("Nao existe `.env` ainda. Copie o `.env.exemplo` e preencha.")
        print("    .env ................. ausente")
    else:
        for chave in ("X_CLIENT_ID", "X_REFRESH_TOKEN"):
            print(f"    {chave:<22} {'ok' if env.get(chave) else 'faltando'}")
        for chave in ("IG_ACCESS_TOKEN", "IG_USER_ID"):
            print(f"    {chave:<22} {'ok' if env.get(chave) else 'faltando'}")
        validade = env.get("IG_ACCESS_TOKEN_EXPIRA_EM")
        if validade:
            dias = (float(validade) - time.time()) / 86400
            print(f"    token do Instagram ... vence em {dias:.0f} dia(s)")
            if dias < 0:
                problemas.append(
                    "O token do Instagram venceu. Rode `py autorizar.py instagram`."
                )
            elif dias < 10:
                avisos.append(
                    f"O token do Instagram vence em {dias:.0f} dia(s); "
                    "a proxima publicacao renova sozinha."
                )

    base_midia = env.get("MEDIA_BASE_URL", "").strip()
    if not base_midia:
        avisos.append(
            "MEDIA_BASE_URL vazio: sem ele o Instagram nao tem de onde baixar a arte."
        )

    # 2. cada post
    print("\n  Posts")
    for post in fila.get("post", []):
        limite = limite_da_rede(post["rede"], env)
        for i, mensagem in enumerate(mensagens_do_post(post), 1):
            rotulo = post["id"] if len(mensagens_do_post(post)) == 1 else f"{post['id']} [{i}]"
            tamanho = len(mensagem["texto"])
            marca = "ok "
            if tamanho > limite:
                marca = "!! "
                problemas.append(
                    f"{rotulo}: {tamanho} caracteres, acima do limite de {limite} do "
                    f"{post['rede'].upper()}."
                )
            elif tamanho > limite * 0.95:
                marca = " ~ "
                avisos.append(f"{rotulo}: {tamanho}/{limite} caracteres, no limite.")
            print(f"    {marca}{rotulo:<30} {tamanho:>5}/{limite} caracteres")

            if mensagem["arte"]:
                arquivo = caminho_arte(mensagem["arte"])
                if not arquivo.exists():
                    problemas.append(f"{rotulo}: arte nao encontrada em {arquivo}")
                    print(f"       arte ausente: {arquivo}")

    # 3. artes do Instagram precisam existir em JPEG num endereco publico
    if online and base_midia:
        print("\n  Enderecos publicos das artes (o Instagram baixa de la)")
        vistos: set[str] = set()
        for post in fila.get("post", []):
            if post["rede"] != "instagram":
                continue
            for mensagem in mensagens_do_post(post):
                if not mensagem["arte"] or mensagem["arte"] in vistos:
                    continue
                vistos.add(mensagem["arte"])
                url = url_da_arte(mensagem["arte"], base_midia)
                ok, detalhe = redes.confere_url_publica(url)
                print(f"    {'ok ' if ok else '!! '}{url}\n       {detalhe}")
                if not ok:
                    problemas.append(f"Arte inacessivel para o Instagram: {url}")
    elif base_midia:
        print("\n  (rode com --online para testar os enderecos das artes)")

    # 4. veredito
    print()
    for aviso in avisos:
        print(f"  aviso:    {aviso}")
    for problema in problemas:
        print(f"  problema: {problema}")
    if problemas:
        print(f"\n  {len(problemas)} problema(s). Nada disso impede voce de publicar")
        print("  na mao; impede o script de publicar por API.\n")
        return 1
    print("\n  Sem problemas encontrados.\n")
    return 0


# ---------------------------------------------------------------------------
# modo: tokens
# ---------------------------------------------------------------------------


def modo_tokens() -> int:
    """Cuida da validade dos tokens. E o modo que a tarefa agendada roda.

    O token longo do Instagram vale 60 dias e morre se ninguem renovar. Como
    a renovacao so pode acontecer com um token ainda vivo, deixar vencer
    significa refazer a autorizacao no navegador. Rodar isto de tempos em
    tempos evita esse tombo.

    Nao publica nada e nao gasta credito do X: so olha o que esta guardado e,
    se o do Instagram estiver perto do fim, pede um novo.
    """
    env = env_opcional()
    if not env:
        sair("Nao existe `.env`. Copie o `.env.exemplo` e preencha.")

    print("\n  SAUDE DOS TOKENS\n")
    saida = 0

    # X: o token de acesso dura pouco e e renovado na hora de publicar. O que
    # importa guardar de pe e o refresh token.
    if env.get("X_REFRESH_TOKEN"):
        print("  X ......... refresh token guardado")
        print("              (o token de acesso e renovado sozinho ao publicar)")
    else:
        print("  X ......... SEM refresh token — rode `py autorizar.py x`")
        saida = 1

    # Instagram: aqui a renovacao acontece de fato.
    if not env.get("IG_ACCESS_TOKEN"):
        print("  Instagram . SEM token — rode `py autorizar.py instagram`")
        return 1

    try:
        dias = (float(env.get("IG_ACCESS_TOKEN_EXPIRA_EM", "0") or 0) - time.time()) / 86400
    except ValueError:
        dias = 0.0

    if dias <= 0:
        print("  Instagram . token VENCIDO — rode `py autorizar.py instagram`")
        return 1

    print(f"  Instagram . token vence em {dias:.0f} dia(s)")
    antes = env.get("IG_ACCESS_TOKEN")
    redes.token_instagram(env)  # renova por dentro se estiver perto do fim
    depois = redes.le_env().get("IG_ACCESS_TOKEN")
    if depois != antes:
        novos_dias = (
            float(redes.le_env().get("IG_ACCESS_TOKEN_EXPIRA_EM", "0") or 0) - time.time()
        ) / 86400
        print(f"              renovado agora: vence em {novos_dias:.0f} dia(s)")
    else:
        print("              ainda longe do fim, nao precisou renovar")

    print()
    return saida


# ---------------------------------------------------------------------------
# modo: ensaio e publicacao
# ---------------------------------------------------------------------------


def mostra_post(post: dict, env: dict) -> None:
    base_midia = env.get("MEDIA_BASE_URL", "").strip()
    limite = limite_da_rede(post["rede"], env)
    print(f"\n  {'='*68}")
    print(f"  {post['id']}   —   {post['rede'].upper()}   —   {post.get('tipo', 'post')}")
    print(f"  {'='*68}")
    if post.get("condicao"):
        print(f"\n  CONDICAO DO PLANO: {post['condicao']}")
    if post.get("lembrete"):
        print(f"  LEMBRETE: {post['lembrete']}")

    for i, mensagem in enumerate(mensagens_do_post(post), 1):
        print(f"\n  --- mensagem {i} ({len(mensagem['texto'])}/{limite} caracteres) ---")
        for linha in mensagem["texto"].splitlines():
            print(f"  | {linha}")
        if mensagem["arte"]:
            if post["rede"] == "instagram":
                print(f"  | [arte] {url_da_arte(mensagem['arte'], base_midia or '???')}")
            else:
                print(f"  | [arte] {caminho_arte(mensagem['arte'])}")
    print()


def valida_para_publicar(post: dict, env: dict) -> None:
    if not post.get("aprovado"):
        sair(
            f"`{post['id']}` esta com `aprovado = false`. "
            "Aprove no posts-aprovados.toml antes de publicar."
        )
    limite = limite_da_rede(post["rede"], env)
    for i, mensagem in enumerate(mensagens_do_post(post), 1):
        if len(mensagem["texto"]) > limite:
            sair(
                f"`{post['id']}` mensagem {i} tem {len(mensagem['texto'])} caracteres, "
                f"acima do limite de {limite}. Encurte o texto na fila — o script nao "
                "corta texto do movimento por conta propria."
            )
        if mensagem["arte"] and post["rede"] == "x":
            if not caminho_arte(mensagem["arte"]).exists():
                sair(f"Arte nao encontrada: {caminho_arte(mensagem['arte'])}")


def confirma(post: dict) -> bool:
    print(f"  Isto vai ao ar AGORA no {post['rede'].upper()}, em nome de @afieldecide.")
    print("  Publicacao nao tem desfazer limpo: apagar depois deixa rastro.")
    print(f"\n  Para confirmar, digite o id do post ({post['id']}) e Enter.")
    print("  Qualquer outra coisa cancela.")
    try:
        resposta = input("\n  > ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n  Cancelado.")
        return False
    if resposta != post["id"]:
        print("\n  Cancelado: o que voce digitou nao bate com o id.")
        return False
    return True


def publica_no_x(post: dict, env: dict) -> dict:
    cliente = redes.token_x(env)
    resultados = []
    anterior = None
    for i, mensagem in enumerate(mensagens_do_post(post), 1):
        midia_ids = []
        if mensagem["arte"]:
            print(f"    subindo arte da mensagem {i}...")
            midia_ids.append(cliente.sobe_imagem(caminho_arte(mensagem["arte"])))
        post_id = cliente.publica(mensagem["texto"], midia_ids, responder_a=anterior)
        anterior = post_id
        url = f"https://x.com/afieldecide/status/{post_id}"
        resultados.append({"post_id": post_id, "url": url})
        print(f"    mensagem {i} publicada: {url}")
    return {"mensagens": resultados}


def publica_no_instagram(post: dict, env: dict) -> dict:
    base_midia = redes.exige(env, "MEDIA_BASE_URL")
    mensagem = mensagens_do_post(post)[0]
    if not mensagem["arte"]:
        sair(f"`{post['id']}` nao tem arte, e o Instagram exige imagem.")

    url = url_da_arte(mensagem["arte"], base_midia)
    ok, detalhe = redes.confere_url_publica(url)
    if not ok:
        sair(
            f"A arte precisa estar publica em JPEG antes de publicar.\n"
            f"  {url}\n  {detalhe}\n"
            "  Rode `py prepara_midia.py`, commite a pasta midia/ e envie ao GitHub."
        )

    cliente = redes.token_instagram(env)
    midia_id = cliente.publica(url, mensagem["texto"])
    print(f"    publicado: id da midia {midia_id}")
    return {"midia_id": midia_id, "url_arte": url}


def modo_publicar(fila: dict, identificador: str, ensaio: bool) -> int:
    env = env_opcional()
    post = acha_post(fila, identificador)

    mostra_post(post, env)

    anterior = ja_publicado(identificador)
    if anterior:
        print(f"  JA PUBLICADO em {anterior['quando']}.")
        print("  Publicar de novo criaria um post duplicado. Cancelado.\n")
        return 1

    if ensaio:
        print("  ENSAIO: nada foi publicado.")
        if not post.get("aprovado"):
            print("  (este post ainda esta com `aprovado = false`)")
        print()
        return 0

    valida_para_publicar(post, env)
    if not confirma(post):
        return 1

    print("\n  publicando...")
    if post["rede"] == "x":
        detalhe = publica_no_x(post, env)
    elif post["rede"] == "instagram":
        detalhe = publica_no_instagram(post, env)
    else:
        sair(f"Rede desconhecida: {post['rede']}")

    anota_registro(
        {
            "id": post["id"],
            "rede": post["rede"],
            "quando": agora(),
            "detalhe": detalhe,
        }
    )
    print(f"\n  Pronto. Comprovante anotado em {REGISTRO.name}.")
    if post.get("lembrete"):
        print(f"  Falta fazer na mao: {post['lembrete']}")
    print()
    return 0


# ---------------------------------------------------------------------------


def main() -> int:
    redes.ajusta_saida()
    analisador = argparse.ArgumentParser(
        description="Publicador da fila do A Fiel Decide.",
        epilog="Sem argumentos, apenas lista a fila.",
    )
    analisador.add_argument("--checar", action="store_true", help="confere a fila inteira")
    analisador.add_argument(
        "--online",
        action="store_true",
        help="com --checar, tambem testa os enderecos publicos das artes",
    )
    analisador.add_argument("--ensaio", metavar="ID", help="mostra o que iria ao ar")
    analisador.add_argument("--publicar", metavar="ID", help="publica de verdade")
    analisador.add_argument(
        "--tokens",
        action="store_true",
        help="confere a validade dos tokens e renova o do Instagram se preciso",
    )
    argumentos = analisador.parse_args()

    if argumentos.tokens:
        return modo_tokens()

    fila = carrega_fila()

    if argumentos.publicar:
        return modo_publicar(fila, argumentos.publicar, ensaio=False)
    if argumentos.ensaio:
        return modo_publicar(fila, argumentos.ensaio, ensaio=True)
    if argumentos.checar:
        return modo_checar(fila, online=argumentos.online)
    return modo_listar(fila)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except redes.ErroDeRede as erro:
        sair(str(erro))
