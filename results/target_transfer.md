# T9: transferência física da assinatura laboratório-sensor

Experimento sintético calibrado em comprimento de onda, com espectro
laboratorial medido do bioHSI, fundos medidos do USGS, mistura bilinear,
três larguras de resposta espectral, cinco atmosferas por seed e target
SNR de 10, 5 e 0 dB. São 45 casos pareados por método.

A família física usa apenas o FWHM declarado do sensor e uma grade fixa
de atmosfera e deslocamento espectral. Nenhum rótulo, máscara ou score
de avaliação seleciona seus parâmetros.

Pd é medido em FAR = 1e-03. Intervalos de 95% usam
4000 réplicas hierárquicas, reamostrando larguras de
sensor e depois seeds dentro de cada largura e SNR.

## Resultado agregado

| Método | AUC média [IC 95%] | Pd@FAR 1e-3 [IC 95%] | Distância AUC ao oráculo |
|---|:---:|:---:|:---:|
| MF espacial, alvo laboratorial | 0.968 [0.962, 0.974] | 0.626 [0.587, 0.672] | 0.024 [0.018, 0.030] |
| MF espacial, transferência nominal | 0.990 [0.988, 0.992] | 0.760 [0.727, 0.787] | 0.002 [0.001, 0.005] |
| Subespaço espacial, família física | 0.777 [0.749, 0.799] | 0.369 [0.340, 0.394] | 0.215 [0.193, 0.244] |
| MF espacial, alvo oráculo | 0.992 [0.991, 0.994] | 0.778 [0.744, 0.805] | 0,000 por definição |

## Resultado por target SNR

| SNR | Método | AUC média [IC 95%] | Pd@FAR 1e-3 [IC 95%] |
|---:|---|:---:|:---:|
| 10 dB | MF espacial, alvo laboratorial | 0.937 [0.922, 0.954] | 0.461 [0.392, 0.546] |
| 10 dB | MF espacial, transferência nominal | 0.987 [0.980, 0.991] | 0.742 [0.708, 0.777] |
| 10 dB | Subespaço espacial, família física | 0.778 [0.737, 0.812] | 0.379 [0.335, 0.418] |
| 10 dB | MF espacial, alvo oráculo | 0.992 [0.990, 0.994] | 0.771 [0.733, 0.804] |
| 5 dB | MF espacial, alvo laboratorial | 0.978 [0.971, 0.984] | 0.667 [0.619, 0.724] |
| 5 dB | MF espacial, transferência nominal | 0.991 [0.990, 0.993] | 0.769 [0.737, 0.798] |
| 5 dB | Subespaço espacial, família física | 0.779 [0.739, 0.814] | 0.376 [0.333, 0.414] |
| 5 dB | MF espacial, alvo oráculo | 0.993 [0.991, 0.995] | 0.784 [0.744, 0.816] |
| 0 dB | MF espacial, alvo laboratorial | 0.989 [0.985, 0.993] | 0.752 [0.712, 0.790] |
| 0 dB | MF espacial, transferência nominal | 0.992 [0.990, 0.993] | 0.770 [0.724, 0.806] |
| 0 dB | Subespaço espacial, família física | 0.775 [0.734, 0.809] | 0.353 [0.311, 0.392] |
| 0 dB | MF espacial, alvo oráculo | 0.992 [0.991, 0.994] | 0.780 [0.733, 0.816] |

## Critério pré-especificado

Diferença da família física menos o alvo laboratorial:

- AUC: -0.191 [-0.217, -0.171]
- Pd@FAR 1e-3: -0.257 [-0.293, -0.221]

O critério de vantagem robusta não foi satisfeito: os intervalos de
AUC e Pd@FAR não ficaram ambos acima de zero. A família física testada
não fecha de forma robusta o gap laboratório-sensor.

## Análise secundária

A transferência nominal era um método declarado no protocolo, mas não era
o método do critério primário de significância. Sua diferença contra o
alvo laboratorial foi:

- AUC: 0.022 [0.016, 0.028]
- Pd@FAR 1e-3: 0.134 [0.097, 0.169]

Os dois intervalos ficaram acima de zero. Descritivamente, o alvo nominal
transferido por metadados quase alcançou o oráculo, enquanto ampliar essa
assinatura para um subespaço de nove variantes introduziu direções que
degradaram a detecção. Este contraste motiva validação independente, não
uma troca retroativa do critério primário.

O alvo oráculo conhece exatamente a transformação usada para gerar cada
cena e serve apenas como teto. O experimento usa alvos implantados e não
substitui o T8 sobre expressão biológica realmente medida.
