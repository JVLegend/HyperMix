# Gates de release antes da publicação

Status: pronto para publicar
Imagem sugerida: badge de CI do repositório após a primeira execução verde

Enquanto a coordenada científica está bloqueada externamente, o HyperMix pode
avançar em uma frente independente: tornar o software instalável, verificável e
citável por outras pessoas.

A preparação da próxima release agora cobre quatro superfícies separadas:

1. o núcleo NumPy e SciPy em Python 3.10 a 3.14;
2. a suíte completa com PyTorch em Python 3.11;
3. o sdist e a wheel, incluindo os dados espectrais curados;
4. os builds do observatório para Sites e Vercel.

O primeiro build local encontrou dois problemas antes que chegassem a uma
release. O metadado moderno de licença PEP 639 conflitava com um classificador
legado redundante, e o smoke test procurava um nome antigo de arquivo. Ambos
foram corrigidos. A wheel então passou a validação de metadados, foi instalada
em um ambiente limpo e conseguiu ler o recurso empacotado real.

Também atualizamos as dependências públicas do observatório. O grafo de
produção passou na auditoria sem vulnerabilidades conhecidas. O tooling local
de Cloudflare ainda herda avisos em uma dependência de desenvolvimento sem
correção compatível disponível, por isso esse risco permanece explícito e
separado do bundle de produção.

A primeira CI remota ficou verde nas oito combinações e superfícies, e o
workflow manual preservou sdist e wheel como artefatos sem publicá-los. As
execuções auditáveis estão em:

- https://github.com/JVLegend/HyperMix/actions/runs/30966762668
- https://github.com/JVLegend/HyperMix/actions/runs/30966867000

Isso não significa que `0.5.0` já foi publicada. PyPI, tag do GitHub e DOI do
Zenodo continuam pendentes até a aprovação do checklist final.
