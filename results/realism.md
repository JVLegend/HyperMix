# Sensibilidade aos componentes de realismo da Fase B

AUC média em target SNR de 20, 10, 5 e 0 dB, com 5 seeds por ponto.
O alvo oráculo é o espectro exato observado pelo sensor. O alvo laboratorial
é a curva antes da SRF e da atmosfera, portanto mede mismatch de implantação.
O benchmark usa uma grade simulada calibrada em comprimento de onda; os MAT
reais atuais não incluem os centros de banda necessários para esta transformação.

| Cenário | MF | MF espacial | ACE | SAM | MF espacial lab | MF espacial a 0 dB |
|---------|:--:|:-----------:|:---:|:---:|:----------------:|:-------------------:|
| Controle estilizado, linear | 0.952 | 0.983 | 0.715 | 0.907 | 0.983 | 0.962 |
| Espectros medidos, linear | 0.976 | 0.995 | 0.719 | 0.968 | 0.995 | 0.990 |
| Medidos + SRF 10 nm | 0.976 | 0.994 | 0.719 | 0.968 | 0.995 | 0.990 |
| Medidos + SRF + atmosfera | 0.976 | 0.994 | 0.719 | 0.968 | 0.913 | 0.990 |
| Medidos + SRF + atmosfera + bilinear | 0.947 | 0.983 | 0.714 | 0.969 | 0.906 | 0.988 |

Interpretação: esta é uma análise de sensibilidade com alvo implantado, não
evidência de generalização para um biossinal remoto naturalmente observado.
