# Release v0.12.2

## Scope

- Release version: 0.12.2
- Projects packaged: 2

## Projects impacted

- root
- flext-infra

## Pull requests since last release

- fix(tests): fixture runtime binds as a site dir; fixture manifests are complete
  (flext-h4lwi) (#2715)
- fix(release): read paginated forge inventories page by page (flext-rb4cl) (#2711)
- fix(codegen): apply the independent review of #2701 (flext-5w9c0) (#2712)
- fix(make): regenerate the Makefile so every verb admits at load5 20 (flext-kugv4)
  (#2710)
- fix(sweep): violations-sweep is repository-scoped; members observed by their own plans
  (flext-oja0z) (#2709)
- fix(validate): the fresh-import probe deadline is the target's typed policy
  (flext-s20br) (#2706)
- fix(tests): fixture checkouts are created on main, never the host default branch
  (flext-v9vtm) (#2707)
- docs(codemod): the checkout-name independence of the rendering key is… (#2704)
- fix(tests): src\_package builds a Git checkout, as Git-owned source discovery requires
  (flext-v9vtm) (#2699)
- fix(validate): one testmon database per project at the real account home (flext-7hcvh)
  (#2700)
- fix(codegen): model-protocol projection tests green at their owners (flext-5w9c0)
  (#2701)
- fix(codemod): flatten the nested \<Project\>.Tests test namespace by native fix
  (ENFORCE-054) (#2702)
- fix(codegen): private and same-depth ambiguous packages never own a re-exported name
  (flext-2nj1w) (#2698)
- test(codemod): layer-zero boundary scenarios scan the lazy loader, not settings
  (flext-rogg4) (#2697)
- fix(codegen): tests root serves public src subpackages; root imports of child-owned
  names move to their owner (flext-2nj1w) (#2695)
- fix(codemod): the catalog rendering key never names the checkout directory (#2696)
- fix(import-law): layer-zero rule ids and wording follow the lazy-only law
  (flext-rogg4) (#2693)
- fix(census): restore impact-map export and removal apply; import-clean planned
  removals (flext-vst3z) (#2690)
- fix(admission): every verb admits at max\_load5 20 (#2691)
- fix(tests): namespace\_workspace registers its member as a real gitlink (flext-aer06)
  (#2689)
- fix(validate): elect the runner's tooling once; empty harness scopes; tests-harness
  admission (flext-orde2) (#2685)
- fix(deps): relock rope dc.9 and flext-cli eb863c08; read the route model through
  resolved\_model\_cls (flext-0fthr) (#2688)
- fix(codegen): retire stale projections in nested mirror packages too (flext-b4gw3.6)
  (#2687)
- test(refactor): apply the review of #2679 (flext-43e72) (#2683)
- fix(import-law): an own letter in a later layer is never routed to from an earlier
  layer (flext-jiu3v) (#2686)
- fix(tests): the shared dependency-wheel cache keeps other content keys (flext-ebewv)
  (#2684)
- test(codegen): retired-projection regression starts from the stale tree, inside the
  slow budget (flext-b4gw3.6) (#2682)
- fix(validate): runner reads its pytest policy from the elected project document
  (flext-orde2) (#2681)
- fix(refactor): the violations sweep drops the retired audit verb (flext-43e72) (#2679)
- fix(validate): publish the tests-harness projections and repair the merged slice
  (flext-orde2) (#2680)
- test(codegen): regression for retired projections runs the real stage within budget
  (flext-b4gw3.6) (#2678)
- fix(tests): a fixture venv binds the generator runtime only when it installs no wheels
  (flext-wnfiu) (#2676)
- fix(refactor): the violations sweep reads its configs' scanner directories, not
  fixture directories (flext-slll0) (#2677)
- feat(validate): harness pytest mode and make tests-harness (flext-orde2) (#2674)
- feat(codegen): chave docs\_site\_unpublished desliga a publicação do site no Pages
  (#2675)
- fix(codegen): drop the tuple-index lambda in protocol\_model\_sources\_from\_source
  (FURB118; flext-b4gw3.6) (#2673)
- fix(codegen): keep protocol sources typed str; report retired projections apart
  (flext-b4gw3.6) (#2672)
- test(refactor): layer-zero tests follow the lazy law; the shared demo project is a Git
  checkout (flext-rogg4) (#2669)
- fix(codegen): facade alias admission reaches aliases in nested namespace classes and
  barrel re-exports (flext-8qf81) (#2671)
- fix(codegen): model-to-protocol stage retires projections of deleted models
  (flext-b4gw3.6) (#2670)
- fix(refactor): rename the accessor origin's module() so it no longer shadows the
  --module field (flext-p7n6q) (#2668)
- test(codegen,codemod): warm the layout admission tests; drop a self-comparing loop
  (re-review of #2666, flext-nhorg) (#2667)
- fix(codegen,tests): primary model layout waits for its protocols facade; cutover tests
  follow the current laws (flext-nhorg) (#2666)
- fix(tests): checkout-root sites read u.Infra.project\_root; semantic-cutover templates
  stay under tests/ (flext-l3vuy) (#2665)
- fix(facade): nested Tests bases keep the upstream test facade first (#2664)
- fix(tests): moved tests/\_utilities helpers resolve the project root (flext-xow5k)
  (#2663)
- fix(tests): moved tests/\_utilities helpers resolve the checkout root, not tests/
  (flext-l3vuy) (#2662)
- fix(lazy-init,import-law): tests root re-exports src public names it does not
  redeclare (#2661)
- fix(tests): drop the duplicate TestsFlextInfraUtilitiesToml base the #2657/#2658 merge
  left (flext-imbhd) (#2660)
- fix(tests): restore the flext\_tests bases the standalone cutover removed from the
  test facades (flext-imbhd) (#2658)
- fix(tests): restore the flext\_tests bases of the four test facades (#2657)
- fix(mise): qualify the installed pinned Mise, not the host reader on PATH
  (flext-3iq28) (#2655)
- wip(preserve): uncommitted flext-infra WIP of flext-wip-flext-cldup.1… (#2649)
- fix(codemod): resolve native tools from the invocation owner, not the scanned root
  (flext-xow5k) (#2654)
- fix(import-law): canonical in-package lazy imports; stand-in exports add no
  import-time edge (#2651)
- fix(tests): read the settings/config class directly, not through the deferred root
  (flext-0b20f) (#2653)
- fix(deps): lock the declared flext-tests dev dependency (flext-0fthr) (#2656)
- perf(lazy): defer the flext-infra config and settings roots (flext-0b20f) (#2652)
- wip(preserve): uncommitted flext-infra WIP of flext-wip-flext-gmpyc (… (#2647)
- wip(preserve): uncommitted flext-infra WIP of flext-wip-flext-grlt5 (… (#2648)
- wip(preserve): uncommitted WIP of worktree flext-hooks3-20261118 (not… (#2645)
- wip(preserve): uncommitted WIP of worktree flext-infra-git-add-all-20… (#2646)
- chore(deps): pin rope 1.15.2+dc.9 (C3 MRO, builtin class cache identity) in
  flext-infra (#2635)
- fix(tests): bind the rope contract suite to real scoped inputs (flext-9l09v) (#2632)
- fix(import-law): layer zero is the lazy loader only; settings and config import
  through the lazy initializer (operator 2026-11-19) (#2636)
- fix(pytest): unwind the suite deadline through pytest and publish the executed prefix
  (flext-itkcb) (#2631)
- fix(pyproject): a declared dev floor owns its distribution by name (#2629)
- fix(validate): per-checkout testmon database and lease; lease wait is admission, not
  suite budget (flext-7hcvh) (#2637)
- fix(codegen): admit governed attached members and pin every Mise lock write (#2634)
- fix(import-law): keep own layer-zero helper imports direct (#2633)
- chore(gitignore): ignore local runtime state and retire the pre-marker hook copy
  (#2630)
- fix(codemod): scope the syntax cascade to native replacement findings (#2622)
- feat(git): public merge-conflict primitives for lane forwards (flext-eo4at) (#2628)
- fix(codemod): concurrent renderings of one digest never share a temp file
  (flext-hlo2m) (#2627)
- fix(make): bound Git discovery at the runtime root (flext-ce0q5) (#2626)
- fix(git): a proven-clean superproject worktree is removed (flext-78vw8) (#2625)
- test(codemod): bind the envelope checker port in the rope consumer fixture (#2623)
- fix(hooks): restore the unconditional validator tail (#2624)
- fix(codegen): never emit the main package twice in hatch sources (#2621)
- fix(hooks): refuse an unsupported hook stage in the dispatch itself (#2620)
- chore(gen): regenerate projections on the dynamic lazy runtime (#2619)
- fix(make): strip an inherited PYTHONDONTWRITEBYTECODE as the ruling requires (#2618)
- fix(infra): tip repairs — F811, direct references, dynamic core lock, member guide
  fixed point (#2617)
- fix(discovery): a member inside a staged preview is scoped by that preview (#2615)
- fix(codegen): give the git-hook validator render its make contract (#2614)
- fix(codegen): a rendered protocol holder replaces its stale disk copy in the aggregate
  (flext-hk02w) (#2608)
- fix(hooks): render a legal no-op stage when no hooks are configured (#2610)
- fix(codegen): keep facade layout when projecting the canonical letter base (#2609)
- fix(codegen): keep fleet dev suppliers and FLEXT sources for standalone consumers
  (#2607)
- fix(infra): green the integration tip (finish the discovery parse-recording test;
  split the facade canonicalizer) (#2606)
- feat(lazy-init): render only the stand-in exports; no member or base lists (#2602)
- fix(pyproject): keep declared direct references of internal requirements (#2604)
- fix(git): exterminate lane admission and lane census (#2603)
- chore(infra): regenerate the managed envrc projection (#2601)
- fix(infra): keep indexed lazy bases on their native route (#2600)
- fix(infra): restore host tool precedence and append uv git transport (#2599)
- fix(gen): resolve the infrastructure repository from the owning superproject (#2598)
- fix(gen): a fleet requirement carries its name, not a source URL (#2595)
- fix(gen): refresh inputs after resolution and read superproject declarations (#2597)
- fix(infra): resolve governed member worktrees and the lazy-init name narrowing (#2596)
- fix(pyproject): plain fleet requirements and lazy-init narrowing (#2594)
- feat(codegen): resolve workspace providers from the generated inventory (#2593)
- fix(gen): read generated public names from \_\_all\_\_ and \_LAZY\_IMPORTS (#2590)
- fix(pyproject): plain requirements for workspace members; break the tests facade cycle
  (#2592)
- fix(infra): unblock the toolchain at the integration tip (#2591)
- fix(gen): admit staged source preview and fix import-law/discovery findings (#2587)
- fix(discovery): require a Git checkout for Python source discovery (WIP) (#2581)
- ci(github): refactor CI workflows to use flext-infra submodule (#2580)
- refactor(protocol-models): delete the route collector left unreachable (#2579)
- fix(semantic-cutover): a facade base class is not a composed public owner (#2578)
- refactor(rope): single owner for lazy export routes (flext-h5l57) (#2577)
- fix(upg): upgrade the executor closure before the cooldown (#2576)
- fix(semantic-cutover): resolve editable source exports from the AST (#2575)
- refactor(rope): add the lazy-export parser to the alias owner (flext-h5l57) (#2571)
- chore(gen): preserve the regenerated projections from the carry-over run (#2574)
- fix(gates): run pyrefly in the project runtime, not the launcher interpreter (#2572)
- fix(upg): upgrade the tool package in the pre-resolution executor (#2570)
- fix(codegen): sweep candidate trees left by killed producers (#2569)
- fix(upg): resolve the pre-resolution executor from the declared sources (#2568)
- fix(hooks): rename the WIP preservation namespace (#2567)
- refactor(protocol-models): delete three unreferenced source helpers (#2566)
- test(import-law): pin the tests namespace root fixed point (#2565)
- fix(gates): let the generating route repair a stale toolchain projection (#2564)
- test(protocols): record the build\_lazy\_import\_map holder gap (flext-h5l57) (#2563)
- fix(import-law): keep the test namespace root import canonical (#2561)
- refactor(gates): read gate evidence through json\_loads (#2562)
- fix(setup): resolve prek inside the activated Mise environment (#2560)
- fix(gen): plan every selected repository and retire stale hooks (#2559)
- fix(pytest): run the suite after a selecting probe that finds failures (#2558)
- fix(lazy-init): collect unpacking names in the class member map (#2557)
- docs: align the runtime, test and make guides with the governed contracts (#2556)
- docs(guide): state the real pytest budget owner (#2555)
- docs(runtime): state the attached-excluded and linked-worktree ownership (#2554)
- docs(guide): name the generated lazy-initializer contract (#2553)
- fix(make): admit the local git file protocol for uv cached checkouts (flext-g7fau)
  (#2552)
- docs(toolchain): drop the retired node entry from the base comment (#2544)
- fix(pytest): fail item deadlines loudly and run the applicable popula… (#2551)
- fix(infra): raise the pytest operator caps to 1800 seconds (#2550)
- fix(lazy-init): a type-checking member is not a runtime class member (#2549)
- fix(codegen): resolve a base holder the family root publishes lazily (flext-58p29)
  (#2548)
- fix(gates): never reclaim a live admission owner's ticket (#2547)
- fix(rope): delete unused \_index\_modules (#2546)
- fix(lazy-init): keep dunder metadata out of the tests facade (#2545)
- fix(codegen): resolve assigned protocol aliases to their source class (#2543)
- fix(codegen): re-read a repository invalidated by a concurrent write (#2542)
- fix(lazy-init): a TYPE\_CHECKING-only annotation is not a stand-in defect (#2540)
- fix(validate): carry the owner import into the probe prelude (flext-cogu4) (#2539)
- fix(validate): resolve a stand-in owner module before comparison (flext-cogu4) (#2538)
- fix(lazy-init): share attribute-chain ancestor bases by their root route (#2537)
- feat(upg): sync pin and lock integrity with codegen projections (#2535)
- feat(gates): add admitted native-gate workspace route (#2534)
- feat(deps): add governed direnv allow, UPG\_PACKAGES, and Git pin convergence
  verification (#2536)
- feat(check): enforce law\_id claim in ast-grep rules catalog (#2533)
- fix(deps): ignore \_\_pycache\_\_ bytecode in deptry source identity (#2532)
- fix(workflows): build and prove docs site once per run (#2531)
- chore(codegen): drop the exclusion for a deleted plan document (#2530)
- fix(pytest): item deadline measures the test call, not plugin bookkeeping (#2529)
- test(infra): inject the scan batch size instead of mutating config
  (flext-itpd1.3.24.1) (#2528)
- chore(history): consolidate archive/exterminated-20261116 into 0.12.0-dev (#2527)
- test(infra): consume public check and pytest surfaces (#2526)
- test: public surfaces only — fixtures use the root; internal-only codegen tests
  exterminated (#2525)
- fix(lazy-init): a part the package's import-time code reads stays real (#2524)
- test(infra): delete schema-shape assertions that encode declaration form (#2523)
- test(codegen): plan facade publication through the public conform boundary (#2522)
- test(codemod): prove field-metadata migration on its declared rule scope (#2521)
- fix: Remove incomplete SOP command stubs causing pyrefly failures (#2519)
- fix(release): admit declared repository namespace packages in wheel boundary (#2520)
- fix(codegen): emit single primary pre-push gate (aihub-b1qla) (#2518)
- fix(envrc): stop exporting VIRTUAL\_ENV to prevent uv mismatch warnings (#2517)
- fix(tooling): preserve passive local checker configuration (#2516)
- fix(codemod): the model\_config autofix converges again and ENFORCE-103 elects its
  repairs (#2515)
- feat: Add test timing gate with pytest-timeout (PR 4) (#2514)
- fix(tests): enforce native suite and item deadlines (#2511)
- fix(check): gate fixtures and gate results match a real workspace (tests/unit/check)
  (#2506)
- fix(codegen): reject unprovisioned generation targets before admission (#2504)
- refactor(check): one type checker — Ruff and Pyrefly own Python analysis (#2505)
- fix(release): a GitHub default merge message states its title in the body (#2510)
- fix(gates): bind resolver inputs to original receipts (#2509)
- fix(deps): refresh Flext Infra supplier lock (#2508)
- feat(codemod): theme laws elect the model\_config prerequisites of the preset rewrites
  (#2503)
- chore(deps): pin Rope 1.15.2+dc.8 (#2502)
- feat(codemod): require-field-description repairs the field with a name-derived
  description (#2500)
- feat(lazy-init): stand-in fidelity gates — rule 5 rejections, no-member exclusion,
  completeness check (ADR-018) (#2499)
- docs(tooling): docker tests require a configured .env (flext-yumvy) (#2498)
- fix(codemod): has/lacks with a tuple or list operand assert it as one element (#2497)
- fix(tests): repair the flext-infra tip tests left red after #2481 (#2490)
- fix(gitignore): attached members keep the standalone ignore policy (#2495)
- fix(mypy): namespace\_packages true for every project (operator ruling 2026-11-14)
  (#2491)
- perf(tests): read the installed Git's local env keys once per session (#2496)
- fix(codegen): inject project custom CI steps into both Docs jobs (#2494)
- fix(lazy-init): ancestor bases shared by import route; one base resolver (ADR-018
  stand-in law, rules 4 and 7) (#2492)
- feat(admission): project extra verbs accept admission overrides (#2493)
- fix(admission): admit setup, gen and check up to load5 160 (#2486)
- feat(docs): run the docs engine as ProperDocs (#2484)
- fix(templates): CQRS gate exclusions match grep's ./ prefix (#2485)
- fix(tests): bootstrap converges; fixtures track their files; tests follow executed
  gates (#2481)
- fix(workspace): attached member renders the workspace profile from every scope (#2483)
- perf(codemod): test the attribute name before the receiver scope search (#2482)
- fix(mod): restore green check after the scan-batch persistence (#2479) (#2480)
- fix(mod): persist ast-grep cache fragments per completed scan batch (#2479)
- wip(preserve): check-complete budget experiment as of 2026-11-13T23:18Z (#2478)
- fix(pytest): a single-process suite stop persists its executed prefix (#2477)
- fix(deps): upg-bounds validates the TOML uv.lock in lax mode (adopted lane, draft)
  (#2471)
- refactor(lazy-init): publish \_\_all\_\_ = tuple(\_LAZY\_IMPORTS) in protocol/family
  initializers (adopted WIP, draft) (#2469)
- fix(pytest): a single-process suite stop persists its executed prefix (adopted lane,
  draft) (#2468)
- fix(tests): absolute eager dunder imports; codemod gate counts its own rule (#2466)
- fix(gates): generated projections do not own duplication findings (#2458)
- test(tooling): fail on any drift of the operator-authorized mypy suspensions
  (flext-ier7x) (#2455)
- feat(admission): preflight resolves every declared tool before a route queues
  (flext-mcjop) (#2453)
- fix(codemod): derive test-namespace first party from project facts (#2470)
- feat(validate): project-owned pytest worker ceiling via the tooling overlay; neutral
  consumer examples (#2467)
- fix(release): list only Conventional Commits subjects in release notes (#2476)
- chore: neutral consumer names in the remaining guide, docstring and tests (#2475)
- chore: neutral consumer data in flext-infra guides, comments and tests (#2474)
- fix(codemod): unblock make mod — unique artifacts, constant unpacking, branchless
  assert rewrites (#2465)
- fix(qlty): exclude mandated PEP 723 metadata from duplication (#2464)
- fix(ci): initialize only declared workspace members (#2463)
- fix(release): collapse untrusted whitespace in release notes (#2456)
- fix(admission): dimensiona o budget do mod para o censo do catálogo (#2462)
- fix(codemod): regenerate the stale pydantic-model-config snapshot (flext-hwxw0)
  (#2461)
- fix(rules): regenera o baseline do teste pydantic-model-config (#2460)
- fix(mod): persisted scan evidence validates from its own JSON (flext-i9939) (#2459)
- fix(codemod): restore the shared scan route on the integration tip (#2457)
- chore(upg): follow the Rope relock and current projection (#2449)
- fix(mod): evidence publication removes native artifacts no evidence references
  (flext-b4gw3.3) (#2448)
- fix(tests): local make tests deselects harness-only remote gates like CI; upg prune
  regression (#2447)
- fix(discovery): a syntax-broken source never aborts check before its … (#2446)
- fix(discovery): a syntax-broken source never aborts check before its gates (#2445)
- fix(loc-cap): generated-source trees never count against the module cap (#2444)
- fix(mod): evidence publication removes native artifacts no evidence r… (#2443)
- fix(import-law): drop the orphaned ImportGraphFacts protocol and its … (#2440)
- fix(tests): the preamble-clone fixture reaches jscpd's floors (#2436)
- fix(tests): two tip fixtures meet their real runtime contracts (reaping reserve, Git
  on PATH) (#2433)
- perf(snapshot): read \_\_all\_\_ from the parse's static facts, not a full binding
  index (flext-opr6o) (#2430)
- perf(codemod): per-source ast-grep scan cache shared by check and mod (flext-f53bg,
  flext-opr6o) (#2425)
- fix(check): the complete route owns each phase's native limit (#2427)
- fix(check): a failed phase ends the verb; pending gates run by declared budget
  (flext-mcjop) (#2426)
- fix(clean): the clean verb covers every declared member (flext-b4gw3.3) (#2437)
- test(check): checker fixtures are real workspaces (tip red: cannot open git
  repository) (#2435)
- fix(lazy-init): examples and scripts roots publish facades; a tier facade is never a
  part (#2434)
- perf(codemod): probe each target environment once, not once per member (#2432)
- test(codemod): compare the published findings as tuples (flext-uwwxc) (#2431)
- fix(codemod): measure findings a stopped scan already published (flext-uwwxc) (#2429)
- fix(import-law): drop the orphaned ImportGraphFacts protocol (follow-up to #2421)
  (#2428)
- docs(execution-context): wrap the Ruff cache paragraph to the configured line length
  (#2424)
- fix(import-law): per-run import graph; delete the persistent store that crashes
  refactor mod (flext-b4gw3.3) (#2421)
- fix(ruff): one shared Ruff cache; Ruff keys its own entries (flext-b4gw3.3) (#2422)
- fix(tests): fleet runtime passes the scratch storage; SourceCandidate takes the tuple
  it compares (#2423)
- chore(gen): project the restored 14 mypy codes into pyproject.toml (#2420)
- test(check): the CLI fixture member is a registered submodule, as in a real workspace
  (#2419)
- test(check): run\_projects fixtures are Git checkouts and read the receipt layout
  (flext-cvh9q) (#2418)
- fix(rules): model\_config ClassVar rule covers FlextModelsPydantic qualifier (#2417)
- perf(codemod): plain writes inside the private staging dir; start fingerprint through
  phase advance (#2416)
- fix(codemod): key the ast-grep rendering by member-relative paths (#2415)
- fix(codemod): scan scratch in the tempfile default, removed on exit (flext-b4gw3.3)
  (#2414)
- test(markdown): format-gate fixtures stop freezing the configured list-marker style
  (#2413)
- perf(mod): the native cascade runs only over sources with a native finding
  (flext-g4wer) (#2412)
- fix: flext-infra tip to zero check findings (#2411)
- fix(codemod): a rule plan of a root without pyproject.toml fails typed (#2409)
- fix(tooling): restore the 14 suspended mypy codes (operator order 2026-11-13) (#2408)
- perf(docs): one policy load per scope and one ruff per fence set (root Docs timeout)
  (#2400)
- feat(codegen): every family facade part is a lazy stand-in, one rule (#2392)
- fix(packaging): uv cache keys cover every wheel input (#2407)
- fix(codemod): a rule selection keeps the generated provider's utilities (#2406)
- fix(git,check,deps,codegen): a Git identity failure is a typed failure on every route,
  never a traceback (#2403)
- fix(upg): upg-bounds reads uv.lock in lax mode; the executor sync drops the retired
  PREPARE\_ENVIRONMENT (#2396)
- fix(codegen): generation holds the mutation barrier from first read to publication
  (#2405)
- fix(upg): the project verb no longer prunes the shared uv cache (flext-27b1m) (#2404)
- fix(mod): the selection is validated before the route queues (ADR-032 fail early)
  (#2402)
- fix(upg): the executor recipe no longer references the deleted PREPARE\_ENVIRONMENT
  (flext-uool9) (#2401)
- fix(deps): migrations elected in one pass under the complexity budget; regenerate
  stale deps projections (#2393)
- fix(codegen): the .mise.toml template reads mise\_version from its own context (#2395)
- fix(detector,ci): unmanaged submodules alone keep a checkout standalone (#2399)
- test(discovery): the ceiling inventory contract lives with the discovery owner (#2398)
- fix(gates): admission arms its budget through the flext-cli process deadline (#2397)
- fix(upg): the project verb no longer prunes Mise tools host-wide (flext-tprlj) (#2394)
- fix(setup): the pre-push hook keeps the push's stdin in memory, never in a git-dir
  file (#2387)
- fix(deps-gate): the FLEXT line is resolved only for internal references; the scan's
  failure comes first (#2386)
- fix(gates): the Pyright gate sizes Node's heap from its recipe's memory bound
  (flext-msgnc) (#2388)
- refactor(codegen): delete the facade publication workarounds Rope no longer needs
  (flext-4hrmg) (#2385)
- fix(codemod): the compat marker read skips a class without annotation source
  (flext-6es59) (#2384)
- fix(tests): fixtures reuse tool data; session cache home under pytest retention
  (#2383)
- fix(setup): prune superseded tool versions on upg; shims path from config (#2381)
- fix(codegen): pin the Rope that binds a TypeAlias publication to its value; .mise.toml
  reads its flat keys (#2382)
- fix(codemod): the scan cache key covers rule documents and the resolved scanner
  (#2380)
- fix(make): every verb runs at idle cgroup weight; only the full forms refuse under
  load (#2379)
- fix(tests): pytest owns its basetemp; the custom per-run scratch is deleted (#2373)
- fix(rope): one project owner keeps Rope state out of repository roots (#2377)
- fix(setup): reuse the installer-default Mise and sync the environment in place (#2372)
- fix(make): every verb is admitted by host load and runs in a cgroup scope (5 GB, 2
  CPUs) (#2374)
- fix(discovery): one Git inventory at the checked root decides Python directories
  (#2375)
- fix(rope): the Pydantic adapter rule emits TypeForm; its tests use the rule scope
  (#2376)
- fix(protocols): resolve published generic bases in model ancestry (#2378)
- feat(gates): host-wide FIFO admission with the budget armed at admission (ADR-032)
  (#2370)
- chore(preserve): worktree WIP of gate-admission-20261112 before retir… (#2369)
- fix(codegen): delete the unreachable workspace declaration block (#2371)
- fix(ci,codegen): fetch an attached member after auth and submodule init; bound build
  targets of a packaged workspace root (#2368)
