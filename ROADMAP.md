# Roadmap do HyperMix

Atualizado em 2026-08-05. Este arquivo define a ordem de trabalho depois das
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
3. abundância e decisão operacional ainda precisam de calibração fora da cena;
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
| 5 | T11, abundância calibrada | Estimativa quantitativa com intervalos | Splits e alvos de T8 |
| 6 | Publicação | Preprint do benchmark e preparação para revisão de software | T8/T9 e uso público |

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

## T11: abundância calibrada e intervalos

Motivação medida: o unmixer melhora Pearson r nas três cenas atuais, mas em
Salinas sua target MAE é 0,0237 contra 0,0073 do MF. Correlação alta não elimina
viés de escala.

- [ ] Separar treino, calibração e avaliação por cena ou experimento.
- [ ] Calibrar a escala de abundância sem usar os rótulos da avaliação.
- [ ] Adicionar intervalos de predição por bootstrap ou método conformal.
- [ ] Medir MAE, viés, cobertura e largura média dos intervalos.
- [ ] Avaliar em simulação e, se o ground truth permitir, nos níveis de indução
      do bioHSI.
- [ ] Escrever `results/abundance_uncertainty.md` e `.json` com IC.

Aceite: a estimativa quantitativa informa erro e cobertura, não apenas ranking
ou correlação.

## Publicação e comunidade

- [ ] Preparar um preprint de benchmark depois de T8 e T9, centrado na auditoria
      de validade e nos resultados negativos reproduzíveis.
- [ ] Registrar decisões pré-especificadas e hashes dos resultados.
- [ ] Abrir issues etiquetadas como `good first issue` e `data validation`.
- [ ] Obter ao menos uma instalação ou reprodução por pessoa externa.
- [ ] Considerar JOSS somente depois de histórico público suficiente, uso
      científico demonstrável e práticas abertas contínuas.
- [ ] Incluir declaração transparente de uso de IA em eventual submissão.

## O que não entra no caminho crítico

- Treinar uma arquitetura maior sem hipótese causal nova.
- Selecionar um regime apenas porque favorece o detector aprendido.
- Tratar pixels correlacionados como milhares de réplicas independentes.
- Atualizar o observatório com números não gerados pelos scripts versionados.
- Apresentar alvo implantado como validação remota de expressão biológica.
