# HyperMix detection leaderboard

Detection AUC across **3 real hyperspectral scenes** (indian_pines, salinas, paviaU) with an implanted bacteriochlorophyll-a target,
averaged over 3 seeds. Different sensors and band counts. The spatial matched
filter applies a fixed Gaussian blur with sigma = 1.5 pixels. `Mean AUC` averages
over all scenes and SNR = 20, 10, 5, 0 dB. The learned detector is trained
**only on simulation**. Reproduce: `python scripts/make_leaderboard.py`.

| Rank | Method | Mean AUC | AUC @ 0 dB |
|-----:|--------|:--------:|:----------:|
| 1 | Learned detector (HyperMix) 🧠 | 0.854 | 0.742 |
| 2 | Matched filter (spatial) | 0.834 | 0.719 |
| 3 | Matched filter | 0.689 | 0.593 |
| 4 | Spectral Angle Mapper | 0.595 | 0.542 |
| 5 | ACE | 0.595 | 0.519 |

## Per-scene AUC @ 0 dB (hardest case)

| Method | indian_pines | salinas | paviaU |
|--------|:---:|:---:|:---:|
| Learned detector (HyperMix) 🧠 | 0.828 | 0.759 | 0.640 |
| Matched filter (spatial) | 0.797 | 0.736 | 0.625 |
| Matched filter | 0.627 | 0.588 | 0.562 |
| Spectral Angle Mapper | 0.562 | 0.541 | 0.523 |
| ACE | 0.530 | 0.520 | 0.508 |
