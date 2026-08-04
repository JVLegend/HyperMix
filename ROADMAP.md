# Roadmap do HyperMix

Atualizado em 2026-08-03. Este arquivo define a ordem de trabalho depois das
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
4. o software ainda não possui uma distribuição pública completa com DOI.

## Ordem executiva

| Ordem | Frente | Resultado que destrava | Dependência |
|---:|---|---|---|
| 1 | T8, bioHSI real | Primeiro teste sem implantação digital | Nenhuma |
| 2 | T9, transferência da assinatura | Reduzir o gap laboratório-sensor sem rótulos de teste | Metadados de T8 |
| 3 | Milestone 3, release | Instalação pública, versão citável e CI | Documentação auditada |
| 4 | T10, abundância calibrada | Estimativa quantitativa com intervalos | Splits e alvos de T8 |
| 5 | Publicação | Preprint do benchmark e preparação para revisão de software | T8/T9 e uso público |

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
- [ ] Baixar `rg_on_sand_induction_54m.zip` para `data/biohsi/`.
- [ ] Inventariar o conteúdo do ZIP sem assumir formato, orientação ou unidade.
- [ ] Documentar cubos, comprimentos de onda, referências branco/escuro,
      controles, regiões experimentais e metadados ausentes.
- [ ] Implementar o loader somente depois dessa inspeção.

Próxima ação bloqueante: concluir a transferência retomável do ZIP de 54 m,
verificar o MD5 e executar `--inspect`. O código oficial confirma o caminho de
um cubo ENVI, um CSV de níveis experimentais, uma assinatura independente de
pellets e ROIs retangulares manuais. Dimensões, binário pareado, unidades e
semântica completa dos rótulos continuam em aberto até a inspeção dos dados.

### T8b: ground truth e protocolo

- [ ] Reconstruir o desenho experimental a partir dos arquivos e do material
      do artigo.
- [ ] Definir regiões positivas, controles e exclusões antes de calcular score.
- [ ] Usar assinatura independente de pellets ou a biblioteca já versionada.
- [ ] Proibir extração da assinatura a partir da região de teste.
- [ ] Escolher a unidade estatística correta. Pixels vizinhos não serão tratados
      como réplicas independentes.
- [ ] Pré-especificar a métrica primária conforme o ground truth disponível:
      contraste ou classificação por região; Pd@FAR somente com máscara pixel a
      pixel defensável.

### T8c: confronto e aceite

- [ ] Reproduzir primeiro o método de contraste do trabalho original.
- [ ] Comparar método original, MF espacial, matched subspace e RX.
- [ ] Tratar o detector aprendido como análise secundária, sem mudar o critério
      depois de observar os resultados.
- [ ] Calcular intervalos sobre regiões, parcelas ou réplicas independentes.
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

- [ ] Definir uma interface `target_transfer` que receba espectro laboratorial,
      comprimentos de onda e metadados do sensor.
- [ ] Construir uma biblioteca física de transformações antes da avaliação.
- [ ] Estimar parâmetros apenas por metadados ou pixels não rotulados.
- [ ] Comparar MF laboratorial, família física, matched subspace e alvo oráculo
      somente quando um oráculo legítimo existir.
- [ ] Medir redução pareada do gap, AUC ou métrica regional e Pd@FAR quando
      aplicável, sempre com IC.
- [ ] Testar primeiro no simulador calibrado e depois no bioHSI real.

Aceite: a regra de transformação é reproduzível e não consulta rótulos de
avaliação. O resultado será reportado mesmo se não reduzir o gap.

## Milestone 3: release pública e citável

- [ ] Atualizar README, contagem de testes e descrição de incerteza.
- [ ] Revisar `CITATION.cff` para não sugerir superioridade ou generalização
      completa do método aprendido.
- [ ] Adicionar CI para Python 3.10 a 3.14 no núcleo sem Torch e Python 3.11 com
      a suíte de treino.
- [ ] Adicionar `CHANGELOG.md`, `CONTRIBUTING.md` e política de suporte.
- [ ] Executar build de sdist e wheel, validação de metadados e instalação em
      ambiente limpo.
- [ ] Publicar `hypermix` no PyPI.
- [ ] Criar release `v0.5.0` no GitHub.
- [ ] Integrar a release ao Zenodo e registrar o DOI no README e no
      `CITATION.cff`.

Aceite: um usuário externo consegue instalar a versão publicada, executar um
exemplo e reproduzir ao menos um benchmark a partir de um clone limpo.

## T10: abundância calibrada e intervalos

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
