# Avaliação de abundância

Target SNR de 10 dB, média de 3 seeds. Pixels de alvo usam abundância > 0.02.
Predições são limitadas ao intervalo físico [0, 1] antes da MAE.

| Cena | MF target r | Unmixer target r | MF target MAE | Unmixer target MAE | Unmixer MAE, todos os pixels |
|------|:-----------:|:----------------:|:-------------:|:------------------:|:-----------------------------:|
| indian_pines | 0.966 | 0.982 | 0.0142 | 0.0081 | 0.0029 |
| salinas | 0.979 | 0.988 | 0.0073 | 0.0237 | 0.0040 |
| paviaU | 0.796 | 0.938 | 0.0177 | 0.0093 | 0.0054 |

Pearson r e target MAE excluem os zeros de fundo. A MAE em todos os pixels
é apresentada apenas como diagnóstico secundário.
