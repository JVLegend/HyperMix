# Diagnóstico da porta de reprodução bioHSI de 54 m

Registrado em 2026-08-04 depois da primeira execução pré-especificada. Este
documento explica por que T8c permanece pausado.

## Resultado principal

A implementação HyperMix do método HKM mais UCLS não reproduziu os nove scores
da Source Data: MAE 0,156114 e Pearson 0,375901. A porta havia sido fixada em
MAE menor ou igual a 0,01 e Pearson maior ou igual a 0,99, portanto falhou.

Para separar um erro no porte de um erro na ligação das coordenadas, a tag
oficial `v.1.0.0` também foi executada diretamente sobre o mesmo cubo. Com o
ambiente moderno disponível, o código dos autores produziu MAE 0,158137 e
Pearson 0,145083 nas regiões candidatas. Ele encontrou 999 clusters depois do
filtro, 16 endmembers finais e score máximo de 0,397950 no mapa completo. Logo,
o mapa contém scores da escala publicada, mas as caixas candidatas não recuperam
as médias publicadas.

| ROI | µM | Publicado | Porte HyperMix | Código oficial direto |
|---:|---:|---:|---:|---:|
| 0 | 250 | 0,259676 | 0,017406 | 0,007528 |
| 1 | 100 | 0,212257 | 0,012184 | 0,009585 |
| 2 | 50 | 0,283760 | 0,011509 | 0,007149 |
| 3 | 25 | 0,295330 | 0,008376 | 0,010034 |
| 4 | 10 | 0,275457 | 0,020620 | 0,016236 |
| 5 | 5 | 0,130564 | 0,016482 | 0,020235 |
| 6 | 1 | 0,031396 | 0,008522 | 0,005601 |
| 7 | 0,1 | 0,008926 | 0,005225 | 0,004082 |
| 8 | 0 | 0,006820 | 0,014807 | 0,013139 |

## O que a falha localiza

O notebook `fig4fg.ipynb` lê
`manually_defined_rectangle_coordinates.json`, criado por cliques sobre a cena
completa. Esse JSON não acompanha o ZIP de 54 m nem o release de código. O ZIP
fornece outro arquivo de parâmetros com recortes, rotações e caixas locais. A
correspondência visual e a igualdade de nove regiões eram evidência plausível,
mas não provavam que essas caixas eram as mesmas usadas para calcular a Figura
4g. A porta de reprodução mostrou que essa ponte não está validada.

Também faltam `plates_col1_labels.csv` e `plates_col2_labels.csv`. A planilha
Source Data recupera os nove níveis e scores da primeira coluna, mas não contém
as coordenadas manuais no cubo.

A execução direta ainda não recria o ambiente histórico completo. O projeto
oficial fixa scikit-learn 1.3.0 e SciPy 1.8.0, incompatíveis com o NumPy 2 atual.
Isso pode alterar clusters e mapas, mas não explica sozinho por que o próprio
mapa direto alcança 0,398 enquanto todas as médias nas caixas candidatas ficam
abaixo de 0,021.

## Decisão

- Não mover caixas usando o mapa de score.
- Não testar MF, RX, matched subspace ou detector aprendido nessas regiões.
- Tratar `TL_POINTS_COORDS` e `BR_POINTS_COORDS` como geometria candidata do
  arquivo de parâmetros, não como coordenadas confirmadas da Figura 4g.
- Solicitar ou localizar o JSON manual, os CSVs de concentração e, se possível,
  o diretório de saída usado na figura.
- Reabrir T8c somente após validar a ponte por reprodução fora da amostra.

Artefatos: `results/real_target_reproduction.json`,
`results/real_target_official_source_audit.json`,
`scripts/reproduce_biohsi_54m.py` e
`scripts/audit_official_biohsi_source.py`. O JSON principal foi reproduzido duas
vezes com SHA-256
`a25651a108e8c593c39937b982b5899f196b4ed4a1e4188090bdf2058dd03ca2`.
