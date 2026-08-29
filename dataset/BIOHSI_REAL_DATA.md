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
para o referencial do cubo exige aplicar recorte e rotação. Essa transformação
foi implementada em `hypermix/biohsi_roi.py` e verificada no overlay
`assets/biohsi_54m_rois.png`. As duas janelas de recorte não contêm
preenchimento, com refletância média em torno de 0,33 na banda 136.

### Resolução pública dos rótulos e lacuna geométrica

Os CSVs e o caminho de assinatura continuam ausentes do ZIP. Os níveis da
primeira coluna foram recuperados por fontes públicas independentes, mas a
geometria usada na Figura 4g ainda não foi recuperada:

1. **Níveis de indução.** `CONC_LABELS_PATHS` aponta para caminhos absolutos da
   máquina dos autores, `plates_col1_labels.csv` e `plates_col2_labels.csv`, que
   não acompanham o ZIP. A aba `4G` da planilha Source Data oficial contém nove
   concentrações e nove scores, correspondentes aos nove retângulos da Figura
   4g: 250, 100, 50, 25, 10, 5, 1, 0,1 e 0 µM.
2. **Assinatura de referência.** `REF_SPECTRA_PATHS` aponta para
   `../infered_RG_on_sand.npy`, fora do arquivo. Note que este não é o
   arquivo usado pelo notebook específico da Figura 4, que carrega a assinatura
   independente `YF10_infered_absorbance_from_pellets_09Jul2024.npy`. Essa curva
   já está preservada na biblioteca do HyperMix.
3. **Controles.** `REF_BLOT_NEG_CTRL_COORDS` e `REF_BLOT_POS_CTRL_COORDS` estão
   vazios. A análise primária usa a região não induzida de 0 µM como referência
   negativa e o limiar de 5 µM definido no notebook oficial.

Os quatro retângulos da segunda amostra não aparecem na tabela `4G` e continuam
sem identidade independente. Eles foram excluídos antes da avaliação. O artefato
`hypermix/data/biohsi_54m_protocol.json` registra fontes, hash, geometria
candidata, rótulos, scores de reprodução e exclusões.

O notebook oficial não usa diretamente `TL_POINTS_COORDS`. Ele carrega
`manually_defined_rectangle_coordinates.json`, produzido interativamente sobre
a cena completa. Esse arquivo não está no ZIP nem no release de código. A
primeira porta de reprodução falhou tanto no porte HyperMix quanto na execução
direta da tag oficial sobre as caixas candidatas. Portanto a igualdade de nove
caixas e a plausibilidade visual não validam a correspondência. O diagnóstico
completo está em `results/real_target_reproduction_diagnosis.md`.

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

## Varredura remota dos demais subconjuntos, 2026-08-28

O diretório central de um ZIP fica no fim do arquivo, então o conteúdo de cada
subconjunto foi listado por requisições HTTP com cabeçalho `Range`, sem baixar os
volumes completos. Cada listagem custou cerca de 3 KiB.

| Subconjunto | Tamanho | Traz rótulo de concentração? | Traz controles? |
|---|---:|---|---|
| `rg_bchla_pellets_ctrl` | 1,54 GB | **sim**, `RG_concentration_map.csv` embutido | série inclui zero |
| `rg_on_sand_24m` | 0,73 GB | não, caminho externo `giha1_plate_OD_labels.csv` | **sim**, positivo e negativo |
| `rg_on_sand_induction_54m` | 0,63 GB | não, caminho externo | não, campos vazios |
| `rg_in_field_sensing` | 2,92 GB | não, só cubo e cabeçalho | não |
| `rg_in_field_sensing_replicates` | 0,72 GB | não, só cubo e cabeçalho | não |
| `rg_wt_aj1_yf6_pellets` | 3,19 GB | não, só cubo, cabeçalho e PNG | não |
| `rg_yf10_gradient_varied_soils` | 1,70 GB | não, só cubo, cabeçalho e PNG | não |

A coluna de rótulo descreve o que **acompanha o ZIP**. No caso do voo de 54 m os
níveis foram recuperados depois por fonte pública independente, conforme a seção
anterior; a lacuna remanescente ali é geométrica, não de rótulo.

### `rg_bchla_pellets_ctrl`, o único com ground truth embutido

O `RG_concentration_map.csv` tem 192 bytes e descreve uma grade de 4 por 12:

```
2000,1000,800,600,400,200,100,50,10,1,0.1,0
2000,1000,800,600,400,200,100,50,10,1,0.1,0
NA,NA,NA,NA,NA,NA,NA,500000,100000,50000,10000,4000
NA,NA,NA,NA,NA,NA,NA,500000,100000,50000,10000,4000
```

