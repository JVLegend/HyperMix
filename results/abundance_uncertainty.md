# T12: abundância calibrada e intervalos

O unmixer é treinado em simulação. A escala afim, o raio conformal e a
avaliação usam implantes e seeds disjuntos. Cada cena-seed tem peso igual
na calibração e é a unidade do bootstrap. A análise é condicional aos
pixels com abundância maior que 0.02.

## Resultado agregado

| Método | MAE [IC 95%] | Viés [IC 95%] | Cobertura 90% [IC 95%] | Largura [IC 95%] |
|---|:---:|:---:|:---:|:---:|
| MF calibrado | 0.0110 [0.0093, 0.0129] | 0.0018 [0.0000, 0.0035] | 0.971 [0.953, 0.988] | 0.0719 [0.0714, 0.0723] |
| Unmixer calibrado | 0.0136 [0.0116, 0.0158] | 0.0035 [-0.0015, 0.0086] | 0.987 [0.975, 0.995] | 0.0815 [0.0807, 0.0822] |

## Diferença pareada, unmixer menos MF

| Métrica | Diferença [IC 95%] |
|---|:---:|
| MAE | 0.0026 [-0.0006, 0.0059] |
| Viés absoluto | 0.0064 [0.0032, 0.0096] |
| Cobertura | 0.016 [-0.005, 0.037] |
| Largura | 0.0096 [0.0090, 0.0102] |

## Por cena

| Cena | Método | MAE | Viés | Cobertura | Largura |
|---|---|---:|---:|---:|---:|
| indian_pines | MF calibrado | 0.0084 | -0.0036 | 0.999 | 0.0720 |
| indian_pines | Unmixer calibrado | 0.0120 | -0.0098 | 0.975 | 0.0798 |
| salinas | MF calibrado | 0.0075 | 0.0038 | 1.000 | 0.0730 |
| salinas | Unmixer calibrado | 0.0187 | 0.0186 | 0.995 | 0.0838 |
| paviaU | MF calibrado | 0.0171 | 0.0053 | 0.915 | 0.0705 |
| paviaU | Unmixer calibrado | 0.0101 | 0.0015 | 0.992 | 0.0807 |

## Critério pré-especificado

Vitória pontual exige que o IC bootstrap pareado de 95% para MAE do unmixer menos MF fique abaixo de zero. Vitória em eficiência dos intervalos exige também cobertura média de pelo menos 0,90 nos dois métodos e IC de 95% da diferença de largura abaixo de zero.

Resultado codificado: `no_calibrated_abundance_advantage`.

## Limitações

- Os intervalos são condicionais a pixels já declarados como alvo. Isto
  não inclui a incerteza de errar a detecção.
- Calibração e avaliação usam implantes diferentes nos mesmos três fundos
  reais. Não há validação em uma nova população de sensores.
- A abundância é fração do simulador, não concentração biológica.
- O raio é constante e deliberadamente conservador. Pixels dentro de uma
  cena são correlacionados, por isso a calibração ocorre em dois níveis:
  quantil dentro do caso e quantil entre casos.
- O unmixer usa features derivados de MF e ACE. Uma vantagem quantitativa
  não altera o veredito de detecção do benchmark.
