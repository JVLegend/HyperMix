# HyperMix detection leaderboard

Detection AUC on the **real Indian Pines** background (AVIRIS) with an
implanted bacteriochlorophyll-a target, averaged over 3 seeds.
`Mean AUC` averages over SNR = 20, 10, 5, 0 dB; `AUC @ 0 dB` is the
hardest, low-SNR case. Reproduce with `python scripts/make_leaderboard.py`.

| Rank | Method | Mean AUC | AUC @ 0 dB |
|-----:|--------|:--------:|:----------:|
| 1 | Learned detector (HyperMix) 🧠 | 0.926 | 0.828 |
| 2 | Matched filter | 0.751 | 0.627 |
| 3 | Spectral Angle Mapper | 0.642 | 0.562 |
| 4 | ACE | 0.632 | 0.530 |
