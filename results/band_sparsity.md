# T7c: esparsidade de banda

As bandas são ordenadas separadamente em cada cubo real não implantado
pelo valor absoluto do vetor do matched filter completo,
`|C^-1 (t - mu)|`. A ordem usa o alvo conhecido e estatísticas não rotuladas
da cena, mas não usa máscaras implantadas nem AUC. Para cada k, o MF é
recalculado apenas nas bandas selecionadas.

O protocolo usa Indian Pines, Salinas e Pavia University, target SNR de
5 e 0 dB e 4 seeds por ponto. Os IC 95% usam 5000 réplicas hierárquicas
sobre cenas e seeds. O MF espacial com sigma 1,5 é a análise primária.

## AUC versus número de bandas

| Top-k | MF espectral [IC 95%] | MF espacial [IC 95%] |
|---:|:---:|:---:|
| 1 | 0.696 [0.555, 0.776] | 0.838 [0.566, 0.984] |
| 2 | 0.789 [0.705, 0.837] | 0.949 [0.867, 0.993] |
| 3 | 0.811 [0.714, 0.868] | 0.948 [0.870, 0.993] |
| 5 | 0.842 [0.741, 0.899] | 0.963 [0.903, 0.997] |
| 10 | 0.871 [0.758, 0.933] | 0.969 [0.921, 0.999] |
| 20 | 0.898 [0.788, 0.962] | 0.983 [0.954, 0.999] |
| 40 | 0.916 [0.813, 0.975] | 0.986 [0.963, 0.999] |
| 80 | 0.925 [0.822, 0.981] | 0.987 [0.964, 0.999] |
| all | 0.921 [0.822, 0.976] | 0.984 [0.964, 0.997] |

## MF espacial por target SNR

| Top-k | 5 dB [IC 95%] | 0 dB [IC 95%] |
|---:|:---:|:---:|
| 1 | 0.849 [0.578, 0.993] | 0.827 [0.550, 0.974] |
| 2 | 0.957 [0.878, 0.997] | 0.941 [0.852, 0.989] |
| 3 | 0.956 [0.881, 0.996] | 0.941 [0.856, 0.989] |
| 5 | 0.972 [0.923, 0.999] | 0.955 [0.881, 0.995] |
| 10 | 0.979 [0.946, 0.999] | 0.959 [0.894, 0.999] |
| 20 | 0.989 [0.970, 0.999] | 0.977 [0.935, 0.999] |
| 40 | 0.991 [0.976, 0.999] | 0.981 [0.946, 0.999] |
| 80 | 0.991 [0.975, 0.999] | 0.982 [0.950, 0.999] |
| all | 0.988 [0.975, 0.997] | 0.979 [0.950, 0.998] |

## Concentração dos coeficientes

| Cena | Bandas totais | k para 50% | k para 80% | k para 90% | Peso absoluto nas top-3 |
|---|---:|---:|---:|---:|---:|
| indian_pines | 200 | 24 | 56 | 74 | 0.098 |
| salinas | 204 | 23 | 59 | 87 | 0.134 |
| paviaU | 103 | 15 | 37 | 53 | 0.161 |

## Leitura

Diferença pareada top-3 menos todas as bandas:

- MF espectral: -0.110 [-0.119, -0.101]
- MF espacial: -0.036 [-0.092, -0.000]

O menor k cuja AUC espacial média ficou a até 0,005 do MF completo foi `20`.
Esse limiar é descritivo e não substitui o IC da diferença top-3 menos all.

O estudo `One Channel Is All You Need` motiva a pergunta, mas avalia
classificação de culturas na competição ICPR 2024. Ele foi publicado nos
anais do ICAISC e não estabelece que três bandas bastem para a detecção
de alvos implantados do HyperMix. Os resultados aqui são específicos a
bacterioclorofila-a sintética e a esta regra target-aware de seleção.

Referência: [One Channel Is All You Need](https://doi.org/10.1007/978-3-032-03705-3_4),
estudo baseado na competição ICPR 2024 e publicado nos anais do ICAISC.
