# Dados bioHSI para validação de alvo real

Este documento separa o que já foi confirmado nas fontes públicas do que ainda
depende da inspeção local do conjunto completo. Ele orienta T8 e não constitui
um resultado de detecção.

## Proveniência

- Artigo: Chemla et al., *Nature Biotechnology* 2026,
  DOI `10.1038/s41587-025-02622-y`.
- Dados: Zenodo `10.5281/zenodo.14756889`, versão 1.0.0, CC BY 4.0.
- Código oficial de análise: Zenodo `10.5281/zenodo.14827801`.
- Primeiro subconjunto: `rg_on_sand_induction_54m.zip`, 628.789.375 bytes,
  MD5 `a5e553d8f0634896b02750086e7eb4a1`.

O manifesto versionado está em `hypermix/data/biohsi_manifest.json`. Os dados
baixados ficam em `data/biohsi/`, que não é incluído no Git.

## Contrato confirmado pelo código oficial

O notebook `04_image_processing/fig4fg.ipynb` referencia:

- o cubo ENVI `rg_on_sand_induction_54m/raw_0_rd_rf_or.hdr`;
- a tabela `rg_on_sand_induction_54m/plates_col1_labels.csv`;
- a assinatura independente
  `absorbance_data/YF10_infered_absorbance_from_pellets_09Jul2024.npy`;
- os centros das bandas registrados no cabeçalho ENVI;
- uma janela de suavização espectral de 11 bandas.

A análise original interpola a assinatura de pellets para os comprimentos de
onda do cubo. Em seguida, aprende endmembers do fundo por K-means hierárquico e
usa UCLS com a assinatura de referência e esses endmembers. O primeiro
coeficiente é usado como score e valores negativos são truncados em zero.

As regiões de interesse não são fornecidas diretamente pelo CSV. O notebook
solicita cliques nos cantos superior esquerdo e inferior direito de cada
retângulo e salva `manually_defined_rectangle_coordinates.json` na pasta de
saída. A primeira coluna do CSV é associada, por ordem, a esses retângulos. Para
uma ROC exploratória, o código considera positivas as regiões cujo valor é
maior ou igual a 5.

Esse limiar e essa máscara serão tratados como uma escolha do código original,
não como ground truth automaticamente adotado pelo HyperMix.

## Inspeção do arquivo de 54 m, concluída em 2026-08-04

O ZIP foi transferido de forma retomável e validado antes de qualquer leitura:
628.789.375 bytes e MD5 `a5e553d8f0634896b02750086e7eb4a1`, ambos conferidos de
forma independente após o download. O inventário foi feito sem extração.

### Conteúdo real do arquivo

O ZIP contém apenas quatro membros:

| Membro | Tamanho |
|---|---:|
| `rg_on_sand_induction_54m/raw_0_rd_rf_or` | 908.587.680 B |
| `rg_on_sand_induction_54m/raw_0_rd_rf_or.hdr` | 4.819 B |
| `rg_on_sand_induction_54m/raw_0_rd_rf_or.png` | 1,2 MiB |
| `rg_on_sand_induction_54m/raw_0_rd_rf_or_params_file.json` | 1.210 B |

> [!warning] Correção do contrato presumido
> `plates_col1_labels.csv` **não está neste ZIP**. A versão anterior deste
> documento registrava esse CSV como parte do subconjunto de 54 m, seguindo o
> notebook oficial. A inspeção mostra que ele não acompanha os dados.

### Cubo ENVI

Todos os campos abaixo vêm do cabeçalho, não de suposição:

| Campo | Valor |
|---|---|
| samples, lines, bands | 682, 1220, 273 |
| data type | 4, ou seja float32 |
| interleave | `bsq` |
| byte order | 0, little-endian |
| header offset | 0 |
| wavelength units | nm |
| map info | Geographic Lat/Lon, WGS84, graus |
| description | `HEADWALL Hyperspec III, RADIANCE, REFLECTANCE, OR` |

O binário pareado é `raw_0_rd_rf_or`, sem extensão. O produto
682 x 1220 x 273 x 4 resulta em 908.587.680 bytes, exatamente o tamanho do
arquivo, o que confirma dimensões, tipo e ausência de deslocamento.

Os 273 comprimentos de onda são estritamente crescentes, de 398,411 nm a
1002,430 nm, com passo médio de 2,2207 nm, mínimo de 2,2200 e máximo de 2,2230.
O `params` declara `WAVELENGTH_RANGE` de 400 a 1000, uma faixa de análise mais
estreita que a cobertura real do sensor.

### Correções já aplicadas e ambiguidade de unidade

As linhas de comentário do cabeçalho registram calibração radiométrica
(`CffHeader`), referência escura (`DarkHeader`), exposição de 6,994 ms,
ortorretificação com DEM e resolução de 0,064 m, inversão de colunas e firmware
`nhs_3.2.0` do sensor `nHS-369`. O nome do arquivo acompanha essa cadeia:
`raw`, `rd`, `rf`, `or`.

Existe uma ambiguidade que precisa ficar explícita. O comentário
`;Units = mW/(cm2*sr*um)` declara unidade de radiância, enquanto a descrição
lista também refletância. Os valores medidos favorecem refletância: em seis
bandas amostradas ao longo de todo o espectro, o intervalo observado foi de 0 a
1,0623, sem negativos e sem NaN. Nenhuma conversão de unidade é aplicada pelo
HyperMix. O dado é lido como está e a ambiguidade é reportada.

