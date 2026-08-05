# O candidato 0.5.0 está pronto, mas ainda não foi publicado

Status: pronto para publicar
Imagem sugerida: badge verde da CI do GitHub

O HyperMix chegou a um release candidate reproduzível para a versão `0.5.0`.
Isto não é ainda uma release no PyPI.

O candidato foi testado em quatro superfícies independentes:

1. núcleo NumPy e SciPy em Python 3.10 a 3.14;
2. suíte completa com PyTorch em Python 3.11;
3. sdist e wheel instalados em ambiente vazio;
4. observatório compilado para Sites e Vercel.

A wheel reportou a versão `0.5.0`, carregou o pacote e encontrou o recurso
espectral curado dentro da distribuição. `twine check` aprovou sdist e wheel. A
execução remota completa ficou verde:

https://github.com/JVLegend/HyperMix/actions/runs/30967741908

A publicação não usará token permanente. Um workflow OIDC foi fixado por SHA e
ligado ao environment `pypi` do GitHub. Quando uma GitHub Release for publicada,
ele reconstruirá os artefatos a partir da tag e pedirá ao PyPI uma credencial de
curta duração.

Ainda falta cadastrar o publisher pendente na conta PyPI, criar a tag e publicar
a release. Depois disso, o pacote será instalado de forma independente e o DOI
do Zenodo será solicitado.

A moldura científica não mudou durante a preparação. Nenhum método aprendido
superou de forma robusta o matched filter espacial nos experimentos concluídos,
e a avaliação do alvo bioHSI real segue pausada pelas coordenadas ausentes.
