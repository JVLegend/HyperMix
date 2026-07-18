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
- target MAE do unmixing em três cenas;
- limitações que devem acompanhar qualquer interpretação dos resultados.

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
- `public/og.png`: imagem de compartilhamento;
- `tests/rendered-html.test.mjs`: testes do HTML renderizado e do escopo do app;
- `vercel.json`: configuração do deploy de produção.
