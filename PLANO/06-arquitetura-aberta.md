# A URNA DE VIDRO — arquitetura aberta do movimento
### Como o A Fiel Decide funciona sem dono, sem servidor de alguém, e sem que ninguém — nem a gente — possa fraudar ou apagar um resultado
*Documento técnico em linguagem de gente. Versão 1 — ago/2026.*

---

## 1. O problema que este documento resolve

Um movimento como este pode morrer de três jeitos:

1. **Captura** — alguém vira "o dono" (do site, do banco de dados, do perfil) e passa a mandar. Vira cartola digital.
2. **Abandono** — a pessoa que segurava tudo cansa, some, ou perde a senha. O movimento evapora.
3. **Queda/censura** — o site cai, a conta é banida, o banco é apagado (por acidente ou por pressão), e não sobra prova de nada.

A resposta pros três é a mesma e tem nome: **Urna de Vidro**. Três propriedades:

> **Tudo replicável** (qualquer um pode clonar o movimento inteiro) ·
> **Tudo verificável** (qualquer um pode recontar qualquer votação) ·
> **Ninguém indispensável** (nenhuma pessoa sozinha liga ou desliga nada).

Uma honestidade antes de começar: **"100% descentralizado, sem nenhum humano" não existe** — nem as DAOs de cripto funcionam assim (sempre há mantenedores). O que existe, e é o que vamos construir, é um sistema onde **nenhuma pessoa específica é necessária** e onde **trair custa mais caro que cooperar**, porque tudo é público. É assim que Wikipedia, Linux e o próprio Bitcoin sobrevivem há décadas.

---

## 2. A decisão mais importante: blockchain sim, mas no lugar certo

Você pediu pra pensar em blockchain. Pensei — e a resposta é **usar blockchain como cartório, não como urna**. Explico:

### ❌ O que NÃO vamos fazer: voto direto na blockchain / token de governança
- **Mata a participação.** Votar on-chain exige carteira cripto, frase-semente, taxa de transação. O torcedor de 60 anos do Fiel Torcedor não vai instalar MetaMask — e o movimento é dele também. Barreira técnica = elitização, o contrário da nossa tese.
- **Token = peso por dinheiro pela porta dos fundos.** Todo esquema de token acaba com alguém acumulando tokens. Nosso princípio é **1 pessoa = 1 voto**, inegociável.
- **Cheiro de golpe.** O risco nº 1 do plano (seção 8 do `02-plano.md`) é "é golpe / querem dinheiro". Aparecer com token/cripto entrega o movimento de bandeja pra essa acusação. O seu rascunho original propunha "tokens de governança" — foi retirado de propósito, pelo mesmo motivo do escrow.

### ✅ O que vamos fazer: blockchain como carimbo de cartório (grátis e invisível pro usuário)
Existe uma ferramenta chamada **OpenTimestamps** (opentimestamps.org, criada em 2016, usada por jornalistas e arquivos públicos). Ela pega a "impressão digital" de um arquivo (o *hash* — um código único que muda se uma vírgula mudar) e **grava essa impressão digital na blockchain do Bitcoin, de graça**, sem precisar comprar cripto nem ter carteira.

O que isso nos dá: ao fechar cada consulta, publicamos o arquivo com todos os votos e carimbamos ele no Bitcoin. A partir daí, **ninguém — nem nós mesmos — consegue alterar um voto sem que o mundo inteiro possa provar a fraude**. O torcedor não precisa entender nada disso: pra ele é só um selo "resultado lacrado" com um botão "verificar".

Em linguagem de arquibancada, e é assim que vamos explicar no site:

> **A urna é de vidro: qualquer um pode recontar os votos.
> E o lacre fica registrado num cartório mundial que ninguém apaga — nem a gente.**

---

## 3. As cinco camadas (o desenho completo)

### Camada 1 — O código: aberto, com licença que impede sequestro
- **Tudo no GitHub**, numa organização (ex.: `github.com/afieldecide`) — não na conta pessoal de ninguém.
- **Licença AGPL-3.0**: qualquer um pode copiar e rodar, mas quem modificar é **obrigado a abrir o código também**. Isso impede que uma empresa ou político pegue a plataforma, feche e transforme em produto próprio.
- **Espelho automático** no Codeberg ou GitLab (se o GitHub sumir, o código continua).
- Cada pessoa que clona o repositório vira, sem saber, um backup completo do movimento — o Git guarda o histórico inteiro com impressão digital de cada mudança.

