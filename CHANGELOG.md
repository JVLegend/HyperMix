# Histórico de mudanças

Este projeto segue versionamento semântico. Mudanças ainda não publicadas ficam
em `Não publicado`; resultados científicos são descritos apenas depois de
medidos pelos scripts versionados.

## Não publicado

Nenhuma mudança registrada.

## 0.5.0 - 2026-08-04

### Adicionado

- aquisição auditável e loader ENVI para o cubo bioHSI real de 54 m;
- protocolo regional pré-especificado e porta de reprodução da Figura 4g;
- métricas de incerteza calibrada e análise de esparsidade de bandas;
- detector auto-supervisionado de fundo e benchmark causal correspondente;
- observatório web bilíngue, responsivo e acessível;
- CI matricial para o núcleo, suíte de pesquisa, pacote e observatório;
- documentação de contribuição, suporte, segurança e preparação de release.

### Resultado científico

- a porta da Figura 4g falhou com as caixas candidatas. T8c permanece pausado
  até que as coordenadas manuais sejam recuperadas;
- em cinco regimes avaliados, nenhum método aprendido superou de forma robusta
  o matched filter espacial bem calibrado.

## 0.4.0 - 2026-07-18

- adicionou o unmixer de abundância e métricas específicas do alvo;
- ampliou o benchmark para três cenas reais de sensores distintos;
- adicionou matched filter espacial, testes de mismatch e metadados de release.

## 0.3.0 - 2026-07-17

- adicionou detector aprendido, benchmark sobre fundo real, dataset espectral
  aberto, baseline SAM e leaderboard reproduzível.
