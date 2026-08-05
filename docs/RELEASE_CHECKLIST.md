# Checklist da release pública

Estado em 2026-08-04: a versão `0.5.0` foi publicada no GitHub, PyPI e Zenodo.
O DOI da versão é `10.5281/zenodo.21799951`.

## Pré-release

- [x] Confirmar CI verde em Python 3.10 a 3.14, suíte de pesquisa, pacote e site.
- [x] Fixar o conteúdo da release e atualizar `CHANGELOG.md`.
- [x] Sincronizar a versão em `pyproject.toml` e `CITATION.cff`.
- [x] Atualizar a contagem de testes e links no README.
- [x] Executar `python -m build` e `python -m twine check dist/*`.
- [x] Instalar a wheel em ambiente limpo e executar um smoke test.
- [x] Conferir que dados curados de `hypermix.data` estão dentro da wheel.
- [x] Verificar que nenhum cubo baixado, segredo ou ambiente entrou no pacote.
- [x] Executar `npm audit --omit=dev` e os builds de Sites e Vercel.
- [x] Automatizar o gate de consistência entre tag, pacote, citação, changelog,
      notas e workflow OIDC.

## Publicação

- [x] Criar o environment `pypi` no GitHub, sem tokens permanentes.
- [x] Criar o projeto `hypermix` no PyPI e configurar Trusted Publishing para
      `JVLegend/HyperMix` e o workflow aprovado.
- [x] Adicionar uma etapa OIDC com `id-token: write`; ela só executa quando uma
      release do GitHub é publicada.
- [x] Criar a tag anotada `v0.5.0` no commit validado `e60cef1`. A tag não foi
      assinada porque não havia identidade de assinatura configurada.
- [x] Conferir os artefatos produzidos por `release-artifacts.yml`.
- [x] Publicar a release no GitHub com notas derivadas do changelog.
- [x] Publicar sdist e wheel no PyPI sem reutilizar o número da versão.
- [x] Ativar e conferir a integração do repositório com Zenodo.
- [x] Registrar o DOI no README e em `CITATION.cff`.

## Pós-release

- [x] Instalar `hypermix==0.5.0` em um ambiente vazio e sem cache.
- [x] Executar o exemplo mínimo do README.
- [ ] Abrir uma issue para qualquer divergência entre pacote, tag e documentação.
- [ ] Registrar uma reprodução externa quando ela existir.

O workflow de artefatos não publica automaticamente. Essa separação evita que
uma tag ou execução manual envie uma versão antes da configuração do PyPI e da
auditoria final.
