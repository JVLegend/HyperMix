# Publicando o HyperMix

Estado da `0.5.0`: publicada no GitHub, PyPI e Zenodo em 2026-08-04. O
procedimento abaixo permanece como registro auditável e base para a próxima
versão.

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

Para a `0.5.0`, o repositório foi habilitado na integração GitHub do Zenodo
depois da GitHub Release. Como a integração não fez ingestão retroativa, o ZIP
exato da tag foi depositado manualmente, sem apagar ou recriar a release e sem
reenviar o pacote ao PyPI. O resultado público é:

- DOI da versão: `10.5281/zenodo.21799951`;
- DOI conceitual: `10.5281/zenodo.21799950`;
- arquivo: `HyperMix-v0.5.0.zip`;
- MD5 no Zenodo: `7ddd27d785bcdad6fd9ccefc66e1c5cb`.

Para versões futuras:

1. entrar em https://zenodo.org/account/settings/github/ com a conta ligada ao
   GitHub;
2. habilitar `JVLegend/HyperMix`;
3. publicar a nova GitHub Release somente depois dos gates;
4. confirmar a ingestão automática do Zenodo e copiar o DOI da versão para o
   README e `CITATION.cff` em um patch posterior.

`.zenodo.json` e `CITATION.cff` contêm a moldura científica honesta. O DOI não
deve ser inventado nem antecipado antes da resposta do Zenodo.
