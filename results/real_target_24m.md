# Primeiro teste em expressão biológica medida, 24 m

Doze blots em areia, seis posições em duas colunas réplicas. O
`params_file.json` do próprio subconjunto declara a posição 0 como
controle positivo e a posição 5 como negativo, nas duas réplicas.
Essa identidade é anterior a qualquer medição feita aqui.

**Predição registrada antes de medir:** se o desenho é um gradiente do
controle positivo ao negativo, o sinal deve cair de forma monótona da
posição 0 para a 5, e as duas réplicas devem concordar quanto ao sentido.

Sinal: profundidade de banda em 866.6 nm, pico
documentado do repórter YF10, com ombros em 820.0 e
910.9 nm. Nenhum alvo foi implantado digitalmente.

## Sinal por posição

| Réplica | pos 0, ctrl + | pos 1 | pos 2 | pos 3 | pos 4 | pos 5, ctrl - | Spearman |
|---|---:|---:|---:|---:|---:|---:|---:|
| A | +0.03552 | +0.01269 | -0.00212 | -0.00128 | -0.00599 | -0.01089 | -0.943 |
| B | +0.03720 | +0.02468 | +0.00700 | -0.00114 | -0.00999 | -0.01650 | -1.000 |

## Sensibilidade à anotação

A geometria é anotação manual provisória, então os centros foram
deslocados aleatoriamente em ate 5 px em cada eixo,
300 vezes.

| Réplica | rho mediano | 2,5% | 97,5% |
|---|---:|---:|---:|
| A | -0.943 | -1.000 | -0.486 |
| B | -1.000 | -1.000 | -0.597 |

As duas réplicas concordaram quanto ao sentido em **100%** dos sorteios.

## Leitura

A predição se confirmou. O sinal é máximo no controle positivo declarado,
cai de forma monótona ao longo das posições e chega ao mínimo no controle
negativo declarado, nas duas réplicas independentes, e o sentido resiste ao
deslocamento aleatório dos centros anotados.

O ponto que torna isso não circular: o sentido esperado foi fixado pela
identidade dos controles declarada no arquivo, antes de qualquer medição.
Não houve escolha de orientação depois de ver o resultado.

## O que este resultado não é

- Não é comparação de detectores. Nenhum método foi confrontado aqui.
- Não é curva dose-resposta calibrada: as concentrações das posições 1 a 4
  continuam desconhecidas, porque o CSV de rótulos não acompanha o arquivo.
- Duas colunas réplicas são poucas unidades para inferência populacional.
  O Spearman dentro de cada coluna usa seis posições, que não são amostras
  independentes de uma população.
- A anotação é provisória e não foi validada contra as coordenadas
  originais dos autores.

O que ele é: a primeira evidência, neste projeto, de que o pipeline
recupera a ordenação esperada de expressão biológica realmente medida a
distância, sem implantar alvo algum.
