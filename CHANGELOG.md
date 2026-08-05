# Histórico de mudanças

Este projeto segue versionamento semântico. Mudanças ainda não publicadas ficam
em `Não publicado`; resultados científicos são descritos apenas depois de
medidos pelos scripts versionados.

## Não publicado

### Documentação

- registrou a publicação pública da `0.5.0`, os hashes dos artefatos e o smoke
  test de instalação independente;
- adicionou badge do PyPI e a lab note da primeira release pública;
- arquivou o ZIP exato da tag `v0.5.0` no Zenodo e registrou os DOI de versão e
  conceitual na documentação citável.

### Adicionado

- criou `hypermix/transfer.py` para transferência laboratório-sensor por SRF,
  atmosfera, deslocamento espectral e ganho, sem rótulos de avaliação;
- adicionou o experimento T9a com AUC, Pd@FAR, distância ao oráculo e IC
  bootstrap em 45 casos pareados;
- ampliou o gate de release para conferir `hypermix.__version__`.

### Resultado científico

- o critério primário da família física por subespaço falhou e degradou AUC e
  Pd@FAR contra o alvo laboratorial;
- em análise secundária, a transferência nominal por metadados quase alcançou o
  oráculo. O achado é sintético, favorece modelagem física estreita e não muda o
  veredito sobre aprendizado.

## 0.5.0 - 2026-08-04

### Adicionado

- aquisição auditável e loader ENVI para o cubo bioHSI real de 54 m;
- protocolo regional pré-especificado e porta de reprodução da Figura 4g;
- métricas de incerteza calibrada e análise de esparsidade de bandas;
- detector auto-supervisionado de fundo e benchmark causal correspondente;
- observatório web bilíngue, responsivo e acessível;
- CI matricial para o núcleo, suíte de pesquisa, pacote e observatório;
- gate de release para impedir divergências entre tag, pacote, citação,
  changelog, notas e publicação OIDC;
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
