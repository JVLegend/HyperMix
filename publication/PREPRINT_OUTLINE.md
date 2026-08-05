# Esqueleto do preprint HyperMix

Estado: estrutura de trabalho, não manuscrito submetido.

## Título provisório

**HyperMix: an open benchmark for honest evaluation of engineered
biosignature detection in hyperspectral imagery**

Alternativa centrada no resultado:

**When a calibrated matched filter is hard to beat: reproducible negative
results for hyperspectral biosignature detection**

## Afirmação central permitida

O HyperMix oferece um benchmark aberto que separa informação do alvo, realismo
físico, estatística do fundo, calibração e decisão operacional. Nos regimes
concluídos, nenhum método aprendido superou de forma robusta um matched filter
espacial bem calibrado. A avaliação em expressão biológica realmente medida
continua bloqueada pela geometria não reproduzida da Figura 4g.

## Estrutura

1. **Motivação**
   - biossensoriamento remoto com repórteres hiperespectrais;
   - risco de confundir baseline fraco com ganho de aprendizado;
   - necessidade de resultados negativos reproduzíveis.
2. **Contratos de informação**
   - alvo exato, família estreita e alvo desconhecido;
   - separação de treino, calibração e avaliação;
   - unidade estatística por cena, SNR e seed.
3. **Benchmark e métodos**
   - fundos reais com alvos implantados;
   - física de sensor e transferência laboratório-sensor;
   - MF, MF espacial, RX, subespaço, MLP e autoencoder de fundo.
4. **Métricas**
   - AUC e Pd@FAR;
   - NLL, Brier e ECE;
   - MAE, viés, cobertura e largura;
   - bootstrap agrupado e critérios pré-especificados.
5. **Resultados**
   - liderança ou empate do MF espacial em detecção;
   - ausência de vantagem aprendida em calibração;
   - falha da hipótese de três bandas;
   - LOD simulado e abundância calibrada;
   - heterogeneidade entre cenas sem seleção narrativa.
6. **Tentativa em alvo biológico real**
   - dados bioHSI, nove rótulos regionais e assinatura independente;
   - porta de reprodução falhou;
   - coordenadas manuais como dependência externa explícita.
7. **Discussão**
   - quando o MF é um baseline especialmente forte;
   - por que features derivadas do MF limitam o MLP;
   - valor científico de um benchmark que não produz uma vitória aprendida.
8. **Reprodutibilidade e comunidade**
   - PyPI, Zenodo, CI e manifesto de evidências;
   - protocolo de clone limpo;
   - chamada para reprodução externa e validação de dados.

## Figuras candidatas

1. Diagrama dos contratos de informação e splits.
2. Painel agregado de AUC e Pd@FAR nos regimes concluídos.
3. Reliability diagram e contraste de NLL/ECE.
4. Curva de AUC por número de bandas.
5. LOD por FWHM e FAR.
6. Abundância calibrada com cobertura e largura.
7. Overlay das caixas candidatas e falha da porta bioHSI.

## Tabela principal

Uma linha por hipótese causal, com baseline justo, método aprendido, métrica
primária, intervalo do contraste, veredito e limitação. Os valores devem ser
extraídos dos JSONs fixados em `publication/evidence_manifest.json`, nunca
copiados de memória.

## Itens ainda necessários antes de submissão

- recuperar ou validar independentemente as coordenadas da Figura 4g;
- obter ao menos uma reprodução por pessoa externa;
- congelar versão, commit e DOI usados no manuscrito;
- redigir declaração transparente sobre assistência de IA;
- selecionar periódico ou servidor de preprint sem ampliar as conclusões.
