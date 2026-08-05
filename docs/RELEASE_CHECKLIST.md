# Checklist da release pública

Estado em 2026-08-04: preparação em andamento. A versão `0.5.0` ainda não foi
publicada no PyPI, GitHub ou Zenodo.

## Pré-release

- [x] Confirmar CI verde em Python 3.10 a 3.14, suíte de pesquisa, pacote e site.
- [ ] Fixar o conteúdo da release e atualizar `CHANGELOG.md`.
- [ ] Sincronizar a versão em `pyproject.toml` e `CITATION.cff`.
- [x] Atualizar a contagem de testes e links no README.
- [x] Executar `python -m build` e `python -m twine check dist/*`.
- [x] Instalar a wheel em ambiente limpo e executar um smoke test.
- [x] Conferir que dados curados de `hypermix.data` estão dentro da wheel.
- [x] Verificar que nenhum cubo baixado, segredo ou ambiente entrou no pacote.
- [x] Executar `npm audit --omit=dev` e os builds de Sites e Vercel.

## Publicação

- [ ] Criar o projeto `hypermix` no PyPI e configurar Trusted Publishing para
      `JVLegend/HyperMix` e o workflow aprovado.
- [ ] Adicionar uma etapa OIDC com `id-token: write` somente depois dessa
      configuração e de aprovação explícita para publicar.
- [ ] Criar a tag assinada `v0.5.0` no commit validado.
- [x] Conferir os artefatos produzidos por `release-artifacts.yml`.
- [ ] Publicar a release no GitHub com notas derivadas do changelog.
- [ ] Publicar sdist e wheel no PyPI sem reutilizar o número da versão.
- [ ] Ativar ou conferir a integração do repositório com Zenodo.
- [ ] Registrar o DOI no README e em `CITATION.cff`.

## Pós-release

- [ ] Instalar `hypermix==0.5.0` em um ambiente vazio.
- [ ] Executar o exemplo mínimo do README.
- [ ] Abrir uma issue para qualquer divergência entre pacote, tag e documentação.
- [ ] Registrar uma reprodução externa quando ela existir.

O workflow de artefatos não publica automaticamente. Essa separação evita que
uma tag ou execução manual envie uma versão antes da configuração do PyPI e da
auditoria final.
