# Roadmap do HyperMix

Atualizado em 2026-08-06. Este arquivo define a ordem de trabalho depois das
Fases A e B e dos testes T1, T7a, T7b e T7c. O `STATUS.md` continua sendo a
fonte dos resultados já medidos. Este roadmap registra hipóteses e entregas
futuras, não resultados antecipados.

## Princípio de decisão

O detector aprendido atual não supera de forma robusta o matched filter
espacial bem calibrado nos regimes testados. As próximas fases não devem buscar
um cenário artificial em que uma rede pareça vencer. Elas devem remover as
limitações que ainda impedem uma conclusão externa:

1. os alvos do benchmark atual são implantados digitalmente;
2. a assinatura de laboratório sofre transformação antes de chegar ao sensor;
3. abundância e decisão operacional foram calibradas fora da avaliação, mas
   ainda não em dado biológico remoto real;
4. conhecer apenas a família do alvo e não o espectro exato precisava de um
   teste sem vazamento.

A distribuição pública deixou de ser bloqueio: `0.5.0` está no PyPI, no GitHub
Releases e no Zenodo com DOI de versão `10.5281/zenodo.21799951`.

## Ordem executiva

| Ordem | Frente | Resultado que destrava | Dependência |
|---:|---|---|---|
| 1 | T8, bioHSI real | Primeiro teste sem implantação digital | Nenhuma |
| 2 | T9, transferência da assinatura | Reduzir o gap laboratório-sensor sem rótulos de teste | Metadados de T8 |
| 3 | Milestone 3, release | Concluído: instalação pública, versão citável e CI | Documentação auditada |
| 4 | T10, alvo retido e detecção cega | Concluído: separa oracle, família e alvo desconhecido | Dois hosts medidos |
| 5 | T11, limite de detecção | Concluído: LOD por FWHM e FAR com calibração externa | Simulador medido |
| 6 | T12, abundância calibrada | Concluído: erro, cobertura e largura com splits externos | Simulador implantado |
| 7 | T13, publicação | Em andamento: cadeia de evidências pronta; falta validação externa | T8 e uso público |

## T8: validação em alvo biológico realmente medido

Pergunta: o pipeline consegue separar regiões com expressão do repórter em um
cubo hiperespectral medido, sem inserir o alvo digitalmente?

Fonte primária: Chemla et al., *Nature Biotechnology* 2026, DOI
`10.1038/s41587-025-02622-y`. Dados: Zenodo
`10.5281/zenodo.14756889`, versão 1.0.0, licença CC BY 4.0.

### T8a: aquisição e inspeção

- [x] Versionar um manifesto curado com DOI, versão, licença, tamanho e MD5.
- [x] Criar `scripts/fetch_biohsi.py` com listagem, download retomável e
      verificação de tamanho e checksum.
- [x] Adicionar testes que não dependem da rede nem do arquivo de 629 MB.
- [x] Auditar o notebook oficial da Figura 4 e documentar o contrato confirmado
      em `dataset/BIOHSI_REAL_DATA.md`.
- [x] Implementar inventário e teste de integridade do ZIP sem extração.
- [x] Baixar `rg_on_sand_induction_54m.zip` para `data/biohsi/`.
- [x] Inventariar o conteúdo do ZIP sem assumir formato, orientação ou unidade.
- [x] Documentar cubos, comprimentos de onda, referências branco/escuro,
      controles, regiões experimentais e metadados ausentes.
- [x] Implementar o loader somente depois dessa inspeção.

T8a está concluído. O ZIP foi validado por tamanho e MD5, inventariado sem
extração e inspecionado. O cubo é ENVI `bsq` float32 little-endian, 682 x 1220 x
273, com 273 bandas de 398,411 nm a 1002,430 nm e 18,00% de preenchimento da
ortorretificação. `hypermix/envi.py` lê esse cubo preservando escala, unidade e
metadados, com testes sintéticos. Os fatos completos estão em
`dataset/BIOHSI_REAL_DATA.md`.

O ZIP não traz os CSVs de indução nem a assinatura citada em
`REF_SPECTRA_PATHS`. T8b resolveu os rótulos por outra fonte pública: a aba `4G`
da planilha Source Data da Nature fornece as nove concentrações e os nove scores
publicados, e a assinatura independente YF10 está no release oficial. A ligação
entre as caixas locais do JSON de parâmetros e as caixas manuais da Figura 4g,
porém, falhou na porta de reprodução e continua aberta.

### T8b: ground truth e protocolo

