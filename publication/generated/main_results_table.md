# Tabela principal gerada

Não edite manualmente. Execute `python scripts/build_publication_assets.py`.

| Eixo | Contraste principal | Resultado com IC 95% | Veredito |
|---|---|---|---|
| Fundo auto-supervisionado, T7a | autoencoder espacial menos MF espacial | AUC -0,011 [-0,023, -0,003]; Pd -0,325 [-0,517, -0,142] | aprendizado pior |
| Incerteza, T7b | ensemble menos MF espacial calibrado | NLL +0,01026 [0,00448, 0,01778]; ECE +0,00397 [0,00208, 0,00560] | aprendizado pior |
| Bandas, T7c | top-3 menos todas as bandas | AUC espacial -0,0356 [-0,0917, -0,0005]; menor k descritivo 20 | três bandas não bastaram |
| Alvo real, T8 | reprodução da Figura 4g nas caixas candidatas | MAE 0,156114; Pearson 0,375901 | porta bloqueada |
| Transferência, T9 | família física menos alvo laboratorial | AUC -0,191 [-0,217, -0,171]; Pd -0,257 [-0,293, -0,221] | aprendizado pior |
| Alvo retido, T10 | MLP familiar menos MF familiar | AUC -0,0135 [-0,0326, -0,0002]; Pd -0,0417 [-0,0859, -0,0036] | aprendizado pior |
| Limite, T11 | LOD em FAR 1e-2 e referência em FAR 1e-3 | nominal 15% a 20% em FAR 1e-2; >20% em FAR 1e-3 | resultado do simulador |
| Abundância, T12 | unmixer menos MF | MAE +0,0026 [-0,0006, 0,0059]; largura +0,0096 [0,0090, 0,0102] | MAE inconclusiva; intervalo pior |