### Camada 2 — O site: estático, gratuito, impossível de derrubar de vez
- Site **estático** (HTML puro, sem servidor "pensante") hospedado no **GitHub Pages** (grátis) com espelho no **Cloudflare Pages** (grátis).
- Domínio próprio (~R$ 40/ano, ex.: `afieldecide.com.br`) apontando pra lá. É o ÚNICO custo fixo do movimento — e qualquer pessoa da rede pode pagar um ano de bolso próprio (não é arrecadação, é contribuição de trabalho, como quem imprime um cartaz).
- **Se o site cair ou o domínio for perdido:** qualquer pessoa faz *fork* do repositório e tem o site inteiro no ar em minutos, em outro endereço. As instruções de "como subir um espelho" ficam no próprio repositório, em português simples.

### Camada 3 — A votação: simples por fora, auditável por dentro
O fluxo de uma consulta, de ponta a ponta:

1. **Cadastro leve:** e-mail verificado + CPF. O CPF serve só pra garantir **1 pessoa = 1 voto** — e **nunca é guardado às claras**: guardamos apenas um código embaralhado dele (HMAC com chave secreta), que permite detectar CPF repetido sem permitir descobrir o CPF de ninguém.
2. **O voto:** a pessoa vota no site/PWA (funciona como app no celular, sem loja de aplicativo). Recebe na hora um **recibo** — um código curto tipo `FD-7K3M-9QRT`.
3. **O fechamento:** ao encerrar a consulta, é publicado o **arquivo público de apuração**: a lista completa de (recibo → escolha → hora), sem nenhum dado pessoal, mais o total. No GitHub, pra sempre.
4. **O lacre:** o arquivo é carimbado no Bitcoin via OpenTimestamps, e a impressão digital (hash) também é publicada como post fixado no perfil do movimento no X — âncora técnica + âncora social.
5. **A conferência:** qualquer torcedor busca o próprio recibo no arquivo e confirma que seu voto está lá, do jeito que votou. Qualquer jornalista ou desconfiado **reconta tudo** com um script de 10 linhas que a gente publica junto. Se o total divulgado não bater com o arquivo, a fraude é provável em público.

**Limite honesto (importante você saber):** o sigilo do voto e a auditoria total têm uma tensão entre si — pra auditar 100% da unicidade de CPFs, seria preciso expor os códigos dos CPFs, o que enfraquece a privacidade. Resolvemos como as eleições de verdade resolvem: a **apuração** é 100% pública (qualquer um reconta), e a **unicidade** é garantida pelo sistema + auditável por qualquer pessoa da rede que se candidate a "mesário digital" (acesso de leitura ao banco, com termo de confidencialidade). Não existe urna perfeita; existe urna com fiscal de todos os partidos.

**Infraestrutura do MVP:** Cloudflare Workers + banco D1, ou Supabase — os planos gratuitos aguentam as primeiras dezenas de milhares de votos. O código de subir a instância é público e documentado ("1 comando e está rodando"), então **a instância oficial é substituível**: se quem hospeda hoje sumir, a rede sobe outra e os dados históricos continuam públicos no GitHub.

### Camada 4 — Os dados: Git como banco do povo
- **Todos os resultados de consultas** e **todos os números do Placar Aberto** (dívida, pagamentos à Caixa, etc., cada um com fonte) vivem num repositório público de dados (arquivos CSV/JSON legíveis por humano e por máquina).
- O painel do site **lê direto desse repositório**. Corrigiu o dado no repositório, o site atualiza.
- Por que Git em vez de um "banco de dados na nuvem"? Porque cada clone é um backup completo, cada mudança fica assinada e datada pra sempre, e **não custa nada**. É, na prática, o banco de dados mais replicado e mais barato que existe.