São duas séries em duplicata. A primeira cobre quatro ordens de grandeza e
**inclui controle zero**. A segunda cobre valores muito mais altos, de 500000 a
4000, com sete células ausentes. O cubo é ENVI `bil`, float32, little-endian,
1600 por 754 com 371 bandas, portanto configuração de sensor diferente da usada
no voo de 54 m.

Duas ressalvas registradas antes de qualquer análise. A unidade das
concentrações não aparece no CSV, então por ora os valores são ordem relativa e
não concentração absoluta. E o CSV dá a grade, não a posição dos poços na
imagem, de modo que o mapeamento espacial continua a ser estabelecido; a
diferença em relação ao voo de 54 m é que uma placa é uma grade regular, um
problema geométrico bem posto.

Este subconjunto é de bancada, não de voo. Ele permite medir limite de detecção
e abundância calibrada sobre espectros medidos com concentração conhecida, mas
não valida detecção a 54 m contra clutter natural. As duas perguntas são
distintas e serão reportadas como tais.

### `rg_on_sand_24m`, melhor que o de 54 m em controles

O `params_file.json` traz doze retângulos e, ao contrário do voo de 54 m,
declara controles: `REF_BLOT_POS_CTRL_COORDS` igual a `[[0, 0], [0, 1]]` e
`REF_BLOT_NEG_CTRL_COORDS` igual a `[[5, 0], [5, 1]]`. A rotação é de 22,44
graus e o recorte tem 287 por 295, com raio de blot de 23,3 pixels. O cubo é
`bsq`, 1410 por 1234 com 273 bandas, e a faixa de análise declarada é de 500 a
900 nm.

O rótulo de concentração continua fora do arquivo, em
`giha1_plate_OD_labels.csv`, mas o nome informa a unidade pretendida,
densidade óptica.

## Inspeção local de `rg_bchla_pellets_ctrl`, 2026-08-28

O ZIP foi transferido de forma retomável, com um supervisor que reiniciou a
transferência após dois `TimeoutError`. Tamanho e MD5 foram conferidos de forma
independente após o download: 1.540.133.184 bytes e
`a62e189eef22baaf36931d126e74c449`, ambos conformes ao manifesto. O ZIP foi criado
em Windows e usa barra invertida como separador, o que exige normalização de
caminho na extração.

### Cubo

Lido com `hypermix/envi.py`, que assim exercita o caminho `bil` além do `bsq` do
voo de 54 m.

| Campo | Valor |
|---|---|
| samples, lines, bands | 1600, 754, 371 |
| interleave | `bil` |
| data type | 4, float32, little-endian |
| wavelengths | 371 valores de 399,590 nm a 1002,490 nm, passo médio 1,6295 nm |
| sensor | `uVS-374`, lente de 24 mm |
| description | `[HEADWALL Hyperspec III]` |

O produto 1600 x 754 x 371 x 4 dá 1.790.297.600 bytes, exatamente o tamanho do
binário. Não há preenchimento: zero por cento dos pixels são nulos em todas as
bandas amostradas, coerente com cena de bancada e não ortorretificada.

Dois pontos de cautela sobre escala. A descrição **não** traz a cadeia
`RADIANCE, REFLECTANCE, OR` presente no voo de 54 m, portanto o nível de
processamento é diferente e não deve ser presumido equivalente. E os valores vão
de 0 a exatamente 3,000 em várias bandas, o que sugere teto de saturação por
recorte. Nenhuma conversão é aplicada; o dado é lido como está.

### Desenho experimental visível

A imagem de referência mostra uma placa padrão de 96 poços, oito linhas por doze
colunas, com conteúdo apenas nas quatro primeiras linhas. Isso é coerente com a
grade de 4 por 12 do `RG_concentration_map.csv`. O passo da grade medido no cubo
é de aproximadamente 71 pixels nos dois eixos, compatível com o passo físico
uniforme de uma placa de 96 poços.

### Geometria NÃO resolvida

O mapeamento entre células do CSV e poços da imagem **não foi estabelecido** e
não deve ser presumido. Três ambiguidades permanecem abertas:

1. **Fase da grade.** Ajustes por contraste e por estrutura de poços vazios
   convergiram para fases diferentes, deslocadas em cerca de uma posição em cada
   eixo. As duas hipóteses cabem dentro da área da placa.
2. **Orientação das colunas.** O texto impresso na placa aparece espelhado na
   imagem, o que sugere inversão de colunas, enquanto o padrão de poços vazios
   das linhas 3 e 4 do CSV sugere o contrário. As duas leituras não foram
   conciliadas.
3. **Borda versus rótulo.** A faixa à direita da imagem contém as letras de linha
   impressas na placa, e uma das fases candidatas coloca a última coluna sobre
   essa faixa em vez de sobre um poço, o que produziria um valor baixo por
   artefato e não por concentração nula.

Enquanto essas três ambiguidades não forem resolvidas por evidência independente
do score de qualquer detector, nenhuma comparação de métodos será executada neste
subconjunto. Em particular, escolher a fase ou a orientação que torna o sinal
mais bonito seria exatamente o erro circular que já bloqueou o voo de 54 m.

