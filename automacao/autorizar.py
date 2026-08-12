#!/usr/bin/env python
"""Gera os tokens de publicacao do X e do Instagram. Roda uma vez por rede.

    py autorizar.py x
    py autorizar.py instagram

Este e o unico passo que exige uma pessoa: abre o navegador, voce entra na
conta @afieldecide e autoriza o aplicativo. Ninguem alem de voce digita senha
em lugar nenhum — nem aqui, nem em chat, nem em arquivo.

O que o script faz depois de voce autorizar: troca o codigo pelo token e grava
no `.env`, que esta no `.gitignore` e nunca vai para o GitHub.

Se o navegador nao voltar para o endereco local (algumas contas so aceitam
endereco https), use o modo manual:

    py autorizar.py x --manual

Nele voce autoriza, copia da barra do navegador o endereco inteiro para onde
foi redirecionado e cola aqui. O codigo vem dentro dele.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import http.server
import secrets
import sys
import threading
import time
import urllib.parse
import webbrowser

import redes

REDIRECIONAMENTO_PADRAO = "http://127.0.0.1:8721/callback"


# ---------------------------------------------------------------------------
# captura do codigo
# ---------------------------------------------------------------------------


class _Ouvinte(http.server.BaseHTTPRequestHandler):
    """Servidor minimo que existe so para receber o redirecionamento."""

    resultado: dict = {}

    def do_GET(self):  # noqa: N802 (nome exigido pela biblioteca)
        consulta = urllib.parse.urlparse(self.path).query
        _Ouvinte.resultado = dict(urllib.parse.parse_qsl(consulta))
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        deu_certo = "code" in _Ouvinte.resultado
        recado = (
            "Autorizado. Pode fechar esta aba e voltar ao terminal."
            if deu_certo
            else "Nao veio codigo nenhum. Volte ao terminal."
        )
        self.wfile.write(
            f"<html><body style='font-family:system-ui;padding:3rem'>"
            f"<h2>A Fiel Decide</h2><p>{recado}</p></body></html>".encode("utf-8")
        )

    def log_message(self, *_):
        pass  # sem ruido no terminal


def espera_codigo(redirecionamento: str, tempo_limite: int = 300) -> dict:
    partes = urllib.parse.urlparse(redirecionamento)
    servidor = http.server.HTTPServer((partes.hostname, partes.port), _Ouvinte)
    servidor.timeout = 1
    _Ouvinte.resultado = {}

    parar = threading.Event()

    def roda():
        while not parar.is_set():
            servidor.handle_request()

    linha = threading.Thread(target=roda, daemon=True)
    linha.start()

    limite = time.time() + tempo_limite
    while not _Ouvinte.resultado and time.time() < limite:
        time.sleep(0.3)
    parar.set()
    servidor.server_close()
    return _Ouvinte.resultado


def codigo_colado() -> str:
    print("\n  Cole aqui o endereco inteiro para onde o navegador foi levado")
    print("  (comeca com o seu endereco de retorno e tem `?code=` no meio):\n")
    colado = input("  > ").strip().rstrip("#_").strip()
    if not colado:
        raise SystemExit("  Nada colado. Cancelado.")
    consulta = urllib.parse.urlparse(colado).query
    valores = dict(urllib.parse.parse_qsl(consulta))
    codigo = valores.get("code")
    if not codigo:
        raise SystemExit("  Nao achei `code=` nesse endereco.")
    return codigo


def abre_navegador(url: str) -> None:
    print("\n  Abrindo o navegador. Se nao abrir, copie o endereco abaixo:\n")
    print(f"  {url}\n")
    try:
        webbrowser.open(url)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# X
# ---------------------------------------------------------------------------


def autoriza_x(env: dict, manual: bool) -> None:
    cliente = redes.exige(env, "X_CLIENT_ID")
    segredo = env.get("X_CLIENT_SECRET", "").strip()
    redirecionamento = env.get("X_REDIRECT_URI", "").strip() or REDIRECIONAMENTO_PADRAO

    # PKCE: o verificador fica so na memoria deste processo. O desafio, que e
    # o resumo dele, e o que viaja pela internet. Assim um codigo interceptado
    # no meio do caminho nao vale nada sem este processo aqui.
    verificador = base64.urlsafe_b64encode(secrets.token_bytes(48)).decode().rstrip("=")
    desafio = (
        base64.urlsafe_b64encode(hashlib.sha256(verificador.encode()).digest())
        .decode()
        .rstrip("=")
    )
    estado = secrets.token_urlsafe(16)

    url = redes.X_AUTORIZA_URL + "?" + urllib.parse.urlencode(
        {
            "response_type": "code",
            "client_id": cliente,
            "redirect_uri": redirecionamento,
            "scope": redes.X_ESCOPOS,
            "state": estado,
            "code_challenge": desafio,
            "code_challenge_method": "S256",
        }
    )

    print("\n  X — autorizacao")
    print(f"  Endereco de retorno: {redirecionamento}")
    print(f"  Permissoes pedidas:  {redes.X_ESCOPOS}")
    abre_navegador(url)

    if manual:
        codigo = codigo_colado()
    else:
        print("  Esperando voce autorizar (ate 5 minutos)...")
        resposta = espera_codigo(redirecionamento)
        if resposta.get("state") != estado:
            raise SystemExit("  O `state` voltou diferente. Autorizacao descartada.")
        codigo = resposta.get("code")
        if not codigo:
            raise SystemExit(f"  Nao veio codigo. Resposta: {resposta}")

    corpo = {
        "grant_type": "authorization_code",
        "code": codigo,
        "redirect_uri": redirecionamento,
        "code_verifier": verificador,
    }
    extra_auth: dict = {}
    if segredo:
        extra_auth["auth"] = (cliente, segredo)
    else:
        corpo["client_id"] = cliente

    import requests

    dados = redes._confere(
        requests.post(
            redes.X_TOKEN_URL,
            data=corpo,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=redes.TEMPO_LIMITE,
            **extra_auth,
        ),
        "X trocar codigo por token",
    )

    if not dados.get("refresh_token"):
        raise SystemExit(
            "  Vieram tokens, mas sem refresh token. Confirme que o escopo\n"
            "  `offline.access` esta marcado no app do X — sem ele voce teria\n"
            "  que autorizar de novo a cada duas horas."
        )

    redes.grava_env("X_ACCESS_TOKEN", dados["access_token"])
    redes.grava_env(
        "X_ACCESS_TOKEN_EXPIRA_EM", str(int(time.time() + int(dados.get("expires_in", 7200))))
    )
    redes.grava_env("X_REFRESH_TOKEN", dados["refresh_token"])

    print("\n  Pronto. Tokens do X gravados no .env.")
    print("  O token de acesso dura pouco e o script renova sozinho;")
    print("  o refresh token e o que voce nao pode perder.\n")


# ---------------------------------------------------------------------------
# Instagram
# ---------------------------------------------------------------------------


def autoriza_instagram(env: dict, manual: bool) -> None:
    import requests

    aplicativo = redes.exige(env, "IG_APP_ID")
    segredo = redes.exige(env, "IG_APP_SECRET")
    redirecionamento = env.get("IG_REDIRECT_URI", "").strip() or REDIRECIONAMENTO_PADRAO

    url = redes.IG_AUTORIZA_URL + "?" + urllib.parse.urlencode(
        {
            "client_id": aplicativo,
            "redirect_uri": redirecionamento,
            "response_type": "code",
            "scope": redes.IG_ESCOPOS,
        }
    )

    print("\n  Instagram — autorizacao")
    print(f"  Endereco de retorno: {redirecionamento}")
    print(f"  Permissoes pedidas:  {redes.IG_ESCOPOS}")
    abre_navegador(url)

    if manual:
        codigo = codigo_colado()
    else:
        print("  Esperando voce autorizar (ate 5 minutos)...")
        resposta = espera_codigo(redirecionamento)
        codigo = resposta.get("code")
        if not codigo:
            raise SystemExit(f"  Nao veio codigo. Resposta: {resposta}")

    # O Instagram devolve o codigo com um `#_` grudado no fim quando ele passa
    # pela barra do navegador. Nao faz parte do codigo.
    codigo = codigo.rstrip("#_")

    curto = redes._confere(
        requests.post(
            f"{redes.IG_OAUTH_HOST}/oauth/access_token",
            data={
                "client_id": aplicativo,
                "client_secret": segredo,
                "grant_type": "authorization_code",
                "redirect_uri": redirecionamento,
                "code": codigo,
            },
            timeout=redes.TEMPO_LIMITE,
        ),
        "Instagram trocar codigo por token curto",
    )

    token_curto = curto.get("access_token")
    usuario = curto.get("user_id")
    if not token_curto:
        raise SystemExit(f"  Instagram nao devolveu token: {curto}")

    # Token curto vale uma hora. Trocamos ja pelo longo, de 60 dias.
    longo = redes._confere(
        requests.get(
            f"{redes.IG_HOST}/access_token",
            params={
                "grant_type": "ig_exchange_token",
                "client_secret": segredo,
                "access_token": token_curto,
            },
            timeout=redes.TEMPO_LIMITE,
        ),
        "Instagram trocar por token longo",
    )
    token_longo = longo.get("access_token")
    if not token_longo:
        raise SystemExit(f"  Instagram nao devolveu token longo: {longo}")
    validade = int(longo.get("expires_in", 60 * 24 * 3600))

    redes.grava_env("IG_ACCESS_TOKEN", token_longo)
    redes.grava_env("IG_ACCESS_TOKEN_EXPIRA_EM", str(int(time.time() + validade)))
    if usuario:
        redes.grava_env("IG_USER_ID", str(usuario))

    print(f"\n  Pronto. Token longo do Instagram gravado no .env.")
    print(f"  Vale {validade // 86400} dias e o script renova sozinho quando publica.")
    if not usuario:
        print("  Nao veio o id da conta; preencha IG_USER_ID no .env a mao.")
    print()


# ---------------------------------------------------------------------------


def main() -> int:
    redes.ajusta_saida()
    analisador = argparse.ArgumentParser(description="Gera os tokens de publicacao.")
    analisador.add_argument("rede", choices=["x", "instagram"])
    analisador.add_argument(
        "--manual",
        action="store_true",
        help="nao abre servidor local; voce cola o endereco de retorno",
    )
    argumentos = analisador.parse_args()

    env = redes.le_env()
    if argumentos.rede == "x":
        autoriza_x(env, argumentos.manual)
    else:
        autoriza_instagram(env, argumentos.manual)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except redes.ErroDeRede as erro:
        print(f"\n  ERRO: {erro}\n", file=sys.stderr)
        raise SystemExit(1)
