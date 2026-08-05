# T11: limite operacional de detecção

Este experimento estima a menor abundância máxima testada que mantém
Pd maior ou igual a 0.80 em todos os níveis superiores.
O LOD nominal usa a média de 12 seeds. O LOD conservador exige que o
limite inferior do IC de 95% também alcance a meta. Não há interpolação
entre pontos da grade.

O ruído é absoluto e fixo por sensor. Ele é calibrado para target SNR
5 dB em 15% de
abundância e não diminui quando a abundância do teste cai. Thresholds
são ajustados em oito cenas sem alvo e avaliados em 12 seeds diferentes.
A regra final usa o maior threshold entre as cenas de calibração, não o
quantil agrupado. Uma auditoria piloto rejeitou o quantil agrupado porque
ele excedeu o FAR em cinco dos seis cenários de validação.
O MF espacial recebe o alvo exato no sensor; portanto os LODs são um teto
algorítmico condicionado a este detector, não garantia de campo.

## LOD por sensor e orçamento de falso-alarme

| FWHM | FAR alvo | FAR obtido [IC 95%] | Budget válido | LOD nominal | LOD conservador |
|---:|---:|:---:|:---:|:---:|:---:|
| 8 nm | 1e-02 | 0.00680 [0.00485, 0.00873] | sim | 15.0% | 20.0% |
| 8 nm | 1e-03 | 0.00037 [0.00010, 0.00076] | sim | > 20.0% ou não validado | > 20.0% ou não validado |
| 12 nm | 1e-02 | 0.00637 [0.00444, 0.00870] | sim | 15.0% | 20.0% |
| 12 nm | 1e-03 | 0.00029 [0.00000, 0.00061] | sim | > 20.0% ou não validado | > 20.0% ou não validado |
| 20 nm | 1e-02 | 0.00285 [0.00124, 0.00484] | sim | 20.0% | > 20.0% ou não validado |
| 20 nm | 1e-03 | 0.00011 [0.00000, 0.00034] | sim | > 20.0% ou não validado | > 20.0% ou não validado |

## Curvas de Pd

