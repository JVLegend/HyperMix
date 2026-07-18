# Detector aprendido vs matched filter espacial sob mistura não-linear

AUC de detecção média em 3 cenas reais, target SNR de 5 e 0 dB, 3 seeds.
O detector é treinado no mesmo modelo de mistura em que é avaliado.
A mistura bilinear usa gamma = 0,5. Os arquivos MAT não contêm centros de
banda, então este teste mantém o alvo aproximado por índice espectral e não
é o benchmark calibrado em comprimento de onda de `realism.md`.

| Mistura | MF espacial | Detector aprendido | Vencedor |
|---------|:-----------:|:------------------:|----------|
| linear | 0.986 | 0.980 | spatial MF |
| bilinear | 0.989 | 0.992 | tie |
