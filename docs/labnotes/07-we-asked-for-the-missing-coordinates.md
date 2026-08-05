# Pedimos publicamente as coordenadas que faltam

Status: pronto para publicar
Imagem sugerida: `assets/biohsi_54m_rois.png`

A validação do alvo biológico real do HyperMix está pausada por um artefato
específico: o arquivo
`manually_defined_rectangle_coordinates.json` usado na Figura 4g do bioHSI.

Antes de contatar os autores, procurei o arquivo no ZIP do Zenodo, na tag
`v.1.0.0`, nos releases, nas branches e no histórico Git dos repositórios
públicos. O notebook carrega o JSON, mas o artefato não está versionado. Os CSVs
de concentração referenciados pelo mesmo notebook também não aparecem nesses
locais.

Em 4 de agosto de 2026, abri um pedido público e reproduzível no repositório
fonte: https://github.com/itai-levin/bioHSI/issues/2

O pedido inclui os resultados exatos da porta de reprodução e aceita qualquer
uma de quatro pontes independentes: o JSON original, o diretório de saída, as
coordenadas completas com a ordem das concentrações ou uma transformação
determinística entre os referenciais.

Enquanto aguardamos, as regiões não serão movidas para melhorar scores. A
comparação entre detectores continua bloqueada. Uma resposta indicando que o
arquivo não está mais disponível também será registrada como limitação do
benchmark.

Isto parece burocracia, mas é parte central do método: primeiro fixamos onde
medir, depois observamos qual detector foi melhor.
