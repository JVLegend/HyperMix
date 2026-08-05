# A release agora falha de forma fechada

Status: pronto para publicar
Imagem sugerida: diagrama tag, pacote, citação e PyPI

Um pacote científico pode passar nos testes e ainda sair com a tag errada, uma
citação antiga ou notas de outra versão. Para reduzir esse risco, o candidato
`0.5.0` do HyperMix ganhou um gate executável de consistência.

Antes de construir ou publicar, o gate confere:

1. a versão declarada em `pyproject.toml`;
2. a mesma versão e data em `CITATION.cff`;
3. a seção correspondente no changelog;
4. as notas públicas da versão;
5. a correspondência exata entre a tag e o pacote;
6. o contrato OIDC do PyPI e o pin por SHA das actions.

Essas verificações rodam na CI, no workflow de artefatos e novamente antes do
upload. Quatro testes exercitam o caminho válido e três formas de divergência.
A suíte completa agora contém 67 testes.

O gate não muda o resultado científico e não transforma um candidato em uma
release. O pacote ainda não foi enviado ao PyPI porque o publisher pendente
precisa ser autorizado pela conta do autor. Tag, GitHub Release e DOI também
continuam ausentes.

Enquanto isso, a questão central permanece documentada sem exagero. Nenhum
método aprendido superou de forma robusta o matched filter espacial nos
experimentos concluídos, e o teste no alvo bioHSI real continua pausado pelas
coordenadas manuais ausentes.
