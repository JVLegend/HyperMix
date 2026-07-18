# T7a: modelo auto-supervisionado do fundo

Avaliação transdutiva em Indian Pines, Salinas e Pavia University,
com alvo implantado, target SNR de 5 e 0 dB e 4 seeds por ponto.
O autoencoder espectral raso é treinado separadamente nos pixels não
rotulados de cada cena de teste. Ele não recebe máscara nem assinatura
do alvo durante o treino. Como os pixels são não rotulados, uma pequena
contaminação por alvos implantados pode estar presente na amostra.

Pd é medido em FAR = 1e-03. Intervalos de 95% usam 5000 réplicas hierárquicas: cenas são reamostradas e,
dentro de cada cena e SNR, seeds são reamostradas. Com apenas três cenas,
os intervalos descrevem este benchmark e não uma população ampla de sensores.

## Resultado agregado

| Método | AUC média [IC 95%] | Pd@FAR 1e-3 [IC 95%] |
|---|:---:|:---:|
| MF espacial | 0.987 [0.968, 0.997] | 0.650 [0.227, 0.872] |
| RX global | 0.539 [0.494, 0.593] | 0.001 [0.001, 0.002] |
| Autoencoder de fundo | 0.869 [0.776, 0.923] | 0.108 [0.003, 0.203] |
| Autoencoder de fundo espacial | 0.976 [0.945, 0.994] | 0.324 [0.087, 0.544] |

## Resultado por target SNR

| SNR | Método | AUC média [IC 95%] | Pd@FAR 1e-3 [IC 95%] |
|---:|---|:---:|:---:|
| 5 dB | MF espacial | 0.990 [0.977, 0.998] | 0.680 [0.298, 0.887] |
| 5 dB | RX global | 0.540 [0.492, 0.602] | 0.001 [0.001, 0.002] |
| 5 dB | Autoencoder de fundo | 0.882 [0.800, 0.932] | 0.112 [0.003, 0.214] |
| 5 dB | Autoencoder de fundo espacial | 0.980 [0.960, 0.994] | 0.310 [0.117, 0.511] |
| 0 dB | MF espacial | 0.984 [0.960, 0.997] | 0.619 [0.159, 0.866] |
| 0 dB | RX global | 0.537 [0.493, 0.588] | 0.001 [0.001, 0.002] |
| 0 dB | Autoencoder de fundo | 0.857 [0.752, 0.916] | 0.104 [0.003, 0.200] |
| 0 dB | Autoencoder de fundo espacial | 0.972 [0.931, 0.994] | 0.339 [0.053, 0.620] |

## Comparação causal pré-especificada

Diferença do autoencoder espacial menos o MF espacial:

- AUC: -0.011 [-0.023, -0.003]
- Pd@FAR 1e-3: -0.325 [-0.517, -0.142]

O critério de vantagem robusta não foi satisfeito: os intervalos de AUC
e Pd@FAR não ficaram ambos acima de zero. Este autoencoder simples não
sustenta uma vantagem causal do aprendizado sobre o MF espacial.

O RX é alvo-agnóstico. O score do autoencoder combina o quantil do MF com
um gate fixo baseado no quantil do erro de reconstrução, com peso 0,5.
Nenhum hiperparâmetro foi escolhido usando rótulos deste experimento.
Isto continua sendo alvo implantado em fundos reais, não detecção remota de
expressão biológica naturalmente observada.