### Camada 5 — A governança: ninguém tem a chave sozinho
- **Regra dos 3:** toda conta crítica (organização GitHub, Cloudflare, domínio, perfis sociais) tem **no mínimo 3 pessoas** com acesso, de núcleos diferentes, com 2FA. Ninguém liga nem desliga nada sozinho.
- **`MANTENEDORES.md` público:** quem são os mantenedores atuais de cada coisa, desde quando, e como a rede troca um mantenedor (por votação no próprio A Fiel Decide — o movimento se governa pela própria ferramenta).
- **Rodízio de porta-voz** (já está no plano) vale também pra infraestrutura: mantenedor é zelador temporário, não dono.
- **Kit de sucessão — o "teste do desaparecimento":** o repositório contém um `RECOMEÇAR.md` que responde: *"se todos os mantenedores sumirem hoje, como um grupo de torcedores reergue tudo num fim de semana?"* Resposta: fork do código (público) + dados históricos (públicos) + subir instância nova (documentado) + anunciar novo endereço. O que se perde? Nada que importe: **as senhas morrem, a urna de vidro fica.**

---

## 4. Privacidade e LGPD (proteção sua e do torcedor)
- **Minimização:** só coletamos e-mail e CPF (embaralhado). Nada de endereço, telefone obrigatório, documento com foto.
- **Finalidade declarada:** política de privacidade simples no site — "seus dados servem só pra garantir 1 pessoa = 1 voto e te avisar de novas consultas (se você quiser)".
- **Nada de venda/uso comercial de dados. Nunca.** Isso entra como cláusula pétrea junto com "não arrecada dinheiro".
- **Direito de sair:** apagar cadastro remove e-mail e o código do CPF; os votos já dados permanecem no arquivo público (são anônimos — só o recibo identifica, e só pra quem o tem).
- Nada de disparo de e-mail/SMS não pedido — coerente com a trava nº 3 do movimento (anti-spam).

## 5. O custo real disso tudo

| Item | Custo |
|---|---|
| GitHub (código + dados + Pages) | R$ 0 |
| Cloudflare (espelho + Workers/D1 no plano free) | R$ 0 |
| OpenTimestamps (carimbo em Bitcoin) | R$ 0 |
| Supabase free (se for a opção do banco) | R$ 0 |
| Domínio `.com.br` | ~R$ 40/ano |
| **Total** | **~R$ 40/ano** |

Coerência total com a trava nº 1: um movimento que custa R$ 40/ano **não tem desculpa pra pedir Pix**.

## 6. Roadmap técnico (fases realistas)

- **Fase 0 — já (esta semana):** site estático no ar em endereço próprio (GitHub Pages + domínio) com manifesto, números e link da petição. A "consulta #01" pode nascer como a própria petição (a assinatura é o primeiro voto).
- **Fase 1 — MVP da urna (2–4 semanas de trabalho):** PWA de voto com cadastro leve, recibo, arquivo público de apuração + carimbo OpenTimestamps. 1 consulta por mês.
- **Fase 2 — Placar Aberto v1:** repositório de dados + painel lendo dele (dívida, Caixa, promessa × entrega).
- **Fase 3 — Rede:** espelhos rodando por núcleos, mesários digitais, `RECOMEÇAR.md` testado de verdade (simular o desaparecimento e reerguer).

## 7. Glossário de bolso (pra você explicar pra qualquer um)
- **Hash / impressão digital:** código único de um arquivo; muda tudo se mudar uma vírgula. É como o lacre de uma urna.
- **OpenTimestamps:** cartório gratuito que grava essa impressão digital no Bitcoin, provando que o arquivo existia naquela data, daquele jeito.
- **Fork / clone:** cópia completa do projeto que qualquer pessoa pode fazer. É o que torna o movimento "à prova de dono".
- **PWA:** site que se comporta como aplicativo no celular, sem depender da loja da Apple/Google.
- **AGPL:** licença que obriga quem usar o código a manter ele aberto. Anti-sequestro.
- **HMAC:** jeito de embaralhar o CPF com uma chave secreta — dá pra saber se um CPF repetiu, sem dar pra descobrir qual CPF é.

---

### O parágrafo que resume (pra colar em qualquer conversa)

> O A Fiel Decide roda em código aberto que qualquer um pode copiar, num site que qualquer um pode reerguer, com votações que qualquer um pode recontar e resultados carimbados na blockchain do Bitcoin — de graça, sem token, sem carteira, sem pedir um centavo. Não tem dono porque **não tem nada pra ser dono**: as chaves são de no mínimo três pessoas, os dados são de todo mundo, e se todos os responsáveis sumirem amanhã, a torcida reergue tudo num fim de semana. A urna é de vidro.
