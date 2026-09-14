# Handoff: automação de namespace e runtime do flext-infra

<!-- TOC START -->
- [1. Pedido, prioridade e limite desta entrega](#1-pedido-prioridade-e-limite-desta-entrega)
- [2. Plano de execução reconstruído e confronto com o resultado](#2-plano-de-execucao-reconstruido-e-confronto-com-o-resultado)
- [3. Documentos e decisões aplicáveis](#3-documentos-e-decisoes-aplicaveis)
- [4. Crítica da execução](#4-critica-da-execucao)
  - [4.1 A principal prioridade não dirigiu as mudanças](#41-a-principal-prioridade-nao-dirigiu-as-mudancas)
  - [4.2 O automatizador foi aplicado antes de provar seus contratos](#42-o-automatizador-foi-aplicado-antes-de-provar-seus-contratos)
  - [4.3 Houve reparações estruturais manuais não reproduzíveis](#43-houve-reparacoes-estruturais-manuais-nao-reproduziveis)
  - [4.4 A mutabilidade foi tratada como grafia de tipo](#44-a-mutabilidade-foi-tratada-como-grafia-de-tipo)
  - [4.5 A evidência foi fragmentada e ficou atrás do código](#45-a-evidencia-foi-fragmentada-e-ficou-atras-do-codigo)
  - [4.6 Gates diferentes estão respondendo perguntas diferentes](#46-gates-diferentes-estao-respondendo-perguntas-diferentes)
  - [4.7 A retomada inicialmente perguntou pelo plano errado](#47-a-retomada-inicialmente-perguntou-pelo-plano-errado)
- [5. O que foi preservado no código](#5-o-que-foi-preservado-no-codigo)
- [6. Evidências executáveis e suas limitações](#6-evidencias-executaveis-e-suas-limitacoes)
- [7. Beads relacionados e uso correto](#7-beads-relacionados-e-uso-correto)
- [8. Sequência concreta de retomada](#8-sequencia-concreta-de-retomada)
  - [8.1 Confirmar o estado e reproduzir a primeira falha](#81-confirmar-o-estado-e-reproduzir-a-primeira-falha)
  - [8.2 Corrigir a automação na ordem das dependências](#82-corrigir-a-automacao-na-ordem-das-dependencias)
  - [8.3 Recuperar a validação funcional](#83-recuperar-a-validacao-funcional)
  - [8.4 Critérios de aceite antes da integração](#84-criterios-de-aceite-antes-da-integracao)
- [9. Limite de encerramento deste handoff](#9-limite-de-encerramento-deste-handoff)
<!-- TOC END -->

Registro crítico da execução de 14/09/2026, preparado por solicitação do
operador. O destinatário é quem retomará a correção. Este documento preserva
evidências e a sequência de retomada; o estado de execução continua no Beads.
O resultado está em **WIP**, sem aceite de runtime completo e sem merge desta
entrega na integração.

O checkpoint de implementação é
[`3bd09bddc`](https://github.com/flext-sh/flext-infra/commit/3bd09bddc2e835a6aa1412945d3859d9b74459e4),
na branch `fix/docs-renderer-contract`, pelo
[PR #732](https://github.com/flext-sh/flext-infra/pull/732), com destino
`0.12.0-dev`. Ele preserva o conjunto compartilhado de 172 arquivos alterados,
com 1.562 inserções e 1.264 remoções. A branch contém também os checkpoints
anteriores de documentação, geração, circuito mod e execução de testes.

## 1. Pedido, prioridade e limite desta entrega

As chamadas do operador estabeleceram esta sequência:

1. Corrigir os problemas de `flext-infra` pela causa raiz, comprovar runtime
   completo e propagar para a branch de desenvolvimento por PR.
2. Usar o `make check` já iniciado e seu `check.lst` como ponto de partida.
   O operador esclareceu que não existia outro log de nohup.
3. Priorizar explicitamente **a automação que corrige namespaces**.
4. Investigar o plano que o agente vinha executando, confrontá-lo com as
   chamadas, criticar os desvios e preparar um handoff com documentos e Beads.
5. Gravar e publicar o estado atual como WIP, preservando o trabalho existente.

A quinta chamada define o encerramento deste checkpoint documental. Ela não
autoriza declarar cumprido o objetivo original nem converter o WIP em uma
entrega aprovada. A integração futura continua exigindo os gates, revisão e
prova após merge. `main` não faz parte do destino solicitado.

Não havia um plano de execução persistido pelo agente neste checkout. A seção
seguinte reconstrói a sequência efetivamente adotada a partir da conversa,
comandos, diffs e logs; não apresenta um documento retrospectivo como se tivesse
sido aprovado antes da implementação.

## 2. Plano de execução reconstruído e confronto com o resultado

| Etapa adotada | Resultado esperado | Evidência e desvio |
| --- | --- | --- |
| Ler `check.lst` e localizar responsáveis | Priorizar causas sistêmicas | A leitura encontrou 1.145 ocorrências de namespace e 298 violações no censo de runtime. Faltou transformar esse inventário em cobertura explícita do `make mod` antes de editar consumidores. |
| Reparar erros de tipos, documentos e descoberta | Desbloquear os caminhos reais | Houve correções úteis, mas foram tratadas como trilhas concorrentes ao problema principal, sem uma prova intermediária de automação estrutural funcionando. |
| Aplicar `make fix-enforcement` | Corrigir ocorrências pelo mecanismo do projeto | A execução registrou 156 correções, 9.931 skips e 81 falhas. Também produziu tipos somente de leitura em contratos mutáveis e uma movimentação de constantes que quebrou o carregamento da CLI. |
| Corrigir o estrago e reduzir limites de arquivo | Recuperar funcionamento e gates | Parte da reparação usou edições manuais repetitivas e extrações de classes/testes fora de `make mod`. A causa do transformador foi corrigida apenas parcialmente. |
| Isolar o runtime standalone e regenerar | Garantir que as verificações exercessem o projeto correto | O Make e o conformador de pyproject foram corrigidos nos responsáveis. `make status` agora confirma o checkout local. Os testes anteriores no runtime do pai não são prova da instalação standalone. |
| Retomar `make mod` após a correção do operador | Comprovar correção automática reproduzível | A tentativa parou em `validate_rule_fixtures` por filesystem somente de leitura no cache. Não chegou à aplicação semântica nem ao ponto fixo. |
| Rodar os gates e integrar | Zero erro, runtime comprovado e PR aprovado | O último check completo desta execução permaneceu vermelho. Não houve rodada completa verde sobre o checkpoint final. O pedido posterior passou a ser preservar WIP e transmitir a retomada. |

## 3. Documentos e decisões aplicáveis

O código e os comandos de `flext-infra` continuam pertencendo a este
repositório. A consulta aos documentos e ao tracker de `flext` foi autorizada
explicitamente pelo operador durante a preparação deste handoff.

- [AGENTS.md local](../../AGENTS.md) e
  [flext-law](../../.agents/skills/flext-law/SKILL.md): responsáveis canônicos,
  preservação de alterações, fluxo estrutural por `make mod` e prova real.
- [ADR-005: SSOT e direção das facades](https://github.com/flext-sh/flext/blob/0.12.0-dev/docs/architecture/adr/005-config-settings-constants-templates-schemas-ssot.md):
  configuração tipada, `c -> t -> p -> m -> u`, publicação transacional e
  migração com remoção dos responsáveis substituídos.
- [ADR-010: padronização e descoberta semântica, §3b](https://github.com/flext-sh/flext/blob/0.12.0-dev/docs/architecture/adr/010-unified-project-standardization-via-codegen.md):
  descoberta em fontes reais, rewiring automático, ausência de progresso como
  falha, zero findings e diagnósticos no aceite.
- [ADR-014: forma das famílias e regras Rope](https://github.com/flext-sh/flext/blob/0.12.0-dev/docs/architecture/adr/014-family-part-shape-rope-codemod-rules.md):
  classes órfãs, wrappers, replicação para consumidores e alinhamento entre os
  gates de namespace e codemod.
- [Plano de reconciliação e contratos Make](https://github.com/flext-sh/flext/blob/0.12.0-dev/docs/plans/2026-09-14-plan-reconciliation.md):
  contexto correlato de `flext-ro6mj.1`, não o plano original desta sessão.
  Sua implementação do coletor não integra o escopo desta retomada.
- [Guia de desenvolvimento](../guides/development.md) e
  [padrão de automação](../guides/skill-automation-pattern.md): sequência nativa
  e responsabilidade de reproduzir mudanças nos consumidores.

Os quatro documentos de `flext` acima foram lidos no checkout em
`206c02ee1dd3f714a8164ade4b5605a6f71b8856`; esses caminhos estavam sem alterações
locais na consulta. Isso identifica a revisão documental, não prova sua
integração remota.

ADR-012 não foi encontrado no diretório de ADRs dessa linha. O bead fechado
`flext-z0zkq` documenta a colisão histórica e determina ADR-005 §§1–2 e os
docstrings de `_settings.py`/`_config.py` como referências do padrão. A referência
local em `AGENTS.md` foi corrigida neste handoff; o restante da frota pertence
a `flext-la3z5`.

Há divergências documentais que não podem ser ocultadas: ADR-005 §6 contém a
proibição antiga de AST; ADR-010 §3b e a skill local descrevem o circuito
AST/Rope/LSP. ADR-010 §2 ainda menciona `APPLY=Y`, enquanto o plano de 14/09
determina retirar `APPLY`. O checkpoint compartilhado contém `APPLY=N`.
Essas diferenças não autorizam reverter contribuições nem escolher uma regra
silenciosamente. A retomada deve reconciliar a intenção vigente no responsável
e seu bead, sem introduzir outra gramática de comandos.

## 4. Crítica da execução

### 4.1 A principal prioridade não dirigiu as mudanças

O problema já era majoritariamente estrutural no primeiro log. Entretanto, o
trabalho concentrou-se em erros pontuais, tipos e extrações manuais. A mudança
de prioridade só ocorreu depois da chamada explícita do operador. O critério
de progresso deveria ter sido uma classe de violação corrigida de ponta a
ponta pelo `make mod`, com consumidores válidos e segunda execução sem efeitos.

| Medida nos logs | Inicial | Último check completo |
| --- | ---: | ---: |
| Namespace total | 1.145 | 1.099 |
| `NS-STRUCT` | 960 | 953 |
| `NS-CONTRACT` | 137 | 97 |
| `NS-IMPORT` | 48 | 49 |
| Namespace em `src` | 256 | 247 |
| Namespace em `tests` | 889 | 852 |
| Violações do censo de runtime | 298 | 298 |

A redução líquida de 46 ocorrências não demonstra convergência. A dimensão
estrutural quase não mudou, e a contagem de importações aumentou. Como houve
edições compartilhadas durante os comandos, essa comparação é descritiva;
não permite atribuir cada diferença a uma alteração específica.

### 4.2 O automatizador foi aplicado antes de provar seus contratos

A movimentação de constantes preservou trechos da expressão sem transportar
corretamente suas dependências, colocou declarações no nível do módulo e deixou
consumidores/importações inconsistentes. O resultado observado foi `NameError`
durante o carregamento da CLI. Corrigir manualmente os oito nomes recuperou
esse caso, mas não ensinou o automatizador a executar a operação corretamente.

O responsável ainda contém `_append_constant` com anexação no nível do módulo,
importações reconhecidas por padrões textuais e `Path.write_text` em múltiplos
arquivos. A correção do cálculo de pontos no import relativo é real e
insuficiente. O lote completo precisa ser planejado, validado e publicado pelo
responsável transacional existente antes que se aceite outra movimentação.

### 4.3 Houve reparações estruturais manuais não reproduzíveis

A extração de modelos de toolchain e a divisão dos testes de conformance foram
feitas fora do fluxo canônico. Os helpers extraídos conservaram nomes privados
usados entre módulos; o PR registra 22 diagnósticos de acesso privado em uma
verificação posterior. A contagem de nomes de testes preservados é útil para
inventário, mas não prova collection, fixtures ou execução equivalentes.

Essas alterações devem ser preservadas e corrigidas para frente. O próximo
agente precisa implementar a transformação reutilizável que reproduz a forma
correta e demonstrar que ela preserva comportamento. Outra divisão manual para
reduzir LOC repetiria o desvio.

### 4.4 A mutabilidade foi tratada como grafia de tipo

Converter `dict` em `Mapping` altera capacidades do contrato. O guard de
`typing_unifier.py` agora reconhece `dict[`, e consumidores afetados receberam
tipos mutáveis ou inferência concreta. Ainda falta provar pelo fluxo completo
a distinção entre parâmetro somente de leitura, parâmetro que é mutado,
atributo mutável, retorno concreto e container serializado.

`flext-6x6jr` especifica o caso de parâmetro. Ele não autoriza alargar todos os
atributos e retornos. Uma substituição indiscriminada, mesmo que reduza um gate,
pode invalidar operações em runtime ou no type checker.

### 4.5 A evidência foi fragmentada e ficou atrás do código

A primeira execução de testes usou o runtime do checkout pai. Depois houve
correção de isolamento, alterações adicionais e regeneração. Logs de check
terminaram enquanto o código continuava mudando. Parte da saída extensa do
fixer não foi preservada integralmente, e um caminho de log foi reutilizado.
Faltou vincular cada rodada a uma revisão e a uma identidade do conjunto de
fontes observado.

No checkout atual, `make status` saiu 0 e confirmou runtime local, 160 pacotes
compatíveis e uv 0.12.10. Uma observação anterior registrou uv 0.12.13. Isso
exige preflight de identidade do toolchain; não permite afirmar que a versão
instalada corresponde ao contrato de newest release apenas porque o status
passou.

### 4.6 Gates diferentes estão respondendo perguntas diferentes

O último check registrou `codemod=0` e `namespace=1099` no mesmo comando.
Portanto, zero no primeiro não prova conformidade de namespace. Em
`class_nesting.py`, a fase retorna plano vazio fora das famílias reconhecidas
e quando encontra no máximo uma classe. Essa fase, isoladamente, não cobre
módulos sem classe, funções soltas ou todos os testes com prefixo incorreto.

Também há um risco a testar em `batch_apply.py`: o loop anuncia cascata, mas
`_validate_fix_match` rejeita novos findings acionáveis após a primeira
transformação. Uma regra pode legitimamente revelar o padrão seguinte. Ainda
não há reprodução deste risco nesta sessão; não deve ser descrito como causa
já comprovada do erro de cache.

### 4.7 A retomada inicialmente perguntou pelo plano errado

Durante este handoff, o agente perguntou pelo caminho de um plano externo.
O operador esclareceu que queria a revisão do plano que o próprio agente
vinha executando. A pergunta transferiu ao operador uma reconstrução que podia
ser feita com a conversa e o histórico. Este documento corrige esse enquadramento.

## 5. O que foi preservado no código

| Responsável ou conjunto | Alteração preservada | Limite da prova |
| --- | --- | --- |
| `templates/project/base/Makefile.j2` e `_utilities/pyproject_conform.py` | Raiz standalone local e declaração uv que encerra descoberta de workspace ancestral | `make status` local passou; teste de isolamento foi acrescentado, sem rodada final verde comprovada |
| `_utilities/project_discovery.py` | Manifesto presente e inválido falha; ausência opcional continua representada pelo contrato | Regressão acrescentada, sem aceite final da suíte |
| `_utilities/docs_contract.py` e modelos de docs | Uso dos tokens tipados do Markdown e tratamento de navegação/âncoras | A branch já contém trabalho concorrente e resultados de docs registrados no PR |
| `workspace/_orchestrator_execution.py` e consumidores de Result | Construção com o contrato genérico esperado | Correções posteriores ao check exigem nova medição |
| `transformers/typing_unifier.py` e consumidores | Guard de mutabilidade e reparação das anotações alargadas indevidamente | Não prova convergência de todos os contratos |
| `_constants/codegen.py` e `codegen/_mise_artifacts_*` | Constantes inseridas na classe responsável e acessos corrigidos | A movimentação automática geral continua incompleta |
| `_models/codegen_toolchain.py` e `_models/codegen.py` | Separação dos modelos de toolchain, mantendo composição por herança | Extração manual; revalidar exports, importação e LOC |
| `tests/unit/codegen/conform_support.py`, `test_codegen_make_contracts.py`, `test_codegen_script_dispatch.py` | Preservação dos testes extraídos do módulo de conformance | Resolver acesso privado e comprovar collection e execução |
| `codemod/batch_apply.py`, `semantic_apply.py` e utilitários semânticos | Aplicação de rewrites acionáveis antes da fase semântica; verificação das fontes propostas | Contribuições compartilhadas; `make mod` completo ainda não foi comprovado |
| Gates de censo/tier, geração e runner de pytest | Evidência causal e preservação do status de falha | Não presumir aprovação a partir da existência da implementação |

O commit é a autoridade para a lista completa de arquivos. Nenhuma parte do
estado compartilhado deve ser descartada para reconstruir artificialmente uma
autoria isolada.

## 6. Evidências executáveis e suas limitações

Todos os comandos de implementação abaixo tiveram cwd na raiz do checkout
`flext-infra`. As consultas ao tracker usam o cwd na raiz de `flext`, conforme
demonstrado pelo operador. Os caminhos absolutos observados estão registrados
nos comentários de evidência do Beads, sem tornar a documentação dependente
da máquina.

| Comando ou evidência | Saída/resultado | O que demonstra |
| --- | --- | --- |
| `make check`, log inicial fornecido pelo operador | Make terminou com erro 2; namespace 1.145; censo 298 | Ponto de partida, não revisão final |
| `make fix-enforcement` | Exit 2; 156 fixed, 0 previewed, 9.931 skipped, 81 failed | Aplicação parcial com falhas; contagens recuperadas da sessão, sem log bruto completo retido |
| `make check`, `check-repair-unrestricted.log` | Exit 2; 1.119 erros agregados: pyrefly 9, mypy 6, LOC 4, censo 1, namespace 1.099; 481,45 s | Última rodada completa diretamente observada nesta execução; terminou em 2026-09-14T21:39:53Z |
| `make mod`, `namespace-mod.log` | Exit 2; `OSError: [Errno 30] Read-only file system` em `mod-rule-fixtures-*` | A execução não passou do preflight de fixtures |
| `make gen` e `make setup`, rodadas anteriores | Exit 0 | Gerador/setup exercitados antes do checkpoint; não certificam o conjunto final |
| Recibos de suíte `20260914T210624.850231Z-2834013` e `20260914T212545.368582Z-3122161` | `raw_return_code=-15`, `timed_out=true`, `forwarded_signal=null` | Execuções interrompidas por timeout; nenhum aceite da suíte completa |
| `make status`, durante o handoff | Exit 0; profile standalone; project e runtime locais; 160 pacotes compatíveis | Preflight local, sem comprovação de todas as funções |
| `git diff --cached --check`, antes do checkpoint | Exit 0 | Integridade textual, não teste funcional |
| Fetch e comparação de referências | Exit 0; HEAD e branch remota iguais a `3bd09bddc`; base `a254c1f3f3e3491a5eea34c6a088c7285e454ca6` | Implementação preservada remotamente; a base é ancestral do checkpoint |

No check completo, as quatro falhas de LOC apontavam `_models/config.py`,
`_utilities/rope_analysis.py`, `codegen/conform.py` e o antigo módulo único de
testes de conformance. A extração posterior invalida essa última medição para
o checkpoint. O agregado `runtime-census=1` representa **298 violações**, não
uma única correção pendente.

Os logs locais estão no scratch externo de `flext-infra`, resolvido pelo
responsável de armazenamento em `config/codegen.yaml`; o comentário de
`flext-5fxu6.4` preserva seu caminho físico observado.
`check-initial.lst` é o `check.lst` concluído, movido para preservar evidência
sem manter um arquivo estranho no layout do projeto. Não há log de nohup.

| Arquivo | SHA-256 observado |
| --- | --- |
| `check-initial.lst` | `89fc6973cf4b67bac6c144c128222e1797146fb4b86ec89b250d5aa92b4674e1` |
| `check-repair-unrestricted.log` | `67e02bad362ceb2a5fcacab555a343a7dfb70eab8e483b90046ce2d06da8c9d6` |
| `namespace-mod.log` | `32e4f10dc734c5e9a5ca5657bd4a60cbfb64b8108519ee1bec1da5cfe5f27424` |

Esses arquivos e `.reports/tests/<execução>/suite-outcome.json` são evidências
locais; não são conteúdo publicado no Git. O PR e este handoff preservam os
resultados relevantes, sem publicar transcrições privadas.

## 7. Beads relacionados e uso correto

Os registros abaixo foram consultados ao vivo com `bd show`, usando `direnv`
para carregar o contexto do checkout `flext`, com cwd em `flext` e exit 0. A tentativa
inicial no cwd `flext-infra` retornou `no beads database found`; isso era uma
diferença de contexto, não prova de indisponibilidade do servidor do operador.

| Bead | Relação com a retomada |
| --- | --- |
| `flext-5fxu6.4` | Responsável principal: gerador/enforcement de infra; exige ciclo completo, ponto fixo e prova após merge |
| `flext-5fxu6` | Programa pai: correções sistêmicas e propagação; não expandir esta entrega automaticamente para a frota |
| `flext-pwmej` | Correlação dos gates: tipos, duplicação, codemod e limites de arquivo |
| `flext-ocxtt` | Critérios de gates de infra e geração sem efeitos; as notas atuais citam também grpc e não provam aceite de infra |
| `flext-6x6jr` | Conversão de container em parâmetro; preservar distinção entre leitura e mutabilidade |
| `flext-k7vvp` | Fixtures/snapshots de `make mod`; existe agora implementação de atualização no responsável, mas falta prova completa |
| `flext-c1vvr` | Cobertura de imports privados em `scripts`; revisar escopo declarado além de `src/tests` |
| `flext-z4ydq` e `flext-t9q8h` | Custo do namespace move e da descoberta de providers; não aumentar limites para esconder repetição de trabalho |
| `flext-mu6mp` | Toda mudança de contrato precisa transportar a migração dos consumidores |
| `flext-la3z5` | Autocorreção de infra antes da frota e reparação das referências obsoletas de ADR |
| `flext-z0zkq` | Evidência histórica da referência ADR-012; fechado para seu escopo original, sem autorização para fechar a frota |

Não foi criado um novo épico nem alterada a hierarquia para representar este
handoff. Comentários de evidência nos responsáveis existentes devem apontar
para este documento, o checkpoint e o PR; nenhum item deve ser fechado com base
no WIP. As referências Cosmos já existentes no PR pertencem às contribuições
correlatas e não substituem o tracker FLEXT desta execução.

## 8. Sequência concreta de retomada

### 8.1 Confirmar o estado e reproduzir a primeira falha

Consultar a branch/PR atuais, absorver as alterações compatíveis, verificar o
runtime por `make status` e identificar a versão efetiva das ferramentas.
Não criar uma instalação paralela nem reutilizar resultados de outro runtime.
Preservar novos logs com nomes próprios e identidade da revisão observada.

O próximo comando funcional é **`make mod`**, no checkout de `flext-infra`.
O erro conhecido é de permissão do sandbox sobre `settings.work_dir`; usar a
autorização de execução apropriada para esse cache, sem hardcode, bypass ou
troca de diretório de trabalho para contornar a falha. Se a raiz resolvida
violar a configuração, corrigir a resolução no responsável antes de prosseguir.
Nesta entrega de handoff, não foi iniciada outra rodada mutante de `make mod`.

### 8.2 Corrigir a automação na ordem das dependências

| Ordem | Responsáveis | Resultado exigido |
| --- | --- | --- |
| 1 | `codemod/batch_gates.py`, `snapshot_reconciler.py`, regras e fixtures declaradas | Fixtures completas validadas, falhas causais e fontes fora do escopo preservadas |
| 2 | `refactor/classvar_constant_autofix.py`, `fixers/rope_fixer.py`, publicação existente | Movimento para a classe correta, dependências de expressão e todos os consumidores preservados, sem escrita parcial |
| 3 | `transformers/typing_unifier.py` e regras de tipos | Contratos de mutabilidade preservados; aliases canônicos compatíveis com uso real |
| 4 | `codemod/semantic_apply.py`, `_utilities/class_nesting.py` e responsáveis CST/Rope | Cobrir órfãos, wrappers, funções/dados soltos, forma das facades e consumidores; bases e subclasses avaliadas com sua dependência real |
| 5 | `codemod/batch_apply.py` e inventário do namespace | Cascata convergente; cada finding acionável resolvido, cada ambiguidade causalmente relatada, nenhum falso ponto fixo |
| 6 | `validate/_namespace_rules`, `validate/runtime_census.py`, gates correspondentes | Mesmo escopo e contratos; relatórios íntegros, sem converter falhas em warning ou sucesso |

As linhas acima são dependências de implementação, não autorização para criar
um segundo motor. Reutilizar as facades e primitivas atuais. Novas regras de
política pertencem aos dados tipados do catálogo. Cada transformação deve ter
casos de comportamento pela interface pública: importação e avaliação das
constantes; alias de consumidor; colisões; herança; collection de testes;
mutação versus leitura; erro antes da publicação; segunda aplicação sem diff.

Antes de ampliar o lote, demonstrar que a transformação reproduz corretamente
um caso real da classe de erro. Em seguida, executar o verbo nativo no escopo
declarado completo. Não substituir isso por uma lista de centenas de arquivos
ou por scripts temporários que reescrevem consumidores.

### 8.3 Recuperar a validação funcional

Depois da automação estrutural, regenerar exports e projeções, corrigir os
contratos de helpers de testes e tratar os módulos acima do limite pelo
responsável de refatoração. Executar a sequência nativa estabelecida:

```bash
make gen
make mod
make gen
make gen
make fix
make fmt
make check
make test
make build
make docs
make gen
```

Uma falha interrompe a invocação e mantém o trabalho na correção do responsável.
Depois de qualquer alteração pertinente, renovar a evidência afetada. Não
ampliar timeout nem remover Testmon para obter um resultado verde. Para testes
interrompidos, usar os recibos e o reportlog do runner atual para localizar a
primeira falha/custo real; contagens parciais não certificam a suíte.

### 8.4 Critérios de aceite antes da integração

- `make mod` termina com exit 0, zero findings de todas as classes, zero
  diagnósticos finais e reaplicação sem mudanças.
- `make check` termina com exit 0, incluindo namespace, censo de runtime,
  tipos, LOC e segurança, sem suprimir ou reduzir o escopo.
- `make test`, build e documentação terminam com exit 0 no runtime declarado;
  a evidência identifica revisão, ambiente, seleção e resultado completo.
- Geração consecutiva atinge ponto fixo; não há responsáveis antigos,
  consumidores sem migração, arquivos temporários ou aliases de compatibilidade.
- O PR contém o escopo real, perde WIP somente após a validação, recebe a
  aprovação exigida e integra por merge commit em `0.12.0-dev`.
- O SHA integrado é revalidado, os Beads recebem as quatro fontes de evidência
  e só então se trata o encerramento. Propagação para consumidores adicionais
  segue seus próprios responsáveis e autorizações.

## 9. Limite de encerramento deste handoff

Preservar e publicar o estado atual foi solicitado explicitamente. Por isso,
um checkpoint WIP com gates vermelhos é o resultado correto desta chamada.
Ele não satisfaz os critérios de conclusão funcional acima. A próxima execução
deve começar pela automação e pela falha causal conhecida, sem recomeçar a
varredura manual nem reutilizar verde de revisões anteriores.
