# Como contribuir

Contribuições de código, documentação e validação independente são bem-vindas.
O HyperMix é um benchmark científico: toda afirmação quantitativa precisa vir
de um script versionado e de um artefato em `results/`.

## Ambientes

O núcleo NumPy e SciPy suporta Python 3.10 a 3.14:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
pytest -q
```

A suíte completa usa Python 3.11 por causa das rodas disponíveis do PyTorch:

```bash
python3.11 -m venv .venv-train
. .venv-train/bin/activate
python -m pip install -e ".[train,reproduce,dev]"
pytest -q
```

O observatório requer Node.js 22:

```bash
cd webapp
npm ci
npm run lint
npm run typecheck
npm run build:vercel
```

## Antes de enviar uma mudança

1. Abra uma issue quando a mudança alterar protocolo, resultado ou interface
   pública.
2. Adicione testes para comportamento novo ou corrigido.
3. Execute a suíte compatível com a mudança e registre o comando real.
4. Não versione cubos baixados, credenciais, ambientes virtuais ou resultados
   gerados fora dos scripts do repositório.
5. Atualize `STATUS.md` somente com fatos medidos e `ROADMAP.md` somente quando
   o critério de aceite tiver sido cumprido.
6. Preserve resultados negativos. Não selecione regimes, regiões ou métricas
   depois de observar qual método venceu.

Os dados grandes são baixados por scripts e validados por manifestos. Consulte
`dataset/` antes de adicionar uma nova fonte.
