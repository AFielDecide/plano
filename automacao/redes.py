"""Camada de acesso ao X e ao Instagram.

Este modulo nao publica nada por conta propria: ele expoe funcoes que o
`publicar.py` chama depois da confirmacao humana.

Regras que valem aqui dentro:
  - Segredo nenhum mora no repositorio. Tudo vem do arquivo `.env`, que esta
    no `.gitignore`.
  - Token que gira (o refresh token do X) e regravado no `.env` de forma
    atomica, para nao existir janela em que o arquivo fique pela metade.
  - Erro de API sobe com o corpo da resposta junto. Sem isso, depurar
    publicacao e adivinhacao.
"""

from __future__ import annotations

import mimetypes
import os
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent
CAMINHO_ENV = RAIZ / ".env"

TEMPO_LIMITE = 60  # segundos por requisicao HTTP


class ErroDeRede(RuntimeError):
    """Falha vinda da API do X ou do Instagram, com o corpo da resposta."""


def ajusta_saida() -> None:
    """Faz o terminal aceitar acento e emoji.

    O console do Windows abre em cp1252, que nao tem emoji. Sem isto, mostrar
    o fio de lancamento na tela levanta UnicodeEncodeError e o ensaio morre
    antes de mostrar o texto. `errors="replace"` garante que, no pior caso,
    aparece um caractere trocado em vez de o programa quebrar.
    """
    for fluxo in (sys.stdout, sys.stderr):
        if hasattr(fluxo, "reconfigure"):
            try:
                fluxo.reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass


# ---------------------------------------------------------------------------
# .env
# ---------------------------------------------------------------------------


def le_env(caminho: Path = CAMINHO_ENV) -> dict[str, str]:
    """Le o `.env` num dicionario. Ignora comentarios e linhas vazias."""
    if not caminho.exists():
        raise FileNotFoundError(
            f"Nao achei {caminho}. Copie o `.env.exemplo` para `.env` e preencha."
        )
    valores: dict[str, str] = {}
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, _, valor = linha.partition("=")
        valores[chave.strip()] = valor.strip().strip('"').strip("'")
    return valores