- [x] Recuperar os nove rótulos da Figura 4g pela Source Data oficial e fixar a
      assinatura independente YF10 já versionada.
- [x] Converter `TL_POINTS_COORDS` e `BR_POINTS_COORDS` do referencial recortado
      e rotacionado para o referencial do cubo como hipótese geométrica.
- [ ] Validar que essa geometria corresponde ao
      `manually_defined_rectangle_coordinates.json` usado na Figura 4g.
- [x] Reconstruir o desenho experimental primário a partir dos arquivos e do material
      do artigo.
- [x] Definir regiões positivas, controle não induzido e exclusões antes de calcular score.
- [x] Usar assinatura independente de pellets da biblioteca já versionada.
- [x] Proibir extração da assinatura a partir da região de teste.
- [x] Escolher a unidade estatística correta. Pixels vizinhos não serão tratados
      como réplicas independentes.
- [x] Pré-especificar AUC regional como métrica primária, Spearman e contraste
      como secundárias, e proibir Pd@FAR pixel a pixel.

T8b está parcialmente concluído em `results/real_target_protocol.md`. Há nove
rótulos, uma assinatura independente e uma hipótese geométrica explícita.
`hypermix/biohsi_roi.py` torna recorte e rotação reproduzíveis, e
`assets/biohsi_54m_rois.png` audita visualmente as caixas candidatas. A porta de
reprodução falhou com MAE 0,156114 e Pearson 0,375901. A tag oficial executada
diretamente também falhou nessas caixas, com MAE 0,158137 e Pearson 0,145083.
O próximo passo é recuperar o JSON manual ou outra ponte independente de
coordenadas. A análise comparativa não pode avançar por ajuste visual ao score.

### T8d: segundo subconjunto real, pellets com concentração conhecida

- [x] Varrer remotamente os seis subconjuntos não abertos por HTTP `Range`, sem
      baixar os volumes.
- [x] Identificar `rg_bchla_pellets_ctrl` como o único com ground truth embutido
      e `rg_on_sand_24m` como o único que declara controles.
- [x] Baixar e verificar o ZIP de pellets por tamanho e MD5.
- [x] Ler o cubo pelo caminho `bil` do leitor e registrar as cautelas de escala.
- [x] Resolver a geometria da placa por anotação manual congelada, com hash,
      script de regeneração e testes offline.
- [x] Fixar a âncora de orientação pelas letras impressas, independente de sinal.
- [ ] **Bloqueante:** identificar a unidade das concentrações do CSV.
- [ ] **Bloqueante:** estabelecer qual linha do CSV corresponde a qual linha da
      placa, por evidência independente de score.
- [ ] Só então definir métrica primária e unidade estatística para este
      subconjunto, tratando poços como unidades e não pixels.

O eixo de detecção permanece intocado neste subconjunto. A sonda pré-especificada
no pico Qy da bacterioclorofila a não recuperou sinal coerente, e o resultado foi
registrado como negativo em vez de substituído por outra janela escolhida a
posteriori.

### T8c: confronto e aceite

- [x] Implementar o método publicado, fixar a porta e registrar a primeira
      tentativa de reprodução, que falhou.
- [x] Auditar as caixas candidatas executando diretamente a tag oficial.
- [ ] Recuperar as coordenadas manuais da Figura 4g e cruzar a porta de
      reprodução sem reposicionar regiões por score.
- [ ] Comparar método original, MF espacial, matched subspace e RX.
- [ ] Tratar o detector aprendido como análise secundária, sem mudar o critério
      depois de observar os resultados.
- [ ] Reportar sensibilidade por região sem apresentar reamostragem como IC
      biológico populacional.
- [ ] Escrever `results/real_target.json` e `results/real_target.md`.
- [ ] Atualizar site e conclusão pública somente após o resultado reproduzível.

Aceite: existe uma avaliação rastreável sobre expressão biológica medida, com
split, unidade estatística e limitações explícitas. Sucesso não significa que o
aprendizado venceu. Uma falha de transferência também é resultado válido.

## T9: transferência física da assinatura laboratório-sensor

Motivação medida: em `results/realism.md`, o MF espacial cai de 0,994 com alvo
no sensor para 0,913 com alvo laboratorial quando atmosfera é introduzida. No
cenário completo, a comparação é 0,983 contra 0,906.

Hipótese: uma família de assinaturas transformadas por resposta espectral do
sensor, atmosfera e iluminação pode reduzir esse gap sem usar rótulos de teste.

- [x] Definir uma interface `target_transfer` que receba espectro laboratorial,
      comprimentos de onda e metadados do sensor.
