# Matriz de evidências do HyperMix

Esta matriz liga cada afirmação principal a um comando versionado, aos
artefatos resultantes, a checksums SHA-256 e à limitação que restringe sua
interpretação. O arquivo executável correspondente é
`publication/evidence_manifest.json`.

## Estado das afirmações

| ID | Afirmação auditável | Estado | Fonte principal | Limitação decisiva |
|---|---|---|---|---|
| T7a | O autoencoder de fundo espacial foi inferior ao MF espacial em AUC e Pd@FAR | sustentada | [`results/background.md`](../results/background.md) | alvo implantado e uma única arquitetura rasa |
| T7b | O ensemble calibrado teve NLL e ECE piores que MF espacial + Platt | sustentada | [`results/uncertainty.md`](../results/uncertainty.md) | calibração nos mesmos três fundos |
| T7c | Três bandas não preservaram a AUC do MF espacial completo | sustentada | [`results/band_sparsity.md`](../results/band_sparsity.md) | seleção target-aware, sem validade universal |
| T8 | A porta da Figura 4g falhou nas caixas candidatas | bloqueada | [`results/real_target_reproduction.md`](../results/real_target_reproduction.md) | coordenadas manuais ausentes |
| T9 | A família ampla falhou; a transferência nominal melhorou apenas na análise secundária | sustentada | [`results/target_transfer.md`](../results/target_transfer.md) | implantes sintéticos, sem validação independente |
| T10 | Nenhum MLP venceu o clássico com o mesmo conhecimento do alvo | sustentada | [`results/blind.md`](../results/blind.md) | somente dois hosts medidos |
| T11 | O LOD simulado ficou em 15% a 20% em FAR 1e-2 | sustentada | [`results/lod.md`](../results/lod.md) | fração do simulador, não concentração |
| T12 | A MAE agregada foi inconclusiva e os intervalos aprendidos foram mais largos | inconclusiva para MAE | [`results/abundance_uncertainty.md`](../results/abundance_uncertainty.md) | abundância condicional à detecção |

## Verificação automática

Em um clone limpo, sem baixar cubos e sem instalar dependências científicas:

```bash
python scripts/verify_evidence_manifest.py
```

Saída esperada:

```text
Evidence bundle verified: 8 claims, 16 files.
```

O comando falha se um artefato estiver ausente, se um checksum divergir, se
houver IDs duplicados ou se um caminho tentar sair do repositório.

## Sincronização do manuscrito

O comando abaixo extrai os valores dos oito JSONs, atualiza o bloco delimitado
da tabela principal e gera uma figura SVG de contrastes e um arquivo de
proveniência com os hashes das fontes:

```bash
python scripts/build_publication_assets.py
python scripts/build_publication_assets.py --check
```

O modo `--check` não escreve arquivos. Ele falha se a tabela, a figura, a
proveniência ou o bloco do manuscrito estiverem desatualizados. Na figura, cada
linha usa escala própria e somente direção e cruzamento do zero são comparáveis.

## Regras de leitura para o preprint

1. `supported` significa sustentado pelo protocolo e pelo artefato indicado,
   dentro das limitações registradas.
2. `inconclusive` não significa equivalência. Significa que o intervalo do
   contraste principal inclui zero.
3. `blocked` não é um resultado de detector. No T8, a geometria precisa ser
   validada antes de qualquer comparação de métodos.
4. Resultados com implantes digitais não podem ser descritos como validação de
   expressão biológica remota.
5. A afirmação transversal continua sendo negativa: nenhum método aprendido
   superou de forma robusta o MF espacial bem calibrado nos regimes concluídos.
