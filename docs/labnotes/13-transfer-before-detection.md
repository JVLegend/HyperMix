# Antes de detectar, transfira a assinatura

Status: pronto para publicar
Imagem sugerida: espectro laboratorial antes e depois da resposta do sensor

Um detector hiperespectral precisa de uma assinatura alvo. O problema é que a
assinatura medida no laboratório não chega intacta a um sensor remoto. A
resposta espectral mistura comprimentos de onda vizinhos, a atmosfera introduz
absorções e a iluminação altera a escala observada.

O T9 do HyperMix transforma esse problema em uma etapa explícita. O novo módulo
recebe o espectro laboratorial, seus comprimentos de onda e metadados físicos do
sensor. Ele pode aplicar:

- reamostragem para as bandas do sensor;
- resposta espectral gaussiana;
- atmosfera simples e radiância de caminho;
- pequeno deslocamento espectral;
- ganho de iluminação.

Também é possível construir uma família de assinaturas plausíveis. Todos os
parâmetros são definidos antes da avaliação. O módulo não recebe rótulos,
máscaras de alvo nem scores do detector.

Essa separação importa. Se a assinatura transferida melhorar a detecção, a
causa testada é modelagem física, não uma rede que aprendeu com o gabarito. Se
ela falhar, o resultado também localiza o problema: a família física escolhida
não descreveu o domínio do sensor de forma útil.

O primeiro experimento usa espectro medido do bioHSI, fundos medidos do USGS,
três larguras de resposta espectral, cinco atmosferas por seed e três níveis de
target SNR. O alvo continua implantado, portanto este teste não substitui a
validação biológica T8.

A próxima nota apresenta o resultado, incluindo a parte que funcionou e a que
falhou.
