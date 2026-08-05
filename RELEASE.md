# Publicando o HyperMix

Estado da `0.5.0`: publicada no GitHub e no PyPI em 2026-08-04. O procedimento
abaixo permanece como registro auditável e base para a próxima versão.

O HyperMix usa PyPI Trusted Publishing. Não crie token permanente e não salve
credenciais no GitHub ou no repositório.

## Contrato do publisher

Cadastre um publisher pendente em https://pypi.org/manage/account/publishing/
com estes valores exatos:

- projeto PyPI: `hypermix`;
- proprietário GitHub: `JVLegend`;
- repositório: `HyperMix`;
- workflow: `publish-pypi.yml`;
- environment: `pypi`.

O workflow `.github/workflows/publish-pypi.yml` recebe um token OIDC de curta
duração somente quando uma GitHub Release é publicada. Ele faz checkout da tag,
reconstrói sdist e wheel, executa `twine check` e publica os dois artefatos.

## Sequência da versão 0.5.0

1. Confirmar que `main` está limpa, sincronizada e com CI verde.
2. Confirmar que `pyproject.toml` e `CITATION.cff` declaram `0.5.0`.
3. Executar `python scripts/check_release.py --tag v0.5.0`.
4. Configurar o publisher pendente do PyPI com o contrato acima.
5. Conferir o environment `pypi` no GitHub.
6. Criar a tag `v0.5.0` no commit validado.
7. Publicar a GitHub Release usando `docs/releases/v0.5.0.md`.
8. Acompanhar o workflow `Publish to PyPI` até o sucesso.
9. Instalar `hypermix==0.5.0` em ambiente vazio e executar o exemplo mínimo.

O gate também roda na CI e antes do upload. Ele bloqueia tag divergente,
versões desencontradas, data inconsistente, notas ausentes, permissões OIDC
incorretas e actions sem pin por SHA.

Não reutilize `0.5.0` se qualquer arquivo chegar ao PyPI. Versões publicadas são
imutáveis.

## DOI do Zenodo

Depois da publicação:

1. entrar em https://zenodo.org/account/settings/github/ com a conta ligada ao
   GitHub;
2. habilitar `JVLegend/HyperMix`;
3. confirmar que a release `v0.5.0` foi arquivada;
4. copiar o DOI para o README e `CITATION.cff` em um patch posterior.

`.zenodo.json` e `CITATION.cff` já contêm a moldura científica honesta. O DOI
não deve ser inventado nem antecipado antes da resposta do Zenodo.
