# HyperMix Observatory

Interface web interativa do benchmark HyperMix. A aplicação apresenta uma
fotografia auditada dos resultados e deixa explícita a principal conclusão
científica: neste protocolo, o matched filter espacial lidera ou empata com o
detector aprendido.

- Produção: https://hypermix-observatory.vercel.app
- Código científico: https://github.com/JVLegend/HyperMix
- Status científico: [../STATUS.md](../STATUS.md)

## O que pode ser explorado

- AUC de detecção em target SNR de 20, 10, 5 e 0 dB;
- sensibilidade a mismatch espectral de 0% a 5%;
- diferença entre alvo oráculo e alvo laboratorial sob sensor e atmosfera;
- três tracks de variabilidade medida do alvo;
- experimento T7a de aprendizado auto-supervisionado do fundo, com AUC,
  Pd@FAR e intervalos de 95%;
- target MAE do unmixing em três cenas;
- limitações que devem acompanhar qualquer interpretação dos resultados.
- interface completa em inglês por padrão, com alternância 🇺🇸/🇧🇷 no topo.
- Map Studio local para enviar um mapa de scores e visualizar uma máscara por
  limiar.

O idioma inicial é inglês. Os botões `EN` e `PT` atualizam todo o conteúdo da
página e também o atributo de idioma do documento, sem trocar a URL nem perder a
âncora que está sendo visualizada.

## Storytelling editorial

A página segue uma ordem causal explícita. O dossiê inicial apresenta cinco
perguntas e cada seção entrega uma resposta antes de conduzir à próxima:

1. baixo sinal e mismatch espectral;
2. realismo físico do laboratório ao sensor;
3. variabilidade medida do alvo;
4. aprendizado auto-supervisionado do fundo;
5. utilidade no unmixing, seguida pelo Map Studio e pelos limites.

O experimento T7a permanece sem inflação. MF espacial obteve AUC 0,987
[0,968, 0,997] e Pd@FAR 0,650 [0,227, 0,872]. O autoencoder espacial obteve
0,976 [0,945, 0,994] e 0,324 [0,087, 0,544]. Os intervalos das diferenças
pareadas ficaram abaixo de zero nas duas métricas. A página registra que essa
instanciação simples falhou, sem extrapolar para todo estimador de fundo.

## Experiência por scroll

O scroll permanece nativo e controla apenas efeitos de apoio à leitura:

- barra fina de progresso global;
- trilho lateral com o capítulo científico ativo;
- parallax leve no hero, limitado ao primeiro viewport;
- reveals de entrada para títulos, painéis e conclusões;
- contexto sticky no dossiê inicial;
- stagger curto em sequências de cards e limitações.

Não há scroll hijacking, smooth-scroll artificial ou snapping. Em telas
compactas, o trilho lateral e o parallax são removidos. Com
`prefers-reduced-motion: reduce`, o conteúdo permanece imediatamente visível e
as transformações decorativas são desativadas. Sem `IntersectionObserver`, a
página também faz fallback para conteúdo estático.

## Map Studio

O Map Studio aceita PNG, JPEG e WebP de até 12 MB. O arquivo é processado
somente no navegador e não é enviado à Vercel. O brilho de cada pixel é tratado
como score, e o controle de limiar destaca os pixels candidatos.

Esse recurso é um visualizador de mapas já produzidos, não um endpoint de
inferência. Uma imagem RGB não contém o cubo hiperespectral nem a assinatura de
alvo necessários para executar o HyperMix. A interface informa essa limitação
junto ao resultado para evitar uma interpretação científica incorreta.

Os números exibidos são uma fotografia curada dos artefatos auditados em
`results/`. O site não executa treinamento nem inferência no navegador e não é
um leaderboard atualizado automaticamente. Quando um experimento mudar, os
valores em `app/page.tsx` e esta documentação devem ser atualizados juntos.

## Desenvolvimento local

Requer Node.js 22.13 ou posterior.

```bash
cd webapp
npm install
npm run dev
```

Abra `http://localhost:3000`. O preview local usa vinext, mantendo o fluxo do
ambiente de desenvolvimento. A aplicação também possui um build Next.js nativo
para a Vercel.

## Verificação

```bash
npm test
npm run build:vercel
npm run lint
```

`npm test` compila o preview e verifica a renderização HTML, o conteúdo de
validade científica e a presença dos controles interativos. `build:vercel`
valida o mesmo app no runtime usado em produção.

## Publicação na Vercel

O arquivo `vercel.json` define Next.js como framework e usa o script
`build:vercel`. Com a Vercel CLI autenticada:

```bash
cd webapp
npx vercel --prod --yes
```

O primeiro deploy cria ou vincula um projeto na conta autenticada. Para manter
o endereço público usado nos metadados e na documentação, associe o deploy ao
alias estável:

```bash
npx vercel alias set <url-do-deploy> hypermix-observatory.vercel.app
```

A pasta `.vercel/` é local e ignorada pelo Git. Nenhum token deve ser commitado.

## Estrutura

- `app/page.tsx`: conteúdo, dados curados e interações;
- `app/globals.css`: sistema visual e responsividade;
- `app/layout.tsx`: metadados, fontes e social card;
- `public/og-v2.png`: imagem de compartilhamento do redesign editorial;
- `tests/rendered-html.test.mjs`: testes do HTML renderizado e do escopo do app;
- `vercel.json`: configuração do deploy de produção.