- [x] Construir uma biblioteca física de transformações antes da avaliação.
- [x] Estimar parâmetros apenas por metadados ou pixels não rotulados.
- [x] Comparar MF laboratorial, família física, matched subspace e alvo oráculo
      somente quando um oráculo legítimo existir.
- [x] Medir redução pareada do gap, AUC ou métrica regional e Pd@FAR quando
      aplicável, sempre com IC.
- [x] Testar primeiro no simulador calibrado.
- [ ] Testar no bioHSI real somente depois de T8 cruzar a porta geométrica.

T9a foi concluído no simulador em 45 casos pareados. O critério primário da
família física falhou: diferença de AUC -0,191 [-0,217, -0,171] e de Pd@FAR
-0,257 [-0,293, -0,221] contra o alvo laboratorial. Como análise secundária, a
transferência nominal melhorou AUC em 0,022 [0,016, 0,028] e Pd em 0,134
[0,097, 0,169], ficando a 0,002 AUC do oráculo. O resultado motiva validação
independente de uma correção física estreita, sem promover o subespaço amplo e
sem alterar retroativamente o critério primário. Detalhes em
`results/target_transfer.md`.

Aceite: a regra de transformação é reproduzível e não consulta rótulos de
avaliação. O resultado será reportado mesmo se não reduzir o gap.

## T10: alvo retido e detecção cega

Pergunta: quando o espectro exato é retirado, o aprendizado consegue extrair
mais informação que um baseline clássico com o mesmo conhecimento disponível?

- [x] Formalizar regimes oracle, família e alvo desconhecido.
- [x] Impedir que features não-oracle aceitem o alvo exato.
- [x] Executar leave-one-host-out bidirecional nos dois espectros biliverdina
      medidos, excluindo a média canônica que vazaria o alvo retido.
- [x] Comparar MF-centroide, subespaço, RX e dois MLPs com informação pareada.
- [x] Medir AUC e Pd@FAR 1e-3 com IC bootstrap em três fundos reais, dois SNRs
      e quatro seeds.
- [x] Escrever `results/blind.md` e `results/blind.json`.

O MLP familiar perdeu para o MF do centroide em AUC, -0,014
[-0,033, -0,000], e Pd, -0,042 [-0,086, -0,004]. O MLP totalmente cego não
superou RX. Nenhum regime aprendido satisfez o critério. Em contraste, o
centroide construído somente com o outro host atingiu AUC 0,983 contra 0,984 do
oracle. Este é um resultado de robustez familiar estreita entre dois hosts, não
uma demonstração de generalização ampla.

Aceite concluído: o contrato de informação está testado, o resultado é
reproduzível e a conclusão negativa para aprendizado foi preservada.

## Milestone 3: release pública e citável

- [x] Atualizar README, contagem de testes e descrição de incerteza.
- [x] Revisar `CITATION.cff` para não sugerir superioridade ou generalização
      completa do método aprendido.
- [x] Adicionar CI para Python 3.10 a 3.14 no núcleo sem Torch e Python 3.11 com
      a suíte de treino.
- [x] Adicionar `CHANGELOG.md`, `CONTRIBUTING.md` e política de suporte.
- [x] Executar build de sdist e wheel, validação de metadados e instalação em
      ambiente limpo.
- [x] Publicar `hypermix` no PyPI.
- [x] Criar release `v0.5.0` no GitHub.
- [x] Integrar a release ao Zenodo e registrar o DOI no README e no
      `CITATION.cff`.

Aceite: um usuário externo consegue instalar a versão publicada, executar um
exemplo e reproduzir ao menos um benchmark a partir de um clone limpo.

A infraestrutura e os artefatos foram validados nas execuções `30966762668` e
`30966867000` do GitHub Actions. O candidato `0.5.0`, inicialmente fixado no
commit `ddced5b`, passou novamente pela CI completa na execução `30967741908`.
A tag publicada aponta para `e60cef1`; PyPI recebeu os artefatos por OIDC, e o
Zenodo preservou a tag no registro `10.5281/zenodo.21799951`. O Milestone 3 está
concluído.

## T11: limite operacional de detecção

Pergunta: qual é a menor abundância simulada que mantém Pd maior ou igual a
0,80 sob um orçamento de falso-alarme calibrado fora da avaliação?

