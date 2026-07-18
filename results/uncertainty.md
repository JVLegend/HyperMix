# T7b: incerteza calibrada

O experimento separa calibração e avaliação por implante. Em cada cena e
target SNR, os seeds 100 e 101 ajustam os calibradores; os seeds 0 a 3
são usados apenas nas métricas. O treino do detector continua restrito a
fundos simulados. Nenhum rótulo de avaliação ajusta rede ou calibrador.

NLL e Brier são médias pixel-wise sem balanceamento em cada caso; o
agregado dá o mesmo peso a cada combinação de cena, SNR e seed. A ECE usa
15 bins uniformes fixos. Os IC 95% usam 5000 réplicas hierárquicas sobre cenas e seeds.
AUC e Pd@FAR são referências de detecção calculadas nos scores antes da
calibração. Com apenas três cenas, os IC descrevem este benchmark.

## Resultado agregado

| Método | NLL [IC 95%] | Brier [IC 95%] | ECE [IC 95%] | AUC [IC 95%] | Pd@FAR 1e-3 [IC 95%] |
|---|:---:|:---:|:---:|:---:|:---:|
| MF + Platt | 0.12953 [0.05716, 0.23007] | 0.03477 [0.01424, 0.06252] | 0.01581 [0.00950, 0.02486] | 0.926 [0.818, 0.984] | 0.471 [0.047, 0.695] |
| MF espacial + Platt | 0.05766 [0.01935, 0.12004] | 0.01540 [0.00517, 0.03152] | 0.00896 [0.00441, 0.01532] | 0.986 [0.963, 0.999] | 0.687 [0.304, 0.896] |
| Aprendido + temperatura | 0.07169 [0.02790, 0.14910] | 0.01968 [0.00770, 0.04008] | 0.01291 [0.00909, 0.01814] | 0.977 [0.936, 0.999] | 0.651 [0.214, 0.885] |
| Ensemble aprendido + temperatura | 0.06792 [0.02710, 0.13866] | 0.01940 [0.00760, 0.03944] | 0.01293 [0.00906, 0.01837] | 0.980 [0.946, 0.999] | 0.630 [0.156, 0.888] |

## Resultado por target SNR

| SNR | Método | NLL [IC 95%] | Brier [IC 95%] | ECE [IC 95%] |
|---:|---|:---:|:---:|:---:|
| 5 dB | MF + Platt | 0.11299 [0.04287, 0.21639] | 0.03032 [0.01089, 0.05847] | 0.01521 [0.00523, 0.02984] |
| 5 dB | MF espacial + Platt | 0.05039 [0.01650, 0.10690] | 0.01339 [0.00472, 0.02755] | 0.00894 [0.00283, 0.01670] |
| 5 dB | Aprendido + temperatura | 0.05906 [0.02160, 0.12035] | 0.01632 [0.00612, 0.03189] | 0.01168 [0.00618, 0.01644] |
| 5 dB | Ensemble aprendido + temperatura | 0.05583 [0.02084, 0.11124] | 0.01613 [0.00602, 0.03132] | 0.01147 [0.00613, 0.01595] |
| 0 dB | MF + Platt | 0.14608 [0.07190, 0.24880] | 0.03922 [0.01779, 0.06826] | 0.01641 [0.01272, 0.02135] |
| 0 dB | MF espacial + Platt | 0.06494 [0.02220, 0.13560] | 0.01740 [0.00582, 0.03619] | 0.00898 [0.00541, 0.01462] |
| 0 dB | Aprendido + temperatura | 0.08432 [0.03253, 0.17996] | 0.02304 [0.00899, 0.04899] | 0.01413 [0.00749, 0.02146] |
| 0 dB | Ensemble aprendido + temperatura | 0.08001 [0.03177, 0.16816] | 0.02268 [0.00889, 0.04817] | 0.01440 [0.00751, 0.02208] |

## Critério pré-especificado

Diferença pareada do ensemble aprendido menos MF espacial, ambos calibrados:

- NLL: 0.01026 [0.00448, 0.01778]
- Brier: 0.00401 [0.00166, 0.00766]
- ECE: 0.00397 [0.00208, 0.00560]
- AUC: -0.006 [-0.015, 0.000]
- Pd@FAR 1e-3: -0.056 [-0.140, -0.005]

O critério não foi satisfeito: NLL e ECE não tiveram simultaneamente
IC favoráveis ao ensemble. O aprendizado não demonstrou vantagem robusta
de incerteza calibrada neste protocolo.

Platt e temperature scaling têm dois parâmetros de calibração. A correção
de intercepto no temperature scaling é necessária porque a rede foi treinada
com perda ponderada, cujo intercepto bruto não representa a prevalência de
implantação. Os diagramas estão em `assets/reliability_uncertainty.png`.

A motivação de Ariel vem da Gaussian Log-Likelihood do desafio, mas este
experimento binário não reproduz a tarefa de recuperação de parâmetros
atmosféricos do Ariel Data Challenge.

Referência: [Ariel Data Challenge: exoplanet atmospheric spectra
reconstruction](https://arxiv.org/abs/2505.08940).
