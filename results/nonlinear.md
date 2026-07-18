# Detector aprendido vs matched filter espacial sob mistura não-linear

AUC de detecção média em 3 cenas reais, target SNR de 5 e 0 dB, 3 seeds.
O detector é treinado no mesmo modelo de mistura em que é avaliado.

| Mistura | MF espacial | Detector aprendido | Vencedor |
|---------|:-----------:|:------------------:|----------|
| linear | 0.986 | 0.980 | spatial MF |
| bilinear | 0.990 | 0.994 | tie |