### Tentativa automática de detecção da grade, resultado negativo

A detecção automática foi tentada e **não convergiu**. O registro do que falhou
importa tanto quanto um sucesso.

O período da grade foi recuperado de forma estável por autocorrelação do
gradiente em banda NIR, onde o corante não absorve: 70 pixels entre colunas e 72
entre linhas, coerentes entre si e com o passo uniforme de uma placa de 96 poços.
A fase, porém, não foi resolvida. Três abordagens independentes, picos do desvio
padrão do contraste, ajuste de grade regular por busca, e correlação com uma
grade sintética, convergiram para fases diferentes, deslocadas em cerca de uma
posição em cada eixo.

A causa foi identificada. O modelo usado supunha interior liso e borda com
gradiente forte, mas cada poço vazio apresenta um **reflexo especular no
centro**. Esse brilho produz gradiente alto no interior e inverte o sinal da
métrica, o que explica tanto os escores negativos em ambas as fases testadas
quanto a divergência entre os ajustes. Nenhuma das fases candidatas foi adotada.

Duas rotas permanecem, e a escolha entre elas ainda não foi feita:

1. Detecção de círculos dimensionada ao diâmetro real do poço, cerca de 60 a 70
   pixels, robusta a reflexo especular.
2. Anotação manual única, congelada em artefato versionado com hash, declarada
   como tal. Essa rota é legítima desde que a anotação seja feita sem consultar
   score de detector e publicada junto do resultado. Na prática, produziria
   exatamente o artefato de coordenadas que falta no arquivo dos autores.

### Geometria resolvida por anotação manual congelada, 2026-08-28

A rota de anotação manual foi executada. O período da grade já era estável por
autocorrelação; a fase foi decidida por inspeção visual de um overlay desenhado
sobre a banda NIR, julgando alinhamento com a estrutura óptica dos poços e nunca
com intensidade de corante. Nenhum score de detector foi consultado.

A grade adotada, no referencial da imagem, tem linhas em `138 + 72k` para k de 0
a 7 e colunas em `433 + 70k` para k de 0 a 11. Os 96 círculos caem sobre os 96
poços, o que está registrado em `assets/biohsi_pellets_plate_grid.png`.

O artefato `hypermix/data/biohsi_pellets_plate_geometry.json` congela essa
geometria com SHA-256 próprio, o MD5 do cubo e as questões ainda abertas. Ele
acompanha o pacote e é validado por testes offline que não dependem do cubo de
1,8 GB. Na prática, é exatamente o artefato de coordenadas que falta no arquivo
publicado pelos autores.

**Âncora de orientação, independente de sinal.** As letras de linha A a H
impressas na placa aparecem na borda **direita** da imagem, correndo de A no topo
a H embaixo. Em uma placa padrão de 96 poços essas letras ficam à esquerda,
portanto a imagem está espelhada horizontalmente e a **coluna física 1
corresponde à coluna mais à direita da imagem**. Essa conclusão vem de rótulo
impresso no plástico, não de qualquer medida espectral.

### O que a geometria ainda não autoriza

Localizar poços não é o mesmo que atribuir concentrações. Três pontos seguem
abertos e impedem qualquer comparação de métodos neste subconjunto:

1. A unidade das concentrações do CSV continua não declarada.
2. A correspondência entre as quatro linhas do CSV e as linhas da placa não foi
   estabelecida.
3. Uma sonda **pré-especificada** de profundidade de banda no pico Qy da
   bacterioclorofila a, 800 nm com ombros em 750 e 860 nm, **não** recuperou
   sinal coerente: valores planos e negativos em toda a placa, inclusive nas
   linhas sem conteúdo aparente. A correlação de Spearman com o log da
   concentração deu -0,542 na orientação da imagem, com sinal **oposto** ao que
   absorção exigiria. Por isso ela não foi usada para decidir orientação nem
   tratada como evidência de detecção.

Duas sondas anteriores foram descartadas por erro declarado de escolha
espectral: contraste 900 menos 540 nm, adequado a corante visível e não a um
pigmento do infravermelho próximo, e profundidade ancorada no máximo da curva de
biblioteca, que cai na banda Soret em 399,6 nm e torna o cálculo degenerado.

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

A análise planejada possui nove retângulos, com lados de poucos pixels. Não há
máscara pixel a pixel publicada. Portanto Pd@FAR **não** é métrica primária
defensável, e o protocolo usa AUC por região, com Spearman e contraste como
secundárias. Existe uma única região por concentração, então reamostragem não
será apresentada como IC de variabilidade biológica. Os quatro retângulos
adicionais permanecem fora da análise primária. Estas regras só serão aplicadas
depois que a ponte geométrica cruzar a porta de reprodução.
