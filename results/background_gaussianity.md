# O fundo medido é gaussiano?

A otimalidade do matched filter vale sob fundo gaussiano com alvo
conhecido. Este teste mede a premissa diretamente, em duas cenas reais
sem alvo, e não usa rótulo algum.

A covariância é ajustada em metade dos pixels e a distância de
Mahalanobis é avaliada na outra metade. Sob gaussiana multivariada, o
quadrado dessa distância segue qui-quadrado com grau igual ao número de
bandas, cujos quantis são obtidos por simulação.

| Cena | Pixels | Bandas | Px por dim. | Curtose exc. mediana | Bandas com exc. > 1 | Assimetria mediana |
|---|---:|---:|---:|---:|---:|---:|
| pellets, poços vazios | 29,424 | 62 | 474.6 | 5.20 | 62 | 1.84 |
| voo 54 m, fundo | 60,000 | 46 | 1304.3 | 0.05 | 9 | 0.52 |

## Quantis da distância de Mahalanobis ao quadrado

| Cena | Quantil | Observado | Esperado se gaussiano | Razão |
|---|---|---:|---:|---:|
| pellets, poços vazios | 0.5 | 45.7 | 61.3 | 0.75 |
| pellets, poços vazios | 0.9 | 89.1 | 76.6 | 1.16 |
| pellets, poços vazios | 0.99 | 349.3 | 90.8 | 3.85 |
| pellets, poços vazios | 0.999 | 1122.4 | 102.1 | 10.99 |
| voo 54 m, fundo | 0.5 | 41.9 | 45.3 | 0.93 |
| voo 54 m, fundo | 0.9 | 70.8 | 58.6 | 1.21 |
| voo 54 m, fundo | 0.99 | 115.1 | 70.9 | 1.62 |
| voo 54 m, fundo | 0.999 | 562.8 | 81.6 | 6.90 |

## Leitura

O padrão é o mesmo nas duas cenas, apesar de sensores, distâncias e
cenários diferentes: o miolo da distribuição é compatível com gaussiano
e a cauda não é. Nas medianas a razão fica abaixo ou perto de 1, e a
partir do quantil 0,99 ela cresce muito.

Isso importa por um motivo operacional preciso. A taxa de falso alarme
é definida exatamente pela cauda do fundo. Detecção a FAR de 1e-3 vive
perto do quantil 0,999, justamente onde a razão medida é de várias
vezes. Um limiar derivado de suposição gaussiana subestima o falso
alarme nessa região.

O resultado também refina, sem contradizer, a conclusão do T7a. Lá a
hipótese era que aprender a estatística do fundo venceria o matched
filter caso o fundo não fosse gaussiano, e o autoencoder testado perdeu.
A medição agora mostra que a porta estava de fato aberta: o fundo tem
cauda pesada. O que falhou foi aquele modelo específico, não a premissa
que motivava a busca.

## O que este teste não separa

Cauda pesada aqui não é sinônimo de ruído não gaussiano do sensor.
Duas fontes ficam confundidas e este protocolo não as distingue:

- **Heterogeneidade de material.** O fundo do voo é tudo que está fora
  das duas janelas experimentais, portanto mistura materiais distintos.
  Uma mistura de classes produz cauda pesada sob um único modelo de
  covariância global, mesmo que cada classe fosse gaussiana.
- **Estrutura óptica.** Os poços vazios contêm bordas, menisco e reflexo
  especular, que são estrutura real da placa e não ruído de sensor. Esse
  reflexo já havia sido identificado ao ajustar a geometria.

Para a decisão operacional as duas fontes têm o mesmo efeito prático,
porque ambas inflam o falso alarme observado em relação ao previsto. Para
explicar o mecanismo, porém, elas precisariam ser separadas, o que exige
um modelo local ou por classe em vez de covariância global.

Este teste descreve as duas cenas medidas disponíveis, não generaliza
para todo fundo natural, e não é por si um resultado de detecção.