def grava_env(chave: str, valor: str, caminho: Path = CAMINHO_ENV) -> None:
    """Regrava UMA chave do `.env`, preservando o resto do arquivo.

    Escreve num temporario e troca com `os.replace`, que e atomico no
    Windows e no Linux: ou o arquivo antigo esta la inteiro, ou o novo.
    Nunca um meio-termo com o token cortado.
    """
    linhas = caminho.read_text(encoding="utf-8").splitlines(keepends=True)
    nova = f"{chave}={valor}\n"
    achou = False
    for i, linha in enumerate(linhas):
        if linha.strip().startswith(f"{chave}="):
            linhas[i] = nova
            achou = True
            break
    if not achou:
        if linhas and not linhas[-1].endswith("\n"):
            linhas.append("\n")
        linhas.append(nova)

    fd, temporario = tempfile.mkstemp(dir=caminho.parent, prefix=".env.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as saida:
            saida.writelines(linhas)
        os.replace(temporario, caminho)
    except BaseException:
        Path(temporario).unlink(missing_ok=True)
        raise


def exige(env: dict[str, str], chave: str) -> str:
    valor = env.get(chave, "").strip()
    if not valor:
        raise ErroDeRede(
            f"Falta `{chave}` no arquivo `.env`. Veja o passo a passo no README."
        )
    return valor


def _confere(resposta: requests.Response, contexto: str) -> dict:
    if resposta.status_code >= 400:
        raise ErroDeRede(
            f"{contexto}: HTTP {resposta.status_code}\n{resposta.text[:2000]}"
        )
    if not resposta.content:
        return {}
    try:
        return resposta.json()
    except ValueError:
        raise ErroDeRede(f"{contexto}: resposta nao era JSON\n{resposta.text[:2000]}")


# ---------------------------------------------------------------------------
# X
# ---------------------------------------------------------------------------

X_TOKEN_URL = "https://api.x.com/2/oauth2/token"
X_AUTORIZA_URL = "https://x.com/i/oauth2/authorize"
X_MIDIA_URL = "https://api.x.com/2/media/upload"
X_POSTS_URL = "https://api.x.com/2/tweets"

# Escopos necessarios para publicar em nome da conta.
# `offline.access` e o que devolve refresh token; sem ele o acesso morre em
# duas horas e cada publicacao viraria um login manual.
X_ESCOPOS = "tweet.read tweet.write users.read media.write offline.access"

# Margem de seguranca: renova o token se faltar menos que isso para expirar.
MARGEM_TOKEN_X = 300  # segundos

# Pedaco do upload em partes. O limite documentado para imagem e 5 MB, entao
# um card de 1080x1080 cabe em poucos pedacos.
TAMANHO_PEDACO = 4 * 1024 * 1024


@dataclass
class ClienteX:
    token: str

    @property
    def cabecalho(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    def sobe_imagem(self, caminho: Path) -> str:
        """Sobe uma imagem em partes (INIT / APPEND / FINALIZE).

        Devolve o `media_id` para anexar ao post. O id vale por tempo
        limitado, entao suba a midia na hora de publicar, nao antes.
        """
        total = caminho.stat().st_size
        tipo = mimetypes.guess_type(caminho.name)[0] or "image/jpeg"

        inicio = _confere(
            requests.post(
                X_MIDIA_URL,
                headers=self.cabecalho,
                data={
                    "command": "INIT",
                    "media_type": tipo,
                    "total_bytes": str(total),
                    "media_category": "tweet_image",
                },
                timeout=TEMPO_LIMITE,
            ),
            f"X INIT de midia ({caminho.name})",
        )
        dados = inicio.get("data", inicio)
        midia_id = dados.get("id") or dados.get("media_id_string")
        if not midia_id:
            raise ErroDeRede(f"X INIT nao devolveu id de midia: {inicio}")

        with caminho.open("rb") as arquivo:
            indice = 0
            while True:
                pedaco = arquivo.read(TAMANHO_PEDACO)
                if not pedaco:
                    break
                _confere(
                    requests.post(
                        X_MIDIA_URL,
                        headers=self.cabecalho,
                        data={
                            "command": "APPEND",
                            "media_id": midia_id,
                            "segment_index": str(indice),
                        },
                        files={"media": (caminho.name, pedaco, tipo)},
                        timeout=TEMPO_LIMITE,
                    ),
                    f"X APPEND parte {indice} ({caminho.name})",
                )
                indice += 1

        fim = _confere(
            requests.post(
                X_MIDIA_URL,
                headers=self.cabecalho,
                data={"command": "FINALIZE", "media_id": midia_id},
                timeout=TEMPO_LIMITE,
            ),
            f"X FINALIZE de midia ({caminho.name})",
        )

        # Imagem normalmente ja sai pronta; video e GIF passam por
        # processamento. Se a API pedir espera, esperamos.
        processando = fim.get("data", fim).get("processing_info")
        while processando and processando.get("state") in {"pending", "in_progress"}:
            time.sleep(max(1, int(processando.get("check_after_secs", 1))))
            estado = _confere(
                requests.get(
                    X_MIDIA_URL,
                    headers=self.cabecalho,
                    params={"command": "STATUS", "media_id": midia_id},
                    timeout=TEMPO_LIMITE,
                ),
                f"X STATUS de midia ({caminho.name})",
            )
            processando = estado.get("data", estado).get("processing_info")
            if processando and processando.get("state") == "failed":
                raise ErroDeRede(f"X falhou ao processar a midia: {processando}")

        return str(midia_id)

    def publica(
        self,
        texto: str,
        midia_ids: list[str] | None = None,
        responder_a: str | None = None,
    ) -> str:
        """Publica um post e devolve o id. `responder_a` encadeia o fio."""
        corpo: dict = {"text": texto}
        if midia_ids:
            corpo["media"] = {"media_ids": midia_ids}
        if responder_a:
            corpo["reply"] = {"in_reply_to_tweet_id": responder_a}

        resposta = _confere(
            requests.post(
                X_POSTS_URL,
                headers={**self.cabecalho, "Content-Type": "application/json"},
                json=corpo,
                timeout=TEMPO_LIMITE,
            ),
            "X publicar post",
        )
        post_id = resposta.get("data", {}).get("id")
        if not post_id:
            raise ErroDeRede(f"X nao devolveu id do post: {resposta}")
        return str(post_id)


def _autenticacao_x(env: dict[str, str]) -> tuple[dict, dict]:
    """Monta a autenticacao do endpoint de token.

    App confidencial (com segredo) usa HTTP Basic; app publico manda o
    `client_id` no corpo. Os dois caminhos existem no X.
    """
    cliente = exige(env, "X_CLIENT_ID")
    segredo = env.get("X_CLIENT_SECRET", "").strip()
    if segredo:
        return {"auth": (cliente, segredo)}, {}
    return {}, {"client_id": cliente}


def token_x(env: dict[str, str]) -> ClienteX:
    """Devolve um cliente do X com token valido, renovando se preciso.

    O X devolve um refresh token novo a cada renovacao. Gravamos o novo
    imediatamente: perder essa gravacao significa refazer a autorizacao no
    navegador.
    """
    acesso = env.get("X_ACCESS_TOKEN", "").strip()
    try:
        expira_em = float(env.get("X_ACCESS_TOKEN_EXPIRA_EM", "0") or 0)
    except ValueError:
        expira_em = 0.0

    if acesso and time.time() < expira_em - MARGEM_TOKEN_X:
        return ClienteX(acesso)

    refresh = exige(env, "X_REFRESH_TOKEN")
    extra_auth, extra_corpo = _autenticacao_x(env)
    resposta = _confere(
        requests.post(
            X_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh,
                **extra_corpo,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=TEMPO_LIMITE,
            **extra_auth,
        ),
        "X renovar token",
    )

    novo_acesso = resposta.get("access_token")
    if not novo_acesso:
        raise ErroDeRede(f"X nao devolveu access_token: {resposta}")
    validade = int(resposta.get("expires_in", 7200))

    grava_env("X_ACCESS_TOKEN", novo_acesso)
    grava_env("X_ACCESS_TOKEN_EXPIRA_EM", str(int(time.time() + validade)))
    if resposta.get("refresh_token"):
        grava_env("X_REFRESH_TOKEN", resposta["refresh_token"])

    env["X_ACCESS_TOKEN"] = novo_acesso
    return ClienteX(novo_acesso)


# ---------------------------------------------------------------------------
# Instagram
# ---------------------------------------------------------------------------

IG_HOST = "https://graph.instagram.com"
IG_OAUTH_HOST = "https://api.instagram.com"
IG_AUTORIZA_URL = "https://www.instagram.com/oauth/authorize"
IG_ESCOPOS = "instagram_business_basic,instagram_business_content_publish"

# Renova o token longo quando faltar menos que isto. Ele vale 60 dias e so
# pode ser renovado depois de 24 horas de vida; nao da para deixar vencer.
MARGEM_TOKEN_IG = 10 * 24 * 3600  # 10 dias em segundos


@dataclass
class ClienteInstagram:
    token: str
    usuario_id: str
    versao: str = "v26.0"

    def _url(self, caminho: str) -> str:
        return f"{IG_HOST}/{self.versao}/{caminho.lstrip('/')}"

    def limite_publicacao(self) -> dict:
        """Quantos posts por API a conta ja gastou na janela de 24 horas."""
        return _confere(
            requests.get(
                self._url(f"{self.usuario_id}/content_publishing_limit"),
                params={"access_token": self.token},
                timeout=TEMPO_LIMITE,
            ),
            "Instagram consultar limite de publicacao",
        )

    def cria_recipiente(self, url_imagem: str, legenda: str) -> str:
        """Passo 1: cria o recipiente da midia. A imagem tem que estar num
        endereco publico, porque o servidor do Instagram vai baixa-la."""
        resposta = _confere(
            requests.post(
                self._url(f"{self.usuario_id}/media"),
                data={
                    "image_url": url_imagem,
                    "caption": legenda,
                    "access_token": self.token,
                },
                timeout=TEMPO_LIMITE,
            ),
            "Instagram criar recipiente",
        )
        recipiente = resposta.get("id")
        if not recipiente:
            raise ErroDeRede(f"Instagram nao devolveu id do recipiente: {resposta}")
        return str(recipiente)

    def estado_recipiente(self, recipiente: str) -> str:
        resposta = _confere(
            requests.get(
                self._url(recipiente),
                params={"fields": "status_code", "access_token": self.token},
                timeout=TEMPO_LIMITE,
            ),
            "Instagram consultar recipiente",
        )
        return str(resposta.get("status_code", "DESCONHECIDO"))

    def publica(self, url_imagem: str, legenda: str, espera: int = 60) -> str:
        """Sobe e publica uma foto. Devolve o id da midia publicada."""
        recipiente = self.cria_recipiente(url_imagem, legenda)

        limite = time.time() + espera
        estado = self.estado_recipiente(recipiente)
        while estado == "IN_PROGRESS" and time.time() < limite:
            time.sleep(3)
            estado = self.estado_recipiente(recipiente)
        if estado == "ERROR":
            raise ErroDeRede(
                f"Instagram nao conseguiu preparar a imagem {url_imagem}. "
                "Quase sempre e o endereco da imagem inacessivel ou fora do formato JPEG."
            )

        resposta = _confere(
            requests.post(
                self._url(f"{self.usuario_id}/media_publish"),
                data={"creation_id": recipiente, "access_token": self.token},
                timeout=TEMPO_LIMITE,
            ),
            "Instagram publicar",
        )
        midia = resposta.get("id")
        if not midia:
            raise ErroDeRede(f"Instagram nao devolveu id da midia: {resposta}")
        return str(midia)


def token_instagram(env: dict[str, str]) -> ClienteInstagram:
    """Cliente do Instagram com token longo valido, renovando se necessario."""
    token = exige(env, "IG_ACCESS_TOKEN")
    usuario = exige(env, "IG_USER_ID")
    versao = env.get("IG_API_VERSAO", "v26.0").strip() or "v26.0"

    try:
        expira_em = float(env.get("IG_ACCESS_TOKEN_EXPIRA_EM", "0") or 0)
    except ValueError:
        expira_em = 0.0

    if expira_em and time.time() > expira_em - MARGEM_TOKEN_IG:
        resposta = _confere(
            requests.get(
                f"{IG_HOST}/refresh_access_token",
                params={"grant_type": "ig_refresh_token", "access_token": token},
                timeout=TEMPO_LIMITE,
            ),
            "Instagram renovar token longo",
        )
        novo = resposta.get("access_token")
        if novo:
            validade = int(resposta.get("expires_in", 60 * 24 * 3600))
            grava_env("IG_ACCESS_TOKEN", novo)
            grava_env("IG_ACCESS_TOKEN_EXPIRA_EM", str(int(time.time() + validade)))
            token = novo

    return ClienteInstagram(token=token, usuario_id=usuario, versao=versao)


def confere_url_publica(url: str) -> tuple[bool, str]:
    """O Instagram baixa a imagem por conta propria. Se o endereco nao
    responder, o erro aparece la na frente e sem explicacao. Melhor conferir
    antes."""
    try:
        resposta = requests.head(url, timeout=20, allow_redirects=True)
        if resposta.status_code >= 400:
            resposta = requests.get(url, timeout=20, stream=True)
    except requests.RequestException as erro:
        return False, f"nao respondeu ({erro.__class__.__name__})"

    if resposta.status_code >= 400:
        return False, f"HTTP {resposta.status_code}"
    tipo = resposta.headers.get("Content-Type", "")
    if "jpeg" not in tipo and "jpg" not in tipo:
        return False, f"Content-Type {tipo or 'ausente'} (o Instagram so aceita JPEG)"
    return True, f"HTTP {resposta.status_code}, {tipo}"
