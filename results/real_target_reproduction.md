# Reprodução bioHSI de 54 m

Gerada pelo script versionado. Esta é uma reprodução do método publicado, não
um resultado de superioridade do HyperMix.

## Veredito

A porta de reprodução foi **não satisfeita**: MAE 0.156114
(limite ≤ 0.01) e Pearson 0.375901
(limite ≥ 0.99). A reprodução não cruzou a porta pré-especificada. O confronto T8c permanece pausado até a divergência ser explicada.

## Scores regionais

| ROI | Concentração, µM | Publicado | Reproduzido | Erro absoluto |
|---:|---:|---:|---:|---:|
| 0 | 250 | 0.259676152 | 0.017406489 | 0.242269663 |
| 1 | 100 | 0.212257450 | 0.012183682 | 0.200073769 |
| 2 | 50 | 0.283760350 | 0.011508988 | 0.272251362 |
| 3 | 25 | 0.295329539 | 0.008376000 | 0.286953539 |
| 4 | 10 | 0.275457456 | 0.020619532 | 0.254837924 |
| 5 | 5 | 0.130564360 | 0.016482082 | 0.114082278 |
| 6 | 1 | 0.031395625 | 0.008521667 | 0.022873957 |
| 7 | 0.1 | 0.008925867 | 0.005225374 | 0.003700493 |
| 8 | 0 | 0.006820293 | 0.014807117 | 0.007986825 |

## Diagnósticos

- Spearman reproduzido versus publicado: 0.100000
- AUC regional reproduzida no limiar ≥ 5 µM: 0.777778
- Spearman entre score reproduzido e concentração: 0.283333
- Contraste médio positivo menos negativo: 0.004911
- Clusters iniciais, retidos e finais: 1000, 999 e 15

## Limites de reprodução

O código oficial fixa scikit-learn 1.3.0 e SciPy 1.8.0. Essas versões não são
compatíveis com o NumPy 2 do ambiente atual. A implementação HyperMix fixa
explicitamente o comportamento histórico do MiniBatchKMeans (`n_init=3`) e
registra abaixo as versões modernas efetivamente usadas. Uma divergência não
deve ser explicada automaticamente por essa diferença sem teste adicional.

As nove caixas são unidades regionais. Não há máscara pixel a pixel nem réplica
biológica por concentração, portanto este arquivo não reporta Pd@FAR nem
intervalo de confiança populacional.

## Ambiente

- Python: 3.11.15
- NumPy: 2.4.6
- SciPy: 1.17.1
- scikit-learn: 1.9.0
- Plataforma: macOS-26.5.2-arm64-arm-64bit
- Código oficial de referência: tag `v.1.0.0`, commit `935e501cf24e28fd77b40c9d111f8e827bd1812c`