- [x] Fixar ruído absoluto por sensor antes de variar abundância.
- [x] Separar oito seeds de calibração sem alvo e 12 seeds de avaliação.
- [x] Validar o FAR obtido em cenas sem alvo independentes.
- [x] Avaliar FWHM 8, 12 e 20 nm, FAR 1e-2 e 1e-3 e abundância 1% a 20%.
- [x] Reportar LOD nominal e conservador, curvas de Pd e IC bootstrap.
- [x] Escrever `results/lod.md`, `.json` e `lod_curves.png`.

Em FAR 1e-2, o LOD nominal foi 15% para 8 e 12 nm e 20% para 20 nm. O
LOD conservador foi 20% para 8 e 12 nm e ficou acima da grade para 20 nm.
Em FAR 1e-3, nenhum sensor alcançou Pd 0,80 até 20%. Todos os thresholds finais
respeitaram o budget médio em seeds independentes.

Aceite concluído: o resultado informa explicitamente o budget, a meta de Pd, o
IC e quando o LOD está acima da faixa avaliada. Ele permanece condicionado ao
simulador e ao MF com alvo exato.

## T12: abundância calibrada e intervalos

Motivação medida: o unmixer melhora Pearson r nas três cenas atuais, mas em
Salinas sua target MAE é 0,0237 contra 0,0073 do MF. Correlação alta não elimina
viés de escala.

- [x] Separar treino, calibração de escala, calibração conformal e avaliação.
- [x] Calibrar a escala de abundância sem usar os rótulos da avaliação.
- [x] Adicionar intervalos split-conformal agrupados por caso.
- [x] Medir MAE, viés, cobertura e largura média dos intervalos.
- [x] Avaliar no simulador implantado. A extensão bioHSI continua dependente do
      ground truth e das coordenadas de T8.
- [x] Escrever `results/abundance_uncertainty.md`, `.json` e `.png` com IC.

Aceite concluído: a estimativa quantitativa informa erro e cobertura, não apenas
ranking ou correlação. O MF calibrado teve MAE 0,0110 e largura 0,0719; o
unmixer, 0,0136 e 0,0815. A diferença de MAE não foi significativa, mas o
unmixer teve viés absoluto e largura significativamente maiores. Não houve
vantagem calibrada do aprendizado.

## Publicação e comunidade

- [x] Criar o esqueleto e a versão interna 0.1 do preprint, centrados na
      auditoria de validade e nos resultados negativos reproduzíveis.
- [x] Registrar decisões, comandos, limitações e hashes dos resultados em um
      manifesto verificável.
- [x] Publicar um protocolo mínimo de reprodução externa a partir de clone
      limpo, com saída esperada explícita.
- [x] Preparar formulários verificáveis para reprodução externa e validação de
      dados, sem abrir comunicação pública em nome de terceiros.
- [x] Abrir a issue pública de reprodução externa, etiquetada como
      `good first issue`, `help wanted` e `data validation`.
- [x] Gerar tabela, figura de contrastes e proveniência do manuscrito
      diretamente dos JSONs, com verificação de drift no CI.
- [ ] Obter ao menos uma instalação ou reprodução por pessoa externa.
- [ ] Considerar JOSS somente depois de histórico público suficiente, uso
      científico demonstrável e práticas abertas contínuas.
- [ ] Incluir declaração transparente de uso de IA em eventual submissão.

### T13: estado atual

O pacote em `publication/` contém oito afirmações e 16 artefatos fixados por
SHA-256. `scripts/verify_evidence_manifest.py` verifica a cadeia inteira sem
dependências científicas. A versão interna 0.1 do manuscrito está pronta em
pt-BR, mas não deve apresentar T8 como concluído. A
[issue pública de reprodução externa](https://github.com/JVLegend/HyperMix/issues/2)
fixa o commit, o comando, a saída esperada e os metadados de aceite. O próximo
aceite é uma execução por pessoa externa e uma resposta dos autores sobre as
coordenadas da Figura 4g. Os formulários de issue exigem proveniência, comandos
e proteção contra seleção de regiões por score.

O T13c removeu a transcrição manual da tabela principal. O gerador padrão liga
os oito eixos aos JSONs, atualiza o bloco delimitado do manuscrito, produz um
SVG vetorial e fixa hashes das fontes. O CI falha se qualquer um dos quatro
materiais sincronizados ficar desatualizado.

## O que não entra no caminho crítico

- Treinar uma arquitetura maior sem hipótese causal nova.
- Selecionar um regime apenas porque favorece o detector aprendido.
- Tratar pixels correlacionados como milhares de réplicas independentes.
- Atualizar o observatório com números não gerados pelos scripts versionados.
- Apresentar alvo implantado como validação remota de expressão biológica.