| FWHM | FAR | Abundância | Pd média [IC 95%] | AUC [IC 95%] |
|---:|---:|---:|:---:|:---:|
| 8 nm | 1e-02 | 1.0% | 0.036 [0.017, 0.061] | 0.657 [0.614, 0.695] |
| 8 nm | 1e-02 | 2.0% | 0.090 [0.056, 0.133] | 0.793 [0.754, 0.828] |
| 8 nm | 1e-02 | 3.0% | 0.186 [0.138, 0.234] | 0.873 [0.844, 0.900] |
| 8 nm | 1e-02 | 5.0% | 0.392 [0.321, 0.466] | 0.949 [0.933, 0.963] |
| 8 nm | 1e-02 | 7.5% | 0.585 [0.489, 0.673] | 0.980 [0.972, 0.986] |
| 8 nm | 1e-02 | 10.0% | 0.714 [0.611, 0.808] | 0.989 [0.985, 0.993] |
| 8 nm | 1e-02 | 15.0% | 0.844 [0.752, 0.925] | 0.995 [0.993, 0.997] |
| 8 nm | 1e-02 | 20.0% | 0.893 [0.811, 0.964] | 0.997 [0.995, 0.998] |
| 8 nm | 1e-03 | 1.0% | 0.004 [0.001, 0.009] | 0.657 [0.614, 0.695] |
| 8 nm | 1e-03 | 2.0% | 0.023 [0.006, 0.046] | 0.793 [0.754, 0.828] |
| 8 nm | 1e-03 | 3.0% | 0.061 [0.029, 0.102] | 0.873 [0.844, 0.900] |
| 8 nm | 1e-03 | 5.0% | 0.218 [0.156, 0.285] | 0.949 [0.933, 0.963] |
| 8 nm | 1e-03 | 7.5% | 0.387 [0.304, 0.471] | 0.980 [0.972, 0.986] |
| 8 nm | 1e-03 | 10.0% | 0.523 [0.421, 0.622] | 0.989 [0.985, 0.993] |
| 8 nm | 1e-03 | 15.0% | 0.691 [0.569, 0.805] | 0.995 [0.993, 0.997] |
| 8 nm | 1e-03 | 20.0% | 0.772 [0.647, 0.885] | 0.997 [0.995, 0.998] |
| 12 nm | 1e-02 | 1.0% | 0.029 [0.014, 0.048] | 0.654 [0.613, 0.689] |
| 12 nm | 1e-02 | 2.0% | 0.082 [0.053, 0.117] | 0.787 [0.750, 0.821] |
| 12 nm | 1e-02 | 3.0% | 0.186 [0.142, 0.229] | 0.868 [0.839, 0.895] |
| 12 nm | 1e-02 | 5.0% | 0.403 [0.335, 0.470] | 0.946 [0.929, 0.961] |
| 12 nm | 1e-02 | 7.5% | 0.591 [0.502, 0.677] | 0.978 [0.970, 0.986] |
| 12 nm | 1e-02 | 10.0% | 0.715 [0.620, 0.806] | 0.989 [0.984, 0.993] |
| 12 nm | 1e-02 | 15.0% | 0.846 [0.758, 0.927] | 0.995 [0.992, 0.997] |
| 12 nm | 1e-02 | 20.0% | 0.897 [0.821, 0.964] | 0.996 [0.995, 0.998] |
| 12 nm | 1e-03 | 1.0% | 0.003 [0.000, 0.006] | 0.654 [0.613, 0.689] |
| 12 nm | 1e-03 | 2.0% | 0.015 [0.003, 0.031] | 0.787 [0.750, 0.821] |
| 12 nm | 1e-03 | 3.0% | 0.042 [0.018, 0.071] | 0.868 [0.839, 0.895] |
| 12 nm | 1e-03 | 5.0% | 0.200 [0.147, 0.256] | 0.946 [0.929, 0.961] |
| 12 nm | 1e-03 | 7.5% | 0.382 [0.300, 0.467] | 0.978 [0.970, 0.986] |
| 12 nm | 1e-03 | 10.0% | 0.514 [0.414, 0.614] | 0.989 [0.984, 0.993] |
| 12 nm | 1e-03 | 15.0% | 0.681 [0.561, 0.795] | 0.995 [0.992, 0.997] |
| 12 nm | 1e-03 | 20.0% | 0.763 [0.643, 0.876] | 0.996 [0.995, 0.998] |
| 20 nm | 1e-02 | 1.0% | 0.015 [0.005, 0.027] | 0.650 [0.603, 0.692] |
| 20 nm | 1e-02 | 2.0% | 0.045 [0.021, 0.075] | 0.782 [0.738, 0.819] |
| 20 nm | 1e-02 | 3.0% | 0.117 [0.079, 0.159] | 0.864 [0.830, 0.894] |
| 20 nm | 1e-02 | 5.0% | 0.304 [0.235, 0.376] | 0.945 [0.928, 0.960] |
| 20 nm | 1e-02 | 7.5% | 0.492 [0.408, 0.574] | 0.979 [0.970, 0.986] |
| 20 nm | 1e-02 | 10.0% | 0.627 [0.531, 0.719] | 0.989 [0.984, 0.993] |
| 20 nm | 1e-02 | 15.0% | 0.785 [0.683, 0.880] | 0.995 [0.993, 0.997] |
| 20 nm | 1e-02 | 20.0% | 0.858 [0.763, 0.943] | 0.997 [0.995, 0.998] |
| 20 nm | 1e-03 | 1.0% | 0.001 [0.000, 0.002] | 0.650 [0.603, 0.692] |
| 20 nm | 1e-03 | 2.0% | 0.004 [0.000, 0.010] | 0.782 [0.738, 0.819] |
| 20 nm | 1e-03 | 3.0% | 0.016 [0.003, 0.032] | 0.864 [0.830, 0.894] |
| 20 nm | 1e-03 | 5.0% | 0.091 [0.054, 0.133] | 0.945 [0.928, 0.960] |
| 20 nm | 1e-03 | 7.5% | 0.241 [0.174, 0.313] | 0.979 [0.970, 0.986] |
| 20 nm | 1e-03 | 10.0% | 0.361 [0.275, 0.448] | 0.989 [0.984, 0.993] |
| 20 nm | 1e-03 | 15.0% | 0.539 [0.423, 0.652] | 0.995 [0.993, 0.997] |
| 20 nm | 1e-03 | 20.0% | 0.649 [0.516, 0.774] | 0.997 [0.995, 0.998] |

## Limites de interpretação

- O resultado usa espectros medidos, fundos USGS simulados, atmosfera
  simples, mistura linear e alvos implantados como blobs.
- A abundância máxima do blob é um parâmetro do simulador, não uma
  concentração biológica diretamente mensurada.
- FWHM isolado não representa todos os efeitos de um sensor. Ruído, PSF,
  amostragem e calibração também afetam o LOD real.
- Se o FAR médio de validação exceder o orçamento, o LOD correspondente
  é reportado como não validado mesmo que a curva de Pd cruze 0,80.
