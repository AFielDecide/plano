# AUTOMAÇÃO DE PUBLICAÇÃO — @afieldecide

Publica a fila da Onda 1 no X e no Instagram por API, lendo os textos de um arquivo de posts aprovados e as credenciais de um `.env` que nunca entra no repositório.

**Nada aqui publica sozinho.** O script pede confirmação digitada antes de cada publicação, e não existe atalho para pular essa confirmação. Isso é decisão de projeto, não descuido: a conta fala em nome de um movimento que se define como sem dono, e voz automatizada sem ninguém olhando contradiz a tese que o próprio material defende.

---

## 1. O que a pesquisa achou (12/08/2026)

As duas plataformas mudaram as regras nos últimos dois anos. O que vale hoje, com a fonte de cada afirmação no fim da seção.

### X — não existe mais publicação de graça

A página oficial de preços descreve **pagamento por uso, sem assinatura**: você carrega crédito e cada chamada desconta. Os preços de escrita relevantes:

| Ação | Custo por requisição |
|---|---|
| Criar post | US$ 0,015 |
| **Criar post que contém link** | **US$ 0,200** |
| Criar post convocado (*summoned*) | US$ 0,010 |
| Ler post | US$ 0,005 |

Leitura tem teto de 2 milhões de posts por ciclo de cobrança. Quando o crédito acaba, a documentação é direta: as requisições ficam bloqueadas até você cobrir o saldo negativo.

**Sobre o plano gratuito:** ele não aparece em lugar nenhum da página oficial de preços atual. Publicações de terceiros relatam que o X encerrou o nível gratuito para novos desenvolvedores em 06/02/2026, migrando todo mundo para o pagamento por uso. Não achei essa data numa página oficial do X, então trate a data como relato de terceiro e o desaparecimento do plano gratuito como fato verificado na fonte primária.

**Quanto custaria a Onda 1 inteira no X**, contando o fio de lançamento (9 mensagens, sendo 1 com link) e os 7 posts avulsos (2 com link):

```
fio de lançamento:   8 × 0,015  +  1 × 0,200  =  US$ 0,32
posts avulsos:       5 × 0,015  +  2 × 0,200  =  US$ 0,48
                                                ----------
                                                 US$ 0,80
```

Menos de um dólar. **O custo não é o obstáculo — o obstáculo é ter que cadastrar meio de pagamento e carregar crédito**, que é um passo a mais e é irredutivelmente humano. E note o desenho de preço: um post com link custa mais de 13 vezes um post sem link. Como quase toda peça do movimento termina em chamada para assinar, vale saber que o link é o item caro.

A tabela de preços **não lista upload de mídia** como item cobrado (só aparece "Media Metadata", US$ 0,005). Não concluí daí que subir imagem é grátis; concluí que não está na tabela.

**Autenticação:** OAuth 2.0, fluxo de código de autorização com PKCE. O escopo que permite publicar é `tweet.write`. O token de acesso, segundo a documentação, "só fica válido por duas horas" a menos que você peça o escopo `offline.access` — que é o que devolve um *refresh token* e evita ter que reautorizar no navegador a cada duas horas. O script pede `tweet.read tweet.write users.read media.write offline.access`.

**Imagem:** `POST https://api.x.com/2/media/upload`, em partes (INIT → APPEND → FINALIZE), que é o caminho recomendado pela documentação; o upload simples existe mas está marcado como antigo. Limite de 5 MB para imagem. O `media_id` devolvido vai no corpo do `POST /2/tweets`, campo `media.media_ids` (até 4). O encadeamento do fio usa `reply.in_reply_to_tweet_id`.

### Instagram — conta profissional sim, Página do Facebook não

Aqui está a novidade que muda o trabalho. Existem **dois caminhos** para a mesma API, e eles têm exigências diferentes:

| | Instagram API **com login do Instagram** | Instagram API com login do Facebook |
|---|---|---|
| Página do Facebook | **Não exige** | Exige |
| Host das chamadas | `graph.instagram.com` | `graph.facebook.com` |
| Permissões para publicar | `instagram_business_basic`, `instagram_business_content_publish` | `instagram_basic`, `instagram_content_publish`, e mais |

A documentação da Meta é literal sobre o primeiro caminho: essa configuração **não exige** uma Página do Facebook vinculada à conta profissional do Instagram. **É esse o caminho que este script usa**, e é o que dispensa criar e manter uma Página do Facebook só para satisfazer a API.

O que continua obrigatório dos dois lados:

- **Conta profissional** (Comercial ou Criador de conteúdo). Conta pessoal não publica por API, ponto.
- **Imagem em endereço público.** A API não recebe arquivo: ela baixa a imagem de uma URL. A documentação diz que a mídia "precisa estar hospedada num servidor publicamente acessível no momento da tentativa", porque o servidor da Meta vai buscá-la.
- **Só JPEG.** Nas palavras da documentação, JPEG é o único formato de imagem suportado. Os cards do projeto são PNG — daí existir o `prepara_midia.py`.
- **Publicação em dois passos:** cria o recipiente em `POST /<IG_ID>/media`, depois publica em `POST /<IG_ID>/media_publish`.
- **Teto de 100 posts publicados por API em janela móvel de 24 horas**, consultável em `GET /<IG_ID>/content_publishing_limit`. A Onda 1 usa 8. Folga total.

**Tokens, e este é o ponto que mais dá dor de cabeça depois:**

| Etapa | Validade |
|---|---|
| Código de autorização | 1 hora, uso único |
| Token curto | 1 hora |
| **Token longo** | **60 dias** |
| Renovação | só depois do token ter 24 horas de vida |

E a armadilha: **token não renovado em 60 dias expira**. Se o movimento passar dois meses sem publicar, o acesso morre e alguém tem que refazer a autorização no navegador. É exatamente por isso que existe o `py publicar.py --tokens` e a tarefa agendada proposta na seção 6.

**Revisão de aplicativo (App Review):** para publicar **apenas na própria conta**, o aplicativo pode ficar em modo de desenvolvimento, e nesse modo ele autentica as contas que têm papel no app (administrador, desenvolvedor, testador). A revisão da Meta — o processo que leva semanas — é para app que serve conta de terceiros. Como aqui a conta do app e a conta do Instagram são a mesma pessoa, esse caminho não deveria ser necessário. **Confirme no painel antes de contar com isso**: esta é a afirmação com base mais fraca de toda a pesquisa, porque a documentação da Meta trata modo de desenvolvimento numa página e publicação em outra, e a síntese é minha.

A versão mais recente da Graph API é a **v26.0**, que é a padrão no `.env.exemplo`.

### Fontes

