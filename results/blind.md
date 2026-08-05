# T10: detecção sem assinatura exata do alvo

Avaliação leave-one-host-out nas três cenas reais do benchmark com alvo
implantado. E. coli é avaliado usando somente P. putida como família
permitida, e vice-versa. O alvo retido aparece apenas na implantação e
no teto oracle. A curva biliverdina canônica não é usada porque contém a
média dos dois hosts e vazaria informação do alvo retido.

A família permitida contém nove perturbações fixas do outro host: três
deslocamentos de uma banda combinados com três inclinações de 3%. O método
cego não recebe alvo nem família. Os MLPs são treinados só em simulação
com fundos medidos do USGS. A avaliação usa target SNR 5 e 0 dB, quatro
seeds e amostragem espacial em lattice fixo de até 96 pontos por eixo,
definida sem consultar rótulos.

Pd é medido em FAR = 1e-03. Intervalos de 95% usam
5000 réplicas hierárquicas, reamostrando cenas, alvos
retidos e seeds dentro de cada SNR. Há somente dois espectros medidos da
família biliverdina, portanto este é um teste pequeno, não uma estimativa
ampla de generalização entre famílias químicas.
Os arquivos MAT não incluem centros de banda. Como nos experimentos
implantados anteriores, as curvas medidas usam a grade de conveniência
linear de 400 a 1000 nm; isto não é calibração espectral do sensor.

## Resultado agregado

| Regime | Método | AUC média [IC 95%] | Pd@FAR 1e-3 [IC 95%] |
|---|---|:---:|:---:|
| oracle | MF espacial, alvo exato, teto oracle | 0.984 [0.960, 0.998] | 0.562 [0.105, 0.810] |
| family | MF espacial, centroide da família | 0.983 [0.956, 0.998] | 0.556 [0.091, 0.808] |
| family | Subespaço espacial da família | 0.903 [0.803, 0.993] | 0.396 [0.039, 0.693] |
| family | MLP, família sem alvo retido | 0.970 [0.924, 0.998] | 0.514 [0.036, 0.783] |
| unknown | RX espacial, sem alvo | 0.511 [0.399, 0.632] | 0.000 [0.000, 0.002] |
| unknown | MLP cego, sem alvo | 0.503 [0.405, 0.607] | 0.000 [0.000, 0.001] |

## Distância ao teto oracle

Valores positivos indicam quanto desempenho foi perdido ao retirar o
espectro exato. O oracle não participa da seleção de método.

| Método operável | Oracle menos método, AUC [IC 95%] | Oracle menos método, Pd [IC 95%] |
|---|:---:|:---:|
| MF espacial, centroide da família | 0.001 [-0.000, 0.005] | 0.006 [-0.000, 0.015] |
| Subespaço espacial da família | 0.082 [0.005, 0.157] | 0.166 [0.058, 0.340] |
| MLP, família sem alvo retido | 0.015 [0.000, 0.037] | 0.048 [0.008, 0.092] |
| RX espacial, sem alvo | 0.474 [0.366, 0.565] | 0.562 [0.104, 0.810] |
| MLP cego, sem alvo | 0.481 [0.390, 0.564] | 0.562 [0.104, 0.810] |

## Resultado por target SNR

| SNR | Método | AUC média [IC 95%] | Pd@FAR 1e-3 [IC 95%] |
|---:|---|:---:|:---:|
| 5 dB | MF espacial, alvo exato, teto oracle | 0.988 [0.971, 0.999] | 0.582 [0.128, 0.836] |
| 5 dB | MF espacial, centroide da família | 0.987 [0.967, 0.999] | 0.577 [0.111, 0.834] |
| 5 dB | Subespaço espacial da família | 0.917 [0.841, 0.996] | 0.433 [0.058, 0.747] |
| 5 dB | MLP, família sem alvo retido | 0.976 [0.942, 0.999] | 0.546 [0.053, 0.825] |
| 5 dB | RX espacial, sem alvo | 0.509 [0.390, 0.645] | 0.000 [0.000, 0.002] |
| 5 dB | MLP cego, sem alvo | 0.499 [0.394, 0.618] | 0.000 [0.000, 0.002] |
| 0 dB | MF espacial, alvo exato, teto oracle | 0.981 [0.953, 0.997] | 0.542 [0.099, 0.794] |
| 0 dB | MF espacial, centroide da família | 0.979 [0.948, 0.997] | 0.535 [0.085, 0.789] |
| 0 dB | Subespaço espacial da família | 0.889 [0.779, 0.991] | 0.359 [0.027, 0.644] |
| 0 dB | MLP, família sem alvo retido | 0.963 [0.911, 0.997] | 0.483 [0.026, 0.747] |
| 0 dB | RX espacial, sem alvo | 0.513 [0.412, 0.622] | 0.001 [0.000, 0.003] |
| 0 dB | MLP cego, sem alvo | 0.508 [0.417, 0.602] | 0.000 [0.000, 0.002] |

## Critério causal congelado para o artefato final

A primeira execução funcionou como auditoria piloto e mostrou que o MF
do centroide era mais forte que o subespaço. Antes de congelar o JSON
final, o critério foi endurecido para usar esse melhor baseline clássico.
A comparação com subespaço foi mantida apenas como diagnóstico.

Cada modelo aprendido é comparado somente ao baseline clássico com a
mesma informação. Vantagem exige que os ICs de AUC e Pd estejam ambos
acima de zero.

MLP família menos MF do centroide da família:

- AUC: -0.014 [-0.033, -0.000]
- Pd@FAR 1e-3: -0.042 [-0.086, -0.004]

Diagnóstico secundário, MLP família menos subespaço da família:

- AUC: 0.067 [0.005, 0.120]
- Pd@FAR 1e-3: 0.118 [-0.003, 0.275]

MLP cego menos RX espacial:

- AUC: -0.007 [-0.026, 0.012]
- Pd@FAR 1e-3: -0.000 [-0.000, 0.000]

Nenhum regime aprendido satisfez o critério nos dois desfechos. Este
teste não estabelece vantagem causal do aprendizado quando a assinatura
exata é retirada.

O oracle não participa do teste de superioridade. Ele apenas quantifica o
custo de não conhecer a assinatura exata. Alvos implantados em fundos reais
não equivalem à detecção remota de expressão biológica naturalmente observada.
