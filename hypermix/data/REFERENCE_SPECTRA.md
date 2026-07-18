# Proveniência dos espectros de referência

`reference_spectra.csv` contém somente as curvas necessárias ao HyperMix,
interpoladas em uma grade de 400 a 1000 nm com passo de 1 nm.

## Endmembers naturais

Fonte: USGS Spectral Library Version 7, pacote ASCII do registro ScienceBase
`586e8c88e4b0f5ce109fccae`. As quatro curvas são reflectâncias medidas:

- Aspen-1 green-top, vegetação verde;
- Grass Golden Dry GDS480, vegetação seca;
- Sand DWO-3-DEL2ar1, areia/solo;
- Seawater Open Ocean SW2, água oceânica.

O material do USGS é domínio público. SHA-256 do pacote usado:
`d232645740869a82aafcad5839448c50b1dc72965ce042d1374f29b7a798a91c`.

## Repórteres biológicos

Fonte: arquivo oficial `VoigtLab/bioHSI-v.1.0.0` no Zenodo, associado a
Chemla et al., *Nature Biotechnology* (2026). As três curvas são absorbâncias
inferidas de pellets:

- YF10, bacterioclorofila a;
- bpHO-smURFP em *E. coli*, complexo SmURFP/biliverdina;
- bpHO-smURFP em *P. putida*, complexo SmURFP/biliverdina.

O arquivo bioHSI usa licença MIT. SHA-256 do arquivo usado:
`3dfc176aa40c2c3740cef9b798116eb018f1a20137acc5c82872a4c58f0cedd8`.

Estas curvas não são reflectância absoluta de superfície. A função
`measured_reporter_library()` remove um baseline robusto de absorbância e usa
a relação de Beer-Lambert para produzir um alvo semelhante a reflectância. O
formato da banda é medido; essa conversão ainda é uma hipótese do simulador.

O artefato pode ser reconstruído com:

```bash
python scripts/fetch_reference_spectra.py
```
