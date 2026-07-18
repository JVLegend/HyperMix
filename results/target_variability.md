# Variabilidade do alvo medido

AUC média em target SNR de 20, 10, 5 e 0 dB, 6 seeds por ponto.
As cenas usam endmembers USGS medidos em um forward model calibrado de
400-1000 nm. O MF nominal recebe a média fixa da biblioteca; o oráculo
recebe a assinatura efetivamente implantada. O detector aprendido é
treinado sobre a variação, mas conserva as cinco features derivadas do
alvo nominal da arquitetura atual.

| Track | MF nominal | MF espacial nominal | Subespaço | Subespaço espacial | Aprendido | Oráculo | Vencedor não-oráculo |
|-------|:----------:|:-------------------:|:---------:|:------------------:|:---------:|:-------:|---------------------|
| Hospedeiro, SmURFP/biliverdina | 0.962 | 0.996 | 0.821 | 0.967 | 0.997 | 0.997 | empate |
| Hospedeiro + sensor + atmosfera | 0.935 | 0.993 | 0.739 | 0.910 | 0.996 | 0.995 | empate |
| Qualquer repórter, BChl ou biliverdina | 0.776 | 0.907 | 0.780 | 0.948 | 0.928 | 0.996 | Subespaço espacial |

## AUC a target SNR de 0 dB

| Track | MF nominal | MF espacial nominal | Subespaço | Subespaço espacial | Aprendido | Oráculo |
|-------|:----------:|:-------------------:|:---------:|:------------------:|:---------:|:-------:|
| Hospedeiro, SmURFP/biliverdina | 0.937 | 0.991 | 0.772 | 0.941 | 0.994 | 0.992 |
| Hospedeiro + sensor + atmosfera | 0.928 | 0.989 | 0.704 | 0.885 | 0.994 | 0.989 |
| Qualquer repórter, BChl ou biliverdina | 0.858 | 0.953 | 0.734 | 0.913 | 0.970 | 0.987 |

O track de família pergunta se qualquer um dos repórteres foi detectado;
não deve ser descrito como variabilidade intra-repórter. O nível de
expressão é representado pela abundância aleatória do implante. O track
de sensor sorteia FWHM entre 6-14 nm e força atmosférica entre 0,7-1,3.
As assinaturas são estratificadas: três cenas por hospedeiro nos tracks
SmURFP e duas por repórter no track de família, em cada nível de SNR.

Este é um benchmark de alvo implantado. Não demonstra detecção remota de
expressão biológica naturalmente observada e ainda não inclui intervalos
de confiança sobre a população de cenas.