- [Preços da API do X](https://docs.x.com/x-api/getting-started/pricing) · [Sobre a API do X](https://docs.x.com/x-api/getting-started/about-x-api) · [OAuth 2.0 com PKCE](https://docs.x.com/resources/fundamentals/authentication/oauth-2-0/authorization-code) · [Upload de mídia](https://docs.x.com/x-api/media/introduction) e [em partes](https://docs.x.com/x-api/media/quickstart/media-upload-chunked) · [Criação de post](https://docs.x.com/x-api/posts/creation-of-a-post)
- [Publicação de conteúdo no Instagram](https://developers.facebook.com/docs/instagram-platform/content-publishing) · [Plataforma do Instagram: visão geral](https://developers.facebook.com/docs/instagram-platform) e [tokens](https://developers.facebook.com/docs/instagram-platform/overview) · [API com login do Instagram](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login) · [Login comercial](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/business-login) · [Versões da Graph API](https://developers.facebook.com/docs/graph-api/guides/versioning)

---

## 2. O que só uma pessoa pode fazer

Esta é a divisão honesta do trabalho. A coluna da esquerda não tem como ser automatizada — envolve login, identidade e dinheiro.

| Só uma pessoa faz | O script faz |
|---|---|
| Entrar nas contas `@afieldecide` | — |
| Criar o app no painel do X e no da Meta | — |
| Cadastrar meio de pagamento e carregar crédito no X | — |
| Deixar a conta do Instagram como profissional | — |
| Clicar em "Autorizar" na tela de permissão | Trocar o código pelo token e guardar no `.env` |
| Aprovar cada post (`aprovado = true`) | Conferir tamanho, arte e endereço da imagem |
| Digitar a confirmação na hora de publicar | Subir a imagem, publicar, encadear o fio, anotar o comprovante |
| — | Renovar o token do Instagram antes de vencer |

Uma regra que não muda por conveniência: **ninguém digita senha das contas em nenhum script, chat ou arquivo deste repositório.** O que existe aqui é token de API, gerado por você no painel, com escopo limitado e revogável a qualquer momento.

---

## 3. Passo a passo — X

1. **Conta de desenvolvedor** em [developer.x.com](https://developer.x.com), com a conta `@afieldecide` logada.
2. **Carregue crédito.** Sem saldo, nenhuma chamada passa.
3. **Crie um projeto e um app.**
4. No app, abra **User authentication settings** e configure:
   - Tipo de app: **Web App, Automated App or Bot** (é o que libera OAuth 2.0).
   - Permissões: **Read and write**.
   - Callback URI: `http://127.0.0.1:8721/callback` — tem que ser idêntico ao que estiver no `.env`.
   - Website URL: `https://afieldecide.github.io/site/`
5. Na aba **Keys and tokens**, copie o **OAuth 2.0 Client ID** (e o Client Secret, se o app for confidencial).
6. No terminal, dentro de `automacao/`:

```bash
py -m pip install -r requirements.txt
```

7. Copie `.env.exemplo` para `.env` e preencha `X_CLIENT_ID` (e `X_CLIENT_SECRET` se houver).
8. Gere o token:

```bash
py autorizar.py x
```

O navegador abre na tela de permissão do X. Você autoriza, o navegador volta para o endereço local, e o script grava o token no `.env`.

Se o X recusar o endereço local, cadastre um endereço `https` que você controle (o próprio site serve) e rode `py autorizar.py x --manual`: você autoriza, copia da barra do navegador o endereço inteiro para onde foi levado, e cola no terminal. O código de autorização vem dentro dele.

---

## 4. Passo a passo — Instagram

1. **A conta `@afieldecide` precisa ser profissional.** No aplicativo do Instagram: Configurações → Tipo de conta → mudar para conta profissional, categoria organização ou comunidade. (Isso já está previsto no PASSO 0 do `PLANO/11-fila-de-posts.md`.)
2. Crie uma conta de desenvolvedor em [developers.facebook.com](https://developers.facebook.com).
3. **Crie um app** e adicione o produto **Instagram**.
4. Abra **API setup with Instagram business login** e:
   - Vincule a conta profissional `@afieldecide`.
   - Copie o **Instagram App ID** e o **Instagram App Secret**. Atenção: não são os mesmos números do app do Facebook; são os específicos do Instagram.
   - Em **Business login settings**, cadastre a Redirect URI `http://127.0.0.1:8721/callback`, idêntica ao `.env`.
5. Preencha `IG_APP_ID` e `IG_APP_SECRET` no `.env`.
6. Gere o token:

```bash
py autorizar.py instagram
```

O script troca o código pelo token curto, troca o curto pelo longo de 60 dias, e grava tudo no `.env` junto com o `IG_USER_ID`.

Se a Meta recusar o endereço local, use `py autorizar.py instagram --manual`, mesma lógica do X.

7. **Prepare as imagens** (o Instagram só aceita JPEG e só baixa de endereço público):

```bash
py prepara_midia.py
```

Isso escreve `automacao/midia/card-*.jpg`. Esses arquivos **precisam ser commitados e enviados ao GitHub**, porque é de lá que o servidor da Meta vai baixá-los. O endereço base já está no `.env.exemplo` apontando para este repositório, que é público.

8. Confira que ficou tudo de pé:

```bash
py publicar.py --checar --online
```

---

## 5. Uso no dia a dia

```bash
py publicar.py                          # lista a fila e o que já foi publicado
py publicar.py --checar --online        # confere tamanho, artes, tokens e endereços
py publicar.py --ensaio d01-ig-lancamento    # mostra na tela o que iria ao ar
py publicar.py --publicar d01-ig-lancamento  # publica, com confirmação digitada
py publicar.py --tokens                 # saúde dos tokens; renova o do Instagram
```

**Como aprovar um post:** abra o `posts-aprovados.toml` e troque `aprovado = false` por `aprovado = true` no item. Essa troca é o ato de aprovação. O script se recusa a publicar item não aprovado, e mesmo aprovado ele ainda pede que você digite o id do post para confirmar — digitar "s" não serve, justamente para não publicar a peça errada por reflexo.

**Comprovantes:** cada publicação anota id, data, link e id do post em `registro-publicacoes.json`. Esse arquivo também é o que impede publicar a mesma peça duas vezes. Vale commitar: é registro público de um movimento que promete transparência.

**Se os acentos aparecerem trocados** num console antigo do Windows, rode `chcp 65001` antes.

### Arquivos

| Arquivo | O que é |
|---|---|
| `posts-aprovados.toml` | A fila. Texto igual ao do `PLANO/11-fila-de-posts.md`, em formato que o script lê |
| `publicar.py` | O publicador. É por onde você passa |
| `redes.py` | Conversa com as APIs do X e do Instagram |
| `autorizar.py` | Gera os tokens. Roda uma vez por rede |
| `prepara_midia.py` | Converte os cards PNG em JPEG para o Instagram |
| `midia/` | Os JPEG. Versionados de propósito: é o endereço público das imagens |
| `.env` | Suas credenciais. **Nunca vai para o GitHub** |
| `registro-publicacoes.json` | Comprovante do que já foi publicado |

---

## 6. Tarefa agendada — proposta

A proposta é deliberadamente conservadora: **a máquina cuida da manutenção, a pessoa cuida da publicação.**

**Tarefa A — Ensaio da manhã** (dias úteis, 8h30)

```bash
py publicar.py --checar --online
```

Confere a fila inteira, os tokens e os endereços das imagens, e avisa o que está fora do lugar. Não publica e não gasta crédito do X: essa checagem não faz nenhuma chamada à API do X. Chega o relatório, você decide o que vai ao ar e roda o `--publicar` do item.

**Tarefa B — Saúde do token** (semanal)

```bash
py publicar.py --tokens
```

É a tarefa que evita o tombo real: o token longo do Instagram morre em 60 dias sem renovação, e depois de morto só se recupera refazendo a autorização no navegador. Rodando toda semana, a renovação acontece sozinha na hora certa.

**O que eu não proponho, e por quê.** Dá para fazer o script publicar sozinho no horário marcado. Deixei de fora de propósito, e por dois motivos que não são técnicos: publicar é irreversível diante do público, e um movimento que promete "sem dono" com a voz publicando sozinha na mão de uma pessoa só entrega o oposto do que promete. Se em algum momento fizer sentido inverter isso, que seja decisão registrada e combinada com o núcleo — a regra dos três do `MANTENEDORES.md` cabe aqui igualzinho —, e não um parâmetro que apareceu escondido num arquivo.

Para criar as duas tarefas na máquina, é só pedir.

---

## 7. O que ficou pendente

Coisas que dependem de você e que travam a publicação por API até serem resolvidas:

1. **Os textos dos dias 2 a 14 não cabem no X.** Foram escritos para a legenda do Instagram, que aceita 2.200 caracteres. No X, conta comum tem 280. A conferência mostra o tamanho de cada um:

   | Post | Caracteres | Limite |
   |---|---|---|
   | `d02-x-tese` | 609 | 280 |
   | `d04-x-semlider` | 672 | 280 |
   | `d06-x-faixa1983` | 583 | 280 |
   | `d08-x-faixabarrada` | 393 | 280 |
   | `d10-x-chamado` | 576 | 280 |
   | `d12-x-nucleo` | 462 | 280 |
   | `d14-x-zelador` | 430 | 280 |

   O fio de lançamento cabe: a maior mensagem tem 278 de 280, com dois de folga. Os avulsos não. Três saídas: encurtar cada um, transformar em fio, ou publicar só no Instagram. **Não encurtei por conta própria** — é texto do movimento, e cortar frase de manifesto sem mandato não é trabalho de script nem meu. Se a conta for Premium o limite muda; nesse caso é só ajustar `X_LIMITE_CARACTERES` no `.env`.

2. **Nada foi testado contra as APIs de verdade**, porque ainda não existem tokens. O que está verificado: a fila carrega, os textos são medidos, as artes existem, os JPEG são gerados, o `.env` é gravado sem corromper, as travas recusam post não aprovado e texto grande demais, a duplicata é barrada, e o `raw.githubusercontent.com` devolve o tipo de imagem certo (testei contra um arquivo que já está público no repositório). O que **não** está verificado: as chamadas de publicação em si, que só dá para exercitar com credencial na mão. A primeira publicação real vai ser o teste — faça pelo `--ensaio` antes.

3. **Confirmar no painel da Meta** que o app em modo de desenvolvimento publica na própria conta sem passar por App Review. Se exigir revisão, o prazo entra na conta do planejamento da Onda 1.

4. **Registrar o gasto do X.** O movimento não arrecada dinheiro — isso é cláusula pétrea e não está em questão aqui, porque gastar não é arrecadar. Mas gasto pago do bolso de uma pessoa é um vínculo de dependência num projeto que promete não ter dono. Menos de um dólar por onda é pouco dinheiro e muito recado: vale decidir com o núcleo se a publicação no X entra assim, e deixar registrado.

---

## 8. Segurança

- O `.env` está no `.gitignore`. Confira com `git status` antes de qualquer commit: se `.env` aparecer na lista, pare.
- Token vazado não se conserta trocando senha. O conserto é revogar o app no painel da rede e gerar outro. Por isso o `.env` mora só na máquina do mantenedor.
- O `refresh token` do X é gravado de forma atômica: o arquivo é escrito num temporário e trocado de uma vez, então não existe momento em que o `.env` fique pela metade com o token cortado.
- Escopos são o mínimo necessário para publicar. O script não lê mensagem direta, não segue ninguém e não apaga nada.
- Os JPEG em `midia/` são públicos de propósito. São as mesmas artes que já vão para as redes — não tem nada ali que não seja para ser visto.
