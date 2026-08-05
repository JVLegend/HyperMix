# HyperMix 0.5.0 está público

Status: publicado
Imagem sugerida: página do pacote no PyPI

O HyperMix `0.5.0` agora pode ser instalado diretamente do Python Package
Index:

```bash
pip install "hypermix[viz]==0.5.0"
```

A publicação foi feita por OIDC, sem guardar um token permanente no GitHub. O
workflow reconstruiu o pacote a partir da tag, executou o gate de consistência,
validou sdist e wheel e enviou os dois arquivos ao PyPI. O publisher pendente
se tornou ativo depois do primeiro upload.

Em seguida, uma instalação independente e sem cache baixou a wheel pública em
um ambiente vazio. Ela confirmou a versão, encontrou o recurso espectral
curado e executou o exemplo mínimo do README. Para `snr_db=10` e `seed=0`, esse
smoke test produziu AUC `0,955064`. Esse número valida a instalação; ele não é
um novo benchmark nem altera a conclusão científica.

Os artefatos públicos têm estes SHA-256:

- wheel: `a8bb453ad75de68d78badcf9bdaa5e0e35deb2c9c92aa2f6c8a284329bb74ae4`;
- sdist: `4e536805d875d4a35ffa525982a1cfc99e7f8e0af425f90f82cc3783788da0c7`.

A versão pública preserva o resultado central do projeto. Nos experimentos
concluídos, nenhum método aprendido superou de forma robusta o matched filter
espacial bem calibrado. A contribuição é o benchmark aberto e auditável.

O próximo registro permanente será o DOI do Zenodo. A integração ainda depende
da autenticação da conta e, portanto, não foi antecipada nem inventada.