### Preenchimento da ortorretificação

Exatos 18,00% dos pixels valem zero em todas as bandas amostradas, e a máscara
coincide banda a banda. Isso é preenchimento fora da faixa imageada, não
medição. Esses pixels não podem entrar em estatística de fundo nem servir de
mínimo para qualquer reescalonamento.

### Geometria experimental disponível

O `params_file.json` descreve duas amostras, `high_flight_day_1_left_img0` e
`high_flight_dat_1_right_img0`, com `SHAPE` igual a `rectangle`:

| Amostra | CROP, linhas x colunas | Extensão | Blots Y x X | Raio | Retângulos |
|---|---|---|---:|---:|---:|
| esquerda | `[[729, 836], [332, 341]]` | 107 x 9 | 9 x 1 | 3 | 9 |
| direita | `[[784, 834], [309, 321]]` | 50 x 12 | 4 x 1 | 4 | 4 |

As coordenadas manuais **estão presentes**, em `TL_POINTS_COORDS` e
`BR_POINTS_COORDS`, com nove retângulos na amostra esquerda e quatro na direita,
treze ao todo. Elas estão no referencial recortado, e o `params` também registra
uma rotação por amostra, de 4,0856 e 1,5074 graus. Converter esses retângulos
para o referencial do cubo exige aplicar recorte e rotação, o que ainda não foi
feito. As duas janelas de recorte foram verificadas no cubo e não contêm
preenchimento, com refletância média em torno de 0,33 na banda 136.

### O que continua ausente

Três dependências externas impedem o ground truth de T8b:

1. **Níveis de indução.** `CONC_LABELS_PATHS` aponta para caminhos absolutos da
   máquina dos autores, `plates_col1_labels.csv` e `plates_col2_labels.csv`, que
   não acompanham o ZIP. Sem eles, os treze retângulos não têm rótulo de
   concentração.
2. **Assinatura de referência.** `REF_SPECTRA_PATHS` aponta para
   `../infered_RG_on_sand.npy`, fora do arquivo. Note que este não é o
   `YF10_infered_absorbance_from_pellets_09Jul2024.npy` citado no notebook da
   Figura 4, e sim uma assinatura distinta.
3. **Controles.** `REF_BLOT_NEG_CTRL_COORDS` e `REF_BLOT_POS_CTRL_COORDS` estão
   vazios nas duas amostras. Este subconjunto não declara controle positivo nem
   negativo.

Enquanto essas três lacunas não forem resolvidas, por outro subconjunto do mesmo
registro Zenodo ou por contato com os autores, T8b não pode fixar regiões
positivas. Nenhum loader, split, máscara ou métrica será derivado dos scores de
um detector.

## Procedimento local

```bash
python scripts/fetch_biohsi.py --list
python scripts/fetch_biohsi.py \
  --dataset rg_on_sand_induction_54m.zip \
  --inspect
```

O download é retomável. Depois de concluído, tamanho e MD5 são verificados
antes de o arquivo `.part` receber o nome final. `--inspect` testa a integridade
do ZIP e lista seus membros sem extrair conteúdo.

## Leitura do cubo no HyperMix

`hypermix/envi.py` foi escrito depois da inspeção e não substitui
`datasets.load_envi_cube`, que continua servindo ao caminho antigo. O loader
antigo não serve a dados medidos por três motivos verificados: aplica min-max
global sobre o cubo inteiro, o que aqui ancoraria o mínimo no preenchimento da
ortorretificação; descarta o cabeçalho, justamente onde estão comprimentos de
onda e unidade; e depende do pacote opcional `spectral`, ausente no ambiente.

O leitor novo mapeia o binário em memória, devolve `(lines, samples, bands)` por
transposição de vista, sem cópia, e preserva valores, comprimentos de onda,
unidade declarada e comentários do cabeçalho. Ele valida o tamanho do binário
contra as dimensões declaradas e recusa arquivos truncados. `envi_nodata_mask`
marca apenas pixels iguais ao sentinela em todas as bandas.

Validação contra o arquivo real: dimensões, tipo, faixa espectral, média por
banda, fração de preenchimento de 18,00% e as duas janelas de recorte foram
reproduzidas exatamente pelo loader. Os testes em `tests/test_envi.py` são
sintéticos e não dependem do arquivo de 629 MB.

## Regra estatística para T8

Pixels vizinhos do mesmo retângulo não serão tratados como réplicas
independentes. O nível de inferência deve seguir as unidades realmente
disponíveis, como regiões, placas, parcelas ou réplicas experimentais.

A inspeção torna essa regra concreta. Existem treze retângulos ao todo, com
lados de poucos pixels e raios declarados de 3 e 4. Não há máscara pixel a pixel
publicada nem controle declarado. Portanto Pd@FAR **não** é métrica primária
defensável neste subconjunto, e o protocolo deve usar contraste ou classificação
por região, com intervalos calculados sobre regiões, não sobre pixels. Treze
unidades também limitam a precisão de qualquer intervalo, o que precisa ser dito
no resultado em vez de mascarado por milhares de pixels correlacionados.
