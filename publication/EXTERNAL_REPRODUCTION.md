# Protocolo mínimo de reprodução externa

## Objetivo

Permitir que uma pessoa sem o ambiente de desenvolvimento do autor confirme,
em menos de um minuto, que os artefatos citados pela narrativa pública são os
mesmos arquivos fixados pela matriz de evidências.

## Caminho mínimo, sem dependências

```bash
git clone https://github.com/JVLegend/HyperMix.git
cd HyperMix
python scripts/verify_evidence_manifest.py
```

Saída esperada:

```text
Evidence bundle verified: 8 claims, 16 files.
```

Este comando verifica integridade e rastreabilidade. Ele não reexecuta treino,
bootstrap nem downloads de dados.

## Caminho científico completo

Crie um ambiente Python 3.11, instale os extras e execute a suíte:

```bash
python3.11 -m venv .venv-reproduce
. .venv-reproduce/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[train,reproduce,dev]"
python -m pytest -q
python scripts/fetch_data.py
```

Cada entrada de `publication/evidence_manifest.json` contém o comando que gera
seu resultado. Os experimentos com treino podem levar vários minutos. O T8
também requer o arquivo bioHSI de aproximadamente 629 MB:

```bash
python scripts/fetch_biohsi.py --dataset rg_on_sand_induction_54m.zip
python scripts/reproduce_biohsi_54m.py
```

O resultado esperado do T8 atual é uma porta de reprodução não satisfeita. Uma
pessoa externa não deve mover as regiões para melhorar a concordância.

## O que registrar ao reproduzir

- sistema operacional e versão do Python;
- commit testado e versão instalada;
- saída do verificador e da suíte;
- hashes divergentes, se houver;
- comandos completos de qualquer experimento reexecutado;
- ausência ou presença do arquivo manual de coordenadas da Figura 4g.

Uma reprodução externa pode ser reportada em uma issue pública, inclusive se
falhar. Falhas de instalação, divergência numérica e documentação ambígua são
resultados úteis para o benchmark.
