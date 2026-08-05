# O prior físico estreito funcionou, a família ampla não

Status: pronto para publicar
Imagem sugerida: painel T9 do HyperMix Observatory

O T9 avaliou 45 casos pareados. Cada caso usou o mesmo cubo, máscara e ruído
para quatro formas de fornecer a assinatura ao detector:

1. espectro laboratorial sem transformação;
2. transferência nominal usando o FWHM declarado do sensor e atmosfera central;
3. família física de nove variantes combinada por matched subspace;
4. alvo oráculo que conhece a transformação exata da cena.

O resultado agregado foi:

| Alvo | AUC [IC 95%] | Pd@FAR 1e-3 [IC 95%] |
|---|:---:|:---:|
| Laboratorial | 0,968 [0,962, 0,974] | 0,626 [0,587, 0,672] |
| Transferência nominal | 0,990 [0,988, 0,992] | 0,760 [0,727, 0,787] |
| Família física | 0,777 [0,749, 0,799] | 0,369 [0,340, 0,394] |
| Oráculo | 0,992 [0,991, 0,994] | 0,778 [0,744, 0,805] |

O critério primário estava congelado para a família física. Ela precisava
superar o alvo laboratorial em AUC e Pd@FAR com os dois intervalos acima de
zero. Falhou com folga: diferença de AUC -0,191 e de Pd -0,257, ambas com IC
inteiramente abaixo de zero.

A transferência nominal era um método declarado, mas não o método do critério
primário. Na análise secundária, ela melhorou AUC em 0,022 [0,016, 0,028] e Pd
em 0,134 [0,097, 0,169]. Sua distância média ao oráculo ficou em apenas 0,002
AUC.

A leitura honesta é dupla. Uma correção física estreita baseada em metadados
quase fechou o gap laboratório-sensor neste simulador. Ao mesmo tempo, ampliar a
assinatura para um subespaço de variantes introduziu direções que destruíram a
detecção. Mais flexibilidade não significou mais robustez.

Este não é um triunfo do aprendizado e não é validação em expressão biológica
remota. É um resultado causal sintético a favor de uma transformação física
específica, com uma falha igualmente importante da alternativa mais ampla. O
próximo teste legítimo é independente e depende da recuperação das coordenadas
do T8.
