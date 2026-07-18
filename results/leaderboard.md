# Leaderboard de detecção do HyperMix

AUC de detecção em **3 cenas hiperespectrais reais** (indian_pines, salinas, paviaU) com alvo de bacterioclorofila-a implantado,
média de 3 seeds. Os sensores e números de bandas diferem. O matched filter
espacial aplica blur gaussiano fixo com sigma = 1,5 pixel. `AUC média` agrega
todas as cenas e target SNR = 20, 10, 5 e 0 dB. O detector aprendido usa apenas
fundos simulados no treino, mas o alvo e o modelo de implante são compartilhados.
Reproduza com `python scripts/make_leaderboard.py`.

| Posição | Método | AUC média | AUC a 0 dB |
|--------:|--------|:---------:|:-----------:|
| 1 | Matched filter (spatial) | 0.990 | 0.982 |
| 2 | Learned detector (HyperMix) 🧠 | 0.987 | 0.972 |
| 3 | Matched filter | 0.943 | 0.908 |
| 4 | ACE | 0.860 | 0.811 |
| 5 | Spectral Angle Mapper | 0.656 | 0.655 |

## AUC por cena a target SNR de 0 dB

| Método | indian_pines | salinas | paviaU |
|--------|:---:|:---:|:---:|
| Matched filter (spatial) | 0.998 | 0.998 | 0.951 |
| Learned detector (HyperMix) 🧠 | 0.998 | 0.998 | 0.919 |
| Matched filter | 0.970 | 0.969 | 0.786 |
| ACE | 0.849 | 0.917 | 0.667 |
| Spectral Angle Mapper | 0.713 | 0.660 | 0.593 |
