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

## Pontos ainda não verificados no arquivo de dados

Até o ZIP terminar de ser transferido e validado, permanecem em aberto:

- dimensões, tipo numérico, interleave e byte order do cubo;
- nome e relação do binário pareado ao cabeçalho ENVI;
- unidades, faixa e ordenação exatas dos comprimentos de onda;
- conteúdo completo e semântica dos níveis em `plates_col1_labels.csv`;
- presença de referências branco/escuro e etapas de correção já aplicadas;
- disponibilidade das coordenadas manuais usadas na publicação;
- quantidade de regiões e réplicas biologicamente independentes.

Nenhum loader específico, split, máscara positiva ou métrica primária será
fixado a partir dos scores de um detector. Essas escolhas serão registradas
antes do confronto entre métodos.

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

## Regra estatística para T8

Pixels vizinhos do mesmo retângulo não serão tratados como réplicas
independentes. O nível de inferência deve seguir as unidades realmente
disponíveis, como regiões, placas, parcelas ou réplicas experimentais. Pd@FAR
só será a métrica primária se o arquivo sustentar uma máscara pixel a pixel
defensável. Caso contrário, o protocolo usará contraste ou classificação por
região com intervalos calculados na unidade experimental.
