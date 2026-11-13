# Release v0.12.1

## Scope

- Release version: 0.12.1
- Projects packaged: 2

## Projects impacted

- root
- flext-infra

## Pull requests since last release

- fix(codegen): a generated facade stops composing an orchestrator moved out of its
  family (#2326)
- fix(release): the lane refreshes only its open pull request (#2325)
- fix(codemod): the semantic planning graph carries the injected envelope checker
  (#2316)
- fix(release): notes GitHub cannot publish fail before the release exists (#2324)
- fix(codegen): facades publish family classes only through MRO composition (#2323)
- fix(codegen): a generated facade stops re-exporting a class moved out of its family
  (#2321)
- fix(release): notes list integration PRs; the PR body is their summary (#2322)
- fix(release): the lane merge takes the base's generated projections (#2320)
- fix(docs): workspace links resolve in standalone checkouts (#2319)
- fix(codemod): key the ast-grep scan cache on source content, not path names (#2317)
- fix(deps): resolve the soupsieve advisory inside the cooldown (#2318)
- feat(codegen): consumer project kind for repositories without code, make lock, README
  marker fix (#2315)
- feat(codegen): apply the dependency cooldown to uv resolution (#2313)
- fix: new projects depend on their upstream; artifact scope tests follow the documented
  contracts (#2312)
- fix(docs): the bundle computes the planned root projection it forwards (#2314)
- fix(check): locked lanes are never merged-but-alive (#2307)
- perf(setup): one flext-infra process verifies and wires the environment (#2310) no
- fix: law-9 re-audit of test-only changes; production defects fixed first (#2308)
- perf(codegen): coalesce fleet planning facts and bound admission (#2293)
- perf(lazy): the flext-infra facades import no declared distribution; config loads
  rules only (flext-df0b6) (#2311)
- style(tests): format the fixture tooling helper (#2309)
- fix: first group of 0.12.0-dev test failures fixed at their root cause (#2302)
- chore(lock): pin FLEXT upstreams to their 0.12.0-dev tips (#2304)
- perf(tests): resolve selection and inventory in one collection pass (#2306)
- fix(codegen): close the verified review findings of #2262/#2264/#2266 (#2300)
- perf(mod): focused make mod within budget; reuse import facts; fix rendering cache key
  (#2305)
- fix(codegen): uv sources follow the FLEXT line; project subscripted sibling bases
  (#2303)
- perf(lazy-init): defer heavy capabilities behind facade-only stand-ins (#2301)
- perf(setup): remove the private setup/upg lifecycle lease (#2298)
- fix(codegen): project protocols for models rooted in m.RootModel (#2297)
- fix(check): active lanes are never merged-but-alive (#2295)
- fix(docs): scope building receives the planned root projection (#2296)
- perf(setup): keep a .venv that already satisfies uv.lock (#2287)
- fix(make): remove the test file selector and validate the gen root (#2285)
- Integrate wt-pre-commit-setup-wip-20261112 into upload-20261007 (#2277)
- fix(security): load generated protocol modules through importlib; format codemod tests
  (#2292)
- fix(rules): ban disabling Python bytecode in every FLEXT project (ENFORCE-128) (#2291)
- fix(codegen): model protocol projection binds only what it writes (#2290)
- fix(codemod): focused mod scans its selection; provision the mod\_workspace
  environment (#2289)
- perf(setup): keep a lock-satisfied .venv, compile bytecode, drop the private
  publication lock (#2288)
- fix(security): declare the subprocess axiom and the bandit skips in the tooling SSOT
  (#2286)
- fix(check): share one warm Mypy cache across worktrees and run Mypy only locally
  (#2284)
- feat(codemod): domain capabilities exempt their own technology prefixes from the
  library-name rule (#2283)
- chore(integration): land upload-20261007 into 0.12.0-dev (docs: model fields keep the
  model) (#2281)
- chore(integration): land upload-20261007 into 0.12.0-dev (2026-11-12 convergence)
  (#2270)
- fix(codegen): skip non-text (binary) files in retired projection planning (#2260)
- Upload 20261007 (#2258)
- fix(codegen): preserve declared editor artifacts and portable bootstrap (#2257)
- chore: retire host-specific bootstrap alias from source (#2256)
- fix(setup): remove broken .bin symlink before mkdir (#2255)
- fix(setup): make .bin directory creation non-fatal (#2254)
- fix(setup): make lifecycle mkdir non-fatal (#2253)
- fix(setup): ignore mkdir errors in bootstrap (#2251)
- fix(setup): make bootstrap report directory creation idempotent (#2250)
- fix(setup): repair Makefile quoting (#2249)
- fix(setup): exclude bootstrap Mise paths from symlink check (#2248)
- fix(base): use default-value style for optional CommandOutput field (#2247)
- fix(gates): use default-value style for optional GateTestIntent field (#2246)
- feat(attestation): candidate admission contract on top of V3 proof (#2245)
- Wip/sweep preserve/xdist worker resolution 20261108 52854e47 (#2244)
- Wip/sweep preserve/test secret rule 0d7bffb0 (#2243)
- Wip/sweep preserve/protocol alias owner 20261108 98d44d04 (#2242)
- Wip/sweep preserve/infra model field protocols 20261108 feb449c2 (#2241)
- Wip/sweep preserve/gen facades speed 182baa95 (#2239)
- Wip/sweep preserve/editor analyzer context f198a752 (#2238)
- Wip/sweep preserve/flext infra rope paren 20261108 03af5731 (#2235)
- Wip/sweep preserve/flext infra mod indent 20261108 89879747 (#2234)
- Wip/sweep preserve/agents md projection e224d59a (#2232)
- Wip/sweep preserve/g6 duplication format scope b8872a85 (#2229)
- Wip/sweep preserve/g4 gates typing 3db69f26 (#2227)
- Wip/sweep preserve/flext infra mise tools ddfd692c (#2223)
- Preserve/flext infra/stash cd7eff0b (#2220)
- Preserve/flext infra/stash 1bb35e4b (#2219)
- fix(rules): one ENFORCE-102 rule for methods without self/cls (#2214)
- feat(codemod): dump without computed fields through the native keyword (#2217)
- fix(codegen): ignore the executor runtime state directory, not only the venv (#2215)
- fix: locked direnv, identifier stems for Python commands, header-declared script verbs
  (#2213)
- fix(markdown): make fix moves the MkDocs list blocks rumdl withholds (#2212)
- feat(codemod): ban runtime skips after reading the environment (#2211)
- chore(deps): rope 1.15.2+dc.6 through make gen/upg (#2216)
- Upload 20261007 (#2218)
- Land upload-20261007 into 0.12.0-dev (2026-11-08 convergence) (#2209)
- fix(codegen): docs jobs read packages for declared registry consumers (#2208)
- fix(codegen): atomic admission preflight before publication (flext-wmzp6) (#2207)
- fix(codegen): project quoted model forward references to sibling protocols (#2204)
- fix(upg): members lock themselves; root composes them (ADR-030, flext-zzynv) (#2201)
- fix(codemod,pytest): import profundo do próprio pacote de topo (B8) e overloads de
  u.Tests.fixture (B7) (#2198)
- test(codegen): credencial de dependência privada fica fora do Git global (#2197)
- fix(cutover): rewrite every test assert by its top-level operator, whole and typed
  (#2195)
- fix(tests): owned connectivity prerequisite skips do not fail the run (#2200)
- feat(mod): migrate flext-command headers to PEP 723 script blocks (#2199)
- fix(codegen): ci-template renders no blank line at EOF (#2189)
- fix(codegen): editor surface refreshes the qlty smells configuration (#2194)
- fix(rules): staticmethod rule ignores scenario-data roots (#2193)
- fix(types): annotate p.\* and remove in-place mutation in infra mutable state (#2181)
- fix(types): annotate instances by protocol (model-annotation-to-protocol rule) (#2178)
- fix(codemod): staged Python view no longer hides declared physical Markdown (#2188)
- fix(rules): staticmethod rule sees a typed self parameter (#2186)
- chore(deps): rope 1.15.2+dc.5 through make gen/upg (#2185)
- feat(rules): declare class methods without self as staticmethod (#2184)
- fix(cutover): read model protocol routes from the workspace session (#2183)
- fix(codemod,deps): consumer make fix/mod crashes (FlextCliUtilities.Infra, absent
  candidate bytes, data-dir naming) (#2182)
- fix(infra): break semantic cutover import cycle (ENFORCE-051) (#2180)
- fix(infra): flext-infra lint gate to 0 findings (#2179)
- fix(codegen): open each lazy-init member snapshot with its own member root (#2176)
- fix(tests): admit tests on the receipt the project's own check wrote (#2177)
- fix(codegen): keep scenario-data roots out of the staged-file check hook (#2175)
- fix(check): runtime-integrity fails when uv.lock is stale against its manifest (#2174)
- Land upload-20261007 into 0.12.0-dev (2026-11-07 convergence) (#2173)
- Land upload-20261007 into 0.12.0-dev (2026-11-07 convergence) (#2172)
- Land upload-20261007 into 0.12.0-dev (2026-11-07 convergence) (#2171)
- fix(batch-gates): rules and selection read through their contracts (rebased) (#2170)
- fix(conform): publication and repository reads use their contracts (rebased) (#2168)
- fix(conform): planning produces the owned plan contract (rebased) (#2166)
- fix(codemod): iteration state reads the plan contract (rebased) (#2164)
- fix(batch-gates): rules and selection read through their contracts (rebased) (#2162)
- fix(codemod): witnesses and iterations read through the AtomicFileState contract
  (rebased) (#2160)
- test(codegen): build invalid payloads through typed JSON adapters (#2157)
- fix(projector): project computed fields bound through any models facade (#2155)
- fix(template): strip the template newline after the rendered hook block (#2154)
- fix(template): avoid the blank line at the end of the generated hook file (#2153)
- fix(template): close the pre-commit hook branch before the macro ends (#2152)
- fix(infra): adopt pending protocol/tooling fixes (mixins, regular packages, alias
  guard) (#2151)
- fix(rope): restore runtime-evaluated base inventory removed by the formats commit
  (#2150)
- fix(projector): guard relative import modules before prefix matching (#2149)
- fix: owned rope spec and typed artifact derivation (#2148)
- fix(deps-gate): scan and issue collection keep the protocol contracts (#2147)
- fix(duplicate-apply): read clone sides through the typed jscpd contract (#2146)
- fix(workspace): spec keeps protocol contracts with owning model schemas (#2145)
- fix(sweep): owned evidence keeps protocol contracts; lint snapshots validate through
  the model (#2144)
- fix(contexts): Makefile render spec keeps protocol contracts with owning schemas
  (#2143)
- fix(contexts): render inputs keep the protocol contract with the owning model schema
  (#2142)
- fix(projector): owned render contracts and native source capabilities (#2141)
- fix(projector): narrow Rope consumers to their native contracts (#2140)
- fix(protocols): capitalized model fields are read-only contracts (#2139)
- fix(census): an inherited namespace never competes with its declaring owner (#2117)
- fix(codemod): render provider export utilities for module-object reads (#2128)
- fix(markdown): rumdl single engine, canonical config, concurrent generation (#2122)
- Upload 20261007 (#2138)
- feat(tooling): allow Pydantic schema hooks as contract dunders (#2137)
- fix(codemod): owned semantic plans and model-boundary witness (#2136)
- fix(codemod): narrow duplicate cure plans through their models (#2135)
- fix(typing): reference the flattened DepsToml protocol family (#2134)
- fix(typing): mutable observation context uses its owned model (#2133)
- fix(ci): align bootstrap submodules to the recorded commit, not a retired branch
  (#2132)
- fix(refactor): contract owner resolution + CI-owned gate (#2123)
- fix(infra): stabilize and integrate upload-20261007 (#2107)
- fix(import-law): unnamed installed provider resolves natively at the boundary (#2102)
- fix(rope): unnamed installed provider contributes no lazy bindings (#2101)
- fix(setup): bootstrap FLEXT via uv pip, sem re-resolução (overlay --no-deps) (#2100)
- Upload 20261007 (#2099)
- Upload 20261007 (#2098)
- \[WIP\] upload-20261007: joint plan flext-1engx integration (#2095)
- Cadi 20261024 (#2096)
- \[WIP\] setup: install the declared Git hook stages with prek (#2093)
- upload-20261007: member-lane identity fixes (lane migration); upg/gen perf follow-ups
  (#2094)
- Stabilize typed codegen and native validation on upload integration lane (#2092)
- Upload 20261007 (#2091)
- fix: update flext-core pin to latest integrated SHA (#2090)
- fix: publish pending flext-infra changes (coalescing + security remediation) (#2089)
- fix: coalesce directory observation and security remediation (#2088)
- fix: apply security remediation and coalesce directory observation (#2087)
- fix: coalesce directory observation in generation pipeline (#2086)
- Upload 20261007 (#2085)
- chore(docs-batch-publication-20261013): preserve fix/docs-batch-publi… (#2081)
- chore(projections-4pt43): preserve fix/projections-4pt43 changes acro… (#2082)
- Fix/infra test green 20261017 (#2079)
- Upload 20261007 (#2084)
- \[WIP\] refactor(workspace): bring environment\_provenance under the loc… (#2083)
- wip (#2080)
- fix(integration): merge the stabilization surgery onto 0.12.0-dev (#2077)
- Fix/gate cures adopt 20261017 (#2078)
- Upload 20261007 (#2075)
- release: bandit gate honors the src-only audit contract in check\_files (#2074)
- release: config\_files composes inherited cli elections under infra authority (#2073)
- Upload 20261007 (#2072)
- Fix/infra dedup 20261017 (#2069)
- Fix/infra loc cap 20261017 (#2068)
- \[WIP\] fix(check): cure census, deps and lint shares on upload 9315ff4 (#2067)
- Upload 20261007 (#2065)
- Codex/declared sources and scheduling 20261016 (#2064)
- Integrate current Infra runtime, Make lifecycle and native proof contracts (#2054)
- fix(infra): green campaign part 2 (flext-90pw7) (#2045)
- chore(fleet-unit-20261010): preserve feat/fleet-unit-20261010 changes… (#2039)
- \[WIP\] fix(codegen): conform derives tooling from the planned lazy-init projection
  (flext-90pw7) (#2044)
- Fix/aihub consumer blockers 20261015 (#2041)
- chore(oud-upload-tip-20ba-20261014): preserve test/oud-upload-tip-20b… (#2033)
- chore(codex-cache-20261012): preserve fix/cache-publication-20261012 … (#2038)
- chore(alias-identity-20261008): preserve fix/alias-identity-20261008 … (#2036)
- chore(ci-root-cause-20261013): preserve fix/infra-ci-root-cause-20261… (#2037)
- chore(nsstatic-codemod-20261012): preserve fix/namespace-static-path-… (#2032)
- chore(mod-family-emenda-20261013): preserve fix/mod-family-emenda-202… (#2020)
- perf(workspace): native capture fits the cold-probe budget (flext-zd80z) (#2030)
- fix(make): restore the attached-member upg delegation and its endif (#2031)
- chore(text-rule-scope-20261008): preserve fix/text-rule-scope-2026100… (#2025)
- chore(deps): mkdocstrings-python floor 2.0.9 (WIP) (#2023)
- Fix/infra postmerge reds 20261016 (#2024)
- fix(workspace): one dataclass inheritance proof; drop the linear base mirror (#2021)
- Fix/native proof on 0.12 20261016 (#2015)
- \[WIP\] merge upload-20261007 tip into the candidate-bootstrap provider… (#2014)
- fix(workspace): prove dataclasses that inherit dataclass fields (#2013)
- Fix/native proof on 0.12 20261016 (#2012)
- \[WIP\] fix(workspace): abstract dataclass receivers and @abstractmetho… (#2011)
- Fix/fleet converge 20261015 (#2010)
- fix(release): resolve the repository-declared integration branch (#2009)
- merge: upload-20261007 into 0.12.0-dev (#2008)
- fix(ci): keep pull\_request runs out of the integration push group (#2003)
- fix(infra): converged upg stages, upg converge activation and snapshot drift (#1991)
- merge: converge upload-20261007 (15f8c6361f7bd2891ac55f80b0f313cfd706… (#1989)
- fix(infra): restore native provenance and workspace lifecycle (#1985)
- fix(codegen): the transaction self-serves its producer authority (#1983)
- upload-20261007 → 0.12.0-dev: the native-reference capture + provenance series (#1982)
- fix(provenance): third-party bindings admit through their executed value (#1981)
- fix(provenance): third-party factories admit through their installed package (#1980)
- fix(provenance): the alias-supplier gate admits third-party receivers (#1979)
- fix(pyproject): restore the requirements-provenance renderer to its complete state
  (#1978)
- fix(codemod): preserve scanner selection and binding ownership (#1976)
- fix(codemod): the resolved-symbol operand check names its own class constant (#1974)
- fix(utilities): the semantic family type-references calls import their owner (#1973)
- Upload 20261007 (#1972)
- fix(codegen): mise artifacts state imports its siblings from their owners + wave fixes
  (#1970)
- fix(models): DeptryDiagnostic.error declares its field description (#1969)
- Upload 20261007 (#1968)
- fix(rope): the analyzed checkout's own barrels always join the alias map (#1967)
- merge: the ast-grep rules corpus duplication exclusion + the adopted 0.12.0-dev state
  (#1966)
- fix(rules): message-variant rewire skips multi-line message blocks (#1965)
- Upload 20261007 → 0.12.0-dev: generator invariant + resilience gates (#1964)
- fix(tooling): resilient bootstrap + render provenance + the deps check gate (#1963)
- fix(codemod): identity enforcement applies to pinned sources only (#1962)
- fix(codemod): installed-package evidence never reaches layout pinning (#1961)
- fix(codemod): evidence-only inputs survive unpinned layouts (#1960)
- fix(codemod): rope pinning covers workspace rewrite targets only (#1959)
- fix(codemod): candidate admission guards destinations, not journal evidence (#1958)
- merge: the policy-overlay selector cure + the adopted 0.12.0-dev state (#1957)
- Upload 20261007 → 0.12.0-dev: wave jscpd-gate + refactors (29ee9cc7f) (#1956)
- fix(layout): gate reads the layered codegen inputs, not the config singleton (#1955)
- fix(check): exclude package-lock.json from the duplication gate (operator-authorized)
  (#1952)
- merge: relink upload-20261007 with 0.12.0-dev — exterminate committed conflict markers
  (flext-yjl38) (#1953)
- Upload 20261007 → 0.12.0-dev: rule wave + concurrent-safe mod engine (#1951)
- fix(rules): scope the test-reality detectors to their genuine targets (#1950)
- fix(import-law): base-less class bodies are typing-only under deferred annotations
  (#1949)
- fix(workspace): standalone self-root is its environment's editable install (#1948)
- fix(api): restore the constants letter the import prune dropped — make mod unbroken
  (#1947)
- fixes (#1946)
- Repair workspace automation, runtime configuration and original CI evidence (#1943)
- feat: fleet automation defaults — strict enforcement, cross-project duplication,
  member-scoped rollout (#1944)
- fix: preserve generation gains and restore strict import boundaries (#1942)
- fix(codegen): fail loud when a managed template render produces no content (#1941)
- Land the config/ wheel include restoration (#1940)
- Upload 20261007 (#1939)
- fix(codegen): script-verb discovery stops emitting the dropped requires\_apply field
  (#1938)
- Upload 20261007 (#1937)
- Integrate/f60h2 20261010 (#1936)
- fix: stabilize runner, generation and semantic owner boundaries (#1933)
- Union/20261010 (#1935)
- fix(gates,codemod): the empty-factory retirement — unblock every consumer's make setup
  (#1934)
- fix(templates,codegen): cure the grand-union collateral — conflict markers,
  mise\_locked, facade scanner, export collector (#1932)
- Integrate/f60h2 20261010 (#1931)
- fix(stabilization): plain self in the conform partials; typed receipt… (#1930)
- Upload 20261007 (#1929)
- grand union: 13 lanes absorvidas + curas de estabilidade (ciclos 1-11) (#1928)
- Fix/envrc host tools 20261010 (#1927)
- fix(codemod): elect text rules by distribution before source inventory (#1926)
- \[WIP\] preserve: alternative tip cures superseded by 9d8678403 (gate-b… (#1925)
- perf(workspace): gen/mod/fix as one fleet unit; cure dev CI reds (#1924)
- Upload 20261007 (#1923)
- Upload 20261007 (#1919)
- fix(gates): flext-infra 0.12.0-dev green again after #1909 (#1916)
- Fix/conform stash cure 20261009 (#1912)
- Upload 20261007 (#1909)
- \[WIP\] fix(make): upg hands off to a fresh make upg when gen publishes a new Makefile
  (#1903)
- fix(tests): lane-guard contract wording + remote HEAD fixture (stability loop cycle
  10) (#1908)
- fix(tests): beads identity dump carries ownership-command defaults (stability loop
  cycle 9) (#1907)
- fix(config,models,locks): beartype floor cap + bare-project coercions + flext-cli
  resolver rev (stability cycles 6-9) (#1906)
- fix(gates): post-#1890 stabilization — census relock, tip reconciliation, pre-existing
  reds at their owners (#1900)
- fix(models): bare --projects coercion on the scope mixin (stability loop cycle 7)
  (#1904)
- fix(config,locks): bare --projects coercion + R1 make/go tool locks (stability loop
  cycle 6) (#1902)
- fix(tests): track the relocated rule catalog directory (stability loop cycle 5)
  (#1901)
- fix(tests): slow-mark the workspace fixed-point conform (stability loop cycle 4)
  (#1899)
- fix(tests): the lease denial contract exercises the public lease boundary (stability
  loop cycle 3) (#1898)
- fix(tests): C19 contract alignment — make selector + hook partition (stability loop
  cycle 2) (#1897)
- fix(bootstrap): join MISE\_SHIMS\_DIR to the lifecycle PATH so fresh clones resolve uv
  (#1895)
- fix(config): make and go as Mise-managed selectors — R1 contract cure (stability loop
  cycle 1) (#1896)
- fix(tests,gen): C19 upg lifecycle contract + stale projection regeneration (runtime
  cures on the integrated tip) (#1894)
- merge: union 0.12.0-dev into upload lane + lints cures (bootstrap constant, stale
  @override, json\_dumps, retire stale mise-artifacts case) (#1893)
- fix(toolchain): resilient setup, host-safe bootstrap and 0.12.2 gate baseline (#1890)
- fix(gates): mypy deferral-trace report poisoning + approval step dispatch-only guard
  (#1892)
- fix: restore native Make bootstrap and manifest-scoped validation (#1889)
- fix(toolchain): prove the mise-locked uv via mise which (#1887)
- merge: absorb the toolchain/gen reconciliation into the dev branch (#1886)
- merge: absorb the upload lane tip into the dev branch (fleet convergence) (#1885)
- fix: import repairs + upload absorption for the dev branch (#1884)
- config(infra): bound the subprocess audit to its three sanctioned owners (#1881)
- Fix/import law gen 20261008 (#1882)
- fix(codegen): drop two dead uv exclude entries (probe-proven) (#1880)
- Fix/rope builtin base 20261008 (#1878)
- Fix/gitmodules owner 20261008 (#1876)
- Fix/import law 20261008 (#1874)
- Fix/upg gitlink pins 20261008 (#1873)
- Stash preserve/flext infra 9 20261007 (#1859)
- land(wave471): adopt upload-20261007 into 0.12.0-dev (#1847)
- fix(security,codemod): subprocess only in the u.Cli.run owner and flext-core;
  flext\_infra never imports flext\_tests (#1844)
- fix(toolchain): supply the Make UV to the mise-proof invocation (#1875)
- \[WIP\] maintained upload convergence and CI owner repairs (#1843)
- fix(maintenance): sonarcloud verbs run-if-available-else-skip — typed absence, never a
  failure (#1871)
- fix(toolchain): pin-first mise bootstrap recovery (setup/gen/upg survive lock-format
  and mise drift) (#1870)
- feat(toolchain): npm-free fleet toolchain; rumdl formats markdown; setup proves tools
  (#1848)
- fix(make,cli-contract): upg never runs check; process options are the flext-cli model
  (#1845)
- fix(utilities): ProcessOptions resolves through m.Cli, never u.Cli (#1846)
- fix(codegen,make): one generated\_source key for protoc trees; upg relocks its
  projected manifest (#1842)
- fix(make): upg converges in one pass; scaffold scenarios plan one surface (#1840)
- fix(ci): green the flext-infra integration tip under the CI profile (#1839)
- fix(codegen): resolve bases read through a provider facade instance (#1838)
- fix(setup,docs): approve projected .envrc in CI; docs build failures name their
  warnings (#1835)
- fix(deps): flext-grpc declares its protobuf runtime (#1837)
- fix(rules,ci): restore inverted rule fixtures; direnv gate is local-only (#1836)
- refactor(conform): dedupe the surface dispatch and pass the integration line as one
  typed object (#1834)
- chore(gen): regenerate CI workflows for the lock-pinned mise install (#1833)
- fix(make): align the upg lifecycle and verify-clean template with what members carry
  (#1832)
- fix(ci): install mise from the mise.lock asset with checksum verification (#1831)
- fix(provenance+gates): prove native workspace members in CI; cure the post-upload tip
  red (#1830)
- fix(codemod): land adopted alias-identity (#1819) with its lint, gen drift and runtime
  defects cured (#1829)
- feat(audit): fail loud on stashes, merged-but-alive branches and orphan worktrees
  (#1828)
- chore(unify): land upload-20261007 into 0.12.0-dev (#1816)
- chore(deps): bump flext-cli/flext-core/flext-tests locks to the 0.12.0-dev tips
  (#1821)
- fix(rope): restore runtime-base workspace roots and project-source mutation law
  (#1818)
- fix(infra): tip residue — staged mod-text/candidate phases, immutable demotion scan,
  fail-loud family exports (#1817)
- fix(infra): fleet-wide mid-code import hoisting + codemod-rules shadowed-config cure +
  thin rope facade (#1812)
- fix(utilities): the composition mixes in the one Dependencies class (#1815)
- hotfix: rope source-text preservation + module-table rebind detection (core gen
  blocker cure) (#1814)
- refactor(utilities): the one-class canonical form — dependencies + rope composite
  (#1810)
- hotfix(upload-20261007): CI=Y gates green — lint/duplication/loc-cap/runtime-census
  zero, dependencies single-class, F0/F1 machinery (#1811)
- fix(gates): CI=Y blocking gates zeroed — runtime-census 0, duplication 0, loc-cap 0,
  part modules landed, test contract asserted (#1809)
- hotfix(0.12.0-dev): the mise\_install fragment provisions the mise.lock-pinned release
  (+ self-render) (#1807)
- fix(deps): republish the standalone git-pin pyproject the S6 adoption rendered over
  (#1805)
- fix(deps): restore the canonical git-pin render over the S6 adoption (#1804)
- merge: integrate #1800 (wave-broken generator cure) with the 0.12.0-dev tip (#1803)
- fix(tooling): deduplicate the strict-errors list the tooling union concatenated
  (#1802)
- fix(utilities): adopt the S6 rope-source-bases split — composite facade over
  inventory/collector/runtime/aliases parts (#1801)
- fix(rope): the alias-map builder reaches lazy\_module\_aliases through the Family name
  (#1799)
- fix(ci-fragments): wire the url.insteadOf rewrite the private-dependency auth header
  documents (#1797)
- fix(utilities): the S6 family facades reclaim distinct names (#1798)
- fix(rope): restore the flat RopeSourceBases re-export the S6 dedup erased (#1796)
- fix(rope): restore the collector hierarchy the #1788 merge mangled in
  rope\_source\_bases (#1795)
- fix(utilities): the flat Dependencies re-export binds the nested mixin, not an empty
  tuple (#1794)
- fix(utilities): deduplicate the doubled Flext prefix from the S6 split class names
  (#1793)
- fix(rope/dependencies): the S6 flat re-exports + the wave's indent damage cure (#1792)
- fix(deps): drop the tool.uv.sources section — the inline git-pins carry the URLs
  (#1791)
- fix(deps): restore the canonical git-pin render for the sibling groups (#1790)
- fix(ci-fragments): mise\_install step indent survives include; private-dep mint covers
  workflow\_dispatch (#1788)
- merge: integrate the upload branch with the 0.12.0-dev tip (tooling.yaml union)
  (#1789)
- Merge Admin 20261007: native mise/uv bootstrap + workspace members + fleet
  stabilization (#1786)
- fix(tooling): resolve the conflicted authorized-exceptions region (union of both
  sides) (#1787)
- fix(packaging): restore the canonical git-pin render for the fleet sibling groups
  (#1785)
- Hotfix/upload 20261007 (#1783)
- fix(rope): subscript stores through non-class-binding names never redefine classes —
  cures flext-2klp8 (#1784)
- fix(tooling): drop the malformed ENFORCE-046 authorized-exception entry (#1782)
- fix(tooling): cure the consumer config crash from the census-exemption placement
  (#1781)
- config(tooling): authorize the backup credential resolver's Secret Service spawn
  (#1780)
- fix(rope): resolve named lazy-import mapping bindings (cures flext-ldif gen) (#1779)
- fix(census): exempt the generated \_\_init\_\_ TYPE\_CHECKING imports from ENFORCE-046
  (#1778)
- fix(infra): bounded bootstrap subprocess relief + batch gate adapters (operator ruling
  2026-10-07) (#1777)
- refactor(rope): source bases split into responsibility parts (S6) + conform chain
  assessment (S8) (#1776)
- refactor(conform): typed project-deps contract for the git-peer refresh (S5c) (#1775)
- refactor(codegen): filesystem modes have one config SSOT + the phase enum owns staging
  (S4) (#1774)
- fix(rope): resolve external references only through resolvable module resources
  (#1773)
- refactor(codegen): journal phase contract as a closed enum + honest Code Map (S2+S3)
  (#1772)
- fix(tooling): freeze the 9 historical evidence docs out of the format gates (#1771)
- chore(gen): consume the shim-tolerant bootstrap in the own Makefile render (#1770)
- fix(codegen): hold the fleet mise at 2026.9.16 — 2026.10.3 provenance verification
  breaks the tool bootstrap (#1769)
- fix(bootstrap): tolerate mise's benign warm-runner shim reshim notice (#1768)
- refactor(codegen): the lazy-init planner is a service, not a model (S1) (#1766)
- fix(tooling): prettier must not reformat the codegen-managed docs projections (#1767)
- hotfix: complete the interrupted protocols/models rename — 105 anchors + canonical
  regen (unblocks gen/audit everywhere) (#1763)
- hotfix: complete the protocols rename anchors + submodule-materialized CI checkout
  (Merge Admin) (#1762)
- fix(ci-template): materialize submodules in the CI checkout — cures the unsatisfiable
  drift gate (#1760)
- chore(rules): operator-ruled ban-model-rebuild disable + pytest11 plugin ignores
  (#1761)
- config(tooling): authorize the snapshot drill's private stem import (#1759)
- merge: integrate the dd261005 convergence wave into 0.12.0-dev (#1758)
- fix(bootstrap): preserve native manifest and locked provenance (#1749)
- fix(namespace-moves): include a block's decorators in its move range (#1757)
- fix(bootstrap): safe completion rebinds + runtime wrapper credential prefix (#1756)
- fix(bootstrap): pass the credential git config as env arguments (#1755)
- fix(bootstrap): keep trimmed-for recipe lines indented too (#1754)
- fix(bootstrap): keep every trimmed recipe line's tabs explicit (#1753)
- fix(bootstrap): keep the credential-store recipe lines indented (#1752)
- fix(lazy-init): render no TYPE\_CHECKING block when groups collapse away (#1751)
- fix(bootstrap): wire the minted private-dependency credential store into the runtime
  env (#1750)
- config(docs): include the site build in the make docs lifecycle (#1748)
- fix(docs-template): grant Pages write to the build job (#1747)
- fix(rope): mirror NamedTuple in external\_identity (function-built class like
  TypedDict) (#1746)
- fix(rope): lazy re-export aliases never shadow real analyzed modules (#1745)
- fix(pytest-runner): read phase receipts by subprocess ownership, not whole\_target
  (#1744)
- fix(bootstrap): allow the projected .envrc during setup (#1743)
- config(tooling): cosmos-docgen measured slow-suite ceiling 600s (#1742)
- fix(codegen): unblock web generation and Make bootstrap (#1739)
- Dd261005 (#1741)
- dd261005 (#1740)
- converge: the dd261005 stabilization onto the current tip (#1738)
- fix(toolchain): provenance policy at the owner + deterministic lock-noise tolerance
  (#1736)
- merge: absorb 0.12.0-dev into dd261005 (the convergence selector threading +
  stabilize) (#1735)
- dd261005 (#1734)
- fix(tooling): canonical subprocess owners join the informative family (#1732)
- fix(codegen): restore the lazy\_init\_planner stub \_\_all\_\_ (#1733)
- fix(models): complete the opt\_in\_check\_gates removal (#1731)
- fix(codegen): retire the opt\_in\_check\_gates declaration (spec field removed by the
  model wave) (#1730)
- fix(models): MypyCacheSpec base follows the registry rename (#1729)
- fix(integration): restore the two files dropped by the second-wave resolutions (#1728)
- integrate: second wave (6 pending) + cure the first-wave conflict markers (#1727)
- integrate: the 3 remaining pending branches (sweep/automations, preserve-sweep5,
  preserved-1656) (#1726)
- integrate: all pending 0.12.0-dev branches (18) — integrate-first, stabilize after
  (#1725)
- fix(docs): regenerate the make-commands projection after the audit-blocking Makefile
  cure (#1724)
- fix(codegen): regenerate the stale phase-zero projections (audit blocking) (#1723)
- wip: preserve concurrent edits (merge-admin sweep4) (#1722)
- wip: preserve concurrent edits (merge-admin sweep3) (#1721)
- wip: preserve concurrent edits (merge-admin sweep2) (#1720)
- Wip/preserve sweep 183747 1 (#1719)
- Wip/test resource limits dirty 20261005 (#1718)
- chore(unify): preserve phase-zero projections and strict provenance correction (#1716)
- feat(automations): workspace fleet-gaps + refactor violations-sweep canonical surfaces
  (#1713)
- fix(markdown): ignore .zcode session artifacts fleet-wide (#1717)
- fix(approval): wrapper parity for custom approval-stage hooks (#1715)
- fix(locks): advance stale branch-pin resolutions to current tips (flext-io8wa
  follow-up) (#1714)
- fix(bootstrap): full cure — whitespace recipe split + readonly + regen
  (flext-io8wa/1k3ca/u8eij, P0) (#1712)
- fix(mise): reconcile the mise.lock with the declared toolchain (setup blocking)
  (#1711)
- fix(bootstrap): restore the green bootstrap template (flext-io8wa, P0) (#1710)
- adopt: mandatory-approval preservation commit a3be7ca80 (fix-forward, cooperative)
  (#1707)
- law(gates): TC001-TC004 blocking by name; mypy/pyright informative (merge-admin
  mandate) (#1706)
- sweep(infra): unsafe-fix law wave 1 (#1708)
- dd261005 (#1709)
- reapply flext-20yyv: mod-loop callbacks, origin-aware accessors, external consumers
  (lost to the sharpening absorb) (#1705)
- unify: merge admin sweep 20261005 — recipe projection truth (receipt diagnostics,
  scratch cure+tracing), aiohttp floor (#1704)
- fix(make): cure the setup bootstrap recipe split (flext-u8eij, P0) (#1690)
- fix(rope): degrade non-class external resolutions to the recognized verdict (#1703)
- fix(bootstrap): one-shell setup recipe; pkgutil runtime-base derivation restored
  (unblocks setup fleet-wide) (#1700)
- fix(rope): degrade conditionally-declared classes to non-class bindings (#1701)
- fix(rope): Attribute-over-Subscript references + the TC-off entry's required reason
  (#1697)
- fix(rope): depth-bound the external-base walk; tolerate conditional bindings in
  external modules (#1699)
- fix(bootstrap): fail loud when the mise scratch mktemp fails (flext-9lnhu) (#1698)
- fix(rope): degrade unresolvable external modules to the recognized verdict (#1696)
- fix(rope): degrade lineage cycles from the line-qualified identity model (#1695)
- fix(rope): cut the reexport resolve cycle with an unresolved-base verdict (#1694)
- fix(rope): worklist the derivation loop against mid-loop definition growth (#1693)
- fix(rope): remove the orphaned external\_reference body from provider\_reference
  (#1692)
- test(rope): pin the non-class planned-binding degradation contract (#1691)
- fix(config): restore the required reason on the TC001-TC004 disabled entry (#1688)
- Fix/facade mro regression vdklb 20261005 (#1687)
- fix(rope): underivable definition degrades instead of crashing make gen (#1686)
- wip(rules): preserve the in-flight namespace-law rule edit (worktree … (#1685)
- fix(lint): informative complexity rules + scoped dated exceptions + pyrefly zero + gen
  cure (#1667)
- WIP: mandatory Make CI and pre-commit approval contract (#1669)
- fix-namespace/fix-accessors as rope-loop callbacks; origin-aware accessor renames
  (flext-20yyv) (#1684)
- fix(codegen): rope installed-distribution bases; dedup parallel-split copies; pyrefly
  informative in CI (#1681)
- fix(rope): treat non-class external resolutions as unresolved bases (#1683)
- fix(docs): scope\_boundary path-reference + module-export docstring + bootstrap
  ignores (#1682)
- wip: preserve lane WIP before worktree retirement sweep 20261005 (mer… (#1651)
- Fix/markdown code origin qtmy2 val20261004 t1410 (#1666)
- Fix/facade mro regression vdklb 20261005 (#1679)
- docs(tooling): record WHY TC001-TC004 can never be re-enabled — they break Pydantic
  classes (#1678)
- fix(rope): skip no-source-module bases — completes the gen cure (stacks #1674) (#1677)
- law(ruff): TC001-TC004 disabled — Ruff never enforces them (bead flext-p7bxt) (#1676)
- fix(models): FlextInfraCodegen base order agrees with the generated facade MRO
  (flext-vdklb) (#1674)
- fix(tooling): restore TC001-TC004 enforced; revoke the same-day off-global attribution
  (#1675)
- fix(bootstrap): runner-shims mise warning expected, not fatal (+ rope convergence)
  (#1673)
- wip(rope): preserve the in-flight external-base lazy-namespace cure (… (#1670)
- Fix/rope unresolved external base (#1671)
- feat(ci): lint joins the CI-excluded local partition (operator order 2026-10-05)
  (#1672)
- Preserve/byuaa runtime 156590b 20261005 (#1668)
- \[WIP\] fix(make): normal testmon admission without automatic slow phases (#1629)
- Wip/wt sweep 20261005/fix/loc cap transaction make env val20261004 t0958 (#1665)
- Wip/wt sweep 20261005/fix/markdown code origin qtmy2 val20261004 t1410 (#1645)
- wip: preserve lane WIP before worktree retirement sweep 20261005 (mer… (#1648)
- Wip/wt sweep 20261005/upg old generation 20261002 (#1655)
- wip: preserve lane WIP before worktree retirement sweep 20261005 (mer… (#1658)
- Fix/rule tests snapshots 20261005 (#1626)
- merge: absorb 0.12.0-dev into the settle-lock refresh lane (#1663)
- wip: preserve lane WIP before worktree retirement sweep 20261005 (mer… (#1661)
- Wip/wt sweep 20261005/fix/profile child rewrite guhb3 val20261004 t1400 (#1650)
- Wip/wt sweep 20261005/fix/loc cap split val20261004 t0958 (#1644)
- Wip/wt sweep 20261005/style/lint tests e501 val20261004 t0956 (#1643)
- wip: preserve lane WIP before worktree retirement sweep 20261005 (mer… (#1642)
- fix(rope): accept PyPackage in the pymodule contract; describe rope models (#1660)
- Wip/wt sweep 20261005/fix/model facade postmerge contract 20261005 (#1647)
- Merge remote-tracking branch 'origin/0.12.0-dev' into verify/mise-boo… (#1646)
- merge(0.12.0-dev): measure tip 761aa105c (#1632)
- Wip/wt sweep 20261005/docs fence outcomes b4rft 20261005 (#1633)
- Wip/wt sweep 20261005/fix/codemod inline import tests val20261004 t1505 (#1631)
- fix(rope): treat call-headed assignments as non-class bindings (#1640)
- Wip/wt sweep 20261005/codemod baseline val20261004 t0955 (#1636)
- wip: preserve lane WIP before worktree retirement sweep 20261005 (mer… (#1638)
- wip: preserve lane WIP before worktree retirement sweep 20261005 (mer… (#1639)
- Wip/wt sweep 20261005/fix/codemod broad annotation tests val20261004 t1510 (#1637)
- wip: preserve lane WIP before worktree retirement sweep 20261005 (mer… (#1630)
- fix(config): drop the duplicate global TC004 exception (the family entry covers every
  file) (#1628)
- fix(rules): drop the duplicated unscoped TC004 entry (validator refused the table)
  (#1627)
- Wip/kilo sweep 20261005/infra docs contract hjrk7 20261005 (#1625)
- law(ruff): block the whole TC001-TC004 family on every file by rule name (operator
  2026-10-05) (#1624)
- feat(lint): never execute TC001-TC004 anywhere; smells joins the local-only partition
  (#1622)
- \[WIP\] fix(rope): planned-source runtime base inventory (flext-ldd4s) (#1617)
- fix(rules): block the TC001-TC004 family from executing everywhere (operator
  2026-10-05) (#1621)
- fix(check): informational mypy/pyright/codemod posture, snapshot-pinned facade rule,
  S2083 stage guard, loc-cap split (#1620)
- feat(make): make mypy, pyright and codemod informative in CI (operator order
  2026-10-05) (#1619)
- fix(codegen): detect generic facade-rebind modules; assignment joins the scope (#1618)
- fix(rules): infer-literal-facade-exports fleet scope + parenthesized tuple constraint
  (#1616)
- fix(setup): preserve locked bootstrap failures (#1614)
- integrate(tip-cure): the operator sharpening lane over the landed ruling base
  (supersedes #1613) (#1615)
- fix(types): operator sharpening gc-eqvqx5 — revert mypy-dodge regressions, dated
  tooling suspensions, mandatory pydantic plugin (#1613)
- fix(pytest): suite stop requires the deadline to pass on the executing clock (U10)
  (#1612)
- fix(deps): read the consolidated mypy ruling field on the tool table phase (#1611)
- fix(codemod): strip dead type-only import scaffolds after import normalization (#1610)
- fix(codegen): restore the project-wide mypy disable\_error\_code render (content lost
  in the #1599 merge) (#1609)
- Merge remote-tracking branch 'origin/0.12.0-dev' into fix/literal-exp… (#1608)
- Lane/validator revert 20261005 (#1607)
- Law/pyrefly ignored cure 20261005 (#1606)
- wip(infra): preserve superproject-checkout residue before integration… (#1605)
- WIP: enforce Pydantic 2 Mypy policy and unify duplicate generator owner (flext-8i57m)
  (#1595)
- WIP: preserve Mise scratch lifecycle status (flext-i7jz1) (#1579)
- WIP: preserve authored model facade namespaces (flext-z5x3y.1) (#1578)
- fix(workspace): settle lock refreshes git peers; lane failure restores base (#1568)
- WIP: adopt loc-cap codegen split (#1558)
- WIP: infer literal root facade exports through owned mod rules (#1580)
- WIP: preserve native SARIF comparison spans (flext-mc15j) (#1560)
- law(pyrefly): drop the prop-decorator ignored-errors surface — the mypy ruling owns it
  (#1603)
- fix(deps): restore jscpd latest — hold premise measured gone (v5.2.0-v5.4.0 all ship
  full platform assets) (#1566)
- fix(mypy): fleet-mandatory defaults — pydantic.mypy always on, ruling codes suppressed
  for every consumer (#1602)
- fix(bootstrap): type the serialized publisher as Generator (#1576)
- WIP: adopt TC001 pydantic runtime roots (#1559)
- fix(mypy): restore the global disable\_error\_code render (merge clobber) (#1601)
- fix(codegen): render one merged disable\_error\_code — double render broke every
  consumer gen (#1599)
- fix(mypy): declare the disable-error-code field the ruling template renders (#1600)
- refactor(mypy): one ruling surface (dedupe #1588 vs #1590/#1591) (#1596)
- feat(mise): bun installs the npm CLIs — SSOT switch + bootstrap env + --trust
  (flext-qwvb5 T6) (#1594)
- fix(mypy): drop the duplicate disable\_error\_code (parallel ruling merges) (#1593)
- fix(make): declare the test scratch root on every pytest verb (cosmos-yj36e.21)
  (#1583)
- law(types): suspend mypy call-arg + pyrefly prop-decorator fleet-wide; pydantic plugin
  mandatory (operator 2026-10-05) (#1590)
- fix(codegen): suspend mypy prop-decorator/call-arg under the dated operator ruling
  (gc-eqvqx5) (#1591)
- feat(mypy): disable prop-decorator and call-arg fleet-wide — pydantic 2 plugin ruling
  (#1589)
- feat(mypy): operator ruling surface — project-wide disable-error-codes
  (u3-field-computed-field) (#1588)
- fix(rules): admit Pattern-A consumer letter rebinds (cosmos-yj36e.15) (#1554)
- fix: cure the integration tip — check findings 3087→2527; toolchain-root analysis for
  the remainder (#1585)
- WIP: fix(tests): restore the contract-correct make-environment suite clobbered by the
  converge commit (#1553)
- chore(deps): retain native setup relock catalog resolution (#1587)
- fix(types): onda 1 mecanica da divida de tipos — mypy 622→478, pyright 581→467 (#1586)
- fix(setup): guarded interrupted-clone recovery (flext-r7po7) (#1577)
- chore(lint): land the auto-fixable census (fmt+fix+mod+mod-text) (#1584)
- fix(tests): adopt the make-environment suite cure from lane make-env-test (flext-k538b
  closure) (#1581)
- chore: adopt the gates src duplication cure from lane gates-src-duplication
  (flext-qwvb5 B-7) (#1582)
- chore: adopt the small-tests lint cure from lane lint-tests-small (flext-qwvb5 B-5)
  (#1575)
- chore: adopt the codemod-alias tests family (4 lanes, timestamp order) (flext-qwvb5
  B-2) (#1573)
- chore: adopt the tests duplication cure from lane tests-duplication (flext-qwvb5 B-4)
  (#1574)
- chore: adopt the codegen tests E501 cure from lane lint-codegen-e501 (flext-qwvb5 B-1)
  (#1571)
- refactor(mise): delete the bootstrap library behind the projected lock scripts
  (flext-k538b) (#1572)
- refactor(toolchain): declarative tools table replaces the per-tool fields
  (flext-qwvb5.2) (#1570)
- chore: adopt the partial-selection test-file cure from lane rjyh1 (flext-qwvb5 B-3)
  (#1569)
- feat(make): file-gate verb fleet-wide + wire the mise-lock reconcile on setup drift
  (#1567)
- WIP: complete lazy scanner static validation (flext-w4luo.1) (#1565)
- WIP: adopt flat lazy export map generator (flext-w4luo.1) (#1562)
- fix(codemod): restore the canonical generator-repair refusal in text gates (#1557)
- refactor(gates): read hook defaults from class data (#1556)
- fix(pytest): make test-file reruns of a declared file exit green (flext-rjyh1) (#1552)
- fix(rules): ban-loose-module-object admits the facade's self-typed fetch\_global
  singleton (cosmos-yj36e.15) (#1551)
- fix(mod,pytest): retire the force-adding checkpoint and the conftest ini shim
  (cosmos-z2vmw) (#1550)
- fix(gen): regenerate the root initializer the #1399 merge left stale (#1407)
- Merge fix/make-config-import: hoist ExternalCacheDirectorySpec (admin… (#1549)
- fix(types): stop mypy 2.4 crashing on the infra service base (#1510)
- test: import the tests u facade as published (ban-local-import-alias) (#1544)
- fix(lint): wrap src lines above the 88-column limit (val202610040808) (#1547)
- fix(codemod): authenticate ast-grep findings with the shared receipt (#1504)
- fix(rules): ban-runtime-alias-rebind sees every imported name (flext-8sgay) (#1548)
- refactor: import own owners as published in gates, services and docs scope
  (ban-local-import-alias, ban-inline-import) (#1539)
- fix(codegen): rebuild the CI shim farm from the pinned Mise release (#1545)
- refactor: type src dict annotations through the t vocabulary (ban-broad-annotation)
  (#1543)
- fix(gates): mypy gate emits the verbose native trace its own report validator requires
  (#1546)
- fix: mod class-scope NameError guard and OPTIONS=Y verb contracts (cosmos-yj36e.18,
  .17) (#1536)
- fix(ci): run the type checkers in the CI check partition (#1541)
- test: import flext\_infra.main as published (ban-local-import-alias) (#1540)
- refactor(codegen): drop the dead mise render payload (flext-qwvb5.1) (#1542)
- fix(lint): static-method recipe keeps override chains and receiver readers
  (flext-wc4sd) (#1537)
- fix(docs): retire TOC sentinel, default the markdown gates, drop legacy audit paths
  (#1538)
- style(lint): bind bootstrap exception messages before raising (val20261004T0956)
  (#1534)
- fix(rules): ban-runtime-alias-rebind catches import-then-rebind (flext-8sgay) (#1535)
- fix(mod,layout): class-stem law admits the owner class nesting derives; keep the root
  sgconfig.yml (val20261004T0825) (#1528)
- refactor(config): compose project managed artifacts in parse and merge steps (#1529)
- refactor(gates): remove the 12 src duplication clones (val202610040808) (#1533)
- refactor(models): drop own-package import aliases in \_models (ban-local-import-alias)
  (#1532)
- fix(codegen): keep Protocol terminal when projecting protocol owners (#1531)
- fix(docs): restore the anchored docs policy template and manifest overrides (#1530)
- refactor(bootstrap): spawn through u.Cli and split by concern below the LOC cap
  (#1525)
- fix(lint): hoist the process entry CLI import (#1527)
- fix(codegen): emit actions/create-github-app-token@v3 with client-id (#1526)
- fix(config): accept project ManagedArtifacts.Ruff (#1513)
- docs(guides): re-project the root guides whose fences pass the fence Ruff policy
  (#1524)
- fix(ci): keep private fetches on the minted app token (#1523)
- fix(lint): identify the module inside its copyright notice (#1522)
- fix(mod): keep a module-level base when its subclass stays outside (#1521)
- fix(mod): keep class-suite sibling references at module level (#1520)
- fix(lint): expand a stub that shares its signature's last line (#1519)
- fix(lint): accept an inline body and a source-scan-ignored module (#1518)
- fix(mod): keep class-nesting from dropping names callers still use (#1517)
- fix(mod): replace a destination import of a shared helper being moved (#1516)
- fix(mypy): resolve t through flext\_infra.typings at the four service bases
  (val202610031920) (#1514)
- fix(mod): replace a destination import of a shared helper being moved (#1512)
- fix(setup): provision absent gitlinks with a depth-1 clone (#1515)
- fix(test): let a slow-only file reach the test-file slow phase (#1511)
- fix(typing): bind service results through a module-level alias (#1509)
- fix(lint): hoist the process entry flext\_cli import (#1507)
- fix(markdown): exclude release-please CHANGELOG output from the markdown gates (#1508)
- fix(check): clear runtime census and markdown residuals on the tip (#1506)
- fix(make): declare the profile-test verbs in the config SSOT (#1505)
- chore(test): declare the algar-oud-mig run-timeout measurement ceiling (300s) (#1503)
- fix(test): declared file target never lets the testmon cache deselect it (#1502)
- fix(docs): commit the generated bootstrap module page (#1501)
- feat(test): caller-overridable test target — make test accepts a single file (#1500)
- feat(test): add make test-file FILE=\<path\> (val20261003T1900) (#1498)
- fix(codegen): the build hook rides in the sdist via force-include (#1497)
- feat(test): add the test-file verb — one declared file through the phased testmon
  pipeline (#1496)
- fix(codegen): the declared build hook rides in the sdist (#1495)
- fix(release): tag the merged release commit wherever it sits (#1494)
- fix(release): the plan's tag listing demands a digit after the prefix (#1493)
- fix(release): latest\_release\_tag skips foreign tag namespaces (#1492)
- fix(codemod): restore the content-keyed rule catalog cache writer (flext-d6dn8)
  (#1491)
- fix(docs): drop the retired machine\_path\_exempt\_paths key from the docs policy
  template (flext-itpd1.10) (#1490)
- fix(setup): locks only via make upg; setup runs despite mise/uv drift (flext-k538b)
  (#1488)
- fix(bootstrap): mise pin resolve exempt from dependency cooldown (#1487)
- fix(make): every verb exports one GitHub credential under GITHUB\_TOKEN, GH\_TOKEN and
  MISE\_GITHUB\_TOKEN (#1486)
- feat(git): branch, stash, remote and merge-probe primitives for wip sweep (#1485)
- fix(rules): exempt the stdlib-only native hook client from ban-ambient-environ-read
  (#1484)
- fix(rules): exempt the lazy defining module from ban-consumer-submodule-import (#1483)
- fix(bootstrap): hold broken tool releases at their newest installable version (#1482)
- fix(models): define MakeGateSuspensionSpec (referenced but never defined) (#1481)
- fix(codegen): converge generator to the module-scope fleet — consumer make gen exit-0
  (#1480)
- fix(codegen): width-aware module-alias imports (flext-xjoph) (#1479)
- fix(lint): TC001 OFF global (operator ruling 2026-10-03 02:57Z) (#1478)
- fix(templates): drop invocation\_namespace kwarg (#1480)
- fix(bootstrap): declare credential\_commands data (#1478)
- fix(models): relocate suspensions field into MakeSpec body (#1477)
- fix(models): relocate suspensions field into MakeSpec (v3) (#1474)
- fix(models): declare check\_gate\_suspensions on MakeSpec (#1473)
- fix(codegen): remove residual additions block (#1472)
- chore(lint): I001 enforced; I002/I003 disabled; TC001 active (operator ruling
  2026-10-03) (#1471)
- fix(codegen): drop undefined 'rows' unpacking and dead additions block (#1470)
- fix(codegen): derive project spec for existing trees in \_plan\_existing\_repository
  (#1469)
- fix(tooling): tests/python ruling glob survives excluded-root filter (#1468)
- fix(lint): FBT003 ZERO em src/flext\_infra (\~203 sites, 3 ondas de agentes) (#1467)
- fix(check): skip mypy verbose LOG lines in the JSON report parser (#1466)
- fix(config): declare ci.local\_check\_gates (schema now requires it) (#1465)
- fix(models): hoist ExternalCacheDirectorySpec to module level (#1464)
- config(tooling): tests/python/\*\* ruff exemptions (mcb tests migration) (#1463)
- integrate: wip/stash-35d24e39fe-adopt (#1462)
- integrate: wip/sonarcloud-readonly-issues (#1461)
- integrate: wip/primary-preserve-20260928-1400 (#1460)
- integrate: r3-v2 (#1459)
- integrate: r3-cache-contract-dedup (#1458)
- integrate: preserve/pr-1140-adopt-20261002 (#1456)
- integrate: preserve/make-fix-ast-unparse-corruption-20260927 (#1455)
- integrate: preserve/infra-suite-profile-20260930-20261002 (#1454)
- integrate: preserve/infra-r6-superseded-20260930 (#1453)
- integrate: pr-1233 (#1452)
- integrate: merge/integration-wave-20261001 (#1451)
- integrate: hotfix/testmon-selection-order-20260924 (#1450)
- integrate: fix/worktree-external-venv-20261001 (#1449)
- integrate: fix/upg-mise-lock-resilience-resync-20260930 (#1448)
- integrate: fix/upg-lock-order-20261001 (#1447)
- integrate: fix/tip-mise-projection-lock-20261001 (#1446)
- integrate: fix/tip-boot-wiring-20261001 (#1445)
- integrate: fix/template-endif-fleet-gen-20261001 (#1444)
- integrate: fix/sonarcloud-issue-model-descriptions-20261002 (#1443)
- integrate: fix/review-1234-runner-env-20261001 (#1442)
- integrate: fix/no-self-use-codemod-20261002 (#1441)
- integrate: fix/mise-toml-tool-pins-align-20261001 (#1438)
- integrate: fix/mise-gh-auth-20260924 (#1437)
- integrate: fix/lazy-init-fixed-point-20261001 (#1436)
- integrate: fix/l2-merge-cures-20261001 (#1434)
- integrate: fix/infra-runner-final-item-stop-20260930 (#1433)
- integrate: fix/infra-mypy-timeout-constant-ref (#1432)
- integrate: fix/infra-env-contracts-ssot-layer-20260930 (#1431)
- integrate: fix/infra-config-overwrite-adopt-20261001 (#1430)
- integrate: fix/infra-codemod-architecture-20260930 (#1429)
- integrate: fix/infra-aihub-worker-ceiling-min-20260929 (#1428)
- integrate: fix/infra-1140-bootstrap-20260930 (#1427)
- integrate: fix/docs-shared-test-import-policy-20260930 (#1426)
- integrate: fix/docs-policy-template-ssot-20260930 (#1425)
- integrate: fix/bootstrap-self-heal (#1424)
- integrate: converge/open-prs-20261001 (#1423)
- integrate: converge/extermination-green-20261001 (#1422)
- integrate: converge/extermination-20261001-pr1260 (#1421)
- integrate: config/scripts-ruff-exceptions-names (#1420)
- integrate: chore/upg-relock-core-installed-distributions-20261002 (#1419)
- integrate: adopt/pytest-deadline-20261001 (#1418)
- integrate: adopt/infra-1257-20261001 (#1417)
- integrate: preserve/stabilize-20261002-20261002 (#1457)
- chore: integracao em lote — mise-version-contract-guard + lazy-facade-typing (#1440)
- integrate: fix/mise-version-contract-guard-20260930 (#1439)
- integrate: fix/lazy-facade-typing (#1435)
- fix(lint): apply the promoted autofixes and the no-self-use recipe fleet-wide (#1395)
- fix(gen): land the corrected lazy-init emission unlocked by the #1402 NameError cure
  (#1403)
- fix(lint): E501 ZERO em src/flext\_infra (199 sites, 3 ondas de agentes) (#1415)
- fix(lint): E501 sweep (\~132 sites, 12 arquivos) — flext-infra src (#1414)
- fix(lint): derive the copyright notice only when a copyright finding asks for it
  (flext-kyv1t) (#1413)
- fix(check): keep the mypy JSON stream clean for the strict report parser (#1412)
- fix(deps): relock with the mypy\<2.4.0 constraint (flext-r4hyh) (#1410)
- fix(codegen): bootstrap owner imports lazy helpers from flext\_core.lazy, never its
  own root (flext-911cm) (#1409)
- fix(deps): hold mypy\<2.4.0 (upstream deferral crash) (#1408)
- fix(deps): first\_party\_namespaces takes the project dir only; gen/fix/fmt fixed
  point on the tip (#1406)
- fix(gen): commit the regenerated lazy-init import form (fixed point) (#1405)
- chore(upg): relock flext-core so u.installed\_distributions resolves (make test was
  AttributeError) (#1404)
- fix(docs): restore the docs-fix fence runner the #1385 merge overwrote (#1401)
- fix(deps): bind the renamed path parameter in first\_party\_namespaces (P0: NameError
  killed the gen conform plan) (#1402)
- fix: shared workspace fixture owner + cure integration-tip reds (8e22b066d, #1381)
  (#1399)
- docs(smells): correct SMELLS\_QLTY\_ARGS docstring (closed-PR recovery, stream R)
  (#1400)
- fix(config): declare the ruff isort table MANAGED (derived first-party projection)
  (#1398)
- fix(codegen): lazy helpers importados do root flext\_core (nunca do submódulo .lazy)
  (#1397)
- \[WIP\] fix(metadata): consume u.installed\_distributions at every distribution scan
  (#1396)
- fix(validate): restore the FlextInfraSonarcloudIssues import (regression of the #1392
  lineage) (#1394)
- chore(ssot): track the integrated flext-infra tip 2b5212275 (#1393)
- fix(deps): restore first\_party\_namespaces payload signature (lost in the #1385
  merge) (#1392)
- fix(bootstrap): a resolved Mise release reaches the pin when the bumped lock is
  unchanged (#1391)
- style(fmt): converge the tip's make fmt fixed point (bootstrap.py, sonarcloud scope
  test) (#1390)
- wip(sonarcloud): readonly issues client + sync surface (rescued) (#1381)
- fix(bootstrap): remove dead mise lock stages crashed before their commit point (#1389)
- Hotfix/tip stabilize 20261001 (#1385)
- fix(mod): clear the lint findings in the class-nesting owner-derivation files (#1370
  follow-up) (#1388)
- merge: update protocol-move and bootstrap fixes onto current 0.12.0-dev (#1384)
- Fix/infra complexity rest 20261002 (#1386)
- \[WIP\] refactor(codegen): split version-file execute into project sync… (#1387)
- fix(bootstrap): retire unjournaled mise lock stages as killed-run orphans (#1378)
- feat(mod): class-nesting derives the module owner for loose modules (#1370)
- feat(lint): static-method fix recipe for Ruff no-self-use (PLR6301) (#1363)
- fix(codegen): workspace SonarCloud scope excludes member checkouts (#1382)
- Merge pull request — SSOT exception for the promoted-command script surface
  (operator-authorized administrative merge; config data, render fixed point proven,
  unblocks fleet member lifts)
- fix(codegen): root workspace checks out its flext-infra subproject in CI (#1373)
- fix(bootstrap): setup never locks; Mise offline outside install/upg; one lock pass per
  upg (#1377)
- fix(bootstrap): self-heal stale mise.lock (adopt jscpd@5.3.3 from manifest) (#1376)
- wip(tooling-rules-kebab): record WIP — bootstrap error wrapping + projection refresh
  (#1374)
- fix(rules): require-service-facade-layers owns the root facade only (#1372)
- fix(bootstrap): cooldown-aware latest fallback in tool bootstrap resolve (#1371)
- fix(tooling): converte códigos ruff para nomes kebab-case (#1369)
- fix(tooling): TRY401 -\> verbose-raise (#1368)
- fix(config): jscpd re-pin 5.3.3 (5.4.0 sem assets) (#1366)
- fix(codegen): import the lazy helpers from the defining module everywhere (#1362)
- config(tooling): operator ruling for scripts/\*\* ruff exemptions (mcb migration)
  (#1365)
- fix(bootstrap): library-owned dirty-tree recovery, submodule-first generator, jscpd
  hold (#1361)
- fix(infra): one first-party rule, strict exception map, startup/gate performance (S1
  follow-up to #1353) (#1360)
- Hotfix/tip stabilize 20261001 (#1357)
- fix(docs): emit the converged DocsAuditPolicySpec from the docs\_confi… (#1356)
- \[WIP\] fix(rules): one first-party owner and one fleet exemption map —… (#1355)
- \[WIP\] merge: adopt 0.12.0-dev into the upg-resolver lane (#1354)
- fix(infra): bootstrap order cure + gate routing — unblock the fleet CI (#1353)
- Merge pull request #1352 from flext-sh/fix/pytest-run-timeout-render-resolution —
  per-project pytest run wall reaches the make wrapper (operator-authorized
  administrative merge; required gates green — ci red = pre-existing tip generation
  instability, reproduced without this change, owned by the fleet stabilization lane)
- fix(codegen): blank\_lines\_before\_exports = \\n único (#1351)
- fix: journal bootstrap surfaces and preserve pytest exits (#1348)
- fix(rules): the ambient-environ rule exempts the config bootstrap boundary (#1349)
- Fix/protocol move usage rewrite (#1347)
- fix(infra): boot receipt parser, lazy-import ordering at the renderer, dead sed rule
  (re-derived) (#1346)
- fix(infra): boot receipt parser, lazy-import ordering at the renderer, dead sed rule
  (#1341)
- fix(bootstrap): a manifest ahead of the lock self-heals in the setup bootstrap (#1345)
- fix(rope): the snapshot project reads the scan-ignore SSOT (#1344)
- chore(tooling): cosmos-charts run-timeout override 600s (#1338)
- fix(rope): the workspace index reads the scan-ignore SSOT (#1343)
- fix(bootstrap): the lock transaction owns redeclared sidecar paths (#1342)
- fix(config): lift the jscpd hold (all six platforms ship assets); relock via make upg
  (#1340)
- fix(config): the toolchain python\_version carries the minor line only (#1339)
- fix(codemod): the semantic inventory reads the scan-ignore SSOT (#1337)
- fix(config): python\_version pinado 3.13.15 (3.13.16 sem assets macos-x64) (#1336)
- fix(config): re-pin jscpd 5.3.3 (5.3.2 não resolve) (#1335)
- fix(conform): fresh-import probes run in the target checkout's own environment (#1334)
- feat(mod): rule config-dict-from-constants (#1333)
- feat(lint): Google docstring convention (operator ruling); exterminate docs
  api\_modules; realign stale tests (#1332)
- fix(runner): owns-no-tests reads the pytest python-files SSOT (#1331)
- fix(models): field defaults become deep-copyable (rule
  pydantic-mappingproxy-default-factory) (#1330)
- fix: drop the stale #1323 hunks that broke the tip's config and pyrefly gate (#1329)
- Fix/sed distribution scope 20261001 (#1327)
- Tip config model sync 20261001 pr (#1325)
- fix: repair the tip after the #1295 merge; lazy-init and Raises fixes; realign the
  tests the setup red hid (#1328)
- Hotfix/tip stabilize 20261001 (#1324)
- Fix/oud worker ceiling 20261001 (#1323)
- fix(models): drop the orphaned RopeRules references (#1301)
- fix(toolchain): relock to the configured holds; Mise hold 2026.9.13; repair the #1289
  merge (#1322)
- fix(config): reconcile tooling/codegen with the exterminated model schema — bootstrap
  GREEN (#1295)
- fix(codegen): match exact external gitignore markers (#1317)
- \[WIP\] merge: adopt 0.12.0-dev into the infra closure lane (#1289)
- \[WIP\] fix(bootstrap): declared GitHub credential sources; relock the toolchain to
  the configured holds (#1320)
- fix(gates): embedded python blocks are python behavior by construction (#1321)
- fix(mod): drop the sed rule targeting an exterminated doc; converge bootstrap receipts
  (#1319)
- fix(gates): duplication reads jscpd virtual names as their real files (#1318)
- fix(refactor): keep batch namespace move running past one failed block (#1306)
- fix(codemod): scope packaged Sed rules to their declared distribution (#1313)
- Fix/infra config overwrite adopt 20261001 (#1316)
- fix(codegen): preserve declared external gitignore blocks (#1314)
- fix(toolchain): pin jscpd 5.3.2 — the only release lockable across all six platforms
  (#1315)
- fix(infra): repair the tip after the admin-merge cascade; make mod judges only its
  rewrites (#1312)
- Fix/mod text declared markdown 20261001 (#1284)
- Fix/ruff compose signature 20260929 (#1126)
- chore(gen): accept the regenerated mise and lazy-init projections (#1125)
- fix(deps): ensure\_ruff apply\_payload composes per-file-ignores (#1311)
- fix(codegen): context\_render composes per-file-ignores (Ruff overlay exterminated)
  (#1310)
- merge: PRs #1124/#1125 (mise jscpd host-invariant + relock tip) na ponta (#1308)
- fix(config): drop the overwrite keys reintroduced beside the exterminated field
  (#1307)
- fix(deps): classmethod binding name and declared set type (follow-up to #1110) (#1118)
- fix(codemod): exterminate the duplicate no-self-use rule whose fix corrupts bodies
  (#1305)
- test(codegen): elect the workspace ruling — members self-scope, the root plans zero
  (#1179)
- Fix/latest selectors 20261001 (#1285)
- test: follow physical external Make environment contract (#1161)
- fix(integration): reconcilia o contrato config-model da ponta e religa os readers
  perdidos (#1299)
- \[WIP\] fix(codegen,mod): make mod works again; notice and \_\_all\_\_ layout phases;
  Mise and jscpd holds (#1304)
- infra: relock latest tool selectors after content-gitlink merge (#1294)
- fix(infra): publish Mise lock and sidecars as one recoverable transaction (#1298)
- fix(mod): constrain declared CSV campaigns to owned paths (#1302)
- feat(codegen): publish declared core lazy helpers at package root (#1300)
- \[WIP\] fix(template): render the Beads projection in Gas City's canonical form
  (#1293)
- \[WIP\] converge: extermination wave 2 — #1280 adoption, generic lint recipes, codemod
  owner partition (#1282)
- fix(config): re-pin jscpd 5.3.3 (5.4.0 segue irresolvavel) (#1303)
- fix(infra): integrate DcBackup generation and gate repairs (#1280)
- fix(adapters): u.TypeAdapter -\> u.type\_adapter (fabrica estavel do core) (#1297)
- fix(adapters): re-aplica u.TypeAdapter (o rebuild restaurou m.TypeAdapter nao
  chamavel) (#1296)
- fix(docs): emit the machine-path frozen-evidence exempt in the docs\_config template
  (#1197)
- Fix/bootstrap latest 20261001 (#1288)
- fix(infra): wire the conform collaborators bundle under its data name (#1287)
- \[WIP\] fix(config): restore the make model fields lost by a stale-file… (#1290)
- Fix/workspace self test testmon (#1291)
- fix(models): restore the artifact container tail truncated by the merge (#1292)
- \[WIP\] adopt unpublished stash 64d3944f4b (flext-infra) (#987)
- \[WIP\] fix(template): lock mise only from the manifest gen rendered (#1283)
- fix(workspace): materialize declared content gitlinks during setup (#1281)
- Fix/mypy cache gate r1 20260930 (#1275)
- Fix/testmon make test ci 20261001 (#1273)
- fix(infra): complete the extermination-wave wiring (models, constants, configs, pins)
  (#1269)
- fix(template): restore single-body verb contract; converge overnight projections
  (fleet gen cure) (#1268)
- fix(infra): drop the orphan endif in the project Makefile template (#1279)
- fix(infra): initialize the inline facade binding view (#1278)
- fix(infra): merge the integration-tip symbol recovery into 0.12.0-dev (#1277)
- fix(infra): import c in deps\_tool\_config\_linters for deferred annotations (#1276)
- \[WIP\] converge: #1234 review fixes + testmon per-marker env + #1257/#1259 adoption
  (#1271)
- fix(infra): restore the mangled ProjectRenderContext packaged-data fields (#1274)
- \[WIP\] fix(docs): restore the typed overview preview limits docs\_render reads
  (#1266)
- fix(infra): resolve\_data\_excludes is a staticmethod like its sibling (#1272)
- fix(infra): finish the L2 merge cures — exterminated names stay out, consumers rewired
  (#1259)
- fix(infra): implement resolve\_data\_excludes for the packaging phase (#1270)
- fix(infra): declare packaged\_data\_excludes on PyprojectDeclaredTopology (#1267)
- fix(infra): refresh the stale transformers package projection (#1265)
- chore(gen): land the tip's generated-surface fixed point (#1115)
- fix(infra): accept the declared version behind a stale lock specifier (#1262)
- fix(codegen): declare pipeline conform\_ports as its bundle model, not t.Port (#1264)
- fix(infra): cure two merge-artifact syntax defects at the tip (#1263)
- fix(codegen): declare conform\_ports as its bundle model, not t.Port (#1261)
- \[WIP\] converge: flext-infra extermination lanes (L1, L2, L3, tip repair,
  TypeAdapter, upg order) (#1260)
- \[WIP\] L1: absolute imports, copyright notice, TC004 exception (continuation) (#1255)
- fix(codegen): the cooldown reaches make upg; upg locks mise only from the rendered
  manifest (#1253)
- fix(infra): restore the gen fixed point and clear the base check reds (#1248)
- fix(tooling): declare the algar-oud-mig pytest worker ceiling (#1256)
- \[WIP\] L2 continuation 2: re-exterminate resurrected rules; deferred self-reference
  as rule data (#1247)
- fix(config): api\_modules + convergencia com o model atual (#1258)
- \[WIP\] refactor(infra): L3 extermination continuation 2 (catch normalization, DI)
  (#1245)
- Converge/infra closure 20261001 (#1244)
- merge: repair da ponta do coordenador (d4740e404) — dangling references (#1254)
- fix(models): restaura SedPatternsSpec/SedPatternSpec perdidos no merge L2 (#1252)
- fix(gates): repair the markdown-code source module mangled by the L2 merge (#1246)
- refactor(config): one external-cache path contract for the tool cache specs (#1250)
- test(ci): prove generated fixed-point rejects a dirty tree (#1243)
- fix(constants): restaura MYPY\_TIMEOUT\_SECONDS\_DEFAULT perdido no merge L2
  (cherry-pick 578653ace) (#1251)
- fix(adapters): 8 singletons chamam m.TypeAdapter (PEP 695 nao chamavel) (#1249)
- \[WIP\] codemod gate contract: continue extermination (#1242)
- \[WIP\] L2 continuation: namespace law as rule data, project-context engine (#1241)
- fix(check): GATE\_TOOLS\_BY\_KIND indefinido quebra o import da frota inteira (#1240)
- \[WIP\] refactor(infra): L3 extermination continuation (DI, coupling, hardcodes)
  (#1239)
- fix(codegen): restore repository root namespace packaging (#1238)
- fix(lock): regenerate flext-infra uv.lock after the lane merges (#1237)
- fix(codegen): one fleet supply-chain cooldown for every resolver (#1231)
- \[WIP\] refactor(infra): exterminate DI, coupling and hardcoded values in the
  declaration and service layers (#1230)
- \[WIP\] L2: exterminate registries, Python-coded rules, catch/fallback code (#1229)
- \[WIP\] chore: exterminate pins, restated tunables and non-public references in
  config, templates and docs (#1228)
- fix(check): remove gate suspension and observational routing; every finding blocks
  (#1223)
- wip(infra): stabilize pytest runner within the fleet suite wall (#1217)
- infra: strict docs policy and typed candidate recovery (#1214)
- fix(infra): adopt typed census and pytest deadline work (#1211)
- feat(infra): guarded Sed recovery and candidate bootstrap (#1210)
- WIP: adopt semantic codemod and generator recovery (#1208)
- fix(lock): regenerate flext-infra uv.lock after the fmt-fixes integration (#1236)
- fix(check): the mypy gate owns project-keyed cache resolution (#1232)
- fix(release): retain declared data in wheel and sdist (#1225)
- fix(codegen): workspace-profile self-test gains the pytest testmon guard and database
  environment (#1235)
- Converge local integration lanes + projections.lock.json v1 + jscpd 5.3.3 pin (#1212)
- converge: integrate the pending flext-infra PRs and close their reds (#1234)
- feat(codegen): project root namespace packages into distributions (#1216)
- fix(infra): honor VCS exclusions in declared package data (#1222)
- fix(infra): retain backup named sources and clean generated artifacts (#1219)
- test(deps): materialize the governed checkout the exclusion contract requires (#1221)
- fix(validate): typed runner stop reserve, receipt-bound profiling, lazy parser
  backends (#1220)
- fix(infra): decompose the six-parameter census violations at their owners (#1218)
- fix(templates): the cleanliness proofs fail loud again (#1209)
- feat(infra): declarative placeholder\_exempt\_paths for frozen-evidence dirs (#1206)
- Fix/infra candidate atomic 20260930 (#1205)
- fix(docs): fence policy by rule name for the renamed/versioned tail r… (#1204)
- Fix/infra upg staging mypy timeout 20260929 (#1203)
- chore(codegen): preserve generated no-keyring Make in candidate lane (#1202)
- feat(infra): run Qlty smells through dedicated make smells (#1199)
- chore(integration): land the orphaned lanes — 1155-adopt, cli-candidate-consumer,
  residue reclaim (#1200)
- docs(infra): add the canonical TOC block to the new codemod guides (#1201)
- feat(infra): declarative CSV and semantic codemod pipeline (#1140)
- fix(infra): green the integration tip — docs\_config exempt, generated fixed point,
  lint/census (#1198)
- chore(flext-infra): integrate the fmt-fixes line into 0.12.0-dev (#1196)
- fix(codegen): dependabot must never open bump PRs against generated projections
  (flext-jfuv6) (#1194)
- fix(codegen): publish candidate Makefiles atomically (#1189)
- feat(make): declarative testmon cache policy — the preserved #1001 delta at its owner
  (flext-j0u23) (#1193)
- fix(make): authenticate only when bootstrap needs network (#1191)
- test(git): prove publication refuses a diverged remote checkpoint (#1177)
- refactor(infra): own envrc contract policy in SSOT, layer, and types (#1192)
- chore(config): dedupe the candidate bootstrap target declaration (#1184)
- fix(markdown): preserve residual and MD013 diagnostics (#1141)
- fix(docs): complete the fence-ignore set with the measured fragment-inherent rules
  (#1190)
- feat: declare package data per project for OUD release (#1171)
- feat(codemod): pair NS-CONTRACT-001 dict-annotation detection with make mod (#1188)
- fix(docs): F821 joins the fence-ignore set — snippets are fragments, not modules
  (#1187)
- test(infra): prove the bounded Mypy memory stop through the public causal
  classification (#1186)
- fix(mod): resolve local private imports before installed package discovery (#1144)
- fix(pytest-runner): suppress the suite stop when every collected item already
  completed (#1185)
- fix(config): fence-ignore policy gains D106/B018; pytest run wall calibrated to the
  real invocation (#1182)
- refactor(supervisor): read poll intervals and ps timeout from the constants SSOT
  (#1183)
- fix(docs): regenerate the api-reference counters so make gen is a fixed point (#1181)
- chore(gen): land the tip's docs projection fixed point (#1180)
- fix(setup): bound private submodule provisioning with explicit Git credentials (#1159)
- build(upg): stage the .mise/locks sidecars in the upg lifecycle (template) (#1167)
- fix(release): admit the claude governance manifest beside agents at the sdist root
  (#1163)
- test(resource-limits): run boundary-rejection cases on the integration budget (#1173)
- refactor(deps): own the lock integrity gate in code, not the Makefile template (#1165)
- fix(docs): fail audit on findings and parse inline commands by intent (#1157)
- fix(beads): tolerate the bd gate serialization marker in composed verification (#1175)
- fix(codegen): plan lazy init in each selected repository (#1155)
- fix(infra): provision physical environments beside worktrees (#1147)
- fix(refactor): classvar relocation autofix reaches nested constants in canonical
  constants.py facades (flext-xwag0) (#1178)
- fix(mise): pin 2026.9.18 and declare the bootstrap release-age policy (#1174)
- fix(validate): content-only namespace receipt + banned-annotation vocabulary (uno8m
  slice) (#1176)
- fix(git-state): guarded worktree checkpoints on the public symlink primitives (#1130)
- fix(check): wire the project mypy-budget SSOT into the standalone check path
  (flext-siwvh) (#1170)
- fix(bootstrap): pin the mise release selector to 2026.9.16 (2026.9.17 upstream
  regression) (#1168)
- fix(markdown): retire MD077 — a dialect rule the canonical docs formatter cannot
  satisfy (#1169)
- fix(mise): fail loud on an absent or drifted aube sidecar before setup does (#1166)
- refactor(ruff): name the exclusion authorities and end the binding ping-pong (#1164)
- fix(validate): banned-annotation vocabulary across the namespace surface (uno8m slice
  1) (#1117)
- fix(validate): verify a planless layout's on-disk export contract (#1162)
- fix(infra): fail loud on a duplicated mise.lock instead of a distant CI failure
  (#1135)
- fix(infra): declare the ai-hub worker ceiling for its suite deadline (#1127)
- docs(registry): the upg verb description covers the verification it now performs
  (#1151)
- fix(markdown): a hint-only rumdl exit is green, not a tool error (#1160)
- fix(repo): generated locks never merge — a textual merge corrupts them (#1149)
- fix(markdown): stop blocking on the formatter hint the fix verb cannot repair (#1148)
- fix(fixers): fix-enforcement keeps typing text; the typing unifier is not its owner
  (#1146)
- fix(git): preserve the index/worktree distinction when copying dirty state (#1145)
- fix(models): a conformed ruff list field may be legitimately empty (#1142)
- fix(make): an upgrade publishes only after the cycle it changed still passes (#1139)
- docs(toolchain): correct the false qlty pin rationale (#1138)
- fix(toolchain): make the upg lock write atomic and self-recovering (#1137)
- fix(mise): reject a lockfile annotation in a generated .mise.toml selector (#1136)
- fix(toolchain): ast\_grep\_version must be an npm specifier, not the aube build id
  (#1119)
- fix(gen): reclaim interrupted-transaction residue instead of failing forever (#1134)
- docs(guides): land the docs fixed point the Docs workflow requires (#1131)
- fix(make): make upg assert its own gen fixed point (#1133)
- fix(infra): optional mypy cache default + four root-cause repairs in ensure\_ruff
  (#1120)
- fix(check): mypy budget as project SSOT + mypy returns to CI (operator 2026-09-29)
  (#1113)
- fix(mise): relock jscpd to a single resolution on the tip (fix-forward) (#1114)
- fix(discovery): accept runtime\_root in runtime\_python and re-resolve … (#1082)
- Fix/mypy supervisor boundary 20260928 (#1081)
- feat(pytest-runner): tagged PytestWorkerCeiling with absolute or CPU-fraction form
  (#1107)
- \[WIP\] preserve lane fix/lazy-init-deterministic-order before retirement (#1079)
- fix(release): admit the governance agent manifest at the sdist root (#1108)
- fix(mise): declare jscpd host-invariant so the lock holds one resolution (#1112)
- chore(gen): consume the relock projections (mise 96527ca3 era) (#1109)
- fix(deps): bind compose\_per\_file\_ignores as a classmethod (restores gen on the tip)
  (#1110)
- fix(ruff): generated-roots owner read + fail-loud exclusions + dead orchestrator
  export pruned (flext-x4l60) (#1111)
- fix(infra): restore instance binding on compose\_per\_file\_ignores (#1075)
- fix(ruff): restore the excluded-roots computation and the static cont… (#1105)
- Fix/infra stabilization r5 20260929 (#1106)
- \[WIP\] preserve dormant worktree dirty state (infra git-owner-refactor… (#1086)
- \[WIP\] fix(codemod): make mod verifies rule-test snapshots, never rewrites them
  (flext-itpd1.7) (#1103)
- \[WIP\] fix(fix): make fix never deletes information (flext-itpd1.5) (#1101)
- \[WIP\] fix(fixers): delete the whole-file regex transformer (flext-itpd1.6) (#1102)
- Fix/1043 adopt 20260929 (#1085)
- fix(mypy): 120s bound, CI Mypy cache restore/save, red-base codemod and test repairs
  (#1104)
- fix(docs): standalone repositories publish the canonical root MkDocs title (#1098)
- fix(validate): populate\_by\_name on the pytest diag extractor (flext-dw54w residue)
  (#1096)
- feat(census): apply every classvar\_relocation violation in one pass (#1100)
- fix(validate): declared content-only roots skip the namespace layout contract (#1099)
- fix(release): carry the project's prepared dist inputs into the staged source (#1097)
- fix(codegen): formatter-stable lazy-init mappings; fix/fmt fixed point; fresh-import
  in the declared runtime (#1095)
- fix(codemod): rewire typing type tuples only when FlextConstantsGuards owns the name
  (#1094)
- fix(validate): zero-test projects run to a typed green receipt (6n6u) (#1092)
- fix(mypy): key the shared cache by project so relocks stay warm; provision propagation
  fixtures once (#1093)
- fix(validate): fresh-import usa o interprete do processo com PYTHONPATH (#1091)
- fix(infra): grouped stabilization — generated .mimosa ignore, one scan-scope owner,
  hermetic mirrors, strict config template, latest build backend (#1090)
- Merge remote-tracking branch 'origin/0.12.0-dev' into fix/fix-accesso… (#1078)
- Fix/codemod observational findings 20260928 (#1077)
- Fix/rewire primitives types 20260929 (#1089)
- \[WIP\] preserve dormant worktree dirty state (infra-config-j2-strict, … (#1087)
- fix(infra): relock onto flext-core d65f7333a, declared ruff exclusions, integrate
  784225084 (#1073)
- Fix/pyproject scripts conditional (#1072)
- chore: land pending primary-checkout commits (flext-infra) (#1070)
- perf(mypy): share one lock-keyed analysis cache across checkouts (#1069)
- refactor(typing): read PRIMITIVES\_TYPES from c (fleet cutover with flext-core#525)
  (#1068)
- refactor(git): one typed owner for the worktree registry (#1067)
- Test/extra verb canonical collision 20260929 (#1066)
- \[WIP\] preserve abandoned lane cold-mypy-2 before adoption (coordinator) (#1065)
- \[WIP\] preserve abandoned lane 6n6u-zero-test before adoption (coordin… (#1064)
- Fix/flext t8p7n forbid gate suspension 20260928 (#1063)
- \[WIP\] fix(pyproject): one parent-walking mise.lock reader for the Tap… (#1062)
- Adopt/pr938 20260928 (#1061)
- \[WIP\] fix(upg): stage uv.lock in a manifest mirror and publish by one… (#1060)
- Fix/release notes markdown 9nvu8 (#1059)
- refactor(git): one canonical owner per ref fact (flext-law conformance) (#1058)
- feat(git): own staged-index probe; generalize git\_is\_ancestor to any pair (#1057)
- fix(deps): projections of root-scoped tool lists keep only existing roots (#1043)
- fix(setup): provision governed gitlinks in GitHub CI before gen (#1056)
- perf(setup): initialize absent governed gitlinks in parallel (#1055)
- chore: null-integrate closed PRs (history only, no content change) (#1054)
- docs(config): document the flext-infra config singleton (#1053)
- fix(release): seed the internal-versions map from the root lock's git entries (#1048)
- test(codegen): guard every declared verb renders an implementation (#1052)
- fix(codegen): declare startup-health-episode as a required beads custom type
  (flext-1xkn4) (#1050)
- refactor(infra): adopt mise version pinning in toolchain models (fix-forward) (#1047)
- fix(gates): canonical-alias treats package:false roots as no-policy-owner trees
  (#1051)
- fix(ci): cache the Mise tool storage on the member jobs (#1049)
- fix(mise): keep github attestation verification for qlty (unbreak consumer setup)
  (#1046)
- fix(tip): re-resolve the flext-cli pin and normalize markdown/format drift (#1045)
- fix(infra): align stale callers with the integration tips (unbreak 0.12.0-dev) (#1041)
- \[WIP\] preserve lane fix/infra-zero-test-baseline-20260927 before reti… (#943)
- fix(pyproject): authenticate taplo through the mise.lock pin, not the selector (#1034)
- fix(gen): canonicalize pyright execution environment order by root (#1039)
- merge: adopt current 0.12.0-dev integration tip into boundary-identit… (#1037)
- test(release): prove generated release notes prettier-stable (adopts 1f8f14933)
  (#1031)
- fix(discovery): accept the declared runtime\_root in runtime\_python (#1040)
- fix(check): constrain Mypy supervisor to typed checker requests (#1004)
- fix(make): render the declared fix-namespace and fix-accessors verbs (#1030)
- fix(ci): reuse the tool caches across CI runs, saved even on failure (#1036)
- chore(config): remove dead extra\_ignored\_patterns overlay field (#1035)
- fix(release): escape merged subjects and bound release-note lines (#1029)
- fix(codemod): publish mod rewrites formatter-clean in the same pass (#1032)
- fix(runner): one-item xdist dispatch makes the declared max-failures stop immediate at
  fleet scale (flext-itpd1.3.7) (#1033)
- fix(mod): reach the formatting fixed point on make mod's first pass (#1028)
- fix(gen): format TOML with the locked Taplo release (#1027)
- fix(semantic-cutover): drop the flattened wrapper docstring at the generator (#1026)
- test(census): prove ENFORCE-079 reports and relocates every class constant (#1025)
- fix(gates): zero-python topologies pass the python checkers with typed receipts
  (#1024)
- fix(census): honor recorded check-gate suspensions for overlapping rule families
  (gc-wisp-d7mnad) (#1023)
- fix(conform): attached members of any family render on the workspace line (#1021)
- fix(make): build verb respects package:false roots — typed noop instead of uv build
  (#1022)
- fix(deps): skip flext-managed=false submodules in workspace project enumeration
  (#1018)
- feat(diagnostics): add the profile-test verb for cold-run pytest profiling
  (flext-itpd1.3.7) (#1020)
- docs(guides): regenerate local-config-overrides through make docs (#1019)
- fix(mise): normalize the pre-bake launcher migration (cold-start detection) (#1017)
- docs(agents): align the header to the composed-member two-mode standard (decision a)
  (#1016)
- fix(binding): preserve consumer resolution and environment ownership (#1003)
- chore(mise): adopt the mise wave — 9.15 pin + toolchain.mise\_version selector + saga
  reconciliation (#1015)
- refactor(fixers): retire unreachable gate adapter (#998)
- fix(validate): fresh-import probes run in the declared target environment (#1013)
- docs(guides): regenerate the execution-context TOC through make docs (#1014)
- fix(check): resolve boundary owners from typed project identity (#1010)
- fix(conform): keep the attached members in the workspace root group (#1008)
- test(docs): update auditor test setup and assertions (#1009)
- fix(deps): uv.lock written by make upg owns every flext-\* pin (#1007)
- fix(codegen): grant ci packages: read only to declared registry consumers (#1006)
- fix(upg): lock tools from the manifest gen renders so one upg converges (#1005)
- fix(codegen): a seed runtime triple starts from the packaged baked copy (#1002)
- fix(codegen): bootstrap Mise from the runtime root pin in attached members
  (flext-305db) (#999)
- fix(infra): resolve the infrastructure source for fully manifest-pinned consumers
  (#1000)
- docs(guides): commit the docs formatter fixed point for using-flext-tests
  (flext-2m968) (#996)
- chore(gen): land the tip generated-surface convergence (gen fixed point) (#995)
- fix(infra): regenerate projections after the work saga retirement (flext-2m968) (#994)
- \[WIP\] fix(infra): retire the resurrected work saga and repair the tip gates
  (flext-2m968) (#993)
- \[WIP\] fix(release): select baseline from integration history (#991)
- fix(infra): restore make gen after the #986/#988/#989 merges (#992)
- fix(constants): import the shared infra constants the workspace owner uses (#990)
- \[WIP\] snapshot live edits in the flext-infra primary checkout (#988)
- fix(constants): import the shared infra constants the workspace owner uses (#989)
- \[WIP\] adopt unpublished stash 5dacd07325 (flext-infra) (#983)
- \[WIP\] adopt unpublished stash 9914c8d341 (flext-infra) (#981)
- fix(codegen,gates): unblock make gen and return the codemod gate to the active set
  (#979)
- \[WIP\] adopt unpublished stash 2fbb50b666 (flext-infra) (#986)
- \[WIP\] adopt unpublished stash 5bed818f05 (flext-infra) (#982)
- fix(config): restore make gen on ab3fb8809 (endpoint origin, testmon cutover, render
  kwargs) (#980)
- fix(infra): restore make gen on the tip after the #945/#959/#970 merges (#975)
- Fix/tip green 2 20260928 (#978)
- fix(pyproject): keep the 0cdeaf4eb document.py - the drop's caller ha… (#977)
- Merge origin/0.12.0-dev: restore make gen + endpoint\_origin managed\_city (#976)
- \[WIP\] preserve lane fix/iac-infra-owner residue (flext-itpd1.3.10) (#964)
- \[WIP\] preserve lane fix/p0-upg-pin-cutover-20260927 residue (flext-itpd1.3.10)
  (#961)
- merge: absorb origin/0.12.0-dev (949 drop #969, tip-green #968) over … (#974)
- \[WIP\] preserve flext-infra state from lane flext (#945)
- fix(infra): restore make gen and clear tip reds after the preservation merges (#972)
- \[WIP\] preserve lane fix/p0-beads-static-identity-20260927 residue (flext-itpd1.3.10)
  (#962)
- \[WIP\] preserve lane fix/infra-red-tests-followup residue (flext-itpd1.3.10) (#963)
- New/sync (#971)
- Fix/tip adopt 959 967 966 (#970)
- fix(models): restore pre-husk deps\_tool\_config and contexts; unbreak the tip imports
  (#965)
- fix(infra): restore ToolchainSpec fields for lint/pyrefly green (#959)
- fix(codegen): implement the render-artifact protocol the K5 refactor declared (#967)
- P0 fix(models): two half-removed owners crashed every flext\_infra import
  (flext-xsuwg) (#966)
- Recovery/p0 20260927/flext n8tk7 0e364848e (#969)
- \[WIP\] Preserve isolated infra lifecycle repairs for adoption (#926)
- Fix/tip green 20260928 (#968)
- \[WIP\] preserve never-committed husk content v8-md-converge/flext-infra (#954)
- \[WIP\] preserve lane fix/post-merge-gen-fixed-point before retirement (#932)
- \[WIP\] preserve lane fix/generator-worktree-and-mise-bootstrap before … (#942)
- \[WIP\] preserve lane wip/audit-infra-20260922 before retirement (#930)
- \[WIP\] preserve lane fix/zero-red-tests before retirement (#928)
- \[WIP\] Preserve abandoned mise launcher-bake slice — the fleet-wide make gen/upg
  blocker (flext-itpd1.3.10) (#957)
- \[WIP\] preserve never-committed husk content v8-model-helpers/flext-infra (#955)
- fix(infra): bake the Mise launchers and complete the cold-start triple (flext-7babo)
  (#958)
- \[WIP\] preserve never-committed husk content v8-gate-speed/flext-infra (#953)
- \[WIP\] preserve lane hotfix/testmon-worker-collection-20260924 before … (#939)
- \[WIP\] preserve never-committed husk content v8-testmon/flext-infra (#956)
- \[WIP\] preserve lane fix/docker-ci-selection-20260926 before retirement (#937)
- \[WIP\] preserve lane fix/docker-ci-policy-20260926 before retirement (#936)
- \[WIP\] preserve never-committed husk content v8-ci-scope/flext-infra (#952)
- \[WIP\] Fix/upg lifecycle hooks (preserved lane; re-evaluate after flext-infra lands)
  (#925)
- fix(infra): allow manifest-owned dependency pin cutovers (#950)
- fix: the renames-tests followup — runner floor, layout spawns, docs scope, modernizer
  probe (#947)
- Fix/inc429 mise upg projection 20260927 (#951)
- fix(infra): compose the shared Rope cycle and typed scaffold manifest (#923)
- fix(docs): stop requiring the generated api-reference surface on package-less scopes
  (#948)
- fix(runtime): exterminate .flext-runtime, repair tip gen, census K3-K5 to zero (#944)
- fix(runtime): complete the .flext-runtime extermination and unbreak the 0.12.0-dev tip
  (#946)
- \[WIP\] refactor(census): one owner per module and per fact (K3, ENFORCE-067) (#920)
- fix(runtime): exterminate the external .flext-runtime state and restore checkout
  environments (#922)
- \[WIP\] refactor(census): rename the 42 forbidden get\_/is\_ accessors (K2) (#918)
- \[WIP\] fix(codegen,tests): clear the flext-infra tip test reds at their owners (#919)
- merge: synchronize recovery with 0.12.0-dev tip \[WIP\] (#916)
- refactor(cli): project-prefix the CLI route and dispatch classes (census K1) (#917)
- Fix/infra check green 20260927 (#915)
- \[WIP\] fix(check): make check green in CI within 120 s (#913)
- Recovery/stabilization 0.12 20260926 (#914)
- Fix/namespace product owner 20260926 (#911)
- Fix/docker ci policy 20260926 (#912)
- Recovery/stabilization 0.12 20260926 infra (#910)
- \[WIP\] merge 0.12.0-dev into the lane (13 tip commits) (#909)
- fix: zero-red convergence — rope fork dc.3, canonical adoption, lifecycle speed (#902)
- fix(namespace): facade stem carries the package identity, not the checkout (#908)
- fix(gen): isort member order is case-insensitive inside a type group (#907)
- fix(pytest): cosmos-docgen ceiling returns to the measured 4 workers (#906)
- fix(pytest): cosmos-docgen declares its measured 8-worker ceiling (#905)
- feat(pytest): per-project worker ceilings in the tooling SSOT (#904)
- fix(docs): prettier never rewraps pandoc-fenced authoring sources (#903)
- test(modernizer): repair the derived-facade probe left unparsable on the tip (#901)
- Fix/zero red tests (#897)
- Fix/zero red convergence 20260925 (#898)
- \[WIP\] fix: preserve frozen runtime identity and native bootstrap repairs (#899)
- Fix/v8 s0 npm lock (#900)
- chore(merge): adopt the direct integration-tip repairs d6a413f32 and … (#896)
- test: repair the rename-campaign tests and the runtime-consumer import probe (#894)
- test(container): drop the dependency-injector bridge fixture (#893)
- fix(layout): cosmos-docgen keeps its presentation SSOT roots (#895)
- Merge pull request #892 from marlonsc/fix/docs-workspace-root-generate-symmetry
- Fix/zero red tests (#891)
- fix: restore post-#881 integration green (stale merge resolutions, pending infra-dedup
  rewrites) (#890)
- fix(tests): repair tip merge residue and drop the detector import workaround (#889)
- Feat/rename campaigns as rule data (#888)
- Fix/infra slow tier green (#887)
- feat(codemod): ship rename campaigns as make mod rule data (infra-dedup) (#881)
- Fix/zero red tests (#886)
- Fix/infra slow tier green (#885)
- fix: pyproject generated header + detector consumes governed SSOT (#884)
- feat(workspace): add the workspace-only propagate verb (one lane per changed member)
  (#883)
- test: drive flext-infra's own suite to zero reds on the integration tip (#882)
- test: exterminate test-law violations in flext-infra's own suite and repair the reds
  they hid (#880)
- refactor(release): one publication lane owner and a collapsed release package (#879)
- feat(coverage): remove the coverage floor; coverage is measured, never gated (#877)
- fix(codegen): elect lazy-init letters from the project's own facade chain (#878)
- feat(codemod): generalize the test-law rule catalog (#875)
- fix(tests): write layout org overlay under tmp\_path, not the installed flext-cli
  package (#876)
- fix(gates): adopt #869 boundary print detection and repair the integration fixed point
  (#874)
- fix(codemod): restore the rope lint exemption and loud None guards in… (#873)
- Fix/zero red convergence 20260925 (#872)
- Merge integration into facade alias and development contract lane (#871)
- Fix/lazy export collision 20260924 (#870)
- fix(make): upg passes no empty lockfile platform list to mise (#868)
- fix(make): workspace members use the workspace runtime; setup parses on the host make
  (#867)
- Fix/zero red tests (#866)
- fix(make): upg runs the declared pre-/post-upg lifecycle hooks (#858)
- fix: integrated suite green (suite-green + 861 convergence) (#865)
- fix(gates,codegen): neutral security skip without src; package:false analyzer dirs
  (#864)
- fix(codemod): facade-base-by-class-name selects FLEXT family facades only (#863)
- fix(layout): GEMINI.md is a canonical agent pointer (#862)
- fix(toolchain): unlocked fleet mode + stale installer cleanup + tip integration (#860)
- fix(docs): surface validate reasons and honor the workspace-root docs contract (#859)
- fix(codegen): drop stale installer projection entries + integrate tip (#856)
- fix: finish post-merge infra convergence (#857)
- Fix/post merge green 20260925 (#854)
- merge: integrate all pending 0.12.0-dev pull requests (#853)
- feat(make): freeze setup installs and centralize lock updates (#845)
- fix(infra): converge activation ownership and strict validation (#849)
- fix(codegen): align facade imports and generated fixture contracts (#847)
- fix(check): preserve native failures and typed observations (#848)
- Merge remote-tracking branch 'origin/0.12.0-dev' into 0.12.0-dev
- fix(gates): keep ast-grep exit semantics in the observational split (#835)
- Merge remote-tracking branch 'origin/0.12.0-dev' into 0.12.0-dev
- merge: land rope lane generator parity cures and the gen/fix fixed-point fix
  (flext-djna9, flext-w2iw4, flext-7gup3, flext-7mo02)
- feat(sonar): sync SonarCloud server-side issue exclusions from the codegen SSOT (#830)
- fix(codemod): facades extend the parent by its declared class name (#829)
- fix(codegen): declare the SonarCloud tests root unconditionally (#828)
- fix(codegen): derive the project package name from the manifest, not the directory
  name (#825)
- fix(deps): write dependency floors to the modernized repository, never the installed
  package (#827)
- feat(codegen): project .sonarcloud.properties fleet-wide from the SSOT (#826)
- Merge remote-tracking branch 'refs/remotes/origin/0.12.0-dev' into 0.12.0-dev
- integrate origin/0.12.0-dev: rope automation wave-6
- merge(0.12.0-dev): absorb integration tip 2026-09-22 wave-4 (no-ff)
- merge(0.12.0-dev): absorb integration tip 2026-09-22 wave-3 (no-ff)
- merge(0.12.0-dev): absorb integration tip 2026-09-22 (no-ff)
- merge(0.12.0-dev): align recovery with integration tip 20260922 (no-ff)
- Merge remote-tracking branch 'origin/0.12.0-dev' into
  recovery/rope-automation-20260921
- \[WIP\] reconcile current integration and enforce transactional runtime verification
- \[WIP\] merge integration while preserving recovered generator repairs
- \[WIP\] absorb latest integration owner repairs
- \[WIP\] absorb integration SCC bootstrap repair
- \[WIP\] absorb current Infra integration into recovery
- \[WIP\] absorb current integration into Rope recovery
- \[WIP\] recover codegen residue through current declaration owners
- \[WIP\] reconcile recovered Beads marker residue with current codegen owners
- \[WIP\] merge recovered generation convergence history into automation recovery
- fix(codegen): declaring-owner letters, declaration-first integration (flext-0in0k.9)
- fix(codegen): declaring-owner letters, declaration-first integration branch,
  one-name-per-line tuples (flext-0in0k.9) (#785)
- fix(codegen): render wrapped imports one name per line; four-per-line LOC-cap
  workaround dies (flext-5fxu6.4.9) (#783)
- Merge remote-tracking branch 'origin/0.12.0-dev' into HEAD
- merge: absorb fleet tip into protocol receipt lane
- fix(codegen): the transaction journal recovers one recorded root, consistently
  (unblocks make gen) (#780)
- chore(rope): preserve rope-modernize uncommitted edits (follow-up #744) (#765)
- fix(codegen,utilities): port the remaining MRO-cutover repairs (repository\_provider,
  Make selector, signature-rules loader) (#779)
- fix(config,models): restore the org layer and collapse the duplicated release family
  (blocks gen + ai-hub check) (#778)
- perf(lazy-init): pack comma entries up to MAX\_LINE\_LENGTH in projections (#777)
- Wip/stabilize 0.12 flext infra 20260919 (#776)
- Fix/conform plan base restore (#775)
- merge: reconcile mirror lineage with import-fixed lineage (flext-v4fmn)
- merge: bring this mirror checkout up to the published integration (fix-forward)
- Merge commit '1fccfca1fd215b761d5f081e5e0faf6802ef3f5a' into 0.12.0-dev
- Merge commit '4100745ca894c47ed02128510fcf4e8f82c7b557' into 0.12.0-dev
- Merge commit 'be1bbc34023ac2922b0a6b07a13b5b06ed1ae2e4' into 0.12.0-dev
- wip
- Merge commit 'd03939aea31b672b4c91e6a831222e510a621482' into 0.12.0-dev
- Merge commit '4ee955c0b3531882eb6ac9a3364599eb4799f52d' into 0.12.0-dev
- Merge remote-tracking branch 'refs/remotes/origin/0.12.0-dev' into 0.12.0-dev
- Merge commit 'd84644f0698f06d81f3be10cc3de2865455841a9' into 0.12.0-dev
- Merge commit '56ffdb5af1809469a61ebf99995637250fdd7fbb' into 0.12.0-dev
- merge: absorb 0.12.0-dev tip (fleet projections + residue adoption) into stabilized
  lineage
- Merge commit 'd81d0d03dc8501fa9cce76081fc2878923a6b4ad' into 0.12.0-dev
- refactor(utils): implement semantic cutover module and refactor dispatch
- Merge commit '30c82b30f5b4ecf6b660a743014a725da13e70da' into 0.12.0-dev
- Merge commit 'ba29d112b8429fb65abffd6e5066c78f75136fa9' into 0.12.0-dev
- merge: worktree-fix-hermetic-gate-child-env into 0.12.0-dev (best of both)
- Merge branch 'stabilize/lazy-init-exports' into 0.12.0-dev
- Merge branch 'wip/stabilize-0.12-flext-infra-20260919' into 0.12.0-dev
- Merge remote-tracking branch 'refs/remotes/origin/0.12.0-dev' into 0.12.0-dev
- fix(conform): allow passive bd ledger exports in composed Beads routes (#768)
- fix(codegen): render bare internal deps at workspace-context root (#767)
- Merge remote-tracking branch 'refs/remotes/origin/0.12.0-dev' into 0.12.0-dev
- wip
- fix(workspace): integrate remote 0.12.0-dev and keep orchestrator fix
- Merge commit '222994200' into 0.12.0-dev
- fixes
- merge: integrate origin 0.12.0-dev
- Merge fix/generated-guide-ownership into 0.12.0-dev
- merge: integrate 0.12.0-dev into governance convergence
- fix(config): canonical Infra owns sed\_patterns (SSOT yaml key validated;
  artifact/release duplicate Infra roots remain for later cutover)
- merge: integrate remote advance before renderer gate
- merge: renderer bootstrap-owner gate (G1) into 0.12.0-dev
- merge: integrate remote 0.12.0-dev with alignment crash fix
- Merge remote-tracking branch 'refs/remotes/origin/0.12.0-dev' into 0.12.0-dev
- merge: integrate origin/0.12.0-dev (PR 740 mod sed list import) with adoption WIP
  af9f4ae34
- Merge branch '0.12.0-dev' of github.com:flext-sh/flext-infra into 0.12.0-dev
- Merge remote-tracking branch 'origin/0.12.0-dev' into 0.12.0-dev
- Merge branch 'v5-exec' into 0.12.0-dev
- Merge branch 'v5-exec' into 0.12.0-dev
- Merge remote-tracking branch 'refs/remotes/origin/0.12.0-dev' into 0.12.0-dev
- Merge branch 'fix/workspace-hygiene-0.12.0' into 0.12.0-dev
- merge: carry docs renderer contract into integration
- Merge remote-tracking branch 'refs/remotes/origin/0.12.0-dev' into 0.12.0-dev
- Merge remote-tracking branch 'refs/remotes/origin/0.12.0-dev' into 0.12.0-dev
- fix(codegen): the owner declares every table it writes (#722)
- fix(codegen): \`initialize\` requires the environment it runs the toolchain in (#720)
- fix(models): the field factory moves to its declared owner, typed (#721)
- feat(gates): an undeclared gitlink fails the gate, fleet-wide (#718)
- chore(flext-infra): preserve lane-r41 changes across 2 paths (#716)
- chore(flext-infra): preserve wip/duplicate/flext/flext-infra changes across 3 paths
  (#715)
- chore(flext-infra): preserve constants-remediation-0.12 changes across 1 paths (#714)
- merge origin/0.12.0-dev into fix/discovery-honours-manifest-exclusions: absorb
  integration
- chore(repo): drop the tracked worktree gitlink and adopt fmt output (#709)
- Merge branch 'fix/untrack-orphan-worktree-gitlink' into 0.12.0-dev
- fix(codemod,models): m is the single owner of ConfigDict; the rule converges every
  consumer (#706)
- chore(flext-infra): preserve fix/flext-5fxu6-infra-enforcement changes across 3 paths
  (#702)
- fix(gates): wire the hermetic child env into every gate (#705)
- Merge remote-tracking branch 'origin/0.12.0-dev' into 0.12.0-dev
- Merge remote-tracking branch 'origin/0.12.0-dev' into 0.12.0-dev
- Merge remote-tracking branch 'origin/0.12.0-dev' into 0.12.0-dev
