# Robustez a mismatch espectral

A assinatura implantada é mantida fixa. Apenas a assinatura fornecida ao
detector é deslocada no eixo normalizado de índices de bandas. Resultados
com target SNR de 5 dB, 3 cenas reais e 3 seeds por cena.
A queda de AUC é relativa ao alvo exato do mesmo método.

| Método | Deslocamento | AUC média | Queda de AUC |
|--------|-------------:|:---------:|:------------:|
| Matched filter | 0.0% | 0.940 | 0.000 |
| Matched filter (spatial) | 0.0% | 0.990 | 0.000 |
| Detector aprendido (HyperMix) | 0.0% | 0.987 | 0.000 |
| Matched filter | 1.0% | 0.899 | 0.041 |
| Matched filter (spatial) | 1.0% | 0.983 | 0.007 |
| Detector aprendido (HyperMix) | 1.0% | 0.973 | 0.014 |
| Matched filter | 2.5% | 0.781 | 0.159 |
| Matched filter (spatial) | 2.5% | 0.920 | 0.070 |
| Detector aprendido (HyperMix) | 2.5% | 0.907 | 0.080 |
| Matched filter | 5.0% | 0.647 | 0.293 |
| Matched filter (spatial) | 5.0% | 0.730 | 0.260 |
| Detector aprendido (HyperMix) | 5.0% | 0.710 | 0.277 |

O deslocamento é expresso como fração da faixa de índices, não em
nanômetros, porque os cubos não compartilham a mesma grade espectral.
Reproduza com `python scripts/run_mismatch_experiment.py`.
