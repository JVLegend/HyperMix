# Protocolo pré-especificado T8: alvo bioHSI de 54 m

Registrado em 2026-08-04, antes de executar qualquer detector sobre as regiões
rotuladas. Este documento fixa a análise primária de T8c. Alterações posteriores
devem ser identificadas como desvios do protocolo.

**Estado pós-registro:** a primeira porta de reprodução falhou. As caixas do
JSON de parâmetros são agora tratadas como geometria candidata, não como as
caixas manuais confirmadas da Figura 4g. T8c está pausado. O resultado não muda
as regras registradas abaixo; ele invalida a ponte geométrica assumida na
primeira tentativa. Veja `results/real_target_reproduction_diagnosis.md`.

## Pergunta

Métodos de detecção hiperespectral ordenam e separam regiões com diferentes
níveis de indução de bacterioclorofila a em um cubo realmente medido a 54 m?

O objetivo não é demonstrar superioridade do aprendizado. O detector aprendido
é uma análise secundária. O primeiro objetivo é reproduzir o método publicado e
estabelecer um confronto regional rastreável.

## Fontes congeladas

- Artigo: Chemla et al., DOI `10.1038/s41587-025-02622-y`.
- Cubo: Zenodo `10.5281/zenodo.14756889`,
  `rg_on_sand_induction_54m.zip`, MD5
  `a5e553d8f0634896b02750086e7eb4a1`.
- Código oficial: `VoigtLab/bioHSI`, tag `v.1.0.0`.
- Concentrações e scores de reprodução: Source Data Figs. 1-4, aba `4G`,
  intervalo `A1:B10`, SHA-256
  `8cb9bb5420e55b7ee27820ec2ea50c214f07538e405b75e271bdc4c91fa8666c`.
- Assinatura: absorbância independente de pellets YF10, chave
  `bacteriochlorophyll_a_yf10` na biblioteca empacotada do HyperMix.
- Geometria candidata: `hypermix/data/biohsi_54m_protocol.json`.

O arquivo XLSX completo não será redistribuído pelo HyperMix. O protocolo guarda
somente os nove valores factuais necessários, com URL e hash da fonte.

## Unidades e rótulos

A primeira tentativa associou os nove retângulos da amostra
`high_flight_day_1_left_img0` à Figura 4g. A reprodução não confirmou essa
associação. A ordem pré-especificada usada no teste foi:

| ROI | Concentração, µM | Classe binária |
|---:|---:|:---:|
| 0 | 250 | positiva |
| 1 | 100 | positiva |
| 2 | 50 | positiva |
| 3 | 25 | positiva |
| 4 | 10 | positiva |
| 5 | 5 | positiva |
| 6 | 1 | negativa |
| 7 | 0,1 | negativa |
| 8 | 0 | negativa |

O limiar de 5 µM é herdado do notebook oficial `fig4fg.ipynb`, que usa
concentração maior ou igual a 5 para sua ROC exploratória. Ele não foi escolhido
a partir dos resultados do HyperMix.

Os quatro retângulos da segunda amostra são excluídos da análise primária porque
não aparecem na tabela Source Data da Figura 4g e ainda não têm identidade
independente confirmada.

## Geometria

As coordenadas são intervalos semiabertos no recorte `[[729, 836], [332, 341]]`
de linhas e colunas. O recorte é rotacionado em 4,08561678 graus com
`scipy.ndimage.rotate`, `reshape=False`. Preenchimento introduzido pela rotação é
NaN e nunca entra em médias ou estatística de fundo.

`scripts/biohsi_roi_overlay.py` gera `assets/biohsi_54m_rois.png`. A posição das
caixas foi verificada visualmente em RGB, sem consultar score de detector.

## Ordem dos métodos

1. Reproduzir K-means hierárquico mais UCLS do código oficial.
2. Matched filter espectral e sua versão espacial.
3. Matched subspace e sua versão espacial.
4. RX global, sem assinatura de alvo.
5. Detector aprendido como análise secundária, somente se sua aplicação não
   exigir treino ou calibração nas nove regiões.

O método oficial usa suavização espectral com janela 11, normalização por máximo
em cada pixel, assinatura negativa de absorbância YF10, endmembers do fundo por
K-means hierárquico e UCLS. Scores negativos são truncados em zero.

## Estatística de fundo e agregação

- Pixels com preenchimento da ortorretificação são excluídos.
- As nove ROIs são excluídas do ajuste de estatística de fundo.
- A configuração primária usa todos os demais pixels válidos da cena.
- Cada mapa produz um único score por ROI: média dos pixels válidos na caixa.
- Suavização espacial deve normalizar pelo peso dos pixels válidos para não
  espalhar o preenchimento zero.

## Métricas

Métrica primária: AUC calculada sobre os nove scores regionais, com seis regiões
positivas e três negativas.

Métricas secundárias:

- correlação de Spearman entre score regional e concentração;
- diferença média entre regiões positivas e negativas;
- tabela completa dos nove scores, sem esconder exceções à monotonicidade.

Pd@FAR pixel a pixel está proibida como métrica primária porque não existe
máscara pixel a pixel publicada. Pixels dentro de uma caixa não são réplicas.

Com apenas nove concentrações e uma região por concentração, nenhum intervalo
será descrito como incerteza biológica populacional. Bootstrap estratificado e
permutação podem aparecer apenas como análises de sensibilidade, acompanhados da
limitação de que as regiões não são réplicas biológicas intercambiáveis.

## Porta de reprodução

Antes do confronto T8c, os nove scores do método oficial serão comparados, sem
reescalonamento, aos nove scores publicados na aba `4G`. Serão reportados MAE,
Pearson, Spearman e o gráfico pareado. A porta será considerada satisfeita
somente se, ao mesmo tempo, o MAE for menor ou igual a 0,01 unidade de score e
Pearson for maior ou igual a 0,99. Estes limites foram registrados antes da
primeira execução sobre as nove regiões. Se a porta falhar, o confronto será
pausado e a divergência será documentada antes de testar outros métodos.

O ambiente oficial lista `scikit-learn==1.3.0` e `scipy==1.8.0`. Como essa
combinação não é compatível com o NumPy 2 do ambiente atual, a reprodução fixa
explicitamente `n_init=3`, o comportamento histórico do MiniBatchKMeans, e usa
uma versão moderna do scikit-learn. A versão efetivamente usada será gravada na
saída. Essa adaptação é uma possível fonte de desvio numérico, não algo a omitir.

## Saídas planejadas

- `results/real_target_reproduction.json` e `.md`;
- `results/real_target_official_source_audit.json` e diagnóstico da porta;
- `results/real_target.json` e `.md`;
- overlay das ROIs e gráfico de reprodução em `assets/`;
- atualização do observatório somente depois de resultados reproduzíveis.
