# Recuperar e manter o contexto de execução

<!-- TOC START -->
- [Começar pela decisão pendente](#comecar-pela-decisao-pendente)
- [Registrar antes de ampliar o trabalho](#registrar-antes-de-ampliar-o-trabalho)
- [Reconciliar decisões com seus responsáveis](#reconciliar-decisoes-com-seus-responsaveis)
- [Diferenciar checkpoint de conclusão](#diferenciar-checkpoint-de-conclusao)
<!-- TOC END -->

O ponto de entrada da estabilização é o
[handoff de namespace e runtime](../roadmap/namespace-automation-handoff-2026-09-14.md).
Ele reconcilia pedidos, plano reconstruído, mudanças, críticas, ADRs e Beads.
O Beads continua sendo o responsável pelo estado de execução; o handoff contém
evidência e instruções de retomada, sem criar uma fila paralela de tarefas.

## Começar pela decisão pendente

Leia a tabela inicial do handoff e o Bead indicado antes de repetir uma busca
ampla. Confirme branch, HEAD, alterações locais, PR e base declarada. Verifique
o runtime por `make status`; o caminho de execução e a versão instalada precisam
corresponder ao código que será validado. Um log anterior ou uma instalação do
workspace pai não certifica o checkout standalone.

Na execução de 14/09/2026, o operador selecionou o tracker do checkout `flext`
explicitamente. O comando Beads precisa do diretório de trabalho dessa raiz,
além do ambiente carregado por `direnv`. Isso é contexto autorizado dessa
execução, não uma regra para procurar runtimes no pai de todo repositório.

## Registrar antes de ampliar o trabalho

Mantenha no início do handoff o pedido vigente, suas exceções, SHA/PR, primeira
falha, última evidência completa e próxima ação concreta. Atualize esse bloco
ao mudar escopo, integrar contribuições, encontrar uma falha diferente ou
publicar um checkpoint. Quando o operador pedir o handoff, entregue o link
disponível imediatamente e indique o estado real da integração.

Cada evidência deve identificar comando, diretório, revisão observada, exit
code e resultado decisivo. Uma execução em andamento, interrompida ou sem seu
exit code não é verde. Alterações concorrentes exigem nova leitura antes de
gravar e tornam necessária a revalidação dos caminhos afetados.

## Reconciliar decisões com seus responsáveis

Use o [mapa de ADRs](../architecture/adr/README.md) para localizar os documentos
reais. Uma referência ausente é um problema documental a corrigir; não invente
um ADR nem reviva uma decisão superada. Registre divergências e a instrução
mais recente que as resolve. Planos de capacidades relacionadas não substituem
o plano de execução da tarefa atual.

Na automação de namespace, investigue catálogo, classificador, transformação,
publicação e consumidores nessa ordem. Um finding zero de codemod não prova
que o gate de namespace está verde. Preserve mutabilidade, herança, imports e
collection; valide a transformação na interface pública antes de ampliar o
lote. Refatorações estruturais continuam passando pelo `make mod`.

## Diferenciar checkpoint de conclusão

Um WIP publicado preserva o trabalho e permite revisão. Conclusão exige os
critérios vigentes, integração e runtime medido no SHA integrado. Nesta
estabilização o operador limitou o aceite de `check` a Ruff, Mypy, Pyright e
Pyrefly; o resultado dos gates customizados continua visível. Essa exceção
pertence à execução e não enfraquece a política geral nem fecha seus defeitos.

O handoff final relaciona PRs, commits de merge e prova após integração aos
Beads. Se algo permanece pendente, o texto deve nomeá-lo e oferecer a próxima
ação executável, sem declarar fechamento funcional.
