# Biblioteca espectral aberta do HyperMix

Biblioteca compacta para detecção hiperespectral de biossinais: endmembers
naturais medidos pelo USGS e absorbâncias de repórteres publicadas com o código
bioHSI de Chemla et al., em uma grade canônica.

## Arquivos

- `hypermix_spectral_library.csv`: uma linha por comprimento de onda;
- `hypermix_spectral_library.npz`: os mesmos dados como arrays NumPy.

## Grade

- 61 bandas, 400-1000 nm, passo de 10 nm, coluna `wavelength_nm`;
- a fonte empacotada em `hypermix/data/reference_spectra.csv` preserva passo de
  1 nm.

## Espectros

| Nome | Unidade/tipo | Proveniência |
|---|---|---|
| `vegetation` | reflectância | USGS Aspen-1 green-top |
| `dry_vegetation` | reflectância | USGS Grass Golden Dry GDS480 |
| `soil` | reflectância | USGS Sand DWO-3-DEL2ar1 |
| `water` | reflectância | USGS Seawater Open Ocean SW2 |
| `bacteriochlorophyll_a_reflectance_surrogate` | alvo modelado | absorbância YF10 convertida por Beer-Lambert |
| `biliverdin_ixalpha_reflectance_surrogate` | alvo modelado | média das absorbâncias SmURFP/biliverdina em dois hospedeiros |
| `bacteriochlorophyll_a_yf10` | absorbância | pellet YF10, bioHSI |
| `smurfp_biliverdin_ecoli` | absorbância | pellet de *E. coli*, bioHSI |
| `smurfp_biliverdin_pputida` | absorbância | pellet de *P. putida*, bioHSI |

## Notas essenciais de validade

- Os endmembers são amostras medidas, mas quatro amostras não representam toda
  a variabilidade de vegetação, solo e água.
- As curvas bioHSI são absorbâncias inferidas de pellets, não reflectância
  absoluta de uma superfície observada remotamente.
- Os alvos semelhantes a reflectância removem o quinto percentil da absorbância
  e aplicam `0,45 * 10**(-A)`. O formato e a magnitude de absorbância são
  medidos; a conversão é uma hipótese explícita do HyperMix.
- O pico medido de YF10 fica em aproximadamente 866 nm. Os picos de
  SmURFP/biliverdina ficam em 641-642 nm, nos dados empacotados a 1 nm.

## Fontes e reconstrução

- USGS Spectral Library Version 7, domínio público, ScienceBase
  `586e8c88e4b0f5ce109fccae`;
- `VoigtLab/bioHSI-v.1.0.0`, licença MIT, Zenodo `14827801`;
- detalhes, membros dos arquivos e checksums em
  `hypermix/data/REFERENCE_SPECTRA.md`.

```bash
python scripts/fetch_reference_spectra.py
python scripts/export_dataset.py
```

## Licença

O código e as transformações do HyperMix usam MIT. Os dados do USGS são domínio
público; os dados bioHSI são redistribuídos sob MIT com atribuição aos autores.
