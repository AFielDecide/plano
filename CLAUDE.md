# Projeto Corinthians — A Fiel Decide

Movimento independente da torcida do Corinthians. Pede voz, voto e transparência no clube, e complementa o SAFiel: o SAFiel traz o capital, A Fiel traz o mandato.

## Onde fica o quê

| Pasta | O que é |
|---|---|
| `site/` | O site no ar. **É um repositório git próprio** (`github.com/afieldecide/site`, GitHub Pages, AGPL-3.0). Commitar de dentro dele |
| `PLANO/` | Manifesto, plano, kits, playbook do núcleo, roteiro de contas |
| `ARTES/` | Geradores de arte em Python (Pillow) para cards, capas e banners |

Site estático puro: HTML, CSS e JS vanilla. Sem framework, sem build, sem servidor pensante. Isso é **requisito político**, não preferência técnica: a cláusula do `site/RECOMEÇAR.md` exige que qualquer torcedor clone o repositório e reergue o site num fim de semana.

Para ver o site local, use o preview `site-fiel` (ou `site-fiel-ds`) do `.claude/launch.json`. Não suba servidor pelo Bash.

## Identidade visual (design system)

Antes de criar ou alterar qualquer tela, componente ou página, leia [`site/design.md`](site/design.md), a fonte da verdade visual deste projeto. O guia visual navegável é [`site/design.html`](site/design.html), que carrega o `styles.css` de produção.

Toda mudança de estilo atualiza `styles.css`, `design.md` e `design.html` **no mesmo commit**, para nunca dessincronizarem. Não introduza cor, fonte, espaçamento ou componente fora dos tokens sem antes registrar no `design.md`.

Resumo do sistema, que o `design.md` detalha: papel e tinta, canto reto em tudo, sombra dura sem desfoque, **nenhuma cor de acento** (a ênfase é a inversão), fontes auto-hospedadas em `fonts/`.

## Nunca tocar

- **Escudo, mascote ou qualquer ativo oficial do Sport Club Corinthians Paulista.** O movimento é independente. A marca dele é a faixa listrada e o losango.
- **As 3 cláusulas pétreas.** A principal: o movimento não arrecada dinheiro. Nenhuma tela, formulário ou texto pode pedir Pix, doação ou dado de pagamento.
- **Fonte por CDN.** As fontes moram em `site/fonts/`.
- **A velocidade dos marquees.** Foi reduzida a pedido.

## Tom dos textos

O material fala com adulto de arquibancada. Registro paulistano com "você", nunca "tu". No máximo um slogan por seção. Negrito só em regra dura e número-chave. **Todo número exibido vem com a fonte citada**, e precisão inventada está proibida. Detalhe em `PLANO/00-LEIA-PRIMEIRO.md`.
