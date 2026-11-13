# Release v0.12.1

## Scope

- Release version: 0.12.1
- Projects packaged: 2

## Projects impacted

- root
- flext-infra

## Pull requests since last release

perf(tests): resolve selection and inventory in one collection pass (#2306)
Merge branch '0.12.0-dev' into perf/test-single-collection-20261112
fix(codegen): close the verified review findings of #2262/#2264/#2266 (#2300)
perf(mod): focused make mod within budget; reuse import facts; fix rendering cache key
(#2305)
Merge remote-tracking branch 'origin/0.12.0-dev' into perf/mod-producers-budget-20261112
Merge branch '0.12.0-dev' into fix/review-findings-20261112
fix(codegen): uv sources follow the FLEXT line; project subscripted sibling bases
(#2303)
Merge origin/0.12.0-dev into fix/uv-sources-follow-flext-line-20261112
Merge branch '0.12.0-dev' into fix/review-findings-20261112
perf(lazy-init): defer heavy capabilities behind facade-only stand-ins (#2301)
merge: 0.12.0-dev into feat/lazy-deferred-capabilities-20261112
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/review-findings-20261112
perf(setup): remove the private setup/upg lifecycle lease (#2298)
fix(codegen): project protocols for models rooted in m.RootModel (#2297)
fix(check): active lanes are never merged-but-alive (#2295)
fix(docs): scope building receives the planned root projection (#2296)
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/review-findings-20261112
merge: 0.12.0-dev into feat/lazy-deferred-capabilities-20261112
Merge branch '0.12.0-dev' into fix/lane-hygiene-active-wip-20261112
merge: 0.12.0-dev into perf/setup-no-lifecycle-lease-20261112
perf(setup): keep a .venv that already satisfies uv.lock (#2287)
fix(make): remove the test file selector and validate the gen root (#2285)
Merge branch '0.12.0-dev' into fix/make-selector-root-20261112
Integrate wt-pre-commit-setup-wip-20261112 into upload-20261007 (#2277)
fix(security): load generated protocol modules through importlib; format codemod tests
(#2292)
fix(rules): ban disabling Python bytecode in every FLEXT project (ENFORCE-128) (#2291)
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/ban-bytecode-disable-20261112
Merge 0.12.0-dev into fix/setup-noop-integrated-20261112
fix(codegen): model protocol projection binds only what it writes (#2290)
Merge branch '0.12.0-dev' into fix/protocol-projection-defects-20261112
fix(codemod): focused mod scans its selection; provision the mod\_workspace environment
(#2289)
perf(setup): keep a lock-satisfied .venv, compile bytecode, drop the private publication
lock (#2288)
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/ban-bytecode-disable-20261112
merge: 0.12.0-dev into fix/codemod-selection-scope-0120-20261112
merge: 0.12.0-dev into perf/setup-noop-when-synced-20261112
fix(security): declare the subprocess axiom and the bandit skips in the tooling SSOT
(#2286)
merge: integrate 0.12.0-dev into fix/make-selector-root-20261112
fix(check): share one warm Mypy cache across worktrees and run Mypy only locally (#2284)
feat(codemod): domain capabilities exempt their own technology prefixes from the
library-name rule (#2283)
merge: origin/0.12.0-dev into hotfix/mypy-cache-worktree-20261112
Merge origin/0.12.0-dev into feat/domain-capability-prefixes-20261112
chore(integration): land upload-20261007 into 0.12.0-dev (docs: model fields keep the
model) (#2281)
merge: 0.12.0-dev into upload-20261007 (#2282)
merge: 0.12.0-dev into upload-20261007
docs(pydantic): model fields keep the model; protocols type every other position (#2280)
chore(integration): land upload-20261007 into 0.12.0-dev (2026-11-12 convergence)
(#2270)
fix(codegen): clear the primary-check findings (#2279)
merge: origin/upload-20261007 into fix/ci-primary-green-20261112-casts
fix(codegen): package participation follows the rendered projection (#2266)
refactor(release): delete the lane receipt transport the release no longer reads (#2268)
fix(codegen): restore complete CI validation and upload test receipts (#2269)
fix(release): publication lanes admit through verify, not agent-lane create (operator
decision required) (#2265)
Merge remote-tracking branch 'origin/upload-20261007' into
fix/release-lane-admission-20261112
fix(codemod): publish rule-test snapshots without changing their meaning (#2267)
fix(codegen): a new project's bootstrap generates, publishes and documents itself
(#2264)
Merge remote-tracking branch 'origin/upload-20261007' into
fix/release-lane-admission-20261112
fix(codemod): bind ClassVar only where an annotator rewrites model\_config (#2263)
feat(codegen): the commit hook provisions with make setup before its check (#2262)
formats
Merge commit '93a3f30d0f03516ef90b6355057fa365dad3ea9c' into upload-20261007
fix(codegen): skip non-text (binary) files in retired projection planning (#2260)
fix(infra): restore lane generation contract
Upload 20261007 (#2258)
Merge branch '0.12.0-dev' into upload-20261007
fix(codegen): preserve declared editor artifacts and portable bootstrap (#2257)
chore: retire host-specific bootstrap alias from source (#2256)
chore: retire host-specific bootstrap alias from source
fix(setup): remove broken .bin symlink before mkdir (#2255)
fix(setup): make .bin directory creation non-fatal (#2254)
fix(setup): make lifecycle mkdir non-fatal (#2253)
fix(setup): ignore mkdir errors in bootstrap (#2251)
fix(setup): make bootstrap report directory creation idempotent (#2250)
fix(setup): repair Makefile quoting (#2249)
fix(setup): exclude bootstrap Mise paths from symlink check (#2248)
fix(base): use default-value style for optional CommandOutput field (#2247)
formats
fix(gates): use default-value style for optional GateTestIntent field (#2246)
feat(attestation): candidate admission contract on top of V3 proof (#2245)
Merge branch '0.12.0-dev' into upload-20261007
Wip/sweep preserve/xdist worker resolution 20261108 52854e47 (#2244)
Wip/sweep preserve/test secret rule 0d7bffb0 (#2243)
Wip/sweep preserve/protocol alias owner 20261108 98d44d04 (#2242)
Wip/sweep preserve/infra model field protocols 20261108 feb449c2 (#2241)
Wip/sweep preserve/gen facades speed 182baa95 (#2239)
Wip/sweep preserve/editor analyzer context f198a752 (#2238)
Wip/sweep preserve/flext infra rope paren 20261108 03af5731 (#2235)
Wip/sweep preserve/flext infra mod indent 20261108 89879747 (#2234)
Wip/sweep preserve/agents md projection e224d59a (#2232)
Wip/sweep preserve/g6 duplication format scope b8872a85 (#2229)
Wip/sweep preserve/g4 gates typing 3db69f26 (#2227)
Wip/sweep preserve/flext infra mise tools ddfd692c (#2223)
Preserve/flext infra/stash cd7eff0b (#2220)
Preserve/flext infra/stash 1bb35e4b (#2219)
fix(rules): one ENFORCE-102 rule for methods without self/cls (#2214)
feat(codemod): dump without computed fields through the native keyword (#2217)
Merge branch '0.12.0-dev' into fix/pyrefly-tests-20261108
fix(codegen): ignore the executor runtime state directory, not only the venv (#2215)
fix: locked direnv, identifier stems for Python commands, header-declared script verbs
(#2213)
Merge branch '0.12.0-dev' into fix/direnv-promoted-stem-20261108
fix(markdown): make fix moves the MkDocs list blocks rumdl withholds (#2212)
feat(codemod): ban runtime skips after reading the environment (#2211)
chore(deps): rope 1.15.2+dc.6 through make gen/upg (#2216)
Merge branch '0.12.0-dev' into fix/rope-dc6-pin-20261108
Merge branch '0.12.0-dev' into fix/ignore-flext-runtime-state-20261108
Merge branch '0.12.0-dev' into fix/static-rule-unify-20261108
Merge branch '0.12.0-dev' into fix/markdown-mkdocs-list-indent-20261108
Merge branch '0.12.0-dev' into fix/connectivity-skip-rule-20261108
Upload 20261007 (#2218)
{"retained\_commits":\[\],"head\_entries":\[{"path":"tests/unit/validate/pytest\_worker\_ceiling\_tests.py","mode":"100644","oid":"c868493d7406a0dfb1d7fe163399706c32144424"}\],"repo\_root":"/home/marlonsc/worktrees/flext-infra/xdist-worker-resolution-20261108","common\_dir":"/home/marlonsc/flext/.git/modules/flext-infra","head":"0f50cb331f9682a44117106f9c7c02d91c2c81c8","branch":"fix/xdist-worker-resolution-20261108","paths":\["tests/unit/validate/pytest\_worker\_ceiling\_tests.py"\],"index\_entries":\[{"path":"tests/unit/validate/pytest\_worker\_ceiling\_tests.py","mode":"100644","oid":"c868493d7406a0dfb1d7fe163399706c32144424"}\],"files":\[{"path":"tests/unit/validate/pytest\_worker\_ceiling\_tests.py","mode":"100644","permissions":420,"oid":"910377612c6cc4006f091e4eb33025ceda9c2e6a"}\]}
{"retained\_commits":\[\],"head\_entries":\[\],"repo\_root":"/home/marlonsc/worktrees/flext-infra/test-secret-rule","common\_dir":"/home/marlonsc/flext/.git/modules/flext-infra","head":"57fcff8179bf1e43b6a251c6cdfbb2d2f409fcf9","branch":"fix/test-secret-literal-rule-20261108","paths":\["src/flext\_infra/config/rules/ast-grep/rules/test-secret-literal.yml","src/flext\_infra/config/rules/ast-grep/tests/test-secret-literal-bind-test.yml","src/flext\_infra/config/rules/ast-grep/tests/test-secret-literal-import-test.yml","src/flext\_infra/config/rules/ast-grep/tests/test-secret-literal-reuse-test.yml","src/flext\_infra/config/rules/ast-grep/tests/test-secret-literal-test.yml","src/flext\_infra/config/rules/ast-grep/utils/function-body-statement.yml","src/flext\_infra/config/rules/ast-grep/utils/secret-credential-assertion.yml","src/flext\_infra/config/rules/ast-grep/utils/secret-credential-name.yml","src/flext\_infra/config/rules/ast-grep/utils/secret-credential-reference.yml","src/flext\_infra/config/rules/ast-grep/utils/secret-credential-slot.yml","src/flext\_infra/config/rules/ast-grep/utils/secret-literal-exempt.yml","src/flext\_infra/config/rules/ast-grep/utils/secret-literal-producer.yml","src/flext\_infra/config/rules/ast-grep/utils/secret-literal-value.yml"\],"index\_entries":\[\],"files":\[{"path":"src/flext\_infra/config/rules/ast-grep/rules/test-secret-literal.yml","mode":"100644","permissions":420,"oid":"0770fb3b2e355becef183d89e8caeabf1b91617c"},{"path":"src/flext\_infra/config/rules/ast-grep/tests/test-secret-literal-bind-test.yml","mode":"100644","permissions":420,"oid":"8b53fea5c981ed17b7f584cb2c4938384e277482"},{"path":"src/flext\_infra/config/rules/ast-grep/tests/test-secret-literal-import-test.yml","mode":"100644","permissions":420,"oid":"7314b79c2217498347eb8c312cbe455af76cadc9"},{"path":"src/flext\_infra/config/rules/ast-grep/tests/test-secret-literal-reuse-test.yml","mode":"100644","permissions":420,"oid":"20816434caf9efb884779be0edc3882f29fce892"},{"path":"src/flext\_infra/config/rules/ast-grep/tests/test-secret-literal-test.yml","mode":"100644","permissions":420,"oid":"370fec892f6df80d030d6a4eaed8677d9528f759"},{"path":"src/flext\_infra/config/rules/ast-grep/utils/function-body-statement.yml","mode":"100644","permissions":420,"oid":"c5a30ad890098332648a7b5119c72b20c915acea"},{"path":"src/flext\_infra/config/rules/ast-grep/utils/secret-credential-assertion.yml","mode":"100644","permissions":420,"oid":"35ab47aefdceacd34b492371c8a58d6913bcaa98"},{"path":"src/flext\_infra/config/rules/ast-grep/utils/secret-credential-name.yml","mode":"100644","permissions":420,"oid":"d5efe4cb43b5011c6d06e13770821e7ac258ffdd"},{"path":"src/flext\_infra/config/rules/ast-grep/utils/secret-credential-reference.yml","mode":"100644","permissions":420,"oid":"decc6a754942e0227754204587717477a3213dde"},{"path":"src/flext\_infra/config/rules/ast-grep/utils/secret-credential-slot.yml","mode":"100644","permissions":420,"oid":"0e14e6c908be6b0c81934c40db27721c5ad90fc4"},{"path":"src/flext\_infra/config/rules/ast-grep/utils/secret-literal-exempt.yml","mode":"100644","permissions":420,"oid":"002a2dbfc0701b2da622330a4de0e2b953b27c37"},{"path":"src/flext\_infra/config/rules/ast-grep/utils/secret-literal-producer.yml","mode":"100644","permissions":420,"oid":"25bcce4f15917003de50f7c5f5323dfb7b917376"},{"path":"src/flext\_infra/config/rules/ast-grep/utils/secret-literal-value.yml","mode":"100644","permissions":420,"oid":"d79c9612f07257f734427bd037df9f6835c6deab"}\]}
{"retained\_commits":\[\],"head\_entries":\[\],"repo\_root":"/home/marlonsc/worktrees/flext-infra/protocol-alias-owner-20261108","common\_dir":"/home/marlonsc/flext/.git/modules/flext-infra","head":"ac7afd1b7ffb8a7ed36b3651d56c796a3f8d3916","branch":"fix/protocol-alias-owner-20261108","paths":\["tests/unit/codegen/test\_protocol\_cross\_module\_alias.py"\],"index\_entries":\[\],"files":\[{"path":"tests/unit/codegen/test\_protocol\_cross\_module\_alias.py","mode":"100644","permissions":420,"oid":"e41c71db14fa5da61d61455b5d26f96b50de8c00"}\]}
{"retained\_commits":\[\],"head\_entries":\[\],"repo\_root":"/home/marlonsc/worktrees/flext-infra/infra-model-field-protocols-20261108","common\_dir":"/home/marlonsc/flext/.git/modules/flext-infra","head":"c3ac3ab8c0d8721ab92e30593c08ddac496a0de0","branch":"fix/infra-model-field-protocols-20261108","paths":\[".bin"\],"index\_entries":\[\],"files":\[{"path":".bin","mode":"120000","permissions":511,"oid":"befd018cc8c41e16572f3a184174701c225b40e8"}\]}
{"retained\_commits":\[\],"head\_entries":\[{"path":"src/flext\_infra/\_utilities/facade\_components.py","mode":"100644","oid":"b2be3d04274e712f8dc7673c10481e1d21fbac1f"}\],"repo\_root":"/home/marlonsc/worktrees/flext-infra/gen-facades-speed","common\_dir":"/home/marlonsc/flext/.git/modules/flext-infra","head":"27186b862b0c292b156e4154f87e53ef57a5e0c4","branch":"fix/gen-facades-speed-20261108","paths":\["src/flext\_infra/\_utilities/facade\_components.py"\],"index\_entries":\[{"path":"src/flext\_infra/\_utilities/facade\_components.py","mode":"100644","oid":"b2be3d04274e712f8dc7673c10481e1d21fbac1f"}\],"files":\[{"path":"src/flext\_infra/\_utilities/facade\_components.py","mode":"100644","permissions":420,"oid":"bd0134722d6c020b932b606ca196147b6bc37b9f"}\]}
{"retained\_commits":\[\],"head\_entries":\[{"path":"src/flext\_infra/codegen/\_conform/existing\_plan.py","mode":"100644","oid":"6cae04b6a3489461f77d6f97096048723814ce17"},{"path":"src/flext\_infra/codegen/\_conform/pyproject\_policy.py","mode":"100644","oid":"36104d4d8b3cc9d09759e7997b6e108d4c0e8089"},{"path":"src/flext\_infra/deps/\_modernizer/document.py","mode":"100644","oid":"1a06bd35df78d07f094a0219e006b3d196e8d1e3"},{"path":"src/flext\_infra/deps/phases/ensure\_pyright.py","mode":"100644","oid":"7607c71f451096485615a1161a7880be39032eaf"},{"path":"tests/unit/codegen/test\_codegen\_conform.py","mode":"100644","oid":"42cb5d709ead1e5bcca2068caa5ba4bc20b740c7"}\],"repo\_root":"/home/marlonsc/worktrees/flext-infra/editor-analyzer-context","common\_dir":"/home/marlonsc/flext/.git/modules/flext-infra","head":"b2eca40d583fdd73cc9456f74031dc7ee8bcb00e","branch":"fix/editor-analyzer-context-20261108","paths":\["src/flext\_infra/codegen/\_conform/existing\_plan.py","src/flext\_infra/codegen/\_conform/pyproject\_policy.py","src/flext\_infra/deps/\_modernizer/document.py","src/flext\_infra/deps/phases/ensure\_pyright.py","tests/unit/codegen/test\_codegen\_conform.py"\],"index\_entries":\[{"path":"src/flext\_infra/codegen/\_conform/existing\_plan.py","mode":"100644","oid":"6cae04b6a3489461f77d6f97096048723814ce17"},{"path":"src/flext\_infra/codegen/\_conform/pyproject\_policy.py","mode":"100644","oid":"36104d4d8b3cc9d09759e7997b6e108d4c0e8089"},{"path":"src/flext\_infra/deps/\_modernizer/document.py","mode":"100644","oid":"1a06bd35df78d07f094a0219e006b3d196e8d1e3"},{"path":"src/flext\_infra/deps/phases/ensure\_pyright.py","mode":"100644","oid":"7607c71f451096485615a1161a7880be39032eaf"},{"path":"tests/unit/codegen/test\_codegen\_conform.py","mode":"100644","oid":"42cb5d709ead1e5bcca2068caa5ba4bc20b740c7"}\],"files":\[{"path":"src/flext\_infra/codegen/\_conform/existing\_plan.py","mode":"100644","permissions":420,"oid":"9e0755a6aea318f8cedd1f2d46a8439f6694c5f7"},{"path":"src/flext\_infra/codegen/\_conform/pyproject\_policy.py","mode":"100644","permissions":420,"oid":"ce982611d46904f446c008113d4fe194d2a3e42b"},{"path":"src/flext\_infra/deps/\_modernizer/document.py","mode":"100644","permissions":420,"oid":"83c663a4a7ef2c3c25fea86573f7c474a0e6b556"},{"path":"src/flext\_infra/deps/phases/ensure\_pyright.py","mode":"100644","permissions":420,"oid":"6fc046a0fea9bae577252623e0b0009ca1641310"},{"path":"tests/unit/codegen/test\_codegen\_conform.py","mode":"100644","permissions":420,"oid":"5b874086e00d325f934e09647892db5f8849ef2c"}\]}
{"retained\_commits":\[\],"head\_entries":\[{"path":"src/flext\_infra/\_utilities/\_rope/restructure.py","mode":"100644","oid":"5c7c30564761c97569e6672f314d97af5d836a79"},{"path":"tests/unit/test\_infra\_rope\_runtime\_pymodule.py","mode":"100644","oid":"13e6926d339e8919d3c4b3da108d8d9c4388ddd0"}\],"repo\_root":"/home/marlonsc/flext-work/flext-infra-rope-paren-20261108","common\_dir":"/home/marlonsc/flext/.git/modules/flext-infra","head":"84a9dca1edf98fc543a6f1b5257f9bcb53578169","branch":"fix/rope-restructure-paren-text-20261108","paths":\["src/flext\_infra/\_utilities/\_rope/restructure.py","tests/unit/test\_infra\_rope\_runtime\_pymodule.py"\],"index\_entries":\[{"path":"src/flext\_infra/\_utilities/\_rope/restructure.py","mode":"100644","oid":"5c7c30564761c97569e6672f314d97af5d836a79"},{"path":"tests/unit/test\_infra\_rope\_runtime\_pymodule.py","mode":"100644","oid":"13e6926d339e8919d3c4b3da108d8d9c4388ddd0"}\],"files":\[{"path":"src/flext\_infra/\_utilities/\_rope/restructure.py","mode":"100644","permissions":420,"oid":"cec9196150bb42eb0a1d1eae3bfc7dc2b11138ab"},{"path":"tests/unit/test\_infra\_rope\_runtime\_pymodule.py","mode":"100644","permissions":420,"oid":"9f0db8f6c9c0cbeb6a9d1456d5bbec2b8f2cf7e6"}\]}
\[WIP\] Merge origin/upload-20261007 into fix/pyrefly-tests-20261108
{"retained\_commits":\[\],"head\_entries":\[{"path":"src/flext\_infra/config/rules/rope/contracts.yaml","mode":"100644","oid":"33624433327ba50976a4ff71b96955066aadf73b"},{"path":"tests/unit/codemod/test\_semantic\_constant\_cutover.py","mode":"100644","oid":"ed1f7b9311b285d5f0a9ce362def10e67807e4b1"}\],"repo\_root":"/home/marlonsc/cosmos-work/flext-infra-mod-indent-20261108","common\_dir":"/home/marlonsc/flext/.git/modules/flext-infra","head":"84a9dca1edf98fc543a6f1b5257f9bcb53578169","branch":"fix/mod-indent-20261108","paths":\["src/flext\_infra/config/rules/rope/contracts.yaml","tests/unit/codemod/test\_semantic\_constant\_cutover.py"\],"index\_entries":\[{"path":"src/flext\_infra/config/rules/rope/contracts.yaml","mode":"100644","oid":"33624433327ba50976a4ff71b96955066aadf73b"},{"path":"tests/unit/codemod/test\_semantic\_constant\_cutover.py","mode":"100644","oid":"ed1f7b9311b285d5f0a9ce362def10e67807e4b1"}\],"files":\[{"path":"src/flext\_infra/config/rules/rope/contracts.yaml","mode":"100644","permissions":420,"oid":"34940639b2b9e49805414ee22f6c49376c2ca703"},{"path":"tests/unit/codemod/test\_semantic\_constant\_cutover.py","mode":"100644","permissions":420,"oid":"90918f765062c521c09cf8fa395d0333570c4978"}\]}
{"retained\_commits":\[\],"head\_entries":\[{"path":".pre-commit-config.yaml","mode":"100644","oid":"df04de26eb3c2206ce18031fd9cf388558c98431"},{"path":"docs/guides/execution-context.md","mode":"100644","oid":"b169626ba146b5eea5c221dd87099d7f0e4c4a45"},{"path":"src/flext\_infra/templates/project/base/.pre-commit-config.yaml.j2","mode":"100644","oid":"0907c97ca31e2fc09981a77fd8d2e0c3254011f6"},{"path":"tests/unit/codegen/test\_codegen\_hook\_conformance.py","mode":"100644","oid":"0e585921b3d86f0962ec1fb9a28907c9639a68e0"}\],"repo\_root":"/home/marlonsc/worktrees/flext-infra/agents-md-projection","common\_dir":"/home/marlonsc/flext/.git/modules/flext-infra","head":"b2eca40d583fdd73cc9456f74031dc7ee8bcb00e","branch":"fix/agents-md-projection-20261108","paths":\[".pre-commit-config.yaml","docs/guides/execution-context.md","src/flext\_infra/templates/project/base/.pre-commit-config.yaml.j2","tests/unit/codegen/test\_codegen\_hook\_conformance.py"\],"index\_entries":\[{"path":".pre-commit-config.yaml","mode":"100644","oid":"f59e1808d32cc9132306800419af0f40feacb950"},{"path":"docs/guides/execution-context.md","mode":"100644","oid":"0816484b328a9840452dc9d1f2c5178700122f63"},{"path":"src/flext\_infra/templates/project/base/.pre-commit-config.yaml.j2","mode":"100644","oid":"2ea3a9c58c3133e6f95b651501c4854097232afd"},{"path":"tests/unit/codegen/test\_codegen\_hook\_conformance.py","mode":"100644","oid":"704149af314166f8fac36dcc14066fd4e41eec68"}\],"files":\[{"path":".pre-commit-config.yaml","mode":"100644","permissions":420,"oid":"f59e1808d32cc9132306800419af0f40feacb950"},{"path":"docs/guides/execution-context.md","mode":"100644","permissions":420,"oid":"0816484b328a9840452dc9d1f2c5178700122f63"},{"path":"src/flext\_infra/templates/project/base/.pre-commit-config.yaml.j2","mode":"100644","permissions":420,"oid":"2ea3a9c58c3133e6f95b651501c4854097232afd"},{"path":"tests/unit/codegen/test\_codegen\_hook\_conformance.py","mode":"100644","permissions":420,"oid":"704149af314166f8fac36dcc14066fd4e41eec68"}\]}
{"retained\_commits":\[\],"head\_entries":\[{"path":"src/flext\_infra/\_constants/check.py","mode":"100644","oid":"b9c004e9f8fe7c4a47a687f82bfef667e184820f"},{"path":"src/flext\_infra/gates/duplication.py","mode":"100644","oid":"4c6a88cf44671fd6e90118df225fe0bf7bcdd93a"},{"path":"tests/unit/check/duplication\_gate\_tests.py","mode":"100644","oid":"e086ba4a9402fcbc15f2c8f6d326bf8551f1374b"}\],"repo\_root":"/home/marlonsc/flext-work/fix/g6-duplication-format-scope","common\_dir":"/home/marlonsc/flext/.git/modules/flext-infra","head":"70c9dcb65dc9e5dc95b47615e4b4e34d102ec7ac","branch":"fix/g6-duplication-format-scope","paths":\["src/flext\_infra/\_constants/check.py","src/flext\_infra/gates/duplication.py","tests/unit/check/duplication\_gate\_tests.py"\],"index\_entries":\[{"path":"src/flext\_infra/\_constants/check.py","mode":"100644","oid":"b9c004e9f8fe7c4a47a687f82bfef667e184820f"},{"path":"src/flext\_infra/gates/duplication.py","mode":"100644","oid":"4c6a88cf44671fd6e90118df225fe0bf7bcdd93a"},{"path":"tests/unit/check/duplication\_gate\_tests.py","mode":"100644","oid":"e086ba4a9402fcbc15f2c8f6d326bf8551f1374b"}\],"files":\[{"path":"src/flext\_infra/\_constants/check.py","mode":"100644","permissions":420,"oid":"7129f59993789a332df390ff7c7f418b5495760d"},{"path":"src/flext\_infra/gates/duplication.py","mode":"100644","permissions":420,"oid":"1d2a5cf58c12fd2a0c79dd374dee8fac28eb2427"},{"path":"tests/unit/check/duplication\_gate\_tests.py","mode":"100644","permissions":420,"oid":"5319e7889e6df6dfd1bf0953d8351c28e4dd5740"}\]}
{"retained\_commits":\[\],"head\_entries":\[{"path":"src/flext\_infra/check/workspace\_check.py","mode":"100644","oid":"1c2262abfcee5d89272b20c10382c6cbe98534ca"},{"path":"tests/utilities\_gates.py","mode":"100644","oid":"94eb85be72eb34100638af7ddb4dd2ca87430dd7"}\],"repo\_root":"/home/marlonsc/flext-work/fix/g4-gates-typing","common\_dir":"/home/marlonsc/flext/.git/modules/flext-infra","head":"70c9dcb65dc9e5dc95b47615e4b4e34d102ec7ac","branch":"fix/g4-gates-typing","paths":\["src/flext\_infra/check/workspace\_check.py","tests/utilities\_gates.py"\],"index\_entries":\[{"path":"src/flext\_infra/check/workspace\_check.py","mode":"100644","oid":"1c2262abfcee5d89272b20c10382c6cbe98534ca"},{"path":"tests/utilities\_gates.py","mode":"100644","oid":"94eb85be72eb34100638af7ddb4dd2ca87430dd7"}\],"files":\[{"path":"src/flext\_infra/check/workspace\_check.py","mode":"100644","permissions":420,"oid":"35088d5f4c400c1bc2b0c7b16d4b84cbfaa9530f"},{"path":"tests/utilities\_gates.py","mode":"100644","permissions":420,"oid":"816d0a3ce99ba7cfe4a42e81f1c94818736f7885"}\]}
{"retained\_commits":\[\],"head\_entries":\[{"path":"src/flext\_infra/codegen/\_conform/artifact\_render.py","mode":"100644","oid":"6a3e6933780742a02a125215b2927fc8d239b1ac"}\],"repo\_root":"/home/marlonsc/cosmos-work/flext-infra-mise-tools","common\_dir":"/home/marlonsc/flext/.git/modules/flext-infra","head":"0f680a406277ad4817ee50192329ccfd5a72d07f","branch":"fix/mise-project-tools-install-20261108","paths":\["src/flext\_infra/codegen/\_conform/artifact\_render.py"\],"index\_entries":\[{"path":"src/flext\_infra/codegen/\_conform/artifact\_render.py","mode":"100644","oid":"6a3e6933780742a02a125215b2927fc8d239b1ac"}\],"files":\[{"path":"src/flext\_infra/codegen/\_conform/artifact\_render.py","mode":"100644","permissions":420,"oid":"0e441b79034e252e5f856fafdeb5eff7f5407896"}\]}
merge: origin/upload-20261007 into fix/static-rule-unify-20261108
\[WIP\] Merge fix/ignore-flext-runtime-state-20261108
\[WIP\] Merge origin/upload-20261007 into fix/rope-dc6-pin-20261108
Merge origin/0.12.0-dev into fix/direnv-promoted-stem-20261108
Merge remote-tracking branch 'origin/upload-20261007' into fix/base-ci-green-20261108
Merge commit 'a9320ac722728742f39efabf471af7df97cb6d4a' into upload-20261007
Merge commit 'c294d087b313aa6b3d2303edfd882a31daaaacb4' into upload-20261007
Merge commit 'a243a98da800a46996821c16b35304855d834897' into upload-20261007
Merge commit '847a8eac2ca4303f8ec5d18fec5cf90904e12c87' into upload-20261007
Merge commit 'f5cccd12fa5ed48ae144e3603a83188e9ef280f7' into upload-20261007
Merge commit '27186b862b0c292b156e4154f87e53ef57a5e0c4' into upload-20261007
Merge commit '57fcff8179bf1e43b6a251c6cdfbb2d2f409fcf9' into upload-20261007
Merge commit 'c3ac3ab8c0d8721ab92e30593c08ddac496a0de0' into upload-20261007
Merge commit '76a04e9be9b7d6917b94e46a7e7fd8e05e1a14c7' into upload-20261007
Merge commit '298647f6febfdc5a1e66b0727bbc331c5466b483' into upload-20261007
Merge commit '448af82ea3d109728c5200fc26684d2b202b16b9' into upload-20261007
Merge commit 'ea9f69e3194ff5512c6ed381f2e10387fd370942' into upload-20261007
Merge commit '79da7d5c94fb13a5f2ff822330fd7ef69adb2caf' into upload-20261007
Merge commit '345f4e6f790d9361e200546b86d329fe1ac1f06c' into upload-20261007
Merge origin/0.12.0-dev into fix/ci-mise-parity-20261108
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/markdown-mkdocs-list-indent-20261108
\[WIP\] Merge origin/0.12.0-dev into fix/pyrefly-zero-20261108
Merge remote-tracking branch 'origin/upload-20261007' into fix/base-ci-green-20261108
Merge origin/0.12.0-dev into fix/ci-mise-parity-20261108
Land upload-20261007 into 0.12.0-dev (2026-11-08 convergence) (#2209)
Merge commit 'f41214eb0d0606e631242d29d8a41e7b240f31bb' into upload-20261007
Merge commit 'af8fe03af13b384ef2f1bc13069305c0dfa39cce' into upload-20261007
Merge commit '3d5dd4a4ae0b8b2d41ee74cedd419be17507812e' into upload-20261007
Merge commit 'ebce79a51168f1afc822a513a9f7fa3bafcc38bf' into upload-20261007
Merge commit 'ea2b6ded9c957b5b7f86669fafc47cc54b7cbfe4' into upload-20261007
Merge remote-tracking branch 'origin/upload-20261007' into
fix/test-secret-literal-rule-20261108
Merge commit '7c3c23b0d29d56ed980256d860df221924ff7130' into upload-20261007
Merge origin/upload-20261007 into fix/gen-facades-speed-20261108
Merge remote-tracking branch 'origin/upload-20261007' into
fix/test-secret-literal-rule-20261108
Merge branch 'fix/base-ci-green-20261108' into upload-20261007
Merge commit '412925e394587f75f8a8d938da9c22b0ab2844b5' into upload-20261007
Merge commit 'e3399eef91b6e5a3ee3640774c4fe491cc151a44' into upload-20261007
Merge commit '222930f6b64fe5cb707d5e7e302b8c91f4ec0493' into upload-20261007
Merge commit '9d2302e3cf415e077f1d281be24babbe38e9d75d' into upload-20261007
Merge commit '98e9b01674426c556a11f09dfe4041b229311dc2' into upload-20261007
Merge commit '5f56827ba4eb5de11f106c0f61e9f33a2d113fe8' into upload-20261007
Merge commit '98198b117729d7d4bee62d04bba63eb81ec5a563' into upload-20261007
Merge commit 'a53d1e674f630ab44a9b74bff4d84f2cd49096f7' into upload-20261007
Merge commit 'c76fb0ba1bd8aed9bc30dbc7b0aa1a4956c6809e' into upload-20261007
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/ci-tool-cache-bounded-dev-20261108
Merge remote-tracking branch 'origin/upload-20261007' into fix/base-ci-green-20261108
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/base-ci-green-20261108
Merge remote-tracking branch 'origin/upload-20261007' into fix/base-ci-green-20261108
Merge commit '095749553908db9f1a37288e5bf1f3884ddd29c8' into upload-20261007
fix(codegen): docs jobs read packages for declared registry consumers (#2208)
Merge commit '23c00dc65873f2ff391cbf856c61488abff82dda' into upload-20261007
Merge commit '403d0e520fa4913373c93101350e9be9adfe0e78' into upload-20261007
Merge remote-tracking branch 'refs/remotes/origin/upload-20261007' into upload-20261007
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/ci-tool-cache-bounded-dev-20261108
merge: integrate tip b2eca40d58 into ci pyrefly sweep
fix(codegen): atomic admission preflight before publication (flext-wmzp6) (#2207)
Merge origin/0.12.0-dev into fix/gen-atomic-admission-20261108
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/ci-tool-cache-bounded-dev-20261108
merge: integrate tip 0f50cb331f into ci pyrefly sweep
fix(ci): the tool cache restores only its exact lock-state key (#2205)
\[WIP\] Merge origin/0.12.0-dev into fix/pyrefly-zero-20261108
merge: integrate 0.12.0-dev 0f50cb331f into the pyrefly convergence lane
merge: land upload-20261007 (#2187, #2196, #2202) through the pyrefly convergence lane
fix(codegen): project quoted model forward references to sibling protocols (#2204)
fix(pytest): run the suite on the submitted project, where check wrote its receipt
(#2202)
fix(upg): members lock themselves; root composes them (ADR-030, flext-zzynv) (#2201)
fix(codemod,pytest): import profundo do próprio pacote de topo (B8) e overloads de
u.Tests.fixture (B7) (#2198)
test(codegen): credencial de dependência privada fica fora do Git global (#2197)
fix(cutover): rewrite every test assert by its top-level operator, whole and typed
(#2195)
fix(tests): owned connectivity prerequisite skips do not fail the run (#2200)
feat(mod): migrate flext-command headers to PEP 723 script blocks (#2199)
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/promoted-header-pep723-20261108
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/test-assert-cutover-ast-20261108
merge: integra a ponta da 0.12.0-dev
fix(codegen): ci-template renders no blank line at EOF (#2189)
merge: integra a ponta da 0.12.0-dev
fix(deps): name declared repository namespaces from the project root for mypy (#2196)
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/test-assert-cutover-ast-20261108
fix(codegen): editor surface refreshes the qlty smells configuration (#2194)
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/p7-ci-insteadof-guard-20261108
merge: integra a ponta da 0.12.0-dev
fix(rules): staticmethod rule ignores scenario-data roots (#2193)
fix(types): annotate p.\* and remove in-place mutation in infra mutable state (#2181)
fix(types): annotate instances by protocol (model-annotation-to-protocol rule) (#2178)
fix(codemod): staged Python view no longer hides declared physical Markdown (#2188)
fix(codegen): index namespaces holding only subpackages; defer only qualified schema
owners (#2187)
fix(rules): staticmethod rule sees a typed self parameter (#2186)
chore(deps): rope 1.15.2+dc.5 through make gen/upg (#2185)
feat(rules): declare class methods without self as staticmethod (#2184)
\[WIP\] Merge origin/0.12.0-dev into fix/gen-existing-flext-scaffold-20261108
\[WIP\] Merge origin/0.12.0-dev into fix/rope-dc5-pin-20261107
fix(cutover): read model protocol routes from the workspace session (#2183)
Merge 0.12.0-dev into fix/semantic-routes-di-20261108
fix(codemod,deps): consumer make fix/mod crashes (FlextCliUtilities.Infra, absent
candidate bytes, data-dir naming) (#2182)
merge: integrate tip 92ce860ccd into ci pyrefly sweep
merge: integrate 0.12.0-dev tip
fix(infra): break semantic cutover import cycle (ENFORCE-051) (#2180)
Merge origin/0.12.0-dev into cutover branch
fix(infra): flext-infra lint gate to 0 findings (#2179)
On fix/pyrefly-sweep-20261107: wip-pyrefly-sweep-dirty
On fix/pyrefly-sweep-20261107: wip-pyrefly-sweep-dirty
Merge 0.12.0-dev into fix/pyrefly-sweep-20261107
fix(codegen): open each lazy-init member snapshot with its own member root (#2176)
fix(tests): admit tests on the receipt the project's own check wrote (#2177)
fix(codegen): keep scenario-data roots out of the staged-file check hook (#2175)
Merge 0.12.0-dev into fix/hook-scenario-exclude-20261107
fix(check): runtime-integrity fails when uv.lock is stale against its manifest (#2174)
\[WIP\] Merge origin/0.12.0-dev into fix/upg-manifest-drift-20261107
Land upload-20261007 into 0.12.0-dev (2026-11-07 convergence) (#2173)
Land upload-20261007 into 0.12.0-dev (2026-11-07 convergence) (#2172)
merge fix/gen-removal-20261107 (bd71341c, qlty generated facades) into upload-20261007
Land upload-20261007 into 0.12.0-dev (2026-11-07 convergence) (#2171)
merge fix/gen-removal-20261107 (6d7915df, flext-otcin) into upload-20261007
merge fix/layout-catalog-roots-20261105 (b33d2958) into upload-20261007 (adopted,
flext-bhvgw)
merge fix/infra-setup-lock-hygiene-20261106 (cc9b9b0b) into upload-20261007 (adopted,
flext-bhvgw)
merge fix/aihub-protocol-guard-20261106 (PR #2156) into upload-20261007
\[WIP\] merge origin/0.12.0-dev into the protocol-guard lane
fix(batch-gates): rules and selection read through their contracts (rebased) (#2170)
fix(conform): publication and repository reads use their contracts (rebased) (#2168)
fix(conform): planning produces the owned plan contract (rebased) (#2166)
fix(codemod): iteration state reads the plan contract (rebased) (#2164)
fix(batch-gates): rules and selection read through their contracts (rebased) (#2162)
fix(codemod): witnesses and iterations read through the AtomicFileState contract
(rebased) (#2160)
test(codegen): build invalid payloads through typed JSON adapters (#2157)
fix(projector): project computed fields bound through any models facade (#2155)
fix(template): strip the template newline after the rendered hook block (#2154)
fix(template): avoid the blank line at the end of the generated hook file (#2153)
fix(template): close the pre-commit hook branch before the macro ends (#2152)
fix(infra): adopt pending protocol/tooling fixes (mixins, regular packages, alias guard)
(#2151)
fix(rope): restore runtime-evaluated base inventory removed by the formats commit
(#2150)
fix(projector): guard relative import modules before prefix matching (#2149)
fix: owned rope spec and typed artifact derivation (#2148)
fix(deps-gate): scan and issue collection keep the protocol contracts (#2147)
fix(duplicate-apply): read clone sides through the typed jscpd contract (#2146)
fix(workspace): spec keeps protocol contracts with owning model schemas (#2145)
fix(sweep): owned evidence keeps protocol contracts; lint snapshots validate through the
model (#2144)
fix(contexts): Makefile render spec keeps protocol contracts with owning schemas (#2143)
fix(contexts): render inputs keep the protocol contract with the owning model schema
(#2142)
fix(projector): owned render contracts and native source capabilities (#2141)
fix(projector): narrow Rope consumers to their native contracts (#2140)
fix(protocols): capitalized model fields are read-only contracts (#2139)
fix(census): an inherited namespace never competes with its declaring owner (#2117)
Merge branch '0.12.0-dev' into preserve/fix/census-inherited-owner-20261101
fix(codemod): render provider export utilities for module-object reads (#2128)
fix(markdown): rumdl single engine, canonical config, concurrent generation (#2122)
Upload 20261007 (#2138)
Merge branch '0.12.0-dev' into fix/markdown-rumdl-20261104
Merge branch '0.12.0-dev' into fix/module-object-provider-exports-20261105
feat(tooling): allow Pydantic schema hooks as contract dunders (#2137)
fix(codemod): owned semantic plans and model-boundary witness (#2136)
fix(codemod): narrow duplicate cure plans through their models (#2135)
fix(typing): reference the flattened DepsToml protocol family (#2134)
fix(typing): mutable observation context uses its owned model (#2133)
fix(ci): align bootstrap submodules to the recorded commit, not a retired branch (#2132)
fix(refactor): contract owner resolution + CI-owned gate (#2123)
\[WIP\] merge origin/upload-20261007 95239a9220 into infra-setup-lock-hygiene lane
\[WIP\] merge origin/upload-20261007 7f145ca341 into infra-setup-lock-hygiene lane
Merge branch 'wip/sweep-preserve/smells-git-inventory-20261105-969abf94' into
upload-20261007
Merge branch 'wip/sweep-preserve/flext-infra-567f0d40' into upload-20261007
Merge branch 'wip/sweep-preserve/diagnostic-path-exception-20261101-874f0aef' into
upload-20261007
Merge branch
'preserve/flext-infra/flext-infra-worktrees\_pytest-enforcement-plugin-20261026-20261102'
into upload-20261007
Merge branch
'preserve/flext-infra/flext-infra-worktrees\_diagnostic-path-exception-20261101-20261102'
into upload-20261007
Merge branch 'fix/smells-git-inventory-20261105' into upload-20261007
Merge branch 'fix/root-rope-single-pin-20261031' into upload-20261007
Merge branch 'fix/model-field-reception-all-positions-20261105' into upload-20261007
Merge branch 'fix/jscpd-semantic-bge-m3-20261105' into upload-20261007
Merge branch 'fix/incident-20261101' into upload-20261007
Merge branch 'fix/formats-sweep-repair-20261105' into upload-20261007
Merge branch 'fix/facade-native-owner-20261101' into upload-20261007
Merge branch 'b1c-dump-unpack-20261105' into upload-20261007
Merge remote-tracking branch 'refs/remotes/origin/upload-20261007' into upload-20261007
fix(codemod): package export utilities read the workspace export facts (#2130)
{"retained\_commits":\[\],"head\_entries":\[\],"repo\_root":"/home/marlonsc/flext-infra-worktrees/smells-git-inventory-20261105","common\_dir":"/home/marlonsc/flext/.git/modules/flext-infra","head":"1eb97efcca91cfabe3bcfccb3451ef73bfef1eaa","branch":"fix/smells-git-inventory-20261105","paths":\[".flext/.venv.lifecycle.lock",".flext/.venv.setup.lock"\],"index\_entries":\[\],"files":\[{"path":".flext/.venv.lifecycle.lock","mode":"100644","permissions":420,"oid":"e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"},{"path":".flext/.venv.setup.lock","mode":"100644","permissions":420,"oid":"e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"}\]}
{"retained\_commits":\[\],"head\_entries":\[{"path":"docs/guides/csv-campaigns.md","mode":"100644","oid":"fed50771763663314778cde56c1543d7f6349680"},{"path":"docs/guides/execution-context.md","mode":"100644","oid":"b39efdf159559d81760e2dcb8df4b8c6f058869c"},{"path":"docs/guides/model-fields-migration.md","mode":"100644","oid":"6c5a3de4e46ca8da2accebcef59b044721887e0e"},{"path":"docs/guides/plan-collection.md","mode":"100644","oid":"3c45aea567466a950361a9c3f66488520b8c2e4d"},{"path":"docs/guides/using-flext-core.md","mode":"100644","oid":"1bbc17820a418a6ec87d3deaed6cbf83d83d059f"},{"path":"docs/guides/using-flext-tests.md","mode":"100644","oid":"32e3307cb284cb2eab2f53f9b6fe02f8b0efc4e9"}\],"repo\_root":"/home/marlonsc/flext-infra-worktrees/diagnostic-path-exception-20261101","common\_dir":"/home/marlonsc/flext/.git/modules/flext-infra","head":"08d5d0f5579b9b26f2804270291a38c8b0451000","branch":"fix/diagnostic-path-exception-20261101","paths":\["docs/guides/csv-campaigns.md","docs/guides/execution-context.md","docs/guides/model-fields-migration.md","docs/guides/plan-collection.md","docs/guides/using-flext-core.md","docs/guides/using-flext-tests.md",".beads.gate.lock"\],"index\_entries":\[{"path":"docs/guides/csv-campaigns.md","mode":"100644","oid":"fed50771763663314778cde56c1543d7f6349680"},{"path":"docs/guides/execution-context.md","mode":"100644","oid":"b39efdf159559d81760e2dcb8df4b8c6f058869c"},{"path":"docs/guides/model-fields-migration.md","mode":"100644","oid":"6c5a3de4e46ca8da2accebcef59b044721887e0e"},{"path":"docs/guides/plan-collection.md","mode":"100644","oid":"3c45aea567466a950361a9c3f66488520b8c2e4d"},{"path":"docs/guides/using-flext-core.md","mode":"100644","oid":"1bbc17820a418a6ec87d3deaed6cbf83d83d059f"},{"path":"docs/guides/using-flext-tests.md","mode":"100644","oid":"32e3307cb284cb2eab2f53f9b6fe02f8b0efc4e9"}\],"files":\[{"path":".beads.gate.lock","mode":"100644","permissions":384,"oid":"e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"},{"path":"docs/guides/csv-campaigns.md","mode":"100644","permissions":420,"oid":"04c342ed33078ddfe6ff65614a044aa0d88ee6b9"},{"path":"docs/guides/execution-context.md","mode":"100644","permissions":420,"oid":"629e6059212243261e63544f48c1e524ad86cb82"},{"path":"docs/guides/model-fields-migration.md","mode":"100644","permissions":420,"oid":"3f462b8a3fb681ebf60cc04a35941c518188f2ee"},{"path":"docs/guides/plan-collection.md","mode":"100644","permissions":420,"oid":"55e06c74c3140c0426a7728e491532fa263a666c"},{"path":"docs/guides/using-flext-core.md","mode":"100644","permissions":420,"oid":"6d580cfc649c111aba9cb3996ec33fddce9ab918"},{"path":"docs/guides/using-flext-tests.md","mode":"100644","permissions":420,"oid":"84ab904a3119e0eea97668904bc6d37d7db9036c"}\]}
{"retained\_commits":\[\],"head\_entries":\[{"path":"src/flext\_infra/\_utilities/\_codemod/native\_package\_utilities.py","mode":"100644","oid":"f30ca24001043c73bc9c71403e888a51779d9443"},{"path":"src/flext\_infra/templates/project/base/.pre-commit-config.yaml.j2","mode":"100644","oid":"88088848f19705dab647b7c6b2038839f3ec8861"}\],"repo\_root":"/home/marlonsc/flext/flext-infra","common\_dir":"/home/marlonsc/flext/.git/modules/flext-infra","head":"e2a3577af05dbfaf6f030fdb70b14d65c7f496dd","branch":"upload-20261007","paths":\["src/flext\_infra/\_utilities/\_codemod/native\_package\_utilities.py","src/flext\_infra/templates/project/base/.pre-commit-config.yaml.j2"\],"index\_entries":\[{"path":"src/flext\_infra/\_utilities/\_codemod/native\_package\_utilities.py","mode":"100644","oid":"857c09521350e06bb0153fd94d61cbfc5e1e1f61"},{"path":"src/flext\_infra/templates/project/base/.pre-commit-config.yaml.j2","mode":"100644","oid":"88088848f19705dab647b7c6b2038839f3ec8861"}\],"files":\[{"path":"src/flext\_infra/\_utilities/\_codemod/native\_package\_utilities.py","mode":"100644","permissions":420,"oid":"1aab01ace7c81ea31e482df14c71089280c2019e"},{"path":"src/flext\_infra/templates/project/base/.pre-commit-config.yaml.j2","mode":"100644","permissions":420,"oid":"bf8ebf09fc33f483c76fb3100a16263a4fd574e8"}\]}
\[WIP\] merge origin/upload-20261007 (798e375c90, #2126 fresh-import ContextT) into the
ENFORCE-003 engine lane
Merge PR #2126: keep PEP 695 parameters in the cross-module probe rebuild
(operator-authorized admin merge)
\[WIP\] merge origin/upload-20261007 (c9655c4e) into the ENFORCE-003 engine lane
Merge PR #2125: keep machine-local Mise overrides out of locked installs (algar-7n4j)
Merge PR #2124: keep protocol mirrors from importing their own holder (algar-n1cp)
merge: integrate remote upload-20261007
Merge branch '0.12.0-dev' into upload-20261007
Merge branch 'upload-20261007' into 0.12.0-dev
fix(infra): stabilize and integrate upload-20261007 (#2107)
Merge remote-tracking branch 'refs/remotes/origin/upload-20261007' into upload-20261007
fix(templates): conftest bootstrap runs in a pytest\_configure hook (#2121)
fix(rules): ban-runtime-alias-rebind no longer misreads a literal \_\_all\_\_ (#2120)
fix(codegen): every projected protocol member ends in the stub (#2119)
Merge commit 'e820be244dc397d36ebc7b2a742d66b5debbc95a' into upload-20261007
fix(codegen): protocol mirrors stop at models another package declares (#2118)
\[WIP\] merge upload-20261007 into fix/rope-dc11-pin-20261101
fix(infra): law-A reroutes, public codemod loop package, tests on public owners (#2115)
\[WIP\] merge upload-20261007 (#2116) into primary-forward lane
Merge origin/upload-20261007 into lane
Merge pull request #2116: restore boot on upload; docs metadata scope; fixtures never
analyzed
Merge origin/upload-20261007 into lane
\[WIP\] merge upload-20261007 into fix/rope-dc11-pin-20261101
Merge remote-tracking branch 'origin/upload-20261007' into upload-20261007
fix(facade): retire nominal publications a composition no longer needs (#2114)
Merge remote-tracking branch 'refs/remotes/origin/upload-20261007' into upload-20261007
fix(facade): no nominal publication for a provider a base already composes (#2113)
Merge origin/upload-20261007 into lane
Merge pull request #2112: semantic-cutover base order, declared owners, orphan skills
retirement
Merge origin/upload-20261007 into lane
Merge pull request #2108: rope fork dc.12 pin; drop dead deptry fallback and duplicate
resource helper
\[WIP\] merge upload-20261007 (7cabdd8d02) into fix/rope-dc11-pin-20261101
\[WIP\] merge origin/upload-20261007 (#2111 stale generated facade re-derives) into the
incident lane
fix(facade): a stale generated facade never blocks its own re-render (#2111)
\[WIP\] merge origin/upload-20261007 (#2110 UP040 identity) into the incident lane
fix(lint): authenticate self-named facade class publications for UP040 (#2110)
\[WIP\] merge origin/upload-20261007 (#2109 facade TypeAlias publication) into the
incident lane
fix(facade): a nominal publication recognizes its own prior rendering (#2109)
\[WIP\] merge upload-20261007 (ffe2980b98) into fix/rope-dc11-pin-20261101
\[WIP\] merge origin/upload-20261007 into the incident lane
fix(gates): adopt deptry report destination fix from the primary checkout (#2106)
merge: adopt de7aa90770 (deptry report destination) committed on the primary checkout
\[WIP\] merge upload-20261007 (56be3b3b) into fix/rope-dc11-pin-20261101
fix(facade): collision guard ignores composed namespaces; clear base lint (#2105)
fix(codegen): gen renders, mod transforms; declared facade owners; gen 891s to 69s
(#2104)
\[WIP\] merge facade-native-owner (f21e9e547c) into fix/rope-dc11-pin-20261101
\[WIP\] merge origin/upload-20261007 (5138ba449f) into facade-native-owner
\[WIP\] merge upload-20261007 into fix/rope-dc11-pin-20261101
\[WIP\] merge import-law reroute fix/incident-20261101 (6803c67580) into
facade-native-owner
\[WIP\] merge fix/facade-native-owner-20261101 (3932f6d11d): facade owner elected by
declaration; dead election members retired
Merge commit '3932f6d11d22afc43df1972a74e4328cbab6b6a2' into upload-20261007
formats
Merge commit 'd71e2b08401d00e963ec04afa799ffe4e2fabe09' into upload-20261007
Merge commit '18a5b22b0b3479766f75493a83b85d277230d6a3' into upload-20261007
Merge commit '08d5d0f5579b9b26f2804270291a38c8b0451000' into upload-20261007
Merge branch 'fix/facade-native-owner-20261101' into upload-20261007
\[WIP\] merge rope fork reference fix (5f7c97995e)
\[WIP\] merge fix/rope-fork-reference-20261101 (5f7c97995e): every rope requirement line
carries the override's fork reference
\[WIP\] merge fix/gen-pure-projection-20261101 (d54233d849): pure-projection gen, facade
publication collapse, declared protocol mirrors
\[WIP\] merge import-law lane fix/incident-20261101 (cc33712ec5) into
gen-pure-projection
\[WIP\] merge fix/gate-concurrency-20261101 (04fe787733): gen holds the mutation lock
for plan+publish; bounded visible wait
\[WIP\] merge upload-20261007 (f8b3503083) into gate-concurrency lane
\[WIP\] merge primary upload-20261007 (f5c583792f) into the integration line
\[WIP\] merge origin/upload-20261007 (1c24f0e2fc) into the integration line
\[WIP\] merge fix/fleet-gaps-census-20261101 (8386733383) into upload-20261007
\[WIP\] merge dc-recon lane fix/integrate-upload-20261007 (6f76f39c4a) into
upload-20261007
\[WIP\] merge integration lane fix/integrate-upload-20261007 (9168832f47)
\[WIP\] merge origin/upload-20261007 into 0.12.0-dev (operator decision 2026-10-31)
fix(import-law): unnamed installed provider resolves natively at the boundary (#2102)
fix(rope): unnamed installed provider contributes no lazy bindings (#2101)
fix(setup): bootstrap FLEXT via uv pip, sem re-resolução (overlay --no-deps) (#2100)
Upload 20261007 (#2099)
Upload 20261007 (#2098)
\[WIP\] upload-20261007: joint plan flext-1engx integration (#2095)
Merge commit '675ca644430b78b8095d5889097060bc885239df' into upload-20261007
Merge remote-tracking branch 'refs/remotes/origin/0.12.0-dev' into upload-20261007
Merge branch '0.12.0-dev' into upload-20261007
Cadi 20261024 (#2096)
Merge branch '0.12.0-dev' into cadi-20261024
\[WIP\] setup: install the declared Git hook stages with prek (#2093)
\[WIP\] merge cadi-20261024 (CA/DI lane) into upload-20261007
\[WIP\] merge pydantic-max-20261024 (flext-infra)
\[WIP\] merge origin/upload-20261007 into cadi-20261024 (adopt concurrent infra work)
\[WIP\] merge upload-20261007 infra checkpoint faf09f9c2 into pydantic-max-20261024
\[WIP\] merge origin/upload-20261007 into cadi-20261024 (adopt published infra work)
\[WIP\] merge pydantic-max-20261024: t.Port field wrappers, hoist-optional-out-of-port
rule
\[WIP\] merge flext-infra upload-20261007 (4a8adf43) into pydantic-max-20261024
\[WIP\] merge pydantic-max-20261024: native setup path, unlocked mise install,
sync-environment removal
\[WIP\] merge pydantic lane: exterminate mise role lock writer
\[WIP\] merge flext-infra upload-20261007 (edd49eb7) into pydantic-max-20261024
Merge pydantic-max-20261024: setup bootstraps from frozen locks
\[WIP\] merge \~/flext upload-20261007 into pydantic-max-20261024
upload-20261007: member-lane identity fixes (lane migration); upg/gen perf follow-ups
(#2094)
merge: adopt 0.12.0-dev after #2092 landed
Stabilize typed codegen and native validation on upload integration lane (#2092)
Merge commit 'ae0ce21631b507243bc8c636a37e38aa38264d8b' into upload-20261007
Upload 20261007 (#2091)
fix: update flext-core pin to latest integrated SHA (#2090)
fix: publish pending flext-infra changes (coalescing + security remediation) (#2089)
fix: coalesce directory observation and security remediation (#2088)
Merge branch '0.12.0-dev' of github.com:flext-sh/flext-infra into 0.12.0-dev
Merge branch 'refs/heads/upload-20261007' into 0.12.0-dev
fix: apply security remediation and coalesce directory observation (#2087)
fix: coalesce directory observation in generation pipeline (#2086)
Upload 20261007 (#2085)
Merge remote-tracking branch 'origin/0.12.0-dev' into upload-20261007
chore(docs-batch-publication-20261013): preserve fix/docs-batch-publi… (#2081)
chore(projections-4pt43): preserve fix/projections-4pt43 changes acro… (#2082)
Merge branch '0.12.0-dev' into fix/projections-4pt43
Merge branch '0.12.0-dev' into fix/docs-batch-publication-20261013
Fix/infra test green 20261017 (#2079)
Merge branch '0.12.0-dev' into fix/infra-test-green-20261017
Upload 20261007 (#2084)
fixes
Merge commit '50d53b094b4904cbdb0e992286469079d1115abb' into upload-20261007
Merge commit 'b4002965dec418486cc8c229c367441501e2115d' into upload-20261007
\[WIP\] refactor(workspace): bring environment\_provenance under the loc… (#2083)
wip (#2080)
fix(integration): merge the stabilization surgery onto 0.12.0-dev (#2077)
Fix/gate cures adopt 20261017 (#2078)
Merge branch '0.12.0-dev' into fix/gate-cures-adopt-20261017
Upload 20261007 (#2075)
Merge commit 'bf5ae75da17ea5308f002811d39b7a23594a3fa1' into upload-20261007
wip
Merge remote-tracking branch 'refs/remotes/origin/upload-20261007' into
fix/pin-rule-yaml-duplicate-key
Merge the stabilization surgery onto integration (bandit src-only in CI, atomic-root,
batch scan, mise scope)
Merge commit '23d5ddc8175f172fcddc6da0b9833c317dedf10c' into upload-20261007
Merge remote-tracking branch 'refs/remotes/origin/upload-20261007' into
fix/gate-cures-adopt-20261017
Merge commit '8813979d96d24a31f8cbcc5f9d779846f16ed5b0' into upload-20261007
Merge commit '05ecb63ee736a0469db0ce15c79006fb3a38b112' into upload-20261007
release: bandit gate honors the src-only audit contract in check\_files (#2074)
release: config\_files composes inherited cli elections under infra authority (#2073)
Upload 20261007 (#2072)
merge: adopt published workspace fixes for native consumer qualification
merge: adopt native writer eligibility and public behavior regressions
\[WIP\] Adopt the published shared rule and capture repairs
merge: adopt public Rope consumer contracts and native regressions
\[WIP\] Adopt the published recovery candidate for SDK qualification
merge: adopt native relative Rope lookup and current captured topology contracts
merge: adopt promoted integration with authenticated publication and declared source
line
\[WIP\] Adopt the current integrated Infra repairs
Fix/infra dedup 20261017 (#2069)
Fix/infra loc cap 20261017 (#2068)
Merge branch '0.12.0-dev' into fix/infra-dedup-20261017
\[WIP\] fix(check): cure census, deps and lint shares on upload 9315ff4 (#2067)
Merge branch '0.12.0-dev' into fix/upload-check-share-20261017
Upload 20261007 (#2065)
Keep one gate catalog and preserve native import ownership (#2066)
\[WIP\] integrate generated import and native encoding owner corrections
\[WIP\] adopt qualified gate registry and generation source history
\[WIP\] adopt current integration preserving typed generation recovery
\[WIP\] adopt integration and exterminate the obsolete gate registry
\[WIP\] adopt current integration recovery and preserved CI history
Unify native scanner inputs and preserve typed generation contracts (#2061)
Merge branch 'upload-20261007' into codex/declared-sources-and-scheduling-20261016
Preserve City service-operation fixes for semantic adoption (#2063)
Merge branch 'upload-20261007' into codex/preserve-city-infra-20261017
chore(integration): reconcile preserved Make CI merge history (#2062)
Merge branch 'upload-20261007' into fix/make-ci-upload-20261013
Codex/declared sources and scheduling 20261016 (#2064)
\[WIP\] adopt preserved integration history fe8cc3da2e
chore(integration): preserve superseded projection history
\[WIP\] adopt coordinated runtime recovery e2e3c21e44
chore(integration): reconcile preserved checkout history
\[WIP\] preserve unfinished Make CI merge and topology inputs
merge: adopt native module consumer integration with source recovery
fix(runtime): wire native module consumers through typed boundaries (#2060)
Merge integrated runtime and provenance repairs into stabilization
Adopt reviewed native provenance and journal integration fixes
fix(codegen): staging intents keep the live producer reference (#2059)
chore(deps): resolve the flext family on upload-20261007 through declared overrides
(#2058)
fix(deps): verify native tool modes and metadata ownership (#2057)
Reconcile reviewed historical flext-infra checkpoint 7b0859265023
Reconcile reviewed historical flext-infra checkpoint f708f8c5738f
Reconcile reviewed historical flext-infra checkpoint ad7f06e0f8f7
merge: preserve reviewed historical workspace projections
merge: preserve reviewed historical workspace projections
merge: preserve reviewed historical workspace projections
merge: preserve reviewed historical workspace projections
merge: preserve reviewed historical workspace projections
merge: preserve reviewed historical workspace projections
merge: preserve reviewed historical workspace projections
\[WIP\] Merge origin/fix/infra-dev-green-20261016 (family overrides) into the loc-cap
lane
\[WIP\] Merge origin/upload-20261007 (2521193b01) into the infra campaign lane
\[WIP\] Merge fix/infra-family-overrides-20261017 (ec78236) into the infra campaign lane
build(gen): integrate the recorded CI generation fixed point
fix(infra): relock flext-cli so make setup resolves the directory query API (#2055)
Merge integration upload-20261007 into toolchain stabilization
\[WIP\] merge origin/fix/infra-dev-green-20261016 into fix/infra-test-green-20261017
\[WIP\] Merge origin/fix/infra-dev-green-20261016 into the loc-cap lane
\[WIP\] Merge origin/fix/infra-dev-green-20261016 into the dedup lane
\[WIP\] Merge origin/upload-20261007 (9315ff4fef) into the infra campaign lane
Merge commit '233f232c005e8e447d173b2baaf5eac524ccfd4b' into upload-20261007
\[WIP\] Merge origin/0.12.0-dev (ea349e9da0, #2054) into the infra campaign lane
Merge commit 'f43d52023aa5222e8ca8b339d6c9a334946afd83' into upload-20261007
Merge commit 'ea349e9da0befe4849d2cd1b561dc67323ecceda' into upload-20261007
Integrate current Infra runtime, Make lifecycle and native proof contracts (#2054)
Merge PR #2053: restore the project-owned CI custom steps (no new failure vs red upload
base; operator-directed integration)
Merge branch '0.12.0-dev' into upload-20261007
Merge upload-20261007 (dea1d3fd9d) into fix/ci-mise-shims-20261017
Merge commit '792913dbca793f9b2495207899db7ac732a6db35' into upload-20261007
Merge commit '8da7d675e99cd29bc053f3813085585c545cf684' into upload-20261007
Merge commit 'ce5c3647586c2dbe373fc5d145c78927a8d53243' into upload-20261007
\[WIP\] merge upload-20261007 into #2051 before the relock
\[WIP\] Merge origin/upload-20261007 (bea7db98bd, #2049) into the infra campaign lane
Merge commit '3168b408492b1ff728fea33a241d09c0eac6fef9' into upload-20261007
\[WIP\] merge current upload and retain public config-layer coverage
Merge commit '94942c105acb7233adf6fc0e3249104d59a1c717' into upload-20261007
wip
\[WIP\] merge existing campaign repairs and remove duplicate export predicate
wip
\[WIP\] merge upload and adopt native constant wiring
\[WIP\] Merge flext-infra#2051 head (7b37fb92a9) into the infra campaign lane
\[WIP\] Merge origin/upload-20261007 (210af3b740) into the infra campaign lane
\[WIP\] merge upload-20261007 (fbbd53eb0b) into the rope engine lane
\[WIP\] Merge origin/upload-20261007 (0a7091376f, #2050) into the infra campaign lane
merge: adopt published upgrade and generation fixes into upload
\[WIP\] Merge rope snapshot-deps lane (b77c8a7) into the infra campaign lane
\[WIP\] Merge origin/upload-20261007 (ce6731d4) into the infra campaign lane
Merge PR #2050: upg resolves views before install; facade planning never targets the
checkout .venv (D33: operator-authorized, base CI red)
\[WIP\] merge upload-20261007 into the rope engine lane: adopt upload's import
extraction, retire my superseded builders
\[WIP\] adopt integrated native generation and toolchain repairs
\[WIP\] Merge upload-20261007 (ce6731d44e) into fix/upg-lock-first-20261016
Merge commit '63e776d6a26dfc42ab039904da10e63865b5bb91' into upload-20261007
Merge commit '646467bff62151ae92503ad2ebd79ca6e7ac483d' into upload-20261007
Merge commit '6c4f2af066538a80e7798cfb071fafb0b08271ba' into upload-20261007
Merge commit 'd34ca3afb55e6d43b2ddb39037b8d3dd92ce2270' into upload-20261007
\[WIP\] Merge fix/infra-dev-green-20261016--rope-overlay (c0471f8): packaged rope
contracts universal-only, repository overlay
\[WIP\] Merge origin/upload-20261007 (f8b6439559) into fix/infra-dev-green-20261016
\[WIP\] adopt integrated generation recovery and shared contract corrections
fixes
\[WIP\] adopt the published producer recovery and validation owners
\[WIP\] merge campaign fix/infra-dev-green-20261016 into typed-factories
\[WIP\] merge upload-20261007 into typed-factories: adopt the completed producer
refactor
\[WIP\] Merge origin/upload-20261007 (7e2607f6eb) into fix/infra-dev-green-20261016
fix(infra): green campaign part 2 (flext-90pw7) (#2045)
refactor: rename methods in codegen preconditions for clarity
\[WIP\] Merge fix/integration-branch-upload-20261016 (672be57): integration branch
upload-20261007
\[WIP\] Merge fix/upload-green-20261016 (fdb8a1764b): one producer capture owner,
capture once
Merge commit '672be57d298c3c018024ffff1e480773128f538c' into upload-20261007
fix
Merge branch 'fix/infra-dev-green-20261016--census' into upload-20261007
Merge branch 'fix/infra-dev-green-20261016--loccap-src' into upload-20261007
Merge branch 'fix/infra-dev-green-20261016--loccap-tests' into upload-20261007
Merge branch 'fix/infra-dev-green-20261016--lint' into upload-20261007
Merge commit '6ac39545d86420d8e0b215087872e6f2053ed9d8' into upload-20261007
Merge commit '7c49b10534c7ac0331e2495b55d51a70e8746465' into upload-20261007
Merge commit '4c03422547f5d40bf35f8a02fda1c15a09dd6e20' into upload-20261007
\[WIP\] Merge origin/upload-20261007 (f34821c718) into fix/infra-dev-green-20261016
Merge commit '847578f67fd8a041eb0c6ebb9166fdac1531aa0b' into upload-20261007
\[WIP\] merge upload-20261007 (f34821c718): one producer capture, no import cycle
Merge origin/upload-20261007 into fix/upload-green-20261016
\[WIP\] Merge origin/upload-20261007 (b2bcbddc37) into fix/infra-dev-green-20261016
\[WIP\] Merge fix/infra-dev-green-20261016--deptry-roots (deptry scan roots from
declared packaging, algar-u9o) into the campaign
\[WIP\] Merge origin/upload-20261007 (runtime-closure provider election) into
fix/infra-dev-green-20261016
\[WIP\] merge current upload API and preserve native lazy-init planning
\[WIP\] Merge origin/upload-20261007 (operator merges) into fix/infra-dev-green-20261016
\[WIP\] adopt workflow generation and scaffold into upload workspace (flext-itpd1.8.22)
Merge fix/infra-dev-green-20261016 (facade-base cure, import-merge generator fix,
regenerated projections) into upload-20261007
\[WIP\] merge origin/upload-20261007 into the lint slice (operator: integrate on
upload-20261007)
\[WIP\] Merge origin/fix/infra-dev-green-20261016 (d718d7e088) into
fix/infra-dev-green-20261016--deptry-roots
\[WIP\] Adopt published native import proof and upload work for integration
stabilization
\[WIP\] Merge 0.12.0-dev into workflow and CI base stabilization
Merge remote-tracking branch 'origin/0.12.0-dev' into 0.12.0-dev
refactor: enhance module handling and YAML parsing across multiple files
refactor: streamline lazy initialization and enhance documentation in existing\_plan and
generated\_function modules
Merge commit '5d1d437d627842331e0450048117aac40faf3c38' into upload-20261007
Merge commit '1ee6ebf6eae1039455201dd74f064c1d0ca38858' into upload-20261007
\[WIP\] Merge origin/0.12.0-dev into fix/infra-dev-green-20261016
refactor: improve code readability and remove unused variables in multiple files
Merge commit 'd5b9eaa706ce5b2e4c53f50dbf056f91add2cf88' into upload-20261007
Merge commit '67079889560ffa740932eb1879bbebff9c270166' into upload-20261007
Merge remote-tracking branch 'origin/0.12.0-dev' into upload-20261007
Merge branch '0.12.0-dev' into fix/campaign-machinery-20261012
chore(fleet-unit-20261010): preserve feat/fleet-unit-20261010 changes… (#2039)
\[WIP\] fix(codegen): conform derives tooling from the planned lazy-init projection
(flext-90pw7) (#2044)
\[WIP\] Merge origin/0.12.0-dev into fix/infra-dev-green-20261016 (resolve #2041 to the
compiling owner)
Fix/aihub consumer blockers 20261015 (#2041)
Merge branch '0.12.0-dev' into fix/aihub-consumer-blockers-20261015
chore(oud-upload-tip-20ba-20261014): preserve test/oud-upload-tip-20b… (#2033)
Merge branch '0.12.0-dev' into feat/fleet-unit-20261010
Merge branch '0.12.0-dev' into test/oud-upload-tip-20ba-20261014
chore(codex-cache-20261012): preserve fix/cache-publication-20261012 … (#2038)
Merge branch '0.12.0-dev' into fix/cache-publication-20261012
chore(alias-identity-20261008): preserve fix/alias-identity-20261008 … (#2036)
chore(ci-root-cause-20261013): preserve fix/infra-ci-root-cause-20261… (#2037)
Merge branch '0.12.0-dev' into fix/alias-identity-20261008
chore(nsstatic-codemod-20261012): preserve fix/namespace-static-path-… (#2032)
chore(mod-family-emenda-20261013): preserve fix/mod-family-emenda-202… (#2020)
perf(workspace): native capture fits the cold-probe budget (flext-zd80z) (#2030)
fix(make): restore the attached-member upg delegation and its endif (#2031)
Merge remote-tracking branch 'origin/0.12.0-dev' into 0.12.0-dev
\[WIP\] merge origin/0.12.0-dev into the capture-budget lane
chore(text-rule-scope-20261008): preserve fix/text-rule-scope-2026100… (#2025)
Merge branch '0.12.0-dev' into fix/mod-family-emenda-20261013
chore(deps): mkdocstrings-python floor 2.0.9 (WIP) (#2023)
Fix/infra postmerge reds 20261016 (#2024)
fix(workspace): one dataclass inheritance proof; drop the linear base mirror (#2021)
Fix/native proof on 0.12 20261016 (#2015)
Merge branch '0.12.0-dev' into fix/native-proof-on-0.12-20261016
\[WIP\] merge upload-20261007 tip into the candidate-bootstrap provider… (#2014)
fix(workspace): prove dataclasses that inherit dataclass fields (#2013)
Merge branch '0.12.0-dev' into fix/fleet-converge-20261015
Fix/native proof on 0.12 20261016 (#2012)
\[WIP\] merge flext-infra 0.12.0-dev (33dd5fd77a) into the native proof lane, one owner
per concern
\[WIP\] merge: origin/0.12.0-dev (#2010, #2011) into the native-proof cures lane
\[WIP\] fix(workspace): abstract dataclass receivers and @abstractmetho… (#2011)
Merge branch '0.12.0-dev' into fix/native-proof-cures-20261016
Fix/fleet converge 20261015 (#2010)
\[WIP\] Merge origin/fix/native-proof-on-0.12-20261016 (cosmos+aihub native proof cures)
into fix/fleet-converge-20261015
\[WIP\] merge aihub native proof cures (379d349) into the native proof lane, one
implementation per cure
\[WIP\] Merge codex generated\_function WIP (63558df382, preserved from the \~/flext
primary) into fix/fleet-converge-20261015
\[WIP\] Merge origin/fix/native-proof-on-0.12-20261016 (cosmos aabafa49b1, owner
dataclass design) into fix/fleet-converge-20261015
\[WIP\] Merge origin/0.12.0-dev (upload landed as #2008, e8012a559d) into
fix/fleet-converge-20261015
\[WIP\] merge flext-infra 0.12.0-dev (e8012a559d) into the native proof lane
\[WIP\] Merge origin/fix/native-dataclass-init-proof-20261016 (cosmos 8f511329bc) into
upload-20261007
\[WIP\] merge: fix/native-proof-on-0.12-20261016 @ aabafa4 (cosmos native proof forms)
into the consumer-blockers lane
fix(release): resolve the repository-declared integration branch (#2009)
\[WIP\] merge flext-infra 0.12.0-dev (8bd2019e) into the native proof lane, adopting the
owner dataclass SDK design
\[WIP\] merge: origin/0.12.0-dev (upload landed, 8bd2019e) into the consumer-blockers
lane
merge: upload-20261007 into 0.12.0-dev (#2008)
\[WIP\] Merge origin/upload-20261007 into fix/fleet-converge-20261015
\[WIP\] merge upload-20261007 (35a382b0af, 821a0be24f) into the native proof lane,
reconciled on the owner dataclass design
Merge remote-tracking branch 'origin/fix/workspace-ci-lock-contract-20261013' into
fix/workspace-ci-lock-contract-20261013
Merge commit 'c9e1199a981530c86c7bbb8d4bb60ad40efaa157' into upload-20261007
\[WIP\] merge upload-20261007 tip into the candidate-bootstrap provider lane (D16)
Merge remote-tracking branch 'refs/remotes/origin/upload-20261007' into upload-20261007
\[WIP\] Merge origin/upload-20261007 into fix/fleet-converge-20261015
Merge commit '15bdd9da1107ba199484a499e31b8d55c4e209b6' into upload-20261007
Merge commit '893faaca027a2d5e26c62649c3c2611c16b6529b' into upload-20261007
Merge commit '112a9f3d4c36baa7ade6387220c1fce1c6a3afca' into upload-20261007
Merge remote-tracking branch 'origin/0.12.0-dev' into 0.12.0-dev
\[WIP\] Merge fix/candidate-bootstrap-workspace-20261015 (cosmos 7a96242) into
fix/fleet-converge-20261015
\[WIP\] Merge origin/hotfix/merge-admin-final-20261007 into fix/fleet-converge-20261015
(snapshot hunks; survivor wins conflicts)
\[WIP\] Merge origin/merge-admin/20261007-exec into fix/fleet-converge-20261015
(snapshot hunks; survivor wins conflicts)
Merge remote-tracking branch 'origin/upload-20261007' into
fix/candidate-bootstrap-workspace-20261015
\[WIP\] Merge origin/cure/infra-parse-20261007 into fix/fleet-converge-20261015
(snapshot hunks; survivor wins conflicts)
\[WIP\] Merge origin/fix/make-lifecycle-complete-20261013 into
fix/fleet-converge-20261015 (snapshot hunks; survivor wins conflicts)
\[WIP\] Merge origin/fix/ruff-pyrefly-20261015 into fix/fleet-converge-20261015
\[WIP\] Merge origin/upload-20261007 into fix/fleet-converge-20261015
Merge current 0.12.0-dev into HML FLEXT lane
Merge branch 'upload-20261007' into fix/ruff-pyrefly-20261015
Merge commit 'df91dd246c70cae22de5f833016bbc1efd98780a' into upload-20261007
Merge commit 'cadf83dba256a7fb153e82385da4feaa3cfdcb12' into upload-20261007
Merge branch 'upload-20261007' into fix/ruff-pyrefly-20261015
Enhance import organization in codegen and validation modules; improve readability in
test utility facade projection
Merge commit '1ebe9efc87059d15f6fa14e20a386d399f658442' into upload-20261007
Merge commit '69279edcd66163680bf770367d3162cc4b8bd196' into upload-20261007
Merge commit '4773b75eb8dc15225d3b3bd2a1ad402b627f9756' into upload-20261007
Merge commit '525ae20d29cf32c42916666ef0bbc704ecb24a90' into upload-20261007
Merge commit '856928a9aca1087b3e9ea81b1ee9cb0f85d032dd' into upload-20261007
Merge commit '060dc390dd30a781b69eeab0ca3f2d2808506426' into upload-20261007
Merge commit '819c93aedf3044c0c52ce17dc2a0b3a72af3c2e5' into upload-20261007
fix(ci): keep pull\_request runs out of the integration push group (#2003)
Merge commit '282c01fd8bc9b509872847429847e09b288526c2' into upload-20261007
Refactor code generation and publication handling
Enhance tests for FlextInfra refactoring and profiling
fix(infra): converged upg stages, upg converge activation and snapshot drift (#1991)
Merge branch '0.12.0-dev' into fix/infra-workspace-make-ci-20261013
Merge branch '0.12.0-dev' into fix/workspace-ci-lock-contract-20261013
merge: adopt integrated FLEXT current API
Merge branch '0.12.0-dev' into fix/fleet-align-20261015
merge: converge upload-20261007 (15f8c6361f7bd2891ac55f80b0f313cfd706… (#1989)
Merge branch '0.12.0-dev' into fix/fleet-align-20261015
Merge branch '0.12.0-dev' into converge/upload-20261010
fix(infra): restore native provenance and workspace lifecycle (#1985)
Merge remote-tracking branch 'origin/0.12.0-dev' into 0.12.0-dev
Merge commit '6a9d563082d9d732e53355530554d6164da2786d' into 0.12.0-dev
Merge commit 'ba70ad7edc12621e59de1034333e9e75169c2078' into 0.12.0-dev
Merge commit 'a08db9f746e735c13c74740865849a1210399591' into upload-20261007
Merge commit 'c77423c84f4fbf79466e40da6bc0693cd8c70717' into upload-20261007
Merge commit '74736bea59d3f0b353b397db77f91d70af552d86' into upload-20261007
Merge remote-tracking branch 'origin/upload-20261007' into fix/fleet-align-20261015
\[WIP\] Refresh OUD bootstrap producer to upload tip
Merge commit 'c0554d46729d14489ffef6562dd664fc8ed764f4' into upload-20261007
Merge commit 'ffcfe6382ea8c7e49862f3ceac7b65256e352988' into
fix/hml-editable-provenance-20261014
Merge commit '8ff35d6ac2289aff7bfbfaaaeecb9a34e9de225e' into upload-20261007
Refactor FlextInfraMiseArtifactsVerification and related components
\[WIP\] reconcile upload-20261007 tip with FLEXT native API fixes
\[WIP\] adopt current FLEXT producer API and preserve HML bootstrap evidence
feat: enhance editable path tests and improve package source handling
\[WIP\] Consolidate adopted codemod sources and shared contract proofs
Merge commit '8ab3eff515abe15cb182eaa3a104b4cceea78438' into upload-20261007
\[WIP\] adopt native callback alias identity repair for associated qualification
\[WIP\] converge workspace qualification with current Infra source owners
wip
\[WIP\] adopt current native reference and transaction authority owners
fix(codegen): the transaction self-serves its producer authority (#1983)
Merge commit '6d79db61eca5253102d006d39331b317c0f95990' into upload-20261007
merge: adopt the resolved provenance state (the union of both walker cures)
Merge commit 'b3e76d76f6a6e07a2602f357a96777603457e277' into upload-20261007
upload-20261007 → 0.12.0-dev: the native-reference capture + provenance series (#1982)
fix(provenance): third-party bindings admit through their executed value (#1981)
\[WIP\] integrate current provenance and publication owners
Merge current upload-20261007 provenance and codemod work into stable validation lane
fix(provenance): third-party factories admit through their installed package (#1980)
fix(provenance): the alias-supplier gate admits third-party receivers (#1979)
fix(pyproject): restore the requirements-provenance renderer to its complete state
(#1978)
fix(codemod): preserve scanner selection and binding ownership (#1976)
Merge commit '733db2a745087b97065ed73549610fc45a5492fc' into upload-20261007
Merge remote-tracking branch 'origin/0.12.0-dev' into upload-20261007
\[WIP\] preserve adopted bootstrap and credential repair history
\[WIP\] reconcile integration and qualify dependency group ownership
\[WIP\] adopt integration and preserve native runtime recovery evidence
fix(codemod): the resolved-symbol operand check names its own class constant (#1974)
fix(utilities): the semantic family type-references calls import their owner (#1973)
Upload 20261007 (#1972)
Merge commit 'db1f6d6907738916a0e84ada84415f2d452c8602' into upload-20261007
feat: enhance uv\_sources and pytest command with new dependency handling and timeout
limits
Refactor and enhance various components in the FlextInfra utilities
Merge commit '535aeb06a3863a968b24559e2d29c49f5b7865b6' into upload-20261007
Merge current upload-20261007 codemod and generation work
feat: enhance governance source handling and improve transaction journal management
merge: adopt upload tip preserving primary work
fix(codegen): mise artifacts state imports its siblings from their owners + wave fixes
(#1970)
fix(models): DeptryDiagnostic.error declares its field description (#1969)
Upload 20261007 (#1968)
fix(rope): the analyzed checkout's own barrels always join the alias map (#1967)
\[WIP\] adopt current Infra integration for CI recovery
Merge commit '0317a99b26e67c8beb6e473c1095d71ae2540166' into upload-20261007
merge: the ast-grep rules corpus duplication exclusion + the adopted 0.12.0-dev state
(#1966)
Merge remote-tracking branch 'origin/0.12.0-dev' into upload-20261007
merge: adopt current infra integration for lifecycle repair
fix(rules): message-variant rewire skips multi-line message blocks (#1965)
Merge commit '3e01704b810022161251173d63ad05b20882de6b' into upload-20261007
Merge commit 'c415378aca78536af14bbd6c5da1ff4d61f83057' into upload-20261007
\[WIP\] adopt generated native-root resolution repair
Upload 20261007 → 0.12.0-dev: generator invariant + resilience gates (#1964)
fix(tooling): resilient bootstrap + render provenance + the deps check gate (#1963)
Merge remote-tracking branch 'refs/remotes/origin/0.12.0-dev' into upload-20261007
\[WIP\] adopt generated workspace ownership repair for standalone validation
fix(codemod): identity enforcement applies to pinned sources only (#1962)
fix(codemod): installed-package evidence never reaches layout pinning (#1961)
fix(codemod): evidence-only inputs survive unpinned layouts (#1960)
fix(codemod): rope pinning covers workspace rewrite targets only (#1959)
fix(codemod): candidate admission guards destinations, not journal evidence (#1958)
merge: preserve native editable policy in the workspace candidate
merge: the policy-overlay selector cure + the adopted 0.12.0-dev state (#1957)
Merge remote-tracking branch 'origin/0.12.0-dev' into upload-20261007
Upload 20261007 → 0.12.0-dev: wave jscpd-gate + refactors (29ee9cc7f) (#1956)
Merge commit '7a4180c36928116be6fca4989cd291c6a37f5e67' into upload-20261007
merge: align runtime ownership primitive in workspace candidate
merge: adopt infra workspace lock contract candidate
Merge commit '96e63362a3da6c77aec4a441d24ee5e87fb05903' into upload-20261007
Merge commit '6a1a893ddb17526cd3a325a80a643c0646f130b2' into upload-20261007
fix(layout): gate reads the layered codegen inputs, not the config singleton (#1955)
merge: adopt current infra CI recovery inputs
fix(check): exclude package-lock.json from the duplication gate (operator-authorized)
(#1952)
Merge remote-tracking branch 'origin/0.12.0-dev' into upload-20261007
Merge branch 'fix/adopt-0120-dev-20261013' into upload-20261007
merge: relink upload-20261007 with 0.12.0-dev — exterminate committed conflict markers
(flext-yjl38) (#1953)
Merge branch 'fix/infra-ci-root-cause-20261013' into upload-20261007
merge: relink upload-20261007 with 0.12.0-dev (supersedes poisoned #1951 tree)
Merge branch 'fix/adopt-0120-dev-20261013' into upload-20261007
merge: relink upload-20261007 with advancing 0.12.0-dev tip (PR #1951) — lane reunion,
no content delta; ours resolution keeps clean files and the lane's deliberate deletions,
exterminating the committed conflict markers (flext-yjl38)
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/adopt-0120-dev-20261013
merge: reconcile infra CI recovery with 0.12.0-dev
Upload 20261007 → 0.12.0-dev: rule wave + concurrent-safe mod engine (#1951)
merge: relink upload-20261007 with advancing tip adda89ff9 (no content delta; lane
reunion)
merge: adopt 0.12.0-dev (test-reality scoping, import-law fixes) onto upload-20261007
rule wave
merge(fleet-automation): integrate the advancing tip
Merge remote-tracking branch 'refs/remotes/origin/upload-20261007' into upload-20261007
merge(fleet-automation): integrate the advancing tip
fix(rules): scope the test-reality detectors to their genuine targets (#1950)
fix(import-law): base-less class bodies are typing-only under deferred annotations
(#1949)
fix(workspace): standalone self-root is its environment's editable install (#1948)
fix(api): restore the constants letter the import prune dropped — make mod unbroken
(#1947)
fixes (#1946)
Repair workspace automation, runtime configuration and original CI evidence (#1943)
merge(fleet-automation): integrate the advancing tip
Merge remote-tracking branch 'origin/0.12.0-dev' into upload-20261007
Merge remote-tracking branch 'origin/upload-20261007' into upload-20261007
merge(fleet-automation): the duplicate-consolidation phase (trivial-tier auto-cure +
structural plans)
feat: fleet automation defaults — strict enforcement, cross-project duplication,
member-scoped rollout (#1944)
merge(fleet-automation): integrate the advancing tip
Merge commit 'ed36ec4010f25deb78e84473dd019a9d68e511d1' into upload-20261007
Merge commit 'b13899659570eaf13f754c87ec42f6b26e9281bd' into upload-20261007
merge(fleet-automation): integrate the advancing tip (per-letter rules generation)
merge(fleet-automation): per-letter facade-self-import scope (cruze is legal assembly)
Merge remote-tracking branch 'refs/remotes/origin/upload-20261007' into upload-20261007
merge(fleet-automation): the three detection rules (facade-self-import gate, test
source-text and production-ast probes)
merge(fleet-automation): integrate the advancing upload tip
merge(fleet-automation): integrate the advanced upload tip with the census cycle cure
merge origin upload-20261007 before pushing gitlink verdict
merge(fleet-automation): integrate the upload-20261007 fixes with the rope
external-binding cure
fix: preserve generation gains and restore strict import boundaries (#1942)
Refactor pipeline stages to utilize result types for error handling
fix(codegen): fail loud when a managed template render produces no content (#1941)
Land the config/ wheel include restoration (#1940)
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/campaign-machinery-20261012
Upload 20261007 (#1939)
Merge remote-tracking branch 'origin/0.12.0-dev' into upload-20261007
fix(codegen): script-verb discovery stops emitting the dropped requires\_apply field
(#1938)
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/script-verb-requires-apply-20261009
Upload 20261007 (#1937)
Merge branch '0.12.0-dev' into upload-20261007
Integrate/f60h2 20261010 (#1936)
Merge branch '0.12.0-dev' into integrate/f60h2-20261010
fix: stabilize runner, generation and semantic owner boundaries (#1933)
Union/20261010 (#1935)
Merge commit 'f97b6370cdffc46d1cca5fa54f3153d7137e36c9' into upload-20261007
fix(gates,codemod): the empty-factory retirement — unblock every consumer's make setup
(#1934)
Merge commit '0bbf7538589d494b9f1d64d7c96f29550d6f3673' into upload-20261007
merge: absorb 0.12.0-dev's parallel evolution — the tip's landed type-debt cures and
test evolutions win where the adopted WIP carried no empty-migration intent; the
stricter markdown verdict survives
Merge branch 'upload-20261007' into fix/empty-factory-migration
Merge commit 'c829557ad601559d6e18459359ccbb0085514b41' into upload-20261007
Merge commit '356faff4297534c970287f42b4ac3fda519fc4eb' into upload-20261007
Merge commit '0cab666bbe2988247fcdd762699966ff0b82692f' into upload-20261007
Merge commit '79beb210e9e1446e2a84cc48011654dc35687252' into upload-20261007
\[WIP\] merge: integrate published generator fixes with strict runner contracts
\[WIP\] merge: reconcile integrated suppliers and regenerate owned artifacts
fix(templates,codegen): cure the grand-union collateral — conflict markers,
mise\_locked, facade scanner, export collector (#1932)
Merge commit 'e74d050af55afaecc39b57cde7eab8a02c2bbc5f' into upload-20261007
Merge commit 'b0854be6f2d1c133e4c909439bdcda88f9979f9b' into upload-20261007
Merge remote-tracking branch 'origin/0.12.0-dev' into upload-20261007
merge: absorb the grand union (13 lanes, cycles 8-11) and the #1931 lane landing from
0.12.0-dev
Integrate/f60h2 20261010 (#1931)
Merge branch '0.12.0-dev' into integrate/f60h2-20261010
fix(stabilization): plain self in the conform partials; typed receipt… (#1930)
Merge branch '0.12.0-dev' into fix/check-findings-20260921
Upload 20261007 (#1929)
\[WIP\] merge: adopt supplier union and repair generated runtime contracts
Merge commit '366f99ba9128ef9162326169c4296186d0b4da52' into upload-20261007
Merge commit '82782206c54f7cb06d4d090e3356c96158125d6a' into upload-20261007
Merge commit 'fa9acb0d6a81c2ff0b692d0a6b4de831dd1619cc' into upload-20261007
grand union: 13 lanes absorvidas + curas de estabilidade (ciclos 1-11) (#1928)
merge: absorb the concurrent 0.12.0-dev landings into the grand union
merge: bring wip/fleet-unit-tipcure-alt-20261010 into the f60h2 integration lane (city
consolidation)
merge: bring fix/testmon-cache-hit-20261010 into the f60h2 integration lane (city
consolidation)
merge: bring fix/envrc-host-tools-20261010 into the f60h2 integration lane (city
consolidation)
merge: bring feat/fleet-unit-20261010 into the f60h2 integration lane (city
consolidation)
merge: bring fix/quality-di-20261010 into the f60h2 integration lane (city
consolidation)
merge: bring fix/empty-default-20261010 into the f60h2 integration lane (city
consolidation)
merge: bring fix/mod-relocation-finding-20261009 tip into the f60h2 integration lane
merge: bring feat/import-law-tier-aliases-20261010 into the f60h2 integration lane
merge: bring wip/tip-green-findings-20261010 into the f60h2 integration lane (city
consolidation)
Fix/envrc host tools 20261010 (#1927)
Merge branch '0.12.0-dev' into fix/envrc-host-tools-20261010
fix(codemod): elect text rules by distribution before source inventory (#1926)
\[WIP\] preserve: alternative tip cures superseded by 9d8678403 (gate-b… (#1925)
\[WIP\] merge: absorb 0.12.0-dev 04ba202ca into testmon/test-full lane
\[WIP\] merge: absorb 0.12.0-dev (#1923 sweep) into tip-green pass 2
perf(workspace): gen/mod/fix as one fleet unit; cure dev CI reds (#1924)
Upload 20261007 (#1923)
\[WIP\] merge: absorb upload-20261007 tip
Merge commit 'b7a879dc9a1c7ba6031322cf002952028b2239ba' into upload-20261007
\[WIP\] merge: absorb 0.12.0-dev and upload-20261007 tips
Merge commit 'd4920ea511f98884fe29071d455bc4b5bd764e80' into upload-20261007
Merge commit '01f57818290d4bc9d7b7719468ea352a55a89585' into upload-20261007
build(config): include scripts in ruff source paths
Merge commit '2839d04cd20945adbf75fbc58382b873506b0a6f' into upload-20261007
Merge commit 'd8f05a2a6b385e61752c48a1a6b84c1ddf81e768' into upload-20261007
Merge commit '654a7fbd74539d55c97acaa20e913dc78624976f' into upload-20261007
\[WIP\] merge origin/0.12.0-dev into fix/empty-default-20261010
\[WIP\] merge: adopt published infra contracts into quality ownership lane
\[WIP\] merge: absorb 0.12.0-dev into fleet-unit
\[WIP\] merge: absorb upload-20261007 into fleet-unit
merge: converge upload-20261007 (15f8c6361f7bd2891ac55f80b0f313cfd706f82c) into
0.12.0-dev (flext-sh/flext#506)
merge: absorb 0.12.0-dev (#1918) before the mypy cache isolation PR
Merge commit '3cf2d88e3640e1dbfecd518abec50a5a7eeca461' into upload-20261007
Upload 20261007 (#1919)
\[WIP\] merge: adopt tip-green lane (#1916) into fleet-unit
Merge commit '5a3ad9fe7851dc528ad8e6ea7e4f733937cc89b8' into upload-20261007
Merge commit 'd69b055e899f8165da6c901ebfa743d8acfd66d8' into upload-20261007
Merge commit '871c3d92e295a070d924ffe74fcab937432889da' into upload-20261007
Merge origin/0.12.0-dev into fix/mod-relocation-finding-20261009
merge: absorb 0.12.0-dev (#1916) into the envrc host-tools lane
fix(gates): flext-infra 0.12.0-dev green again after #1909 (#1916)
Merge commit 'a9934100a7c1a33f44e44d42cc8f3b1fa1162ee7' into upload-20261007
Merge commit '2cc6e0d46cd1d51833dc467b601e56da120a23a2' into upload-20261007
Merge commit 'f4b93473bcac107a045c9570224ac6fcb0666364' into upload-20261007
Merge commit '834f963e5f294ce7b58418f6b712374ab8cc12fa' into upload-20261007
Merge commit 'a99bd2036b2de0ae784cdaea44b1a87979b75c2f' into upload-20261007
Merge commit '9654abbb91d71657cb81ba481b1352867e2a1803' into upload-20261007
Merge commit '6adbfa34fa249550a14b4f67fd82e01e37c9935b' into upload-20261007
Merge commit 'faf8a3bcd936aa75e7d5490ca2fed723448d1f99' into upload-20261007
Merge commit '4e033812649c2db8f0d2fc5c608544295199b058' into upload-20261007
Merge commit '67970403bd82e6baffcc283e9ad61cfdac1d39a5' into upload-20261007
Merge commit 'da4b74b1a16739a7c98bf2f2a653488392bbb008' into upload-20261007
merge: adopt the live dev-import-green finishing work (verify-lane route pair, fail-loud
import-state owner, rope\_source\_bases retirement, lane test rename)
merge: adopt #1905's newest tip fea876ea8 into the f60h2 integration lane
\[WIP\] merge origin/0.12.0-dev into the fleet-unit lane
\[WIP\] merge origin/0.12.0-dev (#1909 upload, #1912 conform-stash cure) into
dev-import-green
merge: land origin/fix/import-law-upload-20261009 residue into the f60h2 integration
lane (REPLANO 3 straggler sweep)
merge: land fix/rebuild-dev-tooling-20261009 into the f60h2 integration lane (REPLANO 3
straggler sweep)
merge: land fix/stubs-by-reality-tip-20261009 into the f60h2 integration lane (REPLANO 3
straggler sweep)
merge: land fix/dev-setup-gen-upg-20261009 into the f60h2 integration lane (REPLANO 3
straggler sweep)
merge: absorb 0.12.0-dev 54e34967d (#1909 upload landing + #1912 conform-stash-cure +
#699 beartype cure) into the f60h2 integration lane
merge: land the codex infra-lane normalization work (4a601322e line) into the f60h2
integration lane
merge: adopt origin/fix/import-law-upload-20261009 (grand union)
merge: adopt recover/redo-d0560ba3c-merge-20261009 (grand union)
merge: adopt fix/stubs-by-reality-tip-20261009 (grand union)
merge: adopt fix/dev-setup-gen-upg-20261009 (grand union)
merge: adopt fix/mod-relocation-finding-20261009 (grand union)
merge: adopt fix/rebuild-dev-tooling-20261009 (grand union)
merge: absorb the concurrent 0.12.0-dev landings (#1909 #1912) into the grand union
merge: adopt the f60h2 integration lane (union 2/13)
merge: adopt the codex lane-normalization lane (union 1/13)
merge: land #1883 dev-import-green residue (receipt producers, typed CodemodAdmission,
worktree env ownership)
Merge branch '0.12.0-dev' into fix/dev-setup-gen-upg-20261009
Fix/conform stash cure 20261009 (#1912)
Merge branch '0.12.0-dev' into fix/import-law-upload-20261009
\[WIP\] merge: origin/0.12.0-dev (#1909 landed) into fix/mod-relocation-finding-20261009
Upload 20261007 (#1909)
Merge commit '638efcf3284e10c8406b35a0872f9a88e239d907' into upload-20261007
Merge commit 'fdfb794ce544da8c2b5e6be77ce3038a00c8db7f' into upload-20261007
Merge commit '0d7627820e30f47196d895fd1e079fbcec64ebc6' into upload-20261007
Merge commit '3c3a3626a6b22ad37b18bdbe372cadd7b3b60a7d' into upload-20261007
\[WIP\] merge: origin/0.12.0-dev (#1903 landed) into fix/mod-relocation-finding-20261009
\[WIP\] fix(make): upg hands off to a fresh make upg when gen publishes a new Makefile
(#1903)
Merge commit '4a601322e3f88a44325f142673dc6a85e74b55fa' into upload-20261007
Merge commit '4a15eb8cd8cbcaa5de557e4e4f72622896065124' into upload-20261007
merge: land #1888 route payload contracts + Ruff recovery validation into the f60h2
integration lane
merge: land #1905 codemod unresolved-declaration-relocation findings (local tip
0853353ac, superset of PR head) into the f60h2 integration lane
merge: land #1903 upg self-handoff transition into the f60h2 integration lane
merge: absorb the stability cures (#1907 #1908) into the upload lane
fix(tests): lane-guard contract wording + remote HEAD fixture (stability loop cycle 10)
(#1908)
fix(tests): beads identity dump carries ownership-command defaults (stability loop cycle
9) (#1907)
merge: land #1900 post-#1890 stabilization (tip 9747327f9) into the f60h2 integration
lane
fix(config,models,locks): beartype floor cap + bare-project coercions + flext-cli
resolver rev (stability cycles 6-9) (#1906)
\[WIP\] merge: origin/0.12.0-dev (#1900 landed) into fix/upg-transition-20261009
\[WIP\] merge: origin/0.12.0-dev (#1900 landed) into fix/mod-relocation-finding-20261009
fix(gates): post-#1890 stabilization — census relock, tip reconciliation, pre-existing
reds at their owners (#1900)
merge: absorb stability-loop cycles 1-7 (origin/0.12.0-dev 56f92450f) into the f60h2
integration lane
\[WIP\] merge: origin/fix/post-1890-stabilize-20261009 into fix/upg-transition-20261009
Merge commit '9faa6a630756c93de3b1ee5231fd3f92c0daa90a' into upload-20261007
\[WIP\] merge: origin/fix/post-1890-stabilize-20261009 into
fix/mod-relocation-finding-20261009
\[WIP\] merge: absorb 0.12.0-dev #1901-#1904 — catalog dir staging kept; make/go follow
operator-ruling-2026-10-10 (system make, go per project)
\[WIP\] merge: retain1891 provenance with current native projections
\[WIP\] merge: consolidate1883 with current generated ownership contracts
\[WIP\] merge: retain1888 ancestry and reconcile its public contracts
\[WIP\] merge: align normalized sources with integration56f92450f
\[WIP\] merge: absorb origin/fix/post-1890-stabilize-20261009 into relocation-finding
lane
\[WIP\] merge: reconcile published integration with retained normalization sources
fix(models): bare --projects coercion on the scope mixin (stability loop cycle 7)
(#1904)
fix(config,locks): bare --projects coercion + R1 make/go tool locks (stability loop
cycle 6) (#1902)
fix(tests): track the relocated rule catalog directory (stability loop cycle 5) (#1901)
\[WIP\] merge: adopt post-1890 stabilize lane as F1 base
fix(tests): slow-mark the workspace fixed-point conform (stability loop cycle 4) (#1899)
fix(tests): the lease denial contract exercises the public lease boundary (stability
loop cycle 3) (#1898)
\[WIP\] merge: absorb 0.12.0-dev after #1890 — keep #1895 shims PATH; make stays
system-owned and go out of the fleet base (operator tool hierarchy), #1896 reinstatement
not adopted
fix(tests): C19 contract alignment — make selector + hook partition (stability loop
cycle 2) (#1897)
fix(bootstrap): join MISE\_SHIMS\_DIR to the lifecycle PATH so fresh clones resolve uv
(#1895)
fix(config): make and go as Mise-managed selectors — R1 contract cure (stability loop
cycle 1) (#1896)
Merge remote-tracking branch 'origin/0.12.0-dev' into upload-20261007
fix(tests,gen): C19 upg lifecycle contract + stale projection regeneration (runtime
cures on the integrated tip) (#1894)
Merge remote-tracking branch 'origin/0.12.0-dev' into upload-20261007
merge: union 0.12.0-dev into upload lane + lints cures (bootstrap constant, stale
@override, json\_dumps, retire stale mise-artifacts case) (#1893)
merge: reconcile the stabilization lane with the integrated 0.12.2 baseline (#1890)
fix(toolchain): resilient setup, host-safe bootstrap and 0.12.2 gate baseline (#1890)
\[WIP\] merge: absorb 0.12.0-dev (#1892) — beads seeding + mypy deferral cure kept; CI
approval stays per-verb on push/PR (setup now resilient, no dispatch-only gate)
fix(gates): mypy deferral-trace report poisoning + approval step dispatch-only guard
(#1892)
\[WIP\] merge: adopt the remote lane head (editor setting, bootstrap storage constant)
merge: union the gate-baseline lane (PR #1890) into upload-20261007
chore(git): align cleanup workbench with published integration
merge: absorb 0.12.0-dev integration tip into upload-20261007 (native bootstrap +
manifest scan cures)
\[WIP\] merge: absorb 0.12.0-dev 289812e48 (#1889 native Make bootstrap and
manifest-scoped validation) into the gate-baseline lane
fix: restore native Make bootstrap and manifest-scoped validation (#1889)
Merge latest integration fixes into native activation lane
\[WIP\] merge the ours-merge recovery lane (restored tests/tooling producers) into
dev-import-green
merge: adopt the ours-merge recovery lane (fix/recover-ours-merge-20261009 @ 36bf41270)
onto 0.12.0-dev e8091fe41
merge: absorb 0.12.0-dev (50c05e11e, #1886) into the ours-merge recovery lane
\[WIP\] merge origin/0.12.0-dev (#1887 uv proof) into dev-import-green
fix(toolchain): prove the mise-locked uv via mise which (#1887)
merge: adopt reviewed recovery admission and typed codemod consumers
\[WIP\] merge origin/0.12.0-dev into dev-import-green (adopt parallel repairs)
merge: absorb the toolchain/gen reconciliation into the dev branch (#1886)
merge: absorb 0.12.0-dev d02394ad0..03f968655 into the conform-stash cure lane (fleet
convergence)
merge: absorb the toolchain/gen reconciliation (model states for the bootstrap manifest
and projections)
fix(recovery): restore the dev line the d0560ba3c ours-merge dropped (tooling, Ruff
policy, 47 producers)
Merge remote-tracking branch 'origin/fix/dev-import-green-20261009' into
recover/target-tree-20261009
Merge commit '2f246377e' into recover/target-tree-20261009
Merge commit 'e999c89e2' into recover/target-tree-20261009
Merge commit 'c7181f26d' into recover/target-tree-20261009
Merge a70552a82 (lane route contracts, mypy report runner, fixes) into the recovery
target
Merge commit 'ba51fbbfb' into recover/target-tree-20261009
merge: absorb the upload lane tip into the dev branch (fleet convergence) (#1885)
merge: absorb the upload lane tip into the dev branch (fleet convergence)
merge: adopt fix/dev-setup-gen-upg-20261009 — the assembled setup/gen/upg cure
(dev-import-green + conform-stash-cure + stubs-by-reality-tip)
fix: import repairs + upload absorption for the dev branch (#1884)
fix(codegen): keep Annotated importable at runtime on the absorbed conform (pydantic
evaluates the request fields at class creation)
Merge remote-tracking branch 'origin/fix/stubs-by-reality-tip-20261009' into
fix/dev-setup-gen-upg-20261009
Merge origin/fix/conform-stash-cure-20261009 into the dev setup/gen/upg integration lane
Merge fix/dev-import-green-20261009 (adopt: 0.12.0-dev imports and generates again)
Merge remote-tracking branch 'origin/upload-20261007' into merge/upload-to-0120-20261009
Merge commit 'ba51fbbfb2e50bec95c4ddefbd460dc1b00d21bb' into upload-20261007
Merge commit 'e999c89e25d859fb4e4ae873d79569bdb900a72e' into upload-20261007
Merge commit 'c7181f26de3214a8d1ac31b8174bccc7c530f44e' into upload-20261007
Merge commit 'd0560ba3c236d5ad938219bb66bd5a9757e2b744' into upload-20261007
Merge remote-tracking branch 'origin/0.12.0-dev' into upload-20261007
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/test-file-selection
config(infra): bound the subprocess audit to its three sanctioned owners (#1881)
Fix/import law gen 20261008 (#1882)
Merge branch '0.12.0-dev' into upload-20261007
fix(codegen): drop two dead uv exclude entries (probe-proven) (#1880)
Merge branch '0.12.0-dev' into fix/gitmodules-owner-20261008
\[WIP\] merge origin/0.12.0-dev into import-law gen lane
Fix/rope builtin base 20261008 (#1878)
Fix/gitmodules owner 20261008 (#1876)
Merge branch '0.12.0-dev' into fix/gitmodules-owner-20261008
Fix/import law 20261008 (#1874)
Merge branch '0.12.0-dev' into fix/import-law-20261008
Fix/upg gitlink pins 20261008 (#1873)
Merge branch '0.12.0-dev' into fix/upg-gitlink-pins-20261008
Stash preserve/flext infra 9 20261007 (#1859)
Merge branch '0.12.0-dev' into stash-preserve/flext-infra-9-20261007
land(wave471): adopt upload-20261007 into 0.12.0-dev (#1847)
Merge branch '0.12.0-dev' into land/wave471-infra
fix(security,codemod): subprocess only in the u.Cli.run owner and flext-core;
flext\_infra never imports flext\_tests (#1844)
Merge branch '0.12.0-dev' into fix/subprocess-owner-20261008
Merge origin/upload-20261007 into fix/rope-builtin-base-20261008
merge: absorb the 0.12.0-dev integration tip back into the upload lane
fix(toolchain): supply the Make UV to the mise-proof invocation (#1875)
Merge fix/tip-make-rope-builtin-20261008 (adopt the rope builtin-base fix and
RUNTIME\_VENV paren)
\[WIP\] merge rope builtin-base hotfix into import-law lane
merge: absorb the 0.12.0-dev integration tip back into the upload lane
\[WIP\] merge origin/0.12.0-dev into import-law lane (upload landed via #1843)
\[WIP\] maintained upload convergence and CI owner repairs (#1843)
\[WIP\] merge origin/upload-20261007 into fix/import-law-20261008
merge: adopt origin/upload-20261007 into gitmodules-owner lane
merge: adopt origin/upload-20261007 into gitmodules-owner lane
fix(maintenance): sonarcloud verbs run-if-available-else-skip — typed absence, never a
failure (#1871)
Merge origin/0.12.0-dev into upload-20261007
\[WIP\] adopt align/upload-20261007-infra (compat session handover a39c67f)
\[WIP\] adopt land/wave471-infra into fix/import-law-20261008
\[WIP\] merge origin/0.12.0-dev into fix/import-law-20261008
Merge remote-tracking branch 'origin/upload-20261007' into land/wave471-infra
merge: integrate origin/0.12.0-dev (pin-first mise bootstrap recovery #1870)
merge: adopt upload-20261007 828cc2fec/100a3e1ee
merge: converge integration bootstrap and typed candidate boundaries
fix(toolchain): pin-first mise bootstrap recovery (setup/gen/upg survive lock-format and
mise drift) (#1870)
merge: integrate the landed npm-free toolchain tip; recovery re-applied on the merged
template
Merge remote-tracking branch 'origin/upload-20261007' into land/wave471-infra
Merge commit '0ab29453ed4bbce9b5907f380bf2450485c89da5' into upload-20261007
Merge commit '57caf6f1a418f8ac431fbe712ec4579a66e0ad93' into upload-20261007
Merge commit 'acbdc980892a4dddd5274993fcd36f373ac2ff7a' into upload-20261007
Merge commit '25516322cb19019601578a59b5979eaad5e41224' into upload-20261007
merge: adopt upload-20261007 cb52c5e14 (unsplit rope source bases)
\[WIP\] merge: synchronize checksum locked toolchain candidate history
\[WIP\] merge: aggregate upload lifecycle repairs into stabilization candidate
merge: adopt checksum locked npm free toolchain in stabilization candidate
Merge remote-tracking branch 'origin/0.12.0-dev' into land/wave471-infra
merge: adopt origin/upload-20261007 into land/wave471-infra
merge: align upload-20261007 with origin/0.12.0-dev
\[WIP\] merge: adopt npm-free integration toolchain for stabilization
feat(toolchain): npm-free fleet toolchain; rumdl formats markdown; setup proves tools
(#1848)
Merge commit 'ec3bd41217571091cfd890b6ab36d9d26293f134' into upload-20261007
merge: integration tip into fix/npm-free-toolchain-20261008
Merge commit '091d65858f165056873610821d3f2f3cbc61f7fd' into upload-20261007
Merge commit '31c94908df38b738e043fd59271e72beb12f0372' into upload-20261007
Merge commit 'dee26eeb5d5fd26e55051407a3a4de2ebe10e815' into upload-20261007
merge: keep shared stabilization repairs aligned with current integration dependencies
merge: adopt integrated upgrade and CLI model contracts
Merge commit 'd921aae22bd279b6c35c1a375098df8c4b86fa1b' into upload-20261007
Merge commit '3f2fd7227fd405399d2e0edff9b9d106da5d390b' into upload-20261007
Merge commit 'f265ffc430298200c1176a1af80549c2d6d2587d' into upload-20261007
Merge commit '1c315e06f0de1111c3705b1c2138b1a1e9b24c2f' into upload-20261007
Merge commit '8537a0f8787b48f9139c07fd9c7ad693addcd6ce' into upload-20261007
Merge commit '77617aa6e2fb15011729a7eef3f9192d0435d589' into upload-20261007
merge: integrate the 0.12.0-dev tip (ProcessOptions via m.Cli #1846, upg never runs
check, single ast-grep run) into the wave lane
merge: adopt published producer pin and cooperative stabilization tip
Merge commit 'a227e05151a3be2af3571d05a7e0b3d99124ef8c' into upload-20261007
refactor: remove duplicate entries and clean up tooling configuration in tooling.yaml
merge: 0.12.0-dev stabilization (#1845) into the subprocess owner lane
fix(make,cli-contract): upg never runs check; process options are the flext-cli model
(#1845)
Merge commit '0520cad0d91b5f0d652e21fbeaf434af40497854' into upload-20261007
Merge commit 'b715980bd46cd696c6138e350f8d7818d2312418' into upload-20261007
Merge commit '410c9b2c88f2ead558236af6e49b80ad53eb6f32' into upload-20261007
Merge commit '78abc03725d196407baad89f1a15404d3b9f53a0' into upload-20261007
merge: aggregate governed scanner fixtures from PR 1841
Merge commit '8b45c00e963f6164e064813a6926159b0055384f' into upload-20261007
merge: adopt 0.12.0-dev ProcessOptions src cure (9f91a29db)
Merge commit '33e615f80140ea1cf9d8b0d122d1c396e440cc2f' into upload-20261007
merge: absorb integration ProcessOptions owner repair
merge: adopt peer subprocess and test dependency boundaries for stabilization
Merge commit 'f551095b79c532779cce0407a13e191723bc5898' into upload-20261007
Merge commit 'f187e7f6e7e8f38aa7f186b866904b1af9ccb7a3' into upload-20261007
Merge remote-tracking branch 'origin/0.12.0-dev' into land/wave471-infra
Merge commit 'ca4c91071ab80a4491039a6ae453f57043e9ac3f' into upload-20261007
Merge commit 'b86ca75284a9850449408535b63453709132d97e' into upload-20261007
Merge commit '3e135ce90561177a8b1648b746757703bad920af' into upload-20261007
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/tip-ci-ast-grep-20261008
Merge commit '0e9dc9a927040d32816ae3dcd61977a5e8c04fb8' into upload-20261007
Merge commit '7c2e065178a8e105feca536fdd4cc19363a32b89' into upload-20261007
Merge commit '3ef47af531dc6f6ce8d90b0eea19d5f77deae355' into upload-20261007
fix(utilities): ProcessOptions resolves through m.Cli, never u.Cli (#1846)
Merge commit 'ef8cb69432e2fb9414921e9c6d1d94bb9c52621c' into upload-20261007
Merge commit 'a3233046784a060360b08ecca461222364f83c8f' into upload-20261007
Merge commit '32fbf627d851a82aa3e69c6f6d4b59c903176188' into upload-20261007
Merge commit '72266123162bec4bd44b1c5804460fe7d04f04a2' into upload-20261007
Merge commit 'b49b65d415af809b683f2963f464eefe18068dd7' into upload-20261007
Merge commit 'bba314d5612f6890df43b82ce2da137125faee96' into upload-20261007
Merge branch 'fix/test-file-selection' into upload-20261007
Merge commit 'cfefcc12c166f64e1a453a9fa9895dc28a9a0817' into upload-20261007
merge: adopt shared scanner fixtures and single invocation ownership
Merge commit 'dddde491d6eee27bbc6dd0a79f725bd369cc1a64' into upload-20261007
Merge commit '989ebd87da9f78309e89e9876adfeb71f7ac5b8f' into upload-20261007
Merge commit 'cd78c9b3770dbd588436525360b88f7109704e23' into upload-20261007
Merge commit 'dfb47c715037b5cdfdb76d67ba907bb0c443f039' into upload-20261007
Merge commit '7485b3fb385ca0dce22fb5d04d86fdaf84d08737' into upload-20261007
Merge commit '0df7d6ec2bc6180126aaf95a455be75cc599c9a4' into upload-20261007
Merge commit 'e7bfb6f5a1c1cfe6e89dd627b8f6f03c8ec344ba' into upload-20261007
Merge commit 'f1205ad459eeae6fd50d03557550cac933a4fe7a' into upload-20261007
Merge commit 'c426dc3e875be58d0ef9ac1cf056a6cfb99145ad' into upload-20261007
Merge commit '99976d42547a2bb278599feb24843d757b0e05f5' into upload-20261007
Merge remote-tracking branch 'origin/upload-20261007' into land/wave471-infra
merge: adopt #1841 (single ast-grep run, fixtures carry the Mise lock)
\[WIP\] merge: adopt upload-20261007 fixes into the landing lane
Refactor tests for code generation and CI workflows
merge: align upload-20261007 with origin/0.12.0-dev
merge: integrate the moved 0.12.0-dev tip into the ast-grep fixture lane
merge: preserve automation work on latest integration tip
merge: converge typed import planning and entity-safe nesting with integration
fix(codegen,make): one generated\_source key for protoc trees; upg relocks its projected
manifest (#1842)
merge: integration tip (#1840 single-pass upg) into the protos/upg lane
fix(make): upg converges in one pass; scaffold scenarios plan one surface (#1840)
\[WIP\] merge: integrate #1839 into the upg single-pass lane
fix(ci): green the flext-infra integration tip under the CI profile (#1839)
merge: integration tip into fix/protos-policy-upg-order-20261008
\[WIP\] merge: integrate the moved 0.12.0-dev tip into the upg single-pass lane
\[WIP\] merge: integrate the moved 0.12.0-dev tip (#1835 and the follow-up CI-context
cures)
fix(codegen): resolve bases read through a provider facade instance (#1838)
merge: adopt current gate partition and regenerate CI policy projection
merge: integration tip into fix/rope-base-resolution-20261008
fix(setup,docs): approve projected .envrc in CI; docs build failures name their warnings
(#1835)
\[WIP\] merge: adopt current integration tip into upload
fix(deps): flext-grpc declares its protobuf runtime (#1837)
\[WIP\] merge: adopt #1835 (fix/ci-direnv-allow-20261008) into the tip-CI lane
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/ci-direnv-allow-20261008
merge: retain latest CI source cures and regenerate aligned candidate
fix(rules,ci): restore inverted rule fixtures; direnv gate is local-only (#1836)
Merge origin/0.12.0-dev into fix/rule-fixtures-context-rewrite-20261008
merge: adopt latest hygiene and alias fixes with preserved CI guard cure
refactor(conform): dedupe the surface dispatch and pass the integration line as one
typed object (#1834)
merge: adopt origin/0.12.0-dev tip; keep only the unique tip-check-debt slices
chore(gen): regenerate CI workflows for the lock-pinned mise install (#1833)
merge: integrate the 0.12.0-dev tip into fix/workflow-projection-drift-20261008
fix(make): align the upg lifecycle and verify-clean template with what members carry
(#1832)
merge: integrate the 0.12.0-dev tip into fix/upg-lock-regressions-20261008
fix(ci): install mise from the mise.lock asset with checksum verification (#1831)
merge: keep current tip and regenerate owned interface
fix(provenance+gates): prove native workspace members in CI; cure the post-upload tip
red (#1830)
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/ci-workspace-member-provenance-20261008
Merge origin/0.12.0-dev into fix/ci-mise-verified-install-20261008
fix(codemod): land adopted alias-identity (#1819) with its lint, gen drift and runtime
defects cured (#1829)
merge: integrate the 0.12.0-dev tip into fix/compat-alias-engine-w1-20261008
merge: adopt current integration and repair formatter contract
\[WIP\] merge: adopt reviewed integration resolutions into upload
feat(audit): fail loud on stashes, merged-but-alive branches and orphan worktrees
(#1828)
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/ci-workspace-member-provenance-20261008
merge: integrate the 0.12.0-dev tip into fix/lane-hygiene-audit-20261008
chore(unify): land upload-20261007 into 0.12.0-dev (#1816)
Merge origin/0.12.0-dev (lock bump) into upload-20261007
merge: adopt fix/alias-identity-20261008 (#1819, flext-itpd1.3.25.2) into the W1
compat-alias engine lane
chore(deps): bump flext-cli/flext-core/flext-tests locks to the 0.12.0-dev tips (#1821)
merge: keep the single recovery candidate aligned with integration
Merge origin/0.12.0-dev into upload-20261007 (fix-forward)
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/alias-identity-20261008
merge: adopt latest integration tip and preserve publication phase contract
fix(rope): restore runtime-base workspace roots and project-source mutation law (#1818)
merge: integrate the 0.12.0-dev tip into fix/rope-runtime-bases-20261008
fix(infra): tip residue — staged mod-text/candidate phases, immutable demotion scan,
fail-loud family exports (#1817)
fix(infra): fleet-wide mid-code import hoisting + codemod-rules shadowed-config cure +
thin rope facade (#1812)
merge: adopt canonical file gates into automation landing lane
merge: adopt requested-file phase repair into automation landing lane
merge: absorb origin/0.12.0-dev into upload-20261007 (fix-forward-adopt)
Merge branch 'dup-261007' into hotfix/upload-20261007
merge: adopt the moved 0.12.0-dev tip — every import-phase conflict resolved to the
tip's facet-lazy canonical form (the later, fleet-wide consolidated spelling); no
content lost (my slice is the hoist on the other 210 files + the codemod-rules shadow
cure, both merged cleanly)
merge: align to the moved integration tip (no-ff, fix-forward)
fix(utilities): the composition mixes in the one Dependencies class (#1815)
merge: integrate the #1814 tip into the composition-cure lane
hotfix: rope source-text preservation + module-table rebind detection (core gen blocker
cure) (#1814)
refactor(utilities): the one-class canonical form — dependencies + rope composite
(#1810)
merge: integrate the #1811 single-class landing into the one-class lane
hotfix(upload-20261007): CI=Y gates green — lint/duplication/loc-cap/runtime-census
zero, dependencies single-class, F0/F1 machinery (#1811)
merge: integrate the 0.12.0-dev tip (day-wave) into the one-class lane
merge: adopt the integration tip 0.12.0-dev (flext-q0oyc, merge-admin final)
merge: adopt the integrated 0.12.0-dev tip (post #1809) — fix-forward union of the
dependencies hoist cure
On hotfix/ci-green-collab-20261007: ci-green WIP
fix(gates): CI=Y blocking gates zeroed — runtime-census 0, duplication 0, loc-cap 0,
part modules landed, test contract asserted (#1809)
fix(deps): update dependency exclusions and refine workspace member rendering logic
chore(config): normalize pyproject.toml formatting
merge: integrate the 0.12.0-dev tip into the sources-gate cure lane
chore(config): adopt the fleet-writer alignment of the SSOTs — taplo spacing
normalization and F0 retired\_projections trimming (guard flext-eles2 tracked-file
drift, collab adoption)
Merge remote-tracking branch 'refs/remotes/origin/0.12.0-dev' into
hotfix/s6-adoption-20261007
wip(infra): preserve concurrent dirty state before S6 adoption
hotfix(0.12.0-dev): the mise\_install fragment provisions the mise.lock-pinned release
(+ self-render) (#1807)
fix(deps): republish the standalone git-pin pyproject the S6 adoption rendered over
(#1805)
fix(deps): restore the canonical git-pin render over the S6 adoption (#1804)
merge: integrate #1800 (wave-broken generator cure) with the 0.12.0-dev tip (#1803)
Merge remote-tracking branch 'origin/0.12.0-dev' into integrate/1800-20261007
Merge commit '8d36e891b2ee89166687c249313201de4237d9c2' into hotfix/upload-20261007
Merge commit '597585fb184bef2a9cfaa5c9be5fb1947e916457' into hotfix/upload-20261007
wip
Merge commit 'b063a6585e861bdb1bc3ca6b6130fa1b5fcaa7fe' into hotfix/upload-20261007
fix(tooling): deduplicate the strict-errors list the tooling union concatenated (#1802)
Merge commit '40539de8eeec6a582885000d40ca7a6657c2f4ce' into hotfix/upload-20261007
Merge commit '4afdf10c2511cba5b3bf9be05ba788b7232963a0' into hotfix/upload-20261007
Merge commit 'f99efa5b97a8e97270cf8523b79008472a68029b' into hotfix/upload-20261007
fix(utilities): adopt the S6 rope-source-bases split — composite facade over
inventory/collector/runtime/aliases parts (#1801)
Merge commit '82f01e56b37602515b8749f9ffae97afa1db10d4' into hotfix/upload-20261007
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/gitpin2-20261007
merge: integrate the 0.12.0-dev tip (#1796-#1799 S6 cures) into the wave-damage hotfix
lane
fix(rope): the alias-map builder reaches lazy\_module\_aliases through the Family name
(#1799)
merge: integrate the 0.12.0-dev tip (ci-fragments #1797) into the alias-map cure lane
fix(ci-fragments): wire the url.insteadOf rewrite the private-dependency auth header
documents (#1797)
fix(utilities): the S6 family facades reclaim distinct names (#1798)
fix(rope): restore the flat RopeSourceBases re-export the S6 dedup erased (#1796)
fix(rope): restore the collector hierarchy the #1788 merge mangled in
rope\_source\_bases (#1795)
merge: adopt the landed Dependencies re-export cure (#1794) — align to tip (no-ff)
fix(utilities): the flat Dependencies re-export binds the nested mixin, not an empty
tuple (#1794)
merge: integrate the 0.12.0-dev tip (S6 collapse + prefix dedup) into the subscript-cure
lane
Merge commit 'ae04647282728b423ead4f8429261472f4372554' into hotfix/upload-20261007
fix(utilities): deduplicate the doubled Flext prefix from the S6 split class names
(#1793)
fix(rope/dependencies): the S6 flat re-exports + the wave's indent damage cure (#1792)
fix(deps): drop the tool.uv.sources section — the inline git-pins carry the URLs (#1791)
fix(deps): restore the canonical git-pin render for the sibling groups (#1790)
merge: adopt the rope walker-pair cure 0bedff673 — rope\_source\_bases consolidated as
the public facade (collector/resolver live in their dedicated inventory/runtime modules,
DRY dedup complete)
merge: adopt the family-facade anchors line 312a7e0e — every import-phase conflict
resolved to the HEAD canonical form (operator ruling: imports stay 'from flext\_infra
import c,m,p,t,u'); mise-artifacts trio stays deleted (F0 extinction); lineage of both
sides preserved
Merge commit 'b34db5ed7a9d9c13e50eee2803ade7fbdc444268' into hotfix/upload-20261007
fix(ci-fragments): mise\_install step indent survives include; private-dep mint covers
workflow\_dispatch (#1788)
merge: integrate the upload branch with the 0.12.0-dev tip (tooling.yaml union) (#1789)
Merge Admin 20261007: native mise/uv bootstrap + workspace members + fleet stabilization
(#1786)
merge: integrate the 0.12.0-dev tip into the upload branch — tooling.yaml union (both
sides' authorized exceptions kept; the tip's canonical formatting wins)
Merge commit '6929af123707580d3866ff9649fdcfcebd6bda73' into hotfix/upload-20261007
Merge commit 'a4d3f58d40c86e914f74e4a8054f2e41279bae32' into hotfix/upload-20261007
fix(tooling): resolve the conflicted authorized-exceptions region (union of both sides)
(#1787)
merge: align hotfix with the 0.12.0-dev integration tip (flext-q0oyc)
fix(packaging): restore the canonical git-pin render for the fleet sibling groups
(#1785)
Hotfix/upload 20261007 (#1783)
merge: integrate the moved integration tip into the upload branch (fix-forward)
fix(rope): subscript stores through non-class-binding names never redefine classes —
cures flext-2klp8 (#1784)
merge(infra): adopt the fleet gitlink state + re-land the 2026-10-07 tests-family and
stdlib-bootstrap rulings (union resolution, no ruling lost)
fix(tooling): drop the malformed ENFORCE-046 authorized-exception entry (#1782)
fix(tooling): cure the consumer config crash from the census-exemption placement (#1781)
config(tooling): authorize the backup credential resolver's Secret Service spawn (#1780)
Merge commit '815fda2ba7b9b521993cc30a51639cef9ac76166' into hotfix/upload-20261007
Merge commit 'cfaecb6f64e836da09d2e40fd7d5126e28c8b042' into hotfix/upload-20261007
fix(rope): resolve named lazy-import mapping bindings (cures flext-ldif gen) (#1779)
fix(census): exempt the generated \_\_init\_\_ TYPE\_CHECKING imports from ENFORCE-046
(#1778)
merge: align the ldif-lazy-map lane to the integration tip (no-ff, fix-forward)
merge: adopt native mise/uv extinction + member workspace sources — F0/F1 machinery
prevails on machinery paths, upstream content adopted (flext-q0oyc)
fix(infra): bounded bootstrap subprocess relief + batch gate adapters (operator ruling
2026-10-07) (#1777)
refactor(rope): source bases split into responsibility parts (S6) + conform chain
assessment (S8) (#1776)
refactor(conform): typed project-deps contract for the git-peer refresh (S5c) (#1775)
refactor(codegen): filesystem modes have one config SSOT + the phase enum owns staging
(S4) (#1774)
fix(rope): resolve external references only through resolvable module resources (#1773)
refactor(codegen): journal phase contract as a closed enum + honest Code Map (S2+S3)
(#1772)
fix(tooling): freeze the 9 historical evidence docs out of the format gates (#1771)
chore(gen): consume the shim-tolerant bootstrap in the own Makefile render (#1770)
fix(codegen): hold the fleet mise at 2026.9.16 — 2026.10.3 provenance verification
breaks the tool bootstrap (#1769)
fix(bootstrap): tolerate mise's benign warm-runner shim reshim notice (#1768)
merge: equalize dd261005 with 0.12.0-dev tip ef35de8ae (#1760, #1761, #1766) — F0
machinery prevails on machinery paths, upstream content adopted
merge: adopt the F0 restoration state (pinned staged engine, regenerated projections)
into the dd261005 lane
refactor(codegen): the lazy-init planner is a service, not a model (S1) (#1766)
fix(tooling): prettier must not reformat the codegen-managed docs projections (#1767)
merge: integrate the moved 0.12.0-dev tip onto the S1 lane (fix-forward)
hotfix: complete the interrupted protocols/models rename — 105 anchors + canonical regen
(unblocks gen/audit everywhere) (#1763)
hotfix: complete the protocols rename anchors + submodule-materialized CI checkout
(Merge Admin) (#1762)
fix(ci-template): materialize submodules in the CI checkout — cures the unsatisfiable
drift gate (#1760)
chore(rules): operator-ruled ban-model-rebuild disable + pytest11 plugin ignores (#1761)
merge: equalize dd261005 with 0.12.0-dev tip — bootstrap manifest provenance and tooling
snapshot drill (#1749, #1758, #1759)
config(tooling): authorize the snapshot drill's private stem import (#1759)
merge: adopt dd261005 lane (import-law wave + rope fixes) onto the codegen-strict
refactor lane
Merge remote-tracking branch 'refs/remotes/origin/dd261005' into dd261005
merge: integrate the dd261005 convergence wave into 0.12.0-dev (#1758)
Merge branch '0.12.0-dev' into dd261005
fix(bootstrap): preserve native manifest and locked provenance (#1749)
merge: integrate the remote dd261005 format commit into the green lane
Merge remote-tracking branch 'infra-origin/0.12.0-dev' into integration/dd261005-green
fix(namespace-moves): include a block's decorators in its move range (#1757)
fix(bootstrap): safe completion rebinds + runtime wrapper credential prefix (#1756)
fix(bootstrap): pass the credential git config as env arguments (#1755)
fix(bootstrap): keep trimmed-for recipe lines indented too (#1754)
fix(bootstrap): keep every trimmed recipe line's tabs explicit (#1753)
fix(bootstrap): keep the credential-store recipe lines indented (#1752)
fix(lazy-init): render no TYPE\_CHECKING block when groups collapse away (#1751)
fix(bootstrap): wire the minted private-dependency credential store into the runtime env
(#1750)
config(docs): include the site build in the make docs lifecycle (#1748)
fix(docs-template): grant Pages write to the build job (#1747)
Merge remote-tracking branch 'origin/0.12.0-dev' into dd261005
fix(rope): mirror NamedTuple in external\_identity (function-built class like TypedDict)
(#1746)
fix(rope): lazy re-export aliases never shadow real analyzed modules (#1745)
merge: converge dd261005 with the 0.12.0-dev integration tip
fix(pytest-runner): read phase receipts by subprocess ownership, not whole\_target
(#1744)
fix(bootstrap): allow the projected .envrc during setup (#1743)
config(tooling): cosmos-docgen measured slow-suite ceiling 600s (#1742)
fix(codegen): unblock web generation and Make bootstrap (#1739)
Merge branch '0.12.0-dev' into fix/web-managed-toml-recovery-20261006
Dd261005 (#1741)
dd261005 (#1740)
converge: the dd261005 stabilization onto the current tip (#1738)
converge: the dd261005 stabilization wave onto the current tip (#1736 lineage)
fix(toolchain): provenance policy at the owner + deterministic lock-noise tolerance
(#1736)
merge: absorb 0.12.0-dev into dd261005 (adopt convergence selector threading + stabilize
before landing provenance policy)
merge: absorb 0.12.0-dev into dd261005 (the convergence selector threading + stabilize)
(#1735)
merge: absorb 0.12.0-dev into dd261005 (the convergence selector threading + stabilize)
converge: dd261005 selector threading onto the integration tip
dd261005 (#1734)
Merge superproject gitlink ad1b1d8f into dd261005
fix(tooling): canonical subprocess owners join the informative family (#1732)
merge: adopt recovered managed bootstrap snapshot in dd261005
merge: preserve workflow metadata snapshot under current runtime owner
fix(codegen): restore the lazy\_init\_planner stub \_\_all\_\_ (#1733)
merge: re-absorb the integration tip
fix(models): complete the opt\_in\_check\_gates removal (#1731)
fix(codegen): retire the opt\_in\_check\_gates declaration (spec field removed by the
model wave) (#1730)
merge: adopt permitted recovery snapshot 8c7874d4603f56d8a719bf8e38dde7087ac6593d in
dd261005
fix(models): MypyCacheSpec base follows the registry rename (#1729)
merge: preserve recovered tooling without duplicate workflow routes
fix(integration): restore the two files dropped by the second-wave resolutions (#1728)
merge: reconcile recovered tooling with current typed render owner
merge: preserve recovered dependency graph with current locked owner
merge: adopt permitted recovery snapshot 2fbb50b666aabeb9fd1a9577ad9ed5c8db8ad34a in
dd261005
merge: preserve model annotation snapshot with current runtime contracts
merge: preserve model recovery history without resurrecting obsolete owners
merge: adopt preserved structured runtime diagnostic evidence
merge: adopt permitted Infra checkpoint e579626699a8548f7fcea8bea416be1b034213e1 in
dd261005
merge: adopt permitted Infra checkpoint cc5d4c966e9dada6c85aefcec6da16f84c92aa2e in
dd261005
merge: adopt preserved template port through canonical source
integrate: second wave (6 pending) + cure the first-wave conflict markers (#1727)
merge: preserve bootstrap continuation source with runtime ownership
integrate: dd261005
integrate: preserve/adopt-1667-template-port-20261005
integrate: epic/loc-cap-split-adopt-val20261004T1750
integrate: preserve/infra-mod-torn2-20261005
integrate: preserve/infra-mod-torn-20261005
integrate: backup/wt-sweep-20261005-noselfuse-v2-20261005
merge: adopt setup drift reconciliation source in dd261005
merge: adopt supplier binding repairs for web
merge: preserve local divergence with global TC suspension contract
merge: adopt preserved sweep tests through canonical public facade
integrate: the 3 remaining pending branches (sweep/automations, preserve-sweep5,
preserved-1656) (#1726)
merge: adopt current supplier integration for web validation
merge: preserve automation branch with current canonical bootstrap
integrate: wip/preserved-1656-noselfuse-v2
integrate: wip/preserve-sweep5-193236
integrate: sweep/automations-20261005
merge: integrate polecat WIP snapshot a17bf6e03 into dd261005 (fix-forward adopt;
graduated tip canonical)
merge: preserve export inference history and fleet-wide owner
merge: adopt web managed TOML recovery supplier
merge: converge with the integrated tip (post #1725)
integrate: all pending 0.12.0-dev branches (18) — integrate-first, stabilize after
(#1725)
merge: integrate pending branch fix/test-file-warm-rerun-val202610040809
(integrate-first, fix after)
merge: integrate pending branch fix/test-file-selection (integrate-first, fix after)
merge: integrate pending branch fix/facade-mro-regression-vdklb-20261005
(integrate-first, fix after)
merge: integrate pending branch fix/ci-informative-typecheck-codemod-20261005
(integrate-first, fix after)
merge: integrate pending branch fix/bootstrap-recipe-comment-continuation
(integrate-first, fix after)
merge: integrate pending branch dd261005 (integrate-first, fix after)
merge: integrate pending branch instr-fresh (integrate-first, fix after)
merge: integrate pending branch polecat/flext-nfa5a (integrate-first, fix after)
merge: integrate pending branch law/gates-posture-20261005 (integrate-first, fix after)
merge: integrate pending branch lane/deferred-rewrite-narrow-20261005 (integrate-first,
fix after)
merge: integrate pending branch lane/tip-green2-20261005 (integrate-first, fix after)
merge: integrate pending branch lane/tip-cure-20261005 (integrate-first, fix after)
merge: adopt mandatory approval parity checkpoint in dd261005
merge: adopt runtime-safe sibling suspension model annotation
merge: preserve instrumentation history with canonical bootstrap
merge: preserve pending tip-green history and current locked inputs
merge: adopt pending Infra checkpoint 7312b094c6d2afde187dd8648513127cfc0d0387 in
dd261005
merge: preserve bootstrap continuation history with Jinja comments
merge: adopt pending Infra checkpoint f8545f9ba0e2cfeba08c22c9c02650731de2477b in
dd261005
merge: adopt pending Infra checkpoint 20d68b071d56dd5735b09bbc72d31193be08dfc9 in
dd261005
merge: adopt pending Infra checkpoint e0ed14db51147ce22e06a8fe8bb5bcd431a32565 in
dd261005
merge: adopt provider-aware strict facade MRO resolution
merge: adopt lazy export repair through canonical generation
merge: adopt pending Infra checkpoint 842a6380d5f7eb12584361394a81ea30bde7ac8c in
dd261005
merge: adopt Rope identity worklist fixed point
merge: preserve informative lint history and authoritative bootstrap
merge: preserve global named TC suspensions in dd261005
merge: adopt pending Infra checkpoint 463e00e145db2cbc43e90f2a276ec5a3bf1a1296 in
dd261005
merge: adopt pending Infra checkpoint 43db7440e9fede70e41e688cd71645ddae9f52bd in
dd261005
merge: adopt mandatory Pydantic mypy contract in dd261005
merge: preserve pending Infra checkpoint 6e48c1c305d39ad66c4bfb2d93567b09ca94e6a9 in
dd261005
merge: preserve pending Infra checkpoint 0682ef6d4b00de739b3395e571e2f8d4021afc95 in
dd261005
merge: adopt bootstrap HOME preservation into dd261005
Merge remote-tracking branch 'origin/0.12.0-dev' into dd261005
fix(docs): regenerate the make-commands projection after the audit-blocking Makefile
cure (#1724)
fix(codegen): regenerate the stale phase-zero projections (audit blocking) (#1723)
wip: preserve concurrent edits (merge-admin sweep4) (#1722)
Merge branch '0.12.0-dev' into wip/preserve-sweep4-190219
wip: preserve concurrent edits (merge-admin sweep3) (#1721)
wip: preserve concurrent edits (merge-admin sweep2) (#1720)
Merge branch '0.12.0-dev' into wip/preserve-sweep2-184719
Wip/preserve sweep 183747 1 (#1719)
Wip/test resource limits dirty 20261005 (#1718)
chore(unify): preserve phase-zero projections and strict provenance correction (#1716)
feat(automations): workspace fleet-gaps + refactor violations-sweep canonical surfaces
(#1713)
Merge branch '0.12.0-dev' into sweep/automations-20261005
fix(markdown): ignore .zcode session artifacts fleet-wide (#1717)
sync: adopt 0.12.0-dev into preserved phase-zero projections
fix(approval): wrapper parity for custom approval-stage hooks (#1715)
fix(locks): advance stale branch-pin resolutions to current tips (flext-io8wa follow-up)
(#1714)
fix(bootstrap): full cure — whitespace recipe split + readonly + regen
(flext-io8wa/1k3ca/u8eij, P0) (#1712)
fix(mise): reconcile the mise.lock with the declared toolchain (setup blocking) (#1711)
Merge remote-tracking branch 'origin/0.12.0-dev' into lane/relock-setup-20261005
fix(bootstrap): restore the green bootstrap template (flext-io8wa, P0) (#1710)
merge: sync current 0.12.0-dev integration tip into the automations lane
adopt: mandatory-approval preservation commit a3be7ca80 (fix-forward, cooperative)
(#1707)
Merge branch '0.12.0-dev' into adopt/mandatory-approval-20261005
law(gates): TC001-TC004 blocking by name; mypy/pyright informative (merge-admin mandate)
(#1706)
sweep(infra): unsafe-fix law wave 1 (#1708)
Merge branch '0.12.0-dev' into sweep/infra-unsafefix-20261005
dd261005 (#1709)
merge: absorb the pool's second ruff pass over the automations surfaces
merge: adopt the mandatory-approval preservation commit (fix-forward, cooperative)
merge: sync current integration before independent resolver repairs
merge: unsafe-fix operator law 2026-10-05 into sweep lane (make fix always
--unsafe-fixes)
Merge commit '800382f651648082deb2b512f98c00956105ef15' into 0.12.0-dev
Merge commit 'd2879e880dc4c25cea6e6e357f183aaeb50d3e4b' into 0.12.0-dev
Merge commit 'ba73c040671763ebcd2060d9790b34a28ee1338c' into 0.12.0-dev
Merge commit '21150917bb2bc189ef5de9f6c602691601fcb5fa' into 0.12.0-dev
Merge commit '50965184dc59349865ecf0c5402192dbd61676c9' into 0.12.0-dev
Merge commit '424461ecd5f528a9a61d2ec037ee6db88bb811b1' into 0.12.0-dev
Merge commit '4ad7a470c5dfea9e2d9bef5f07990b2b1f3b8fe7' into 0.12.0-dev
Merge commit '56e1ede26ca2fc5803f0d47fc8bda5e0e2a7b1a1' into 0.12.0-dev
Merge commit 'e7b2a6425884f01dde5f57f020b19d1a409e3ffa' into 0.12.0-dev
Merge commit 'b8c648eb4177f4b12c71a133fc0219a2a0741f8c' into 0.12.0-dev
reapply flext-20yyv: mod-loop callbacks, origin-aware accessors, external consumers
(lost to the sharpening absorb) (#1705)
unify: merge admin sweep 20261005 — recipe projection truth (receipt diagnostics,
scratch cure+tracing), aiohttp floor (#1704)
unify: preserve the working state (merge admin sweep 20261005)
chore: absorb tip into the sharpening lane
fix(make): cure the setup bootstrap recipe split (flext-u8eij, P0) (#1690)
Merge remote-tracking branch 'origin/0.12.0-dev' into fix-verbs-mod-loop-20261005
fix(rope): degrade non-class external resolutions to the recognized verdict (#1703)
merge: re-sync with the integration tip
fix(bootstrap): one-shell setup recipe; pkgutil runtime-base derivation restored
(unblocks setup fleet-wide) (#1700)
merge: re-absorb the moving tip (worklist + reexport cycle cures)
merge: absorb the lane's recipe-shell function-boundary refinement (their newest
Makefile hand-patch; the template port re-renders it)
merge: absorb 0.12.0-dev (depth-bound walker evolution takes precedence)
fix(rope): degrade conditionally-declared classes to non-class bindings (#1701)
merge: absorb the integration tip (rope walk cures #1692-#1699, TC reason restore)
merge: adopt the rope lane's iterations (#1697/#1699) for the shared walker
fix(rope): Attribute-over-Subscript references + the TC-off entry's required reason
(#1697)
merge origin/0.12.0-dev into fix/walker-attribute-subscript-order (cycle 1)
fix(rope): depth-bound the external-base walk; tolerate conditional bindings in external
modules (#1699)
fix(bootstrap): fail loud when the mise scratch mktemp fails (flext-9lnhu) (#1698)
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/walker-attribute-subscript-order
fix(rope): degrade unresolvable external modules to the recognized verdict (#1696)
fix(rope): degrade lineage cycles from the line-qualified identity model (#1695)
Merge remote-tracking branch 'origin/0.12.0-dev' into fix-verbs-mod-loop-20261005
fix(rope): cut the reexport resolve cycle with an unresolved-base verdict (#1694)
fix(rope): worklist the derivation loop against mid-loop definition growth (#1693)
Merge remote-tracking branch 'origin/0.12.0-dev' into fix-verbs-mod-loop-20261005
fix(rope): remove the orphaned external\_reference body from provider\_reference (#1692)
test(rope): pin the non-class planned-binding degradation contract (#1691)
fix(config): restore the required reason on the TC001-TC004 disabled entry (#1688)
Fix/facade mro regression vdklb 20261005 (#1687)
Merge branch '0.12.0-dev' into fix/facade-mro-regression-vdklb-20261005
fix(rope): underivable definition degrades instead of crashing make gen (#1686)
Merge branch '0.12.0-dev' into fix/rope-underivable-definition-degrade-20261005
Merge branch '0.12.0-dev' into fix/facade-mro-regression-vdklb-20261005
wip(rules): preserve the in-flight namespace-law rule edit (worktree … (#1685)
fix(lint): informative complexity rules + scoped dated exceptions + pyrefly zero + gen
cure (#1667)
WIP: mandatory Make CI and pre-commit approval contract (#1669)
Merge branch '0.12.0-dev' into fix/mandatory-approval-parity-20261005
Merge branch '0.12.0-dev' into fix/lint-informative-rules-20261005
fix-namespace/fix-accessors as rope-loop callbacks; origin-aware accessor renames
(flext-20yyv) (#1684)
Merge branch '0.12.0-dev' of github.com:flext-sh/flext-infra into
fix/tc001-tc004-global-off-4536i-20261005
merge: re-absorb the moving integration tip (#1681/#1683 rope +
pyrefly-informative-in-CI)
fix(codegen): rope installed-distribution bases; dedup parallel-split copies; pyrefly
informative in CI (#1681)
merge: re-absorb the moving tip; their rope/CI surfaces, my TC-off per direct order
Merge remote-tracking branch 'origin/0.12.0-dev' into fix-verbs-mod-loop-20261005
fix(rope): treat non-class external resolutions as unresolved bases (#1683)
merge: re-sync with the integration tip; adopt the landed #1677/#1679 rope and facade
cures
merge: adopt current integration for strict qualified source derivation
fix(docs): scope\_boundary path-reference + module-export docstring + bootstrap ignores
(#1682)
wip: preserve lane WIP before worktree retirement sweep 20261005 (mer… (#1651)
merge: integrate the owner lane's facade MRO fix and tooling state; TC001-TC004 return
to OFF per the operator's newest order
Fix/markdown code origin qtmy2 val20261004 t1410 (#1666)
Merge branch '0.12.0-dev' into fix/markdown-code-origin-qtmy2-val20261004T1410
Fix/facade mro regression vdklb 20261005 (#1679)
docs(tooling): record WHY TC001-TC004 can never be re-enabled — they break Pydantic
classes (#1678)
fix(rope): skip no-source-module bases — completes the gen cure (stacks #1674) (#1677)
law(ruff): TC001-TC004 disabled — Ruff never enforces them (bead flext-p7bxt) (#1676)
Merge branch '0.12.0-dev' into wip/wt-sweep-20261005/testdup-val202610040808
Merge branch '0.12.0-dev' into fix/markdown-code-origin-qtmy2-val20261004T1410
Merge branch '0.12.0-dev' into fix/lint-informative-rules-20261005
fix(models): FlextInfraCodegen base order agrees with the generated facade MRO
(flext-vdklb) (#1674)
Merge branch '0.12.0-dev' of github.com:flext-sh/flext-infra into
fix/tc001-tc004-global-off-4536i-20261005
fix(tooling): restore TC001-TC004 enforced; revoke the same-day off-global attribution
(#1675)
merge: re-absorb the moving integration tip (their codegen.yaml rope convergence;
projection regenerated)
Merge branch '0.12.0-dev' into fix/models-facade-mro-order-20261005
fix(bootstrap): runner-shims mise warning expected, not fatal (+ rope convergence)
(#1673)
wip(rope): preserve the in-flight external-base lazy-namespace cure (… (#1670)
Merge branch '0.12.0-dev' into wip/rope-external-base-lazy-namespace-preserve-20261005
Fix/rope unresolved external base (#1671)
feat(ci): lint joins the CI-excluded local partition (operator order 2026-10-05) (#1672)
merge: integrate 0.12.0-dev tip into the rope unresolved-base cure
merge: integrate the owner lane's CI partition; their Makefile wins (projected surface)
merge: re-absorb the moving integration tip (theirs for the post-8d7b4d4b5 hunks;
advisory + exceptions retained)
merge: absorb the owner lane's push
Preserve/byuaa runtime 156590b 20261005 (#1668)
\[WIP\] fix(make): normal testmon admission without automatic slow phases (#1629)
Wip/wt sweep 20261005/fix/loc cap transaction make env val20261004 t0958 (#1665)
Merge branch '0.12.0-dev' into
wip/wt-sweep-20261005/fix/loc-cap-transaction-make-env-val20261004T0958
Wip/wt sweep 20261005/fix/markdown code origin qtmy2 val20261004 t1410 (#1645)
Merge branch '0.12.0-dev' into
wip/wt-sweep-20261005/fix/markdown-code-origin-qtmy2-val20261004T1410
wip: preserve lane WIP before worktree retirement sweep 20261005 (mer… (#1648)
Merge branch '0.12.0-dev' into
wip/wt-sweep-20261005/model-facade-producer-z5x3y-20261005
Wip/wt sweep 20261005/upg old generation 20261002 (#1655)
wip: preserve lane WIP before worktree retirement sweep 20261005 (mer… (#1658)
Merge branch '0.12.0-dev' into wip/wt-sweep-20261005/infra-tip-stabilize-20261001
merge: integrate the cooperating lane's gen cure with the scoped dated exceptions
merge: re-sync with the integration tip (#1626 landed); keep the hoist and the tip's
rope walker
merge: absorb the retirement sweep and rope cures into the qtmy2 adoption
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/ci-informative-typecheck-codemod-20261005
merge: sync with the integration tip; restore the pkgutil runtime-base derivation to
unbreak make gen
merge: adopt integration while retaining mandatory global TC004 data
Fix/rule tests snapshots 20261005 (#1626)
merge: absorb 0.12.0-dev into the settle-lock refresh lane (#1663)
wip: preserve lane WIP before worktree retirement sweep 20261005 (mer… (#1661)
merge: integrate 0.12.0-dev tip into the markdown-code gate lane (flext-qtmy2)
Wip/wt sweep 20261005/fix/profile child rewrite guhb3 val20261004 t1400 (#1650)
Wip/wt sweep 20261005/fix/loc cap split val20261004 t0958 (#1644)
Wip/wt sweep 20261005/style/lint tests e501 val20261004 t0956 (#1643)
wip: preserve lane WIP before worktree retirement sweep 20261005 (mer… (#1642)
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/ci-informative-typecheck-codemod-20261005
fix(rope): accept PyPackage in the pymodule contract; describe rope models (#1660)
Wip/wt sweep 20261005/fix/model facade postmerge contract 20261005 (#1647)
Merge remote-tracking branch 'origin/0.12.0-dev' into verify/mise-boo… (#1646)
Merge branch '0.12.0-dev' into wip/wt-sweep-20261005/fix/loc-cap-split-val20261004T0958
Merge branch '0.12.0-dev' into
wip/wt-sweep-20261005/style/lint-tests-e501-val20261004T0956
Merge branch '0.12.0-dev' into wip/wt-sweep-20261005/lazy-root-import-20261002
merge(0.12.0-dev): measure tip 761aa105c (#1632)
Wip/wt sweep 20261005/docs fence outcomes b4rft 20261005 (#1633)
Merge branch '0.12.0-dev' into wip/wt-sweep-20261005/docs-fence-outcomes-b4rft-20261005
Wip/wt sweep 20261005/fix/codemod inline import tests val20261004 t1505 (#1631)
Merge branch '0.12.0-dev' into
wip/wt-sweep-20261005/fix/codemod-inline-import-tests-val20261004T1505
fix(rope): treat call-headed assignments as non-class bindings (#1640)
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/ci-informative-typecheck-codemod-20261005
Wip/wt sweep 20261005/codemod baseline val20261004 t0955 (#1636)
wip: preserve lane WIP before worktree retirement sweep 20261005 (mer… (#1638)
wip: preserve lane WIP before worktree retirement sweep 20261005 (mer… (#1639)
Wip/wt sweep 20261005/fix/codemod broad annotation tests val20261004 t1510 (#1637)
Merge branch '0.12.0-dev' into wip/wt-sweep-20261005/adopt-lint-codemod-20261005
wip: preserve lane WIP before worktree retirement sweep 20261005 (mer… (#1630)
wip: preserve lane WIP before worktree retirement sweep 20261005 (merge-admin)
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/ci-informative-typecheck-codemod-20261005
fix(config): drop the duplicate global TC004 exception (the family entry covers every
file) (#1628)
fix(rules): drop the duplicated unscoped TC004 entry (validator refused the table)
(#1627)
merge: adopt the #1622 TC-family global block and the smells partition
Wip/kilo sweep 20261005/infra docs contract hjrk7 20261005 (#1625)
law(ruff): block the whole TC001-TC004 family on every file by rule name (operator
2026-10-05) (#1624)
feat(lint): never execute TC001-TC004 anywhere; smells joins the local-only partition
(#1622)
Merge branch '0.12.0-dev' into feat/tc001-tc004-blocking
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/ci-informative-typecheck-codemod-20261005
\[WIP\] fix(rope): planned-source runtime base inventory (flext-ldd4s) (#1617)
fix(rules): block the TC001-TC004 family from executing everywhere (operator 2026-10-05)
(#1621)
fix(check): informational mypy/pyright/codemod posture, snapshot-pinned facade rule,
S2083 stage guard, loc-cap split (#1620)
merge: adopt the #1619 CI partition posture as the landed base
Merge branch '0.12.0-dev' of github.com:flext-sh/flext-infra into
adopt/tests-duplication-20261005
feat(make): make mypy, pyright and codemod informative in CI (operator order 2026-10-05)
(#1619)
fix(codegen): detect generic facade-rebind modules; assignment joins the scope (#1618)
merge: adopt the #1616 fleet-wide rule scope, keep the snapshot-pinned constraint-free
semantics
chore: adopt current integration into runnerfix lane (flext-wqygc)
merge: adopt integrated bootstrap checkpoint for phase recovery
fix(rules): infer-literal-facade-exports fleet scope + parenthesized tuple constraint
(#1616)
fix(setup): preserve locked bootstrap failures (#1614)
integrate(tip-cure): the operator sharpening lane over the landed ruling base
(supersedes #1613) (#1615)
Merge remote-tracking branch 'origin/0.12.0-dev' into integrate/tip-cure-20261005
merge: adopt current integration and preserve strict policy contract
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/no-self-use-descriptor-nch48-20261005
fix(types): operator sharpening gc-eqvqx5 — revert mypy-dodge regressions, dated tooling
suspensions, mandatory pydantic plugin (#1613)
merge: absorb current integration into locked setup repair
chore: absorb the integration tip into the operator sharpening lane
Merge remote-tracking branch 'origin/0.12.0-dev' into
verify/mise-bootstrap-i7jz1-postmerge-20261005
fix(pytest): suite stop requires the deadline to pass on the executing clock (U10)
(#1612)
merge: reconcile current integration for policy post-merge proof
fix(deps): read the consolidated mypy ruling field on the tool table phase (#1611)
fix(codemod): strip dead type-only import scaffolds after import normalization (#1610)
fix(codegen): restore the project-wide mypy disable\_error\_code render (content lost in
the #1599 merge) (#1609)
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/literal-exp… (#1608)
Lane/validator revert 20261005 (#1607)
Law/pyrefly ignored cure 20261005 (#1606)
wip(infra): preserve superproject-checkout residue before integration… (#1605)
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/literal-export-inference-w4luo-20261005
Merge commit '63243ad8aad11e2999b954677c237b534f6f0ee2' into
lane/validator-revert-20261005
WIP: enforce Pydantic 2 Mypy policy and unify duplicate generator owner (flext-8i57m)
(#1595)
Merge branch '0.12.0-dev' into fix/mypy-pydantic-policy-8i57m-20261005
Merge commit 'df27d1d1d4ea1882a7d4e5b2486d7478a8e2edc0' into
lane/validator-revert-20261005
WIP: preserve Mise scratch lifecycle status (flext-i7jz1) (#1579)
WIP: preserve authored model facade namespaces (flext-z5x3y.1) (#1578)
Merge branch '0.12.0-dev' into fix/model-facade-producer-z5x3y-20261005
fix(workspace): settle lock refreshes git peers; lane failure restores base (#1568)
WIP: adopt loc-cap codegen split (#1558)
Merge branch '0.12.0-dev' into epic/loc-cap-split-adopt-val20261004T1750
WIP: infer literal root facade exports through owned mod rules (#1580)
Merge remote-tracking branch 'origin/0.12.0-dev' into adopt/pyrefly-cure-20261005
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/literal-export-inference-w4luo-20261005
WIP: preserve native SARIF comparison spans (flext-mc15j) (#1560)
merge: absorb 0.12.0-dev (mise lock drift fix + jscpd/latest + mypy fleet defaults)
merge: absorb 0.12.0-dev (mise lock drift fix + jscpd/latest + mypy fleet defaults)
law(pyrefly): drop the prop-decorator ignored-errors surface — the mypy ruling owns it
(#1603)
merge: absorb latest integration into the SARIF spans lane
Merge remote-tracking branch 'origin/0.12.0-dev' into lane/validator-revert-20261005
fix(deps): restore jscpd latest — hold premise measured gone (v5.2.0-v5.4.0 all ship
full platform assets) (#1566)
merge: absorb the disable-error-code field fix into the jscpd lane
fix(mypy): fleet-mandatory defaults — pydantic.mypy always on, ruling codes suppressed
for every consumer (#1602)
fix(bootstrap): type the serialized publisher as Generator (#1576)
WIP: adopt TC001 pydantic runtime roots (#1559)
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/mypy-fleet-mandatory-defaults
merge: absorb 0.12.0-dev into the settle-lock refresh lane
fix(mypy): restore the global disable\_error\_code render (merge clobber) (#1601)
merge: absorb 0.12.0-dev (disable-error-code single render + bun SSOT cycle)
merge: absorb 0.12.0-dev (disable-error-code single render + bun SSOT cycle)
merge: absorb 0.12.0-dev (disable-error-code single render + bun SSOT cycle)
merge: absorb 0.12.0-dev (disable-error-code single render + bun SSOT cycle)
merge: absorb 0.12.0-dev into the loc-cap split (cure the two live LOC\_CAP reds)
fix(codegen): render one merged disable\_error\_code — double render broke every
consumer gen (#1599)
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/mypy-disable-error-code-single-render
merge: absorb the disable-error-code field fix
fix(mypy): declare the disable-error-code field the ruling template renders (#1600)
merge: absorb integration into the jscpd latest lane
merge: absorb 0.12.0-dev integration into the SARIF comparison-span lane
merge: absorb integration into the SARIF spans lane
refactor(mypy): one ruling surface (dedupe #1588 vs #1590/#1591) (#1596)
merge: absorb the duplicate-key fix and bun toolchain switch
merge: absorb integration into the bootstrap Generator lane
feat(mise): bun installs the npm CLIs — SSOT switch + bootstrap env + --trust
(flext-qwvb5 T6) (#1594)
merge: unify Mypy policy owner while preserving integration work
merge: absorb 0.12.0-dev integration into the Generator-typed serialized publisher lane
fix(mypy): drop the duplicate disable\_error\_code (parallel ruling merges) (#1593)
fix(make): declare the test scratch root on every pytest verb (cosmos-yj36e.21) (#1583)
merge: adopt current Mypy policy integration into flext-8i57m
chore: absorb the mypy-pydantic law tip into the bun installer lane
law(types): suspend mypy call-arg + pyrefly prop-decorator fleet-wide; pydantic plugin
mandatory (operator 2026-10-05) (#1590)
fix(codegen): suspend mypy prop-decorator/call-arg under the dated operator ruling
(gc-eqvqx5) (#1591)
feat(mypy): disable prop-decorator and call-arg fleet-wide — pydantic 2 plugin ruling
(#1589)
Merge remote-tracking branch 'origin/0.12.0-dev' into lane/mypy-suppress-20261005
feat(mypy): operator ruling surface — project-wide disable-error-codes
(u3-field-computed-field) (#1588)
merge: converge with 0.12.0-dev tip b3b81bee1 (adopts merged #1585 squash + #1554)
merge origin/0.12.0-dev (b3b81bee1, incl. PR 1554) into
fix/test-scratch-tmpdir-val20261004T2257
fix(rules): admit Pattern-A consumer letter rebinds (cosmos-yj36e.15) (#1554)
fix: cure the integration tip — check findings 3087→2527; toolchain-root analysis for
the remainder (#1585)
Merge branch '0.12.0-dev' into epic/tc001-pydantic-runtime-val20261004T1750
WIP: fix(tests): restore the contract-correct make-environment suite clobbered by the
converge commit (#1553)
Merge integration with native Make regeneration (flext-i7jz1)
merge: converge with 0.12.0-dev tip b80187d2e (adopts #1586 type-debt wave 1 + #1587)
chore(deps): retain native setup relock catalog resolution (#1587)
Merge remote-tracking branch 'origin/0.12.0-dev' into chore/setup-lock-catalog-20261005
fix(types): onda 1 mecanica da divida de tipos — mypy 622→478, pyright 581→467 (#1586)
fix(setup): guarded interrupted-clone recovery (flext-r7po7) (#1577)
merge: adopt current environment and auto-fix owner cures
merge: converge with 0.12.0-dev tip 464c4ca6c (adopts #1584 auto-fixable census)
chore(lint): land the auto-fixable census (fmt+fix+mod+mod-text) (#1584)
fix(tests): adopt the make-environment suite cure from lane make-env-test (flext-k538b
closure) (#1581)
merge: converge with 0.12.0-dev tip 26f2334eb (adopts 1582/1575 + fleet cures)
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/mise-bootstrap-scratch-lifecycle-i7jz1-20261005
merge: adopt integration fixes into setup recovery lane
chore: adopt the gates src duplication cure from lane gates-src-duplication (flext-qwvb5
B-7) (#1582)
chore: adopt the gates src duplication cure from lane gates-src-duplication (flext-qwvb5
B-7)
chore: adopt the small-tests lint cure from lane lint-tests-small (flext-qwvb5 B-5)
(#1575)
merge: converge with 0.12.0-dev tip 04159b02d (codemod-alias tests family)
chore: absorb integration tip into the lint-tests-small adoption
merge: converge with integration tip 04159b02d (adopts B-1..B-4, 1572 bootstrap delete,
1570 toolchain table)
merge: converge with 0.12.0-dev tip 04159b02d
merge: adopt B-2 codemod-alias tests family (PR 1573, 4 lanes timestamp order)
merge: adopt B-1 codegen tests E501 cure (PR 1571, lane lint-codegen-e501)
chore: adopt the codemod-alias tests family (4 lanes, timestamp order) (flext-qwvb5 B-2)
(#1573)
chore: absorb integration tip into the codemod-alias adoption
merge: absorb configured infra integration into model producer
merge: converge with 0.12.0-dev tip cafb60feb (adopt PRs 1574/1571/1572/1570/1569 +
setup lock reconcile removal)
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/mise-bootstrap-scratch-lifecycle-i7jz1-20261005
chore: adopt the tests duplication cure from lane tests-duplication (flext-qwvb5 B-4)
(#1574)
chore: adopt the codegen tests E501 cure from lane lint-codegen-e501 (flext-qwvb5 B-1)
(#1571)
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/oic-bootstrap-contextmanager-xolve-20261005
chore: converge with merged tip b15b64dc8 (post-merge validation run)
refactor(mise): delete the bootstrap library behind the projected lock scripts
(flext-k538b) (#1572)
refactor(toolchain): declarative tools table replaces the per-tool fields
(flext-qwvb5.2) (#1570)
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/literal-export-inference-w4luo-20261005
merge origin/0.12.0-dev (105ddb5ab) into fix/rebind-consumer-admission-val20261004T1652
merge: absorb current infra integration into model producer
chore: adopt the partial-selection test-file cure from lane rjyh1 (flext-qwvb5 B-3)
(#1569)
chore: adopt the small-tests lint cure from lane lint-tests-small (flext-qwvb5 B-5)
merge: converge with 0.12.0-dev tip 8a984e235 (file-gate + setup reconcile wiring)
chore: adopt the tests duplication cure from lane tests-duplication (flext-qwvb5 B-4)
chore: adopt fix/codemod-alias-tests-infra-shapes-val20261004T1450 (flext-qwvb5 B-2,
timestamp order)
chore: adopt fix/codemod-alias-tests-u-shapes-val20261004T1440 (flext-qwvb5 B-2,
timestamp order)
chore: adopt fix/codemod-alias-tests-utilities-class-val20261004T1430 (flext-qwvb5 B-2,
timestamp order)
chore: adopt fix/codemod-alias-tests-infra-main-val20261004T1425 (flext-qwvb5 B-2,
timestamp order)
Merge remote-tracking branch 'infra-origin/0.12.0-dev' into
fix/docs-fence-outcomes-b4rft-20261005
chore: adopt the codegen tests E501 cure from lane lint-codegen-e501 (flext-qwvb5 B-1)
merge: absorb latest integration without discarding formatter checkpoint
chore: adopt the partial-selection test-file cure from lane rjyh1 (flext-qwvb5 B-3)
chore: absorb integration tip 8a984e235 (partial-selection cure + #1567) into the
toolchain-tools lane
feat(make): file-gate verb fleet-wide + wire the mise-lock reconcile on setup drift
(#1567)
merge: converge with 0.12.0-dev tip (val2026100418xx)
WIP: complete lazy scanner static validation (flext-w4luo.1) (#1565)
chore: absorb integration tip 47ae54ce8 into the toolchain-tools table lane
(flext-qwvb5.2)
merge: absorb landed lazy-init producer into SARIF test lane
Merge integration into reviewed lazy scanner candidate
WIP: adopt flat lazy export map generator (flext-w4luo.1) (#1562)
Merge integration into adopted lazy export map checkpoint
merge: absorb integration into SARIF evidence lane
Merge origin/0.12.0-dev into fix/rebind-consumer-admission-val20261004T1652
Merge origin/0.12.0-dev into style/lint-codegen-e501-val20261004T0956
Merge origin/0.12.0-dev into fix/codemod-broad-annotation-tests-val20261004T1510
Merge origin/0.12.0-dev into fix/codemod-inline-import-tests-val20261004T1505
Merge origin/0.12.0-dev into fix/codemod-alias-tests-infra-shapes-val20261004T1450
Merge origin/0.12.0-dev into fix/codemod-alias-tests-u-shapes-val20261004T1440
Merge origin/0.12.0-dev into fix/codemod-alias-tests-utilities-class-val20261004T1430
Merge origin/0.12.0-dev into fix/codemod-alias-tests-infra-main-val20261004T1425
Merge origin/0.12.0-dev into baseline
fix(codemod): restore the canonical generator-repair refusal in text gates (#1557)
Merge origin/0.12.0-dev into fix/text-gates-generator-repair-msg-val20261004T1415
merge: adopt the loc-cap split onto 0.12.0-dev
merge: adopt TC001 pydantic runtime roots onto 0.12.0-dev
Merge origin/0.12.0-dev into style/lint-codegen-e501-val20261004T0956
Merge origin/0.12.0-dev into fix/codemod-broad-annotation-tests-val20261004T1510
Merge origin/0.12.0-dev into fix/codemod-inline-import-tests-val20261004T1505
Merge origin/0.12.0-dev into fix/codemod-alias-tests-infra-shapes-val20261004T1450
Merge origin/0.12.0-dev into fix/codemod-alias-tests-u-shapes-val20261004T1440
Merge origin/0.12.0-dev into fix/codemod-alias-tests-utilities-class-val20261004T1430
Merge origin/0.12.0-dev into fix/codemod-alias-tests-infra-main-val20261004T1425
refactor(gates): read hook defaults from class data (#1556)
merge origin/0.12.0-dev into flext-8fjvg-gate-defaults
Merge origin/0.12.0-dev into fix/markdown-code-origin-qtmy2-val20261004T1410
merge: integrate origin/0.12.0-dev into epic/make-env-test-val20261004T1556
Merge origin/0.12.0-dev into fix/test-file-cache-hit-rjyh1-val20261004T1335
Merge origin/0.12.0-dev into fix/loc-cap-transaction-make-env-val20261004T0958
Merge origin/0.12.0-dev into fix/profile-child-rewrite-guhb3-val20261004T1400
Merge origin/0.12.0-dev into fix/tests-duplication-val20261004T0958
fix(pytest): make test-file reruns of a declared file exit green (flext-rjyh1) (#1552)
Merge origin/0.12.0-dev into fix/test-file-cache-hit-rjyh1-val20261004T1335
Merge origin/0.12.0-dev into baseline
Merge origin/0.12.0-dev into fix/text-gates-generator-repair-msg-val20261004T1415
merge: integrate origin/0.12.0-dev (d56dca798) into epic/make-env-test-val20261004T1556
fix(rules): ban-loose-module-object admits the facade's self-typed fetch\_global
singleton (cosmos-yj36e.15) (#1551)
Merge origin/0.12.0-dev into fix/test-file-cache-hit-rjyh1-val20261004T1335
fix(mod,pytest): retire the force-adding checkpoint and the conftest ini shim
(cosmos-z2vmw) (#1550)
Merge origin/0.12.0-dev into baseline
Merge origin/0.12.0-dev into baseline
fix(gen): regenerate the root initializer the #1399 merge left stale (#1407)
Merge fix/make-config-import: hoist ExternalCacheDirectorySpec (admin… (#1549)
fix(types): stop mypy 2.4 crashing on the infra service base (#1510)
test: import the tests u facade as published (ban-local-import-alias) (#1544)
fix(lint): wrap src lines above the 88-column limit (val202610040808) (#1547)
fix(codemod): authenticate ast-grep findings with the shared receipt (#1504)
fix(rules): ban-runtime-alias-rebind sees every imported name (flext-8sgay) (#1548)
refactor: import own owners as published in gates, services and docs scope
(ban-local-import-alias, ban-inline-import) (#1539)
fix(codegen): rebuild the CI shim farm from the pinned Mise release (#1545)
refactor: type src dict annotations through the t vocabulary (ban-broad-annotation)
(#1543)
fix(gates): mypy gate emits the verbose native trace its own report validator requires
(#1546)
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/mypy-gate-verbose-trace-20261004
fix: mod class-scope NameError guard and OPTIONS=Y verb contracts (cosmos-yj36e.18, .17)
(#1536)
Merge origin/0.12.0-dev into fix/codemod-alias-tests-u-val20261004T1045
Merge origin/0.12.0-dev into fix/codemod-broad-annotation-src-val20261004T1020
Merge origin/0.12.0-dev into fix/codemod-alias-src-misc-val20261004T1015
Merge origin/0.12.0-dev into baseline
fix(ci): run the type checkers in the CI check partition (#1541)
Merge origin/0.12.0-dev into fix/lint-src-line-length-val202610040808
Merge origin/0.12.0-dev into fix/loc-cap-transaction-make-env-val20261004T0958
Merge origin/0.12.0-dev into fix/tests-duplication-val20261004T0958
Merge remote-tracking branch 'infra-origin/0.12.0-dev' into
epic/mod-class-scope-val20261004T1005
Merge origin/0.12.0-dev into fix/codemod-alias-tests-u-val20261004T1045
Merge origin/0.12.0-dev into fix/codemod-broad-annotation-src-val20261004T1020
Merge origin/0.12.0-dev into fix/codemod-alias-src-misc-val20261004T1015
test: import flext\_infra.main as published (ban-local-import-alias) (#1540)
Merge origin/0.12.0-dev into fix/lint-src-line-length-val202610040808
Merge origin/0.12.0-dev into fix/loc-cap-split-val20261004T0958
Merge origin/0.12.0-dev into fix/tests-duplication-val20261004T0958
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/ci-shim-farm-rebind-val202610040808
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/ci-type-gates-ju3u2-val20261004
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/ci-type-gates-ju3u2-val20261004
Merge origin/0.12.0-dev into codemod-baseline-val20261004T0955
Merge origin/0.12.0-dev into fix/codemod-alias-src-misc-val20261004T1015
Merge origin/0.12.0-dev into fix/codemod-alias-tests-main-val20261004T1025
refactor(codegen): drop the dead mise render payload (flext-qwvb5.1) (#1542)
Merge origin/0.12.0-dev into fix/codemod-broad-annotation-src-val20261004T1020
Merge origin/0.12.0-dev into fix/codemod-alias-tests-u-val20261004T1045
Merge origin/0.12.0-dev into codemod-baseline-val20261004T0955
Merge origin/0.12.0-dev into fix/codemod-alias-src-misc-val20261004T1015
Merge origin/0.12.0-dev into fix/codemod-alias-tests-main-val20261004T1025
fix(lint): static-method recipe keeps override chains and receiver readers (flext-wc4sd)
(#1537)
Merge origin/0.12.0-dev into style/lint-tests-e501-val20261004T0956
Merge origin/0.12.0-dev into style/lint-tests-small-val20261004T0956
Merge origin/0.12.0-dev into style/lint-codegen-e501-val20261004T0956
fix(docs): retire TOC sentinel, default the markdown gates, drop legacy audit paths
(#1538)
style(lint): bind bootstrap exception messages before raising (val20261004T0956) (#1534)
Merge remote-tracking branch 'infra-origin/0.12.0-dev' into
epic/mod-class-scope-val20261004T1005
Merge origin/0.12.0-dev into style/lint-src-exc-msg-val20261004T0956
fix(rules): ban-runtime-alias-rebind catches import-then-rebind (flext-8sgay) (#1535)
Merge origin/0.12.0-dev into fix/codemod-alias-tests-main-val20261004T1025
Merge origin/0.12.0-dev into fix/codemod-alias-src-misc-val20261004T1015
Merge origin/0.12.0-dev into style/lint-src-exc-msg-val20261004T0956
fix(mod,layout): class-stem law admits the owner class nesting derives; keep the root
sgconfig.yml (val20261004T0825) (#1528)
Merge branch '0.12.0-dev' into fix/root-gates-class-stem-layout-val20261004
refactor(config): compose project managed artifacts in parse and merge steps (#1529)
Merge branch '0.12.0-dev' into fix/managed-artifacts-ruff-val20261003T2105
refactor(gates): remove the 12 src duplication clones (val202610040808) (#1533)
Merge origin/0.12.0-dev into style/lint-src-exc-msg-val20261004T0956
Merge origin/0.12.0-dev into fix/codemod-alias-tests-main-val20261004T1025
Merge origin/0.12.0-dev into fix/src-duplication-val202610040808
refactor(models): drop own-package import aliases in \_models (ban-local-import-alias)
(#1532)
Merge origin/0.12.0-dev into fix/codemod-alias-models-val20261004T0955
Merge origin/0.12.0-dev into fix/loc-cap-split-val202610040808
fix(codegen): keep Protocol terminal when projecting protocol owners (#1531)
fix(docs): restore the anchored docs policy template and manifest overrides (#1530)
On fix/src-duplication-val202610040808: srcdup-baseline
merge(0.12.0-dev): measure tip 761aa105c
merge(0.12.0-dev): adopt tip 761aa105c under the managed-artifacts loader split
refactor(bootstrap): spawn through u.Cli and split by concern below the LOC cap (#1525)
Merge origin/0.12.0-dev into fix/bootstrap-subprocess-split-val202610040808
fix(lint): hoist the process entry CLI import (#1527)
Merge origin/0.12.0-dev into fix/bootstrap-subprocess-split-val202610040808
Merge origin/0.12.0-dev into fix/lint-main-import-val202610040808
fix(codegen): emit actions/create-github-app-token@v3 with client-id (#1526)
Merge origin/0.12.0-dev into fix/bootstrap-subprocess-split-val202610040808
Merge infra-origin/0.12.0-dev into epic/docs-policy-val20261004
fix(config): accept project ManagedArtifacts.Ruff (#1513)
Merge origin/0.12.0-dev into fix/bootstrap-subprocess-split-val202610040808
docs(guides): re-project the root guides whose fences pass the fence Ruff policy (#1524)
merge(0.12.0-dev): adopt tip 1e0a361ba under the Ruff config field
merge(0.12.0-dev): adopt tip 1e0a361ba under the mypy 2.4 bound fix
merge(0.12.0-dev): adopt tip 1e0a361ba under the codemod receipt fix
fix(ci): keep private fetches on the minted app token (#1523)
fix(lint): identify the module inside its copyright notice (#1522)
fix(mod): keep a module-level base when its subclass stays outside (#1521)
fix(mod): keep class-suite sibling references at module level (#1520)
fix(lint): expand a stub that shares its signature's last line (#1519)
fix(lint): accept an inline body and a source-scan-ignored module (#1518)
fix(mod): keep class-nesting from dropping names callers still use (#1517)
fix(mod): replace a destination import of a shared helper being moved (#1516)
fix(mypy): resolve t through flext\_infra.typings at the four service bases
(val202610031920) (#1514)
fix(mod): replace a destination import of a shared helper being moved (#1512)
Merge remote-tracking branch 'origin/0.12.0-dev' into lane/mypy-internal-cure-20261003
merge: adopt 0.12.0-dev tip (CliResultValue bounds) under the typings import cure
merge(0.12.0-dev): adopt integration tip into the helper-move lane
fix(setup): provision absent gitlinks with a depth-1 clone (#1515)
merge(0.12.0-dev): adopt integration tip into the helper-move lane
merge: adopt integration tip into the shallow submodule lane
fix(test): let a slow-only file reach the test-file slow phase (#1511)
merge(0.12.0-dev): adopt the integration tip under the Ruff config field
merge(0.12.0-dev): adopt integration tip into the helper-move lane
fix(typing): bind service results through a module-level alias (#1509)
merge(0.12.0-dev): adopt integration tip into the slow-file lane
merge: integrate origin/0.12.0-dev into the mypy bound lane
fix(lint): hoist the process entry flext\_cli import (#1507)
merge(0.12.0-dev): adopt the integration tip under the mypy 2.4 bound fix
merge(0.12.0-dev): adopt integration tip before the lint entry import hoist
merge: integrate origin/0.12.0-dev into the mypy bound lane
fix(markdown): exclude release-please CHANGELOG output from the markdown gates (#1508)
fix(check): clear runtime census and markdown residuals on the tip (#1506)
merge: integrate origin/0.12.0-dev into the mypy bound lane
merge(0.12.0-dev): adopt integration tip into the check residual lane
merge(0.12.0-dev): adopt tip before the lint entry import hoist
fix(make): declare the profile-test verbs in the config SSOT (#1505)
merge(0.12.0-dev): adopt the tip under the codemod receipt fix
chore(test): declare the algar-oud-mig run-timeout measurement ceiling (300s) (#1503)
fix(test): declared file target never lets the testmon cache deselect it (#1502)
fix(docs): commit the generated bootstrap module page (#1501)
merge(0.12.0-dev): adopt tip under the bootstrap doc fix
feat(test): caller-overridable test target — make test accepts a single file (#1500)
feat(test): add make test-file FILE=\<path\> (val20261003T1900) (#1498)
merge(0.12.0-dev): adopt tip under the test-file tests
fix(codegen): the build hook rides in the sdist via force-include (#1497)
feat(test): add the test-file verb — one declared file through the phased testmon
pipeline (#1496)
fix(codegen): the declared build hook rides in the sdist (#1495)
fix(release): tag the merged release commit wherever it sits (#1494)
fix(release): the plan's tag listing demands a digit after the prefix (#1493)
fix(release): latest\_release\_tag skips foreign tag namespaces (#1492)
fix(codemod): restore the content-keyed rule catalog cache writer (flext-d6dn8) (#1491)
fix(docs): drop the retired machine\_path\_exempt\_paths key from the docs policy
template (flext-itpd1.10) (#1490)
fix(setup): locks only via make upg; setup runs despite mise/uv drift (flext-k538b)
(#1488)
fix(bootstrap): mise pin resolve exempt from dependency cooldown (#1487)
fix(make): every verb exports one GitHub credential under GITHUB\_TOKEN, GH\_TOKEN and
MISE\_GITHUB\_TOKEN (#1486)
feat(git): branch, stash, remote and merge-probe primitives for wip sweep (#1485)
fix(rules): exempt the stdlib-only native hook client from ban-ambient-environ-read
(#1484)
merge: absorb origin/0.12.0-dev (20be0757) into polecat lane flext-nfa5a
fix(rules): exempt the lazy defining module from ban-consumer-submodule-import (#1483)
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/lazy-defining-module-rule-exempt-20261002
fix(bootstrap): hold broken tool releases at their newest installable version (#1482)
fix(models): define MakeGateSuspensionSpec (referenced but never defined) (#1481)
fix(codegen): converge generator to the module-scope fleet — consumer make gen exit-0
(#1480)
fix(codegen): width-aware module-alias imports (flext-xjoph) (#1479)
fix(lint): TC001 OFF global (operator ruling 2026-10-03 02:57Z) (#1478)
fix(templates): drop invocation\_namespace kwarg (#1480)
fix(bootstrap): declare credential\_commands data (#1478)
fix(models): relocate suspensions field into MakeSpec body (#1477)
fix(models): relocate suspensions field into MakeSpec (v3) (#1474)
fix(models): declare check\_gate\_suspensions on MakeSpec (#1473)
fix(codegen): remove residual additions block (#1472)
chore(lint): I001 enforced; I002/I003 disabled; TC001 active (operator ruling
2026-10-03) (#1471)
fix(codegen): drop undefined 'rows' unpacking and dead additions block (#1470)
fix(codegen): derive project spec for existing trees in \_plan\_existing\_repository
(#1469)
fix(tooling): tests/python ruling glob survives excluded-root filter (#1468)
fix(lint): FBT003 ZERO em src/flext\_infra (\~203 sites, 3 ondas de agentes) (#1467)
fix(check): skip mypy verbose LOG lines in the JSON report parser (#1466)
fix(config): declare ci.local\_check\_gates (schema now requires it) (#1465)
fix(models): hoist ExternalCacheDirectorySpec to module level (#1464)
Merge fix/make-config-import: hoist ExternalCacheDirectorySpec (admin, direct)
config(tooling): tests/python/\*\* ruff exemptions (mcb tests migration) (#1463)
integrate: wip/stash-35d24e39fe-adopt (#1462)
integrate: wip/stash-35d24e39fe-adopt — develop wins (full 0.12.0-dev tree)
integrate: wip/sonarcloud-readonly-issues (#1461)
integrate: wip/primary-preserve-20260928-1400 (#1460)
integrate: wip/primary-preserve-20260928-1400 — develop wins (full 0.12.0-dev tree)
integrate: r3-v2 (#1459)
integrate: r3-v2 — develop wins (full 0.12.0-dev tree)
integrate: r3-cache-contract-dedup (#1458)
integrate: preserve/pr-1140-adopt-20261002 (#1456)
integrate: preserve/pr-1140-adopt-20261002 — develop wins (full 0.12.0-dev tree)
integrate: preserve/make-fix-ast-unparse-corruption-20260927 (#1455)
integrate: preserve/make-fix-ast-unparse-corruption-20260927 — develop wins (full
0.12.0-dev tree)
integrate: preserve/infra-suite-profile-20260930-20261002 (#1454)
integrate: preserve/infra-suite-profile-20260930-20261002 — develop wins (full
0.12.0-dev tree)
integrate: preserve/infra-r6-superseded-20260930 (#1453)
integrate: preserve/infra-r6-superseded-20260930 — develop wins (full 0.12.0-dev tree)
integrate: pr-1233 (#1452)
integrate: merge/integration-wave-20261001 (#1451)
integrate: hotfix/testmon-selection-order-20260924 (#1450)
integrate: hotfix/testmon-selection-order-20260924 — develop wins (full 0.12.0-dev tree)
integrate: fix/worktree-external-venv-20261001 (#1449)
integrate: fix/upg-mise-lock-resilience-resync-20260930 (#1448)
integrate: fix/upg-lock-order-20261001 (#1447)
integrate: fix/tip-mise-projection-lock-20261001 (#1446)
integrate: fix/tip-mise-projection-lock-20261001 — develop wins (full 0.12.0-dev tree)
integrate: fix/tip-boot-wiring-20261001 (#1445)
integrate: fix/tip-boot-wiring-20261001 — develop wins (full 0.12.0-dev tree)
integrate: fix/template-endif-fleet-gen-20261001 (#1444)
integrate: fix/template-endif-fleet-gen-20261001 — develop wins (full 0.12.0-dev tree)
integrate: fix/sonarcloud-issue-model-descriptions-20261002 (#1443)
integrate: fix/review-1234-runner-env-20261001 (#1442)
integrate: fix/no-self-use-codemod-20261002 (#1441)
integrate: fix/mise-toml-tool-pins-align-20261001 (#1438)
integrate: fix/mise-gh-auth-20260924 (#1437)
integrate: fix/lazy-init-fixed-point-20261001 (#1436)
integrate: fix/l2-merge-cures-20261001 (#1434)
integrate: fix/l2-merge-cures-20261001 — develop wins (full 0.12.0-dev tree)
integrate: fix/infra-runner-final-item-stop-20260930 (#1433)
integrate: fix/infra-mypy-timeout-constant-ref (#1432)
integrate: fix/infra-mypy-timeout-constant-ref — develop wins (full 0.12.0-dev tree)
integrate: fix/infra-env-contracts-ssot-layer-20260930 (#1431)
integrate: fix/infra-config-overwrite-adopt-20261001 (#1430)
integrate: fix/infra-codemod-architecture-20260930 (#1429)
integrate: fix/infra-codemod-architecture-20260930 — develop wins (full 0.12.0-dev tree)
integrate: fix/infra-aihub-worker-ceiling-min-20260929 (#1428)
integrate: fix/infra-aihub-worker-ceiling-min-20260929 — develop wins (full 0.12.0-dev
tree)
integrate: fix/infra-1140-bootstrap-20260930 (#1427)
integrate: fix/docs-shared-test-import-policy-20260930 (#1426)
integrate: fix/docs-policy-template-ssot-20260930 (#1425)
integrate: fix/bootstrap-self-heal (#1424)
integrate: converge/open-prs-20261001 (#1423)
integrate: converge/open-prs-20261001 — develop wins (full 0.12.0-dev tree)
integrate: converge/extermination-green-20261001 (#1422)
integrate: converge/extermination-green-20261001 — develop wins (full 0.12.0-dev tree)
integrate: converge/extermination-green-20261001 — develop wins (full 0.12.0-dev tree)
integrate: converge/extermination-20261001-pr1260 (#1421)
integrate: converge/extermination-20261001-pr1260 — develop wins (full 0.12.0-dev tree)
integrate: config/scripts-ruff-exceptions-names (#1420)
integrate: chore/upg-relock-core-installed-distributions-20261002 (#1419)
integrate: adopt/pytest-deadline-20261001 (#1418)
integrate: adopt/pytest-deadline-20261001 — develop wins (full 0.12.0-dev tree)
integrate: adopt/infra-1257-20261001 (#1417)
integrate: adopt/infra-1257-20261001 — develop wins (full 0.12.0-dev tree)
Merge remote-tracking branch 'origin/0.12.0-dev' into HEAD
Merge remote-tracking branch 'origin/0.12.0-dev' into HEAD
Merge remote-tracking branch 'origin/0.12.0-dev' into HEAD
Merge remote-tracking branch 'origin/0.12.0-dev' into HEAD
Merge remote-tracking branch 'origin/0.12.0-dev' into HEAD
Merge remote-tracking branch 'origin/0.12.0-dev' into HEAD
Merge remote-tracking branch 'origin/0.12.0-dev' into HEAD
Merge remote-tracking branch 'origin/0.12.0-dev' into HEAD
Merge remote-tracking branch 'origin/0.12.0-dev' into HEAD
Merge remote-tracking branch 'origin/0.12.0-dev' into HEAD
Merge remote-tracking branch 'origin/0.12.0-dev' into HEAD
Merge remote-tracking branch 'origin/0.12.0-dev' into HEAD
Merge remote-tracking branch 'origin/0.12.0-dev' into HEAD
Merge remote-tracking branch 'origin/0.12.0-dev' into HEAD
Merge remote-tracking branch 'origin/0.12.0-dev' into HEAD
Merge remote-tracking branch 'origin/0.12.0-dev' into HEAD
integrate: preserve/stabilize-20261002-20261002 (#1457)
Merge branch '0.12.0-dev' into preserve/stabilize-20261002-20261002
Merge remote-tracking branch 'origin/0.12.0-dev' into HEAD
Merge remote-tracking branch 'origin/0.12.0-dev' into HEAD
Merge remote-tracking branch 'origin/0.12.0-dev' into HEAD
Merge remote-tracking branch 'origin/0.12.0-dev' into HEAD
Merge remote-tracking branch 'origin/0.12.0-dev' into HEAD
Merge remote-tracking branch 'origin/0.12.0-dev' into HEAD
chore: integracao em lote — mise-version-contract-guard + lazy-facade-typing (#1440)
integrate: fix/mise-version-contract-guard-20260930 (#1439)
Merge branch '0.12.0-dev' into fix/mise-version-contract-guard-20260930
integrate: fix/lazy-facade-typing (#1435)
Merge branch '0.12.0-dev' into fix/lazy-facade-typing
merge: integra fix/mise-version-contract-guard-20260930 na 0.12.0-dev (integracao em
lote, diretriz do operador)
merge: integra fix/lazy-facade-typing na 0.12.0-dev (integracao em lote, diretriz do
operador)
fix(lint): apply the promoted autofixes and the no-self-use recipe fleet-wide (#1395)
fix(gen): land the corrected lazy-init emission unlocked by the #1402 NameError cure
(#1403)
fix(lint): E501 ZERO em src/flext\_infra (199 sites, 3 ondas de agentes) (#1415)
fix(lint): E501 sweep (\~132 sites, 12 arquivos) — flext-infra src (#1414)
fix(codemod): settle the rule catalog cache lane onto the integration tip (flext-d6dn8)
fix(lint): derive the copyright notice only when a copyright finding asks for it
(flext-kyv1t) (#1413)
\[WIP\] merge fix/lint-notice-lazy-20261003 for combined verification
fix(check): keep the mypy JSON stream clean for the strict report parser (#1412)
\[WIP\] merge 0.12.0-dev (382d73570, #1410) into fix/rule-catalog-cache-20261002
fix(deps): relock with the mypy\<2.4.0 constraint (flext-r4hyh) (#1410)
fix(codegen): bootstrap owner imports lazy helpers from flext\_core.lazy, never its own
root (flext-911cm) (#1409)
merge 0.12.0-dev (db9fc5bff, #1408) into fix/core-upg-cyclic-binding-20261002
fix(deps): hold mypy\<2.4.0 (upstream deferral crash) (#1408)
fix(deps): first\_party\_namespaces takes the project dir only; gen/fix/fmt fixed point
on the tip (#1406)
merge 0.12.0-dev into fix/tool-tables-project-dir-20261002
fix(gen): commit the regenerated lazy-init import form (fixed point) (#1405)
Merge remote-tracking branch 'origin/0.12.0-dev' into sync-1403-20261002
Merge remote-tracking branch 'origin/0.12.0-dev' into sync-1395-20261002
\[WIP\] Merge origin/0.12.0-dev (#1402 NameError fix) into relock lane
chore(upg): relock flext-core so u.installed\_distributions resolves (make test was
AttributeError) (#1404)
merge 0.12.0-dev (#1402) into chore/upg-core-installed-distributions-20261002
fix(docs): restore the docs-fix fence runner the #1385 merge overwrote (#1401)
fix(deps): bind the renamed path parameter in first\_party\_namespaces (P0: NameError
killed the gen conform plan) (#1402)
Merge remote-tracking branch 'origin/0.12.0-dev' into land-1395-20261002
fix: shared workspace fixture owner + cure integration-tip reds (8e22b066d, #1381)
(#1399)
\[WIP\] merge origin/0.12.0-dev into fix/docs-fix-1385-repair-20261002
docs(smells): correct SMELLS\_QLTY\_ARGS docstring (closed-PR recovery, stream R)
(#1400)
Merge branch '0.12.0-dev' into fix/workspace-sonar-scope-findings-20261002
fix(config): declare the ruff isort table MANAGED (derived first-party projection)
(#1398)
fix(codegen): lazy helpers importados do root flext\_core (nunca do submódulo .lazy)
(#1397)
\[WIP\] fix(metadata): consume u.installed\_distributions at every distribution scan
(#1396)
fix(validate): restore the FlextInfraSonarcloudIssues import (regression of the #1392
lineage) (#1394)
\[WIP\] preserve uncommitted state of infra-mise-resync (abandoned since 2026-09-30)
chore(ssot): track the integrated flext-infra tip 2b5212275 (#1393)
\[WIP\] preserve uncommitted state of infra-codemod-architecture-20260930 (abandoned
since 2026-09-30)
\[WIP\] Merge origin/0.12.0-dev into fix/upg-converges-old-generation-20261002
fix(deps): restore first\_party\_namespaces payload signature (lost in the #1385 merge)
(#1392)
fix(bootstrap): a resolved Mise release reaches the pin when the bumped lock is
unchanged (#1391)
style(fmt): converge the tip's make fmt fixed point (bootstrap.py, sonarcloud scope
test) (#1390)
\[WIP\] merge origin/0.12.0-dev (d17365746) into
fix/workspace-sonar-scope-findings-20261002
wip(sonarcloud): readonly issues client + sync surface (rescued) (#1381)
merge 0.12.0-dev — keep the readonly-issues client WIP, adopt dev landings
\[WIP\] preserve uncommitted state of aihub-workers-min-20260929 (abandoned since
2026-09-30)
fix(bootstrap): remove dead mise lock stages crashed before their commit point (#1389)
Hotfix/tip stabilize 20261001 (#1385)
merge: PR #1381 sonarcloud readonly issues client with develop wins
\[WIP\] merge origin/0.12.0-dev into fix/workspace-sonar-scope-findings-20261002
merge 0.12.0-dev — keep the hotfix-stabilize cures, adopt dev's parallel landings
merge: PR #1385 hotfix/tip stabilize with develop wins
fix(mod): clear the lint findings in the class-nesting owner-derivation files (#1370
follow-up) (#1388)
merge: update protocol-move and bootstrap fixes onto current 0.12.0-dev (#1384)
Fix/infra complexity rest 20261002 (#1386)
\[WIP\] refactor(codegen): split version-file execute into project sync… (#1387)
\[WIP\] Merge origin/0.12.0-dev into fix/upg-converges-old-generation-20261002
fix(bootstrap): retire unjournaled mise lock stages as killed-run orphans (#1378)
\[WIP\] Merge origin/0.12.0-dev into fix/infra-complexity-rest-20261002
feat(mod): class-nesting derives the module owner for loose modules (#1370)
feat(lint): static-method fix recipe for Ruff no-self-use (PLR6301) (#1363)
fix(codegen): workspace SonarCloud scope excludes member checkouts (#1382)
Merge origin/0.12.0-dev into fix/no-self-use-codemod-20261002
\[WIP\] merge origin/0.12.0-dev into fix/workspace-sonar-scope-20261002
Merge origin/0.12.0-dev into feat/class-nesting-owner-derivation-20261002
chore(gen): land the current renders post-absorption
Merge pull request — SSOT exception for the promoted-command script surface
(operator-authorized administrative merge; config data, render fixed point proven,
unblocks fleet member lifts)
fix(codegen): root workspace checks out its flext-infra subproject in CI (#1373)
Merge remote lane commit 40572761f (relock) into fix/no-self-use-codemod-20261002
\[WIP\] Merge origin/0.12.0-dev into feat/class-nesting-owner-derivation-20261002
\[WIP\] Merge origin/0.12.0-dev (0a08f13e5 base fix) into
fix/no-self-use-codemod-20261002
fix(bootstrap): setup never locks; Mise offline outside install/upg; one lock pass per
upg (#1377)
Merge origin/0.12.0-dev into fix/mise-offline-20261002
Merge origin/0.12.0-dev into fix/mise-offline-20261002
fix(bootstrap): self-heal stale mise.lock (adopt jscpd@5.3.3 from manifest) (#1376)
wip(tooling-rules-kebab): record WIP — bootstrap error wrapping + projection refresh
(#1374)
fix(rules): require-service-facade-layers owns the root facade only (#1372)
fix(bootstrap): cooldown-aware latest fallback in tool bootstrap resolve (#1371)
\[WIP\] Merge origin/0.12.0-dev into feat/class-nesting-owner-derivation-20261002
fix(tooling): converte códigos ruff para nomes kebab-case (#1369)
fix(tooling): TRY401 -\> verbose-raise (#1368)
fix(config): jscpd re-pin 5.3.3 (5.4.0 sem assets) (#1366)
fix(codegen): import the lazy helpers from the defining module everywhere (#1362)
config(tooling): operator ruling for scripts/\*\* ruff exemptions (mcb migration)
(#1365)
merge: adopt the bootstrap resilience cure (#1361) into the lazy-module lane
fix(bootstrap): library-owned dirty-tree recovery, submodule-first generator, jscpd hold
(#1361)
fix(infra): one first-party rule, strict exception map, startup/gate performance (S1
follow-up to #1353) (#1360)
merge: adopt 0.12.0-dev (#1357) into the stabilization lane
merge: update protocol-move and bootstrap fixes onto current 0.12.0-dev
\[WIP\] merge 0.12.0-dev into fix/infra-relock-20261001 — adopt the 9 newest tip commits
Hotfix/tip stabilize 20261001 (#1357)
Merge branch '0.12.0-dev' into hotfix/tip-stabilize-20261001
merge: adopt 0.12.0-dev (#1353-#1356) into the stabilization lane
fix(docs): emit the converged DocsAuditPolicySpec from the docs\_confi… (#1356)
\[WIP\] fix(rules): one first-party owner and one fleet exemption map —… (#1355)
\[WIP\] merge: adopt 0.12.0-dev into the upg-resolver lane (#1354)
Merge branch '0.12.0-dev' into hotfix/tip-stabilize-20261001
fix(infra): bootstrap order cure + gate routing — unblock the fleet CI (#1353)
\[WIP\] merge origin lane head (adopt 2dc1bbe97)
merge: adopt the run-wall render cure (#1352) and the blank-lines renderer fix (#1351)
Merge pull request #1352 from flext-sh/fix/pytest-run-timeout-render-resolution —
per-project pytest run wall reaches the make wrapper (operator-authorized administrative
merge; required gates green — ci red = pre-existing tip generation instability,
reproduced without this change, owned by the fleet stabilization lane)
\[WIP\] merge 0.12.0-dev into fix/infra-relock-20261001 — adopt #1351
merge: adopt the tip's fleet relock (#1348) into the lazy-module lane
fix(codegen): blank\_lines\_before\_exports = \\n único (#1351)
WIP on fix/flext-tests-lock-bump-20261002: ade6cb648 fix(deps): bump flext-tests lock to
a51262e1 (#175) — tip wheel ships \_protocols/enforcement.py; committed lock still
pinned c9a9ca53 whose protocols.py imports the missing module, breaking every consumer
make test
\[WIP\] merge: adopt 0.12.0-dev (#1348, #1349) into the upg-resolver lane
\[WIP\] merge 0.12.0-dev into fix/infra-relock-20261001 — adopt #1343..#1349
fix: journal bootstrap surfaces and preserve pytest exits (#1348)
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/infra-config-overwrite-adopt-20261001
fix(rules): the ambient-environ rule exempts the config bootstrap boundary (#1349)
\[WIP\] merge: adopt 0.12.0-dev into the upg-resolver lane
merge: adopt current Infra integration into bootstrap lane
Fix/protocol move usage rewrite (#1347)
Merge branch '0.12.0-dev' into fix/protocol-move-usage-rewrite
fix(infra): boot receipt parser, lazy-import ordering at the renderer, dead sed rule
(re-derived) (#1346)
fix(infra): boot receipt parser, lazy-import ordering at the renderer, dead sed rule
(#1341)
Merge branch '0.12.0-dev' into fix/boot-receipt-lazy-order-20261001
fix(bootstrap): a manifest ahead of the lock self-heals in the setup bootstrap (#1345)
fix(rope): the snapshot project reads the scan-ignore SSOT (#1344)
chore(tooling): cosmos-charts run-timeout override 600s (#1338)
fix(rope): the workspace index reads the scan-ignore SSOT (#1343)
merge: adopt declared upg bootstrap from existing lane
merge: adopt current Infra integration before upg bootstrap
\[WIP\] merge(0.12.0-dev): integrate the tip (#1335-#1342) into the relock lane
fix(bootstrap): the lock transaction owns redeclared sidecar paths (#1342)
merge: absorb 0.12.0-dev tip (jscpd hold lifted, relock via upg #1340) into the charts
timeout + python pin model lane
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/infra-config-overwrite-adopt-20261001
fix(config): lift the jscpd hold (all six platforms ship assets); relock via make upg
(#1340)
\[WIP\] merge: integrate origin/0.12.0-dev
fix(config): the toolchain python\_version carries the minor line only (#1339)
merge: rebase protocol-move hotfix onto current 0.12.0-dev tip
fix(codemod): the semantic inventory reads the scan-ignore SSOT (#1337)
fix(config): python\_version pinado 3.13.15 (3.13.16 sem assets macos-x64) (#1336)
fix(config): re-pin jscpd 5.3.3 (5.3.2 não resolve) (#1335)
\[WIP\] merge(0.12.0-dev): integrate the tip into the relock lane
fix(conform): fresh-import probes run in the target checkout's own environment (#1334)
feat(mod): rule config-dict-from-constants (#1333)
feat(lint): Google docstring convention (operator ruling); exterminate docs
api\_modules; realign stale tests (#1332)
merge(0.12.0-dev): integrate #1330 and #1331 into the follow-up lane
merge(infra): adopt integration runner repair
\[WIP\] merge: integrate origin/0.12.0-dev for the ConfigDict-from-constants rule
fix(runner): owns-no-tests reads the pytest python-files SSOT (#1331)
fix(models): field defaults become deep-copyable (rule
pydantic-mappingproxy-default-factory) (#1330)
\[WIP\] merge: integrate origin/0.12.0-dev for the mappingproxy default codemod
merge(0.12.0-dev): integrate #1327 and #1329 into the follow-up lane
\[WIP\] merge: integrate origin/0.12.0-dev 0e4b206bf (#1325 restored docs.api\_modules;
its form wins on the tip, extermination deferred to the owner)
fix: drop the stale #1323 hunks that broke the tip's config and pyrefly gate (#1329)
Fix/sed distribution scope 20261001 (#1327)
Merge branch '0.12.0-dev' into fix/sed-distribution-scope-20261001
merge(0.12.0-dev): integrate #1323, #1324 and #1328 into the follow-up lane
Tip config model sync 20261001 pr (#1325)
Merge branch '0.12.0-dev' into tip-config-model-sync-20261001-pr
fix: repair the tip after the #1295 merge; lazy-init and Raises fixes; realign the tests
the setup red hid (#1328)
Hotfix/tip stabilize 20261001 (#1324)
Fix/oud worker ceiling 20261001 (#1323)
Merge branch '0.12.0-dev' into fix/oud-worker-ceiling-20261001
\[WIP\] merge: integrate origin/0.12.0-dev 9fd121512 (#1301) before landing the #1295
cure
fix(models): drop the orphaned RopeRules references (#1301)
merge(0.12.0-dev): integrate #1322, #1295 and #1317 into the follow-up lane
\[WIP\] merge: integrate origin/0.12.0-dev d16ba2339 (#1322 mise hold 2026.9.13 + relock
+ #1289 repair; supersedes this lane's hold commit)
\[WIP\] merge: integrate origin/0.12.0-dev 3f23cde52 (#1295) to exterminate its
merge-storm residue
fix(toolchain): relock to the configured holds; Mise hold 2026.9.13; repair the #1289
merge (#1322)
Merge branch '0.12.0-dev' into fix/rope-rules-orphans-20261001
fix(config): reconcile tooling/codegen with the exterminated model schema — bootstrap
GREEN (#1295)
Merge branch '0.12.0-dev' into fix/bootstrap-config-reconcile-20261001
\[WIP\] merge: integrate origin/0.12.0-dev 30e499ba6 into the mise hold hotfix lane
fix(codegen): match exact external gitignore markers (#1317)
merge: adopt current Infra integration into Sed identity lane
merge(0.12.0-dev): integrate #1320 and #1289 into the relock lane
\[WIP\] merge: integrate origin/0.12.0-dev for the mise hold bootstrap hotfix
\[WIP\] merge: adopt 0.12.0-dev into the infra closure lane (#1289)
Merge branch '0.12.0-dev' into converge/infra-closure-20261001
\[WIP\] merge: integrate origin/0.12.0-dev for the candidate re-bootstrap (#1320
credential sources)
\[WIP\] fix(bootstrap): declared GitHub credential sources; relock the toolchain to the
configured holds (#1320)
\[WIP\] merge(0.12.0-dev): integrate #1319 and #1321 into the relock lane
fix(gates): embedded python blocks are python behavior by construction (#1321)
fix(mod): drop the sed rule targeting an exterminated doc; converge bootstrap receipts
(#1319)
\[WIP\] merge(0.12.0-dev): integrate the tip (#1316, #1313, #1306, #1318) into the
relock lane
merge: integrate current 0.12.0-dev into Sed identity cure
\[WIP\] merge: integrate origin/0.12.0-dev acadcb606 for the candidate bootstrap
campaign
fix(gates): duplication reads jscpd virtual names as their real files (#1318)
merge: adopt current infra integration into gitignore fix lane
fix(refactor): keep batch namespace move running past one failed block (#1306)
Merge branch '0.12.0-dev' into fix/protocol-move-usage-rewrite
fix(codemod): scope packaged Sed rules to their declared distribution (#1313)
Fix/infra config overwrite adopt 20261001 (#1316)
fix(codegen): preserve declared external gitignore blocks (#1314)
fix(toolchain): pin jscpd 5.3.2 — the only release lockable across all six platforms
(#1315)
fix(infra): repair the tip after the admin-merge cascade; make mod judges only its
rewrites (#1312)
Fix/mod text declared markdown 20261001 (#1284)
Merge branch '0.12.0-dev' into fix/mod-text-declared-markdown-20261001
On wip/infra-stabilize-20261001: make-fix residue pre-1312-adopt
\[WIP\] merge(0.12.0-dev): adopt #1308/#1310/#1311/#1125; the tip owns the toolchain
releases
Fix/ruff compose signature 20260929 (#1126)
Merge branch '0.12.0-dev' into fix/ruff-compose-signature-20260929
\[WIP\] merge(#1309): adopt the compose\_per\_file\_ignores naming and complete it
chore(gen): accept the regenerated mise and lazy-init projections (#1125)
Merge branch '0.12.0-dev' into fix/mise-jscpd-relock-tip-20260929
fix(deps): ensure\_ruff apply\_payload composes per-file-ignores (#1311)
\[WIP\] merge: integrate origin/0.12.0-dev 824da2282; the tip now carries this lane's
make-fix output
fix(codegen): context\_render composes per-file-ignores (Ruff overlay exterminated)
(#1310)
\[WIP\] merge(0.12.0-dev): adopt the #1294-#1307 landings into the module-layout lane
merge: adopt current Infra integration and retain source cure
merge: PRs #1124/#1125 (mise jscpd host-invariant + relock tip) na ponta (#1308)
merge: absorve fix/mise-jscpd-host-invariant (PR #1124)
fix(config): drop the overwrite keys reintroduced beside the exterminated field (#1307)
fix(deps): classmethod binding name and declared set type (follow-up to #1110) (#1118)
fix(codemod): exterminate the duplicate no-self-use rule whose fix corrupts bodies
(#1305)
Merge branch '0.12.0-dev' into fix/ruff-heal-refinements-20260929
test(codegen): elect the workspace ruling — members self-scope, the root plans zero
(#1179)
Merge branch '0.12.0-dev' into fix/beads-gate-lock-vocabulary-20260930
Fix/latest selectors 20261001 (#1285)
Merge branch '0.12.0-dev' into fix/latest-selectors-20261001
merge: adopt #1298 mise atomic transaction + #1302 + #1294
test: follow physical external Make environment contract (#1161)
fix(integration): reconcilia o contrato config-model da ponta e religa os readers
perdidos (#1299)
\[WIP\] fix(codegen,mod): make mod works again; notice and \_\_all\_\_ layout phases;
Mise and jscpd holds (#1304)
Merge branch '0.12.0-dev' into feat/module-layout-mod-phases-20261001
merge: integrate the remote PR branch updates
infra: relock latest tool selectors after content-gitlink merge (#1294)
fix(infra): publish Mise lock and sidecars as one recoverable transaction (#1298)
fix(mod): constrain declared CSV campaigns to owned paths (#1302)
merge: adopt #1300 core lazy helpers and #1293 Beads projection
\[WIP\] merge: integrate origin/0.12.0-dev ffc96ebca (#1293) for its post-merge proof
feat(codegen): publish declared core lazy helpers at package root (#1300)
\[WIP\] fix(template): render the Beads projection in Gas City's canonical form (#1293)
merge: adopt the extermination-wave tip (#1282 + jscpd re-pin)
Merge branch '0.12.0-dev' into fix/nonpackage-gitlink-postmerge-20261001
Merge branch '0.12.0-dev' into fix/mise-lock-atomic-20261001
Merge branch '0.12.0-dev' into fix/core-lazy-generator-policy-20261001
Merge branch '0.12.0-dev' into fix/mod-declarative-csv-20261001
\[WIP\] merge(0.12.0-dev): adopt the #1282 landing 0e8280b50 into the module-layout lane
\[WIP\] merge: adopt 0.12.0-dev 0e8280b50 (#1282) — lane tree equals the tip
merge: adopt the 0.12.0-dev tip into the config-model sync lane
\[WIP\] converge: extermination wave 2 — #1280 adoption, generic lint recipes, codemod
owner partition (#1282)
Merge branch '0.12.0-dev' into converge/extermination-20261001
fix(config): re-pin jscpd 5.3.3 (5.4.0 segue irresolvavel) (#1303)
merge: adopt current Infra integration after release gate landing
merge: adopt current infra integration into CSV campaign guard
\[WIP\] merge(0.12.0-dev): adopt the #1280 landing a5099219f; the lane already carries
its content
\[WIP\] merge: adopt 0.12.0-dev a5099219f (#1280) into the tip-stabilization lane
fix(infra): integrate DcBackup generation and gate repairs (#1280)
merge: absorve a lane do #1280 (DcBackup + gate repairs) na ponta
\[WIP\] merge: join the member checkout with the lane head e1dbbe530
Merge remote-tracking branch 'origin/fix/release-packaging-boundary-20261001' into
fix/mise-lock-atomic-20261001
\[WIP\] merge(#1280): adopt the qlty/census gate separation; keep the owners its tip
merge regressed
\[WIP\] merge(0.12.0-dev): adopt #1197/#1287/#1288/#1296/#1297; keep the newer owners a
stale lane overwrote
Merge remote-tracking branch 'origin/fix/release-packaging-boundary-20261001' into
fix/mise-lock-atomic-20261001
merge: adopt fail-closed qlty publication baseline
merge: adopt updated qlty fixture from infra integration candidate
merge: adopt current PR 1280 integration head
merge: adopt current infra generator and quality gate baseline
merge: adopt existing Mise lock stage owner from PR 1286
chore: absorb the integration tip into bootstrap repair
fix(adapters): u.TypeAdapter -\> u.type\_adapter (fabrica estavel do core) (#1297)
fix(adapters): re-aplica u.TypeAdapter (o rebuild restaurou m.TypeAdapter nao chamavel)
(#1296)
merge: adopt integration generator and gitlink fixes without discarding modular owners
\[WIP\] merge(#1280): adopt the declarative text codemods and the config-derived CI
branches
\[WIP\] merge(0.12.0-dev): adopt #1281/#1290/#1291/#1292; keep the decomposed owners
#987 shadowed
Merge branch '0.12.0-dev' into fix/infra-external-env-tests-20260930
Merge branch '0.12.0-dev' into fix/beads-gate-lock-vocabulary-20260930
fix(docs): emit the machine-path frozen-evidence exempt in the docs\_config template
(#1197)
Merge branch '0.12.0-dev' into fix/docs-config-frozen-evidence-exempt-20260930
Fix/bootstrap latest 20261001 (#1288)
fix(infra): wire the conform collaborators bundle under its data name (#1287)
\[WIP\] fix(config): restore the make model fields lost by a stale-file… (#1290)
Merge branch '0.12.0-dev' into hotfix/beads-config-gc-canonical-20261001
Merge branch '0.12.0-dev' into fix/conform-collaborators-wiring-r2
Merge branch '0.12.0-dev' into fix/bootstrap-latest-20261001
Fix/workspace self test testmon (#1291)
Merge branch '0.12.0-dev' into fix/tip-config-schema-skew-20261001
Merge branch '0.12.0-dev' into fix/workspace-self-test-testmon
fix(models): restore the artifact container tail truncated by the merge (#1292)
\[WIP\] merge(#1280): adopt the static-method migration and the docs wrap
\[WIP\] adopt unpublished stash 64d3944f4b (flext-infra) (#987)
Merge branch '0.12.0-dev' into wip/stash-64d3944f4b-adopt
merge: adopt concurrent infra documentation
\[WIP\] fix(template): lock mise only from the manifest gen rendered (#1283)
fix(workspace): materialize declared content gitlinks during setup (#1281)
Fix/mypy cache gate r1 20260930 (#1275)
Merge branch '0.12.0-dev' into fix/mypy-cache-gate-r1-20260930
Fix/testmon make test ci 20261001 (#1273)
Merge branch '0.12.0-dev' into fix/testmon-make-test-ci-20261001
Merge integration into non-package gitlink setup lane
merge(#1280): adopt the release-packaging lane, every hunk reviewed
merge(0.12.0-dev): adopt the tip, every hunk reviewed; exterminations stay exterminated
merge: integrate testmon CI cache while retaining full-suite contract
merge: integrate mypy cache gate fixes without fast forward
Merge remote-tracking branch 'origin/fix/bootstrap-hacks-20261001' into
converge/extermination-20261001
Merge integration base into Flext Infra repair lane
fix(infra): complete the extermination-wave wiring (models, constants, configs, pins)
(#1269)
merge: integrate latest 0.12.0-dev into testmon lane
Merge remote-tracking branch 'origin/0.12.0-dev' into pr-1273
fix(template): restore single-body verb contract; converge overnight projections (fleet
gen cure) (#1268)
chore: adopt the orphan-endif template cure
Merge remote-tracking branch 'origin/0.12.0-dev' into pr-1275
Merge remote-tracking branch 'origin/0.12.0-dev' into pr-1275
fix(infra): drop the orphan endif in the project Makefile template (#1279)
chore: integrate the latest convergence state
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/template-endif-fleet-gen-20261001
fix(infra): initialize the inline facade binding view (#1278)
fix(infra): merge the integration-tip symbol recovery into 0.12.0-dev (#1277)
Merge remote-tracking branch 'origin/fix/integration-tip-symbol-recovery-20261001' into
fix/integration-recovery-merge
merge(0.12.0-dev): adopt L2 consumer rewiring into testmon lane
fix(infra): import c in deps\_tool\_config\_linters for deferred annotations (#1276)
\[WIP\] converge: #1234 review fixes + testmon per-marker env + #1257/#1259 adoption
(#1271)
Merge branch '0.12.0-dev' into fix/review-1234-runner-env-20261001
fix(infra): restore the mangled ProjectRenderContext packaged-data fields (#1274)
\[WIP\] fix(docs): restore the typed overview preview limits docs\_render reads (#1266)
fix(infra): resolve\_data\_excludes is a staticmethod like its sibling (#1272)
fix(infra): finish the L2 merge cures — exterminated names stay out, consumers rewired
(#1259)
Merge branch '0.12.0-dev' into fix/l2-merge-cures-20261001
fix(infra): implement resolve\_data\_excludes for the packaging phase (#1270)
Merge branch '0.12.0-dev' into fix/l2-merge-cures-20261001
fix(infra): declare packaged\_data\_excludes on PyprojectDeclaredTopology (#1267)
merge(0.12.0-dev): adopt current integration into testmon lane
merge current flext-infra integration base
merge(0.12.0-dev @26949866b): adopt #1260-#1264; keep slow-phase reserves and
single-receipt profile binding; delete consumerless Sed spec models
fix(infra): refresh the stale transformers package projection (#1265)
chore(gen): land the tip's generated-surface fixed point (#1115)
\[WIP\] merge(0.12.0-dev): adopt the tip's projection fix (3d2fda4e4)
merge(#1259): adopt l2 merge cures; keep MYPY\_TIMEOUT\_SECONDS\_MAX, checkout-local
.venv; drop FLEET\_BOUND and retired silent-failure gate
fix(infra): accept the declared version behind a stale lock specifier (#1262)
\[WIP\] merge: adopt 0.12.0-dev into the infra closure lane
fix(codegen): declare pipeline conform\_ports as its bundle model, not t.Port (#1264)
fix(infra): cure two merge-artifact syntax defects at the tip (#1263)
chore: adopt the green-gate convergence lane (PR #1257)
merge(0.12.0-dev): bring the lane up to date with the integration tip
merge(#1257): adopt the tip green-convergence lane
fix(codegen): declare conform\_ports as its bundle model, not t.Port (#1261)
\[WIP\] converge: flext-infra extermination lanes (L1, L2, L3, tip repair, TypeAdapter,
upg order) (#1260)
merge(0.12.0-dev): adopt integration into testmon contract lane
Merge remote-tracking branch 'origin/0.12.0-dev' into adopt/infra-1257-20261001
merge: adopt the convergence wave pushed onto this lane
merge(0.12.0-dev): integrate the integration-wave tip into the repair lane
Merge remote-tracking branch 'origin/0.12.0-dev' into converge/extermination-20261001
merge(converge): adopt #1253 (upg locks mise once from the rendered manifest);
exterminated pieces stay deleted
Merge remote-tracking branch 'origin/fix/type-adapter-constructor-20261001' into
converge/extermination-20261001
merge(converge): L3 DI/coupling/hardcode lane; conform ports kept, Rope cycle and old
governance model stay deleted
chore: adopt the coordinator's detector and bootstrap repair continuation
merge(0.12.0-dev): bring the lane up to date
\[WIP\] L1: absolute imports, copyright notice, TC004 exception (continuation) (#1255)
merge(0.12.0-dev): bring the lane up to date
fix(codegen): the cooldown reaches make upg; upg locks mise only from the rendered
manifest (#1253)
merge(0.12.0-dev): bring the lane up to date
fix(infra): restore the gen fixed point and clear the base check reds (#1248)
fix(tooling): declare the algar-oud-mig pytest worker ceiling (#1256)
merge(0.12.0-dev): bring the lane up to date
\[WIP\] L2 continuation 2: re-exterminate resurrected rules; deferred self-reference as
rule data (#1247)
fix(config): api\_modules + convergencia com o model atual (#1258)
merge(0.12.0-dev): bring the lane up to date
\[WIP\] refactor(infra): L3 extermination continuation 2 (catch normalization, DI)
(#1245)
merge(0.12.0-dev): bring the lane up to date
Converge/infra closure 20261001 (#1244)
Merge remote-tracking branch 'origin/fix/codemod-gate-contract-20261001' into
converge/extermination-20261001
merge(0.12.0-dev): bring the lane up to date
merge(converge): L2 rules-as-data lane; deletion wins (modernize\_orchestrator, unused
rope fact models)
merge(converge): tip-repair lane; the exterminated mypy env knob and 600s bound stay
deleted, class-form markdown sources kept
Merge integration tip into the infra closure lane
merge(infra): adopt coordinator tip repair
merge(0.12.0-dev): integrate the newest tip into the tip-repair lane
\[WIP\] merge(0.12.0-dev): adopt the tip repair
merge: absorb the fleet's parallel cures (Sed models, packaging exclusions)
merge: repair da ponta do coordenador (d4740e404) — dangling references (#1254)
chore: absorb the integration tip
\[WIP\] merge(0.12.0-dev): adopt the integration tip into the L3 lane
chore: adopt the coordinator's mypy-timeout and model-graph repair chain
merge(infra-repair): adopt coordinator tip repair for h0kyc validation
merge: absorve ponta corrente
merge: repair da ponta do coordenador (dangling references + bootstrap)
merge(0.12.0-dev): adopt latest integrated model repair
fix(models): restaura SedPatternsSpec/SedPatternSpec perdidos no merge L2 (#1252)
merge(0.12.0-dev): adopt latest fixed point and toolchain repairs
merge(0.12.0-dev): adopt integrated infra state for h0kyc validation
fix(gates): repair the markdown-code source module mangled by the L2 merge (#1246)
merge(infra): adopt current integration branch and generated owners
refactor(config): one external-cache path contract for the tool cache specs (#1250)
test(ci): prove generated fixed-point rejects a dirty tree (#1243)
fix(constants): restaura MYPY\_TIMEOUT\_SECONDS\_DEFAULT perdido no merge L2
(cherry-pick 578653ace) (#1251)
chore: integrate the model-graph completion wave into the tip-repair lane
\[WIP\] merge(0.12.0-dev): adopt the integration tip
\[WIP\] merge(0.12.0-dev): adopt the integration tip into the L3 lane
fix(adapters): 8 singletons chamam m.TypeAdapter (PEP 695 nao chamavel) (#1249)
\[WIP\] merge(0.12.0-dev): bring the tip-repair lane up to date
merge: reconcile fixed-point test with current integration base
\[WIP\] merge(0.12.0-dev): adopt the tip after #1240, #1241 and #1242
\[WIP\] codemod gate contract: continue extermination (#1242)
\[WIP\] merge(0.12.0-dev): adopt the integration tip into the L3 lane
Merge branch '0.12.0-dev' into fix/codemod-gate-contract-20261001
\[WIP\] L2 continuation: namespace law as rule data, project-context engine (#1241)
merge(0.12.0-dev): bring the lane up to date
merge: integrate the 0.12.0-dev tip (#1238-#1240: namespace packaging restore, L3
continuation, GATE\_TOOLS\_BY\_KIND import fix) into the workspace self-test +
template-balance lane
merge(0.12.0-dev): integrate the newest tip into the review follow-up lane
\[WIP\] merge(0.12.0-dev): adopt the integrated tip after #1223 landed
\[WIP\] merge(0.12.0-dev): adopt the integration tip into the L2 lane
fix(check): GATE\_TOOLS\_BY\_KIND indefinido quebra o import da frota inteira (#1240)
\[WIP\] refactor(infra): L3 extermination continuation (DI, coupling, hardcodes) (#1239)
fix(codegen): restore repository root namespace packaging (#1238)
merge(0.12.0-dev): bring the lane up to date
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/exterminate-di-coupling-hardcode-20261001
merge: integrate 0.12.0-dev tip (fmt-fixes integration + lock regen) into the workspace
self-test testmon lane
fix(lock): regenerate flext-infra uv.lock after the lane merges (#1237)
fix(codegen): one fleet supply-chain cooldown for every resolver (#1231)
merge(0.12.0-dev): bring the lane up to date, preserving its changes
\[WIP\] refactor(infra): exterminate DI, coupling and hardcoded values in the
declaration and service layers (#1230)
merge(0.12.0-dev): bring the lane up to date, preserving its changes
\[WIP\] L2: exterminate registries, Python-coded rules, catch/fallback code (#1229)
merge(0.12.0-dev): bring the lane up to date, preserving its changes
\[WIP\] chore: exterminate pins, restated tunables and non-public references in config,
templates and docs (#1228)
merge(0.12.0-dev): bring the lane up to date, preserving its changes
fix(check): remove gate suspension and observational routing; every finding blocks
(#1223)
merge(0.12.0-dev): bring the lane up to date, preserving its changes
wip(infra): stabilize pytest runner within the fleet suite wall (#1217)
merge(0.12.0-dev): bring the lane up to date, preserving its changes
infra: strict docs policy and typed candidate recovery (#1214)
Merge remote-tracking branch 'origin/0.12.0-dev' into pr-1217
merge(0.12.0-dev): bring the lane up to date, preserving its changes
fix(infra): adopt typed census and pytest deadline work (#1211)
merge(0.12.0-dev): bring the lane up to date, preserving its changes
feat(infra): guarded Sed recovery and candidate bootstrap (#1210)
merge(0.12.0-dev): bring the lane up to date, preserving its changes
WIP: adopt semantic codemod and generator recovery (#1208)
merge(0.12.0-dev): bring the lane up to date, preserving its changes
merge: integrate current Flext infra base after PR landings
Merge remote-tracking branch 'origin/0.12.0-dev' into pr-1217
fix(lock): regenerate flext-infra uv.lock after the fmt-fixes integration (#1236)
fix(check): the mypy gate owns project-keyed cache resolution (#1232)
merge(0.12.0-dev): bring the lane up to date, preserving its changes
fix(release): retain declared data in wheel and sdist (#1225)
merge(0.12.0-dev): bring the lane up to date, preserving its changes
merge(0.12.0-dev): bring the lane up to date, preserving its changes
fix(codegen): workspace-profile self-test gains the pytest testmon guard and database
environment (#1235)
Converge local integration lanes + projections.lock.json v1 + jscpd 5.3.3 pin (#1212)
Merge remote-tracking branch 'origin/0.12.0-dev' into adopt/infra-1232-20261001
merge(0.12.0-dev): bring the lane up to date, preserving its changes
merge(0.12.0-dev): bring the lane up to date, preserving its changes
merge(0.12.0-dev): bring the lane up to date, preserving its changes
merge(0.12.0-dev): bring the lane up to date, preserving its changes
merge(0.12.0-dev): bring the lane up to date, preserving its changes
Merge integration tip into the external-cache contract lane
converge: integrate the pending flext-infra PRs and close their reds (#1234)
merge: adopt Mise release-age bootstrap fix
merge: integrate 0.12.0-dev and repair packaging validation
\[WIP\] merge #1215: venv is only RUNTIME\_ROOT/.venv (flext-h2a9h)
\[WIP\] merge #1224 (abandoned \>1h): per-project testmon database and a separate slow
phase
Merge #1224 fix/pytest-slow-phase-20261001: per-project testmon database and a separate
slow phase
Merge #1213 fix/runtime-census-parameters-20261001: cure the census parameter smells
through domain models
Merge #1227 fix/ci-precommit-gate-partition-20261001: derive the CI and pre-commit
partition from the gate kind
Merge #1226 fix/census-smells-to-make-smells-20261001: make smells owns every smell
family
Merge #1223 fix/codemod-gate-contract-20261001: exterminate gate suspensions and
observational routing
Merge #1215 fix/venv-runtime-root-only-20261001: the environment is
\<RUNTIME\_ROOT\>/.venv only
Merge fix/mise-release-age-default-20261001: keep the Mise release-age cooldown
(flext-ueukr)
Merge canonical text codemod provider into strict docs recovery
Merge integration baseline into strict docs recovery
Merge integration tip into the mypy cache gate lane
feat(codegen): project root namespace packages into distributions (#1216)
\[WIP\] merge integration tip 8fd247f4b into the codemod gate lane
\[WIP\] merge 0.12.0-dev into census smells lane
fix(infra): honor VCS exclusions in declared package data (#1222)
Merge integration tip into root-namespace-packaging lane
Merge integration base after infra PR landing
Merge parallel infra resolution into packaging fix
fix(infra): retain backup named sources and clean generated artifacts (#1219)
merge: adopt Infra integration provider into Docs recovery
Merge integration tip 0.12.0-dev (profiling lane) into the census domain-model lane
Merge remote-tracking branch 'origin/fix/mod-text-recovery-20261001' into
fix/latest-selectors-20261001
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/mod-text-recovery-20261001
Merge the author's parallel resolution of the same tip integration
test(deps): materialize the governed checkout the exclusion contract requires (#1221)
Merge integration base into dcbackup infra fixes
Merge integration tip into backup-named-sources lane
merge: integrate the tip into the exclusion-fixture lane
fix(validate): typed runner stop reserve, receipt-bound profiling, lazy parser backends
(#1220)
Merge remote-tracking branch 'origin/fix/pytest-suite-deadline-20260930' into
fix/mod-text-recovery-20261001
merge: adopt typed candidate bootstrap provider
Merge the census lane (with #1218) into the closure lane
Merge integration tip 0.12.0-dev (#1218) into the census domain-model lane
merge: adopt pytest suite deadline repairs
fix(infra): decompose the six-parameter census violations at their owners (#1218)
Merge the census lane (tip 0.12.0-dev integrated) into the closure lane
Merge integration tip 0.12.0-dev into the census domain-model lane
Merge integration tip (second advance): adopt PytestInvocation and RuffProjectFacts
contracts
merge: reconcile namespace packaging with current infra base
Merge integration base into dcbackup codegen fix
merge: integrate the advanced tip into the census lane
fix(templates): the cleanliness proofs fail loud again (#1209)
Merge remote-tracking branch 'origin/fix/infra-docs-strict-20261001' into
fix/mod-text-recovery-20261001
Merge branch 'fix/mod-text-recovery-20261001' of github.com:flext-sh/flext-infra into
fix/infra-docs-strict-20261001
Merge origin/0.12.0-dev into Docs audit recovery
Merge census root-cause cure (flext-infra#1213) into the closure lane
merge: adopt typed mod-text and runtime-census repairs into pytest lane
Merge current runtime census owner into pytest deadline lane
merge: integrate current Infra 0.12.0-dev into pytest deadline lane
Merge integration tip 0.12.0-dev into runner profiling lane
merge: integrate current flext-infra line for namespace packaging
merge: absorve nova ponta upstream (4 commits) na convergencia local
merge(infra): preserve integration changes in codemod recovery lane
Merge runtime census repair into pytest deadline candidate
Merge 0.12.0-dev into pytest deadline adoption lane
merge: integrate the tip's census projection updates
Merge 0.12.0-dev after Infra placeholder policy landing
feat(infra): declarative placeholder\_exempt\_paths for frozen-evidence dirs (#1206)
merge(infra): adopt integration advances into mod-text lane
Merge 0.12.0-dev into runtime census parameters lane
merge(infra): integrate typed runtime census boundaries
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/infra-placeholder-exempt-20260930
merge: absorve origin/0.12.0-dev (25 commits: #1199-#1205) na lane local de convergencia
merge(infra): compose Qlty smells with declarative text recovery
Fix/infra candidate atomic 20260930 (#1205)
Merge branch '0.12.0-dev' into fix/infra-candidate-atomic-20260930
fix(docs): fence policy by rule name for the renamed/versioned tail r… (#1204)
Fix/infra upg staging mypy timeout 20260929 (#1203)
Merge branch '0.12.0-dev' into fix/infra-upg-staging-mypy-timeout-20260929
chore(codegen): preserve generated no-keyring Make in candidate lane (#1202)
Merge branch '0.12.0-dev' into fix/infra-no-keyring-20260930
feat(infra): run Qlty smells through dedicated make smells (#1199)
chore(integration): land the orphaned lanes — 1155-adopt, cli-candidate-consumer,
residue reclaim (#1200)
docs(infra): add the canonical TOC block to the new codemod guides (#1201)
merge: land the interrupted-invocation residue reclaim fix
merge: land the lazy-init multirepo adoption lane (venv fallback + relock)
feat(infra): declarative CSV and semantic codemod pipeline (#1140)
Merge Infra integration remote into pytest timeout lane
merge: integrate 0.12.0-dev into the model-fields codemod lane
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/infra-model-fields-20260930
fix(infra): green the integration tip — docs\_config exempt, generated fixed point,
lint/census (#1198)
merge: integrate the remote lane state
merge: integrate 0.12.0-dev (through #1196) into the candidate-atomic lane
Merge branch 'fix/mypy-cache-gate-r1-20260930' into 0.12.0-dev
Merge branch 'fix/tip-green-3-20260928' into 0.12.0-dev
Merge branch 'fix/docs-config-template-policy-20260930' into 0.12.0-dev
chore(flext-infra): integrate the fmt-fixes line into 0.12.0-dev (#1196)
merge(fmt-fixes): integrate the fmt-fixes line into 0.12.0-dev
Merge branch 'fix/infra-candidate-atomic-20260930' into 0.12.0-dev
Merge branch 'fix/reclaim-transaction-residue-20260930' into 0.12.0-dev
Merge branch 'fix/infra-private-policy-20260930' into 0.12.0-dev
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/docs-config-template-policy-20260930
Merge remote-tracking branch 'origin/fix/infra-candidate-atomic-20260930' into
fix/infra-candidate-atomic-20260930
Merge branch 'fix/infra-no-keyring-20260930' into 0.12.0-dev
Merge branch 'fix/infra-aihub-worker-ceiling-20260929' into 0.12.0-dev
Merge branch 'fix/infra-1155-adopt-20260930' into 0.12.0-dev
Merge branch 'fix/infra-1167-adopt-20260930' into 0.12.0-dev
Merge branch 'fix/infra-docs-quality-d9nzw-20260930' into 0.12.0-dev
Merge branch 'fix/infra-cli-candidate-consumer-20260930' into 0.12.0-dev
Merge branch 'fix/infra-mypy-budget-20260930' into 0.12.0-dev
Merge branch 'fix/infra-codemod-architecture-20260930' into 0.12.0-dev
fix(codegen): dependabot must never open bump PRs against generated projections
(flext-jfuv6) (#1194)
Merge branch 'fix/docs-fence-policy-20260930' into 0.12.0-dev
Merge branch 'fix/docs-shared-test-import-policy-20260930' into 0.12.0-dev
Merge branch 'fix/docs-hidden-reports-20260930' into 0.12.0-dev
Merge branch 'fix/infra-docs-toc-convergence-20260930' into 0.12.0-dev
Merge branch 'fix/infra-git-guide-toc-20260930' into 0.12.0-dev
Merge branch 'fix/infra-model-fields-20260930' into 0.12.0-dev
chore: integrate the 0.12.0-dev tip (candidate wave) into the codemod pipeline lane
Merge current Infra integration into docs artifact lane
fix(codegen): publish candidate Makefiles atomically (#1189)
Merge branch '0.12.0-dev' into fix/infra-candidate-atomic-20260930
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/infra-model-fields-20260930
feat(make): declarative testmon cache policy — the preserved #1001 delta at its owner
(flext-j0u23) (#1193)
Merge current Infra integration into docs artifact lane
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/infra-candidate-atomic-20260930
fix(make): authenticate only when bootstrap needs network (#1191)
test(git): prove publication refuses a diverged remote checkpoint (#1177)
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/git-checkpoint-worktree-state-20260930
Merge origin/0.12.0-dev into guide TOC lane
refactor(infra): own envrc contract policy in SSOT, layer, and types (#1192)
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/infra-model-fields-20260930
Merge origin/0.12.0-dev into guide TOC lane
merge: integrate 0.12.0-dev into the checkpoint lane
chore(config): dedupe the candidate bootstrap target declaration (#1184)
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/infra-model-fields-20260930
fix(markdown): preserve residual and MD013 diagnostics (#1141)
Merge origin/0.12.0-dev into guide TOC lane
fix(docs): complete the fence-ignore set with the measured fragment-inherent rules
(#1190)
Merge integration base into bootstrap credential lane
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/infra-model-fields-20260930
Merge origin/0.12.0-dev into guide TOC lane
Merge branch '0.12.0-dev' of github.com:flext-sh/flext-infra into
fix/markdown-convergence-20260930
Merge current Infra integration into docs artifact lane
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/infra-docs-toc-convergence-20260930
feat: declare package data per project for OUD release (#1171)
feat(codemod): pair NS-CONTRACT-001 dict-annotation detection with make mod (#1188)
Merge origin/0.12.0-dev into guide TOC lane
Merge current Infra integration into docs artifact lane
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/infra-docs-toc-convergence-20260930
Merge branch '0.12.0-dev' of github.com:flext-sh/flext-infra into
fix/infra-cli-candidate-consumer-20260930
merge: integrate 0.12.0-dev into the checkpoint lane
fix(docs): F821 joins the fence-ignore set — snippets are fragments, not modules (#1187)
Merge origin/0.12.0-dev into guide TOC lane
Merge current Infra integration into docs artifact lane
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/infra-docs-toc-convergence-20260930
test(infra): prove the bounded Mypy memory stop through the public causal classification
(#1186)
fix(mod): resolve local private imports before installed package discovery (#1144)
fix(pytest-runner): suppress the suite stop when every collected item already completed
(#1185)
Merge branch '0.12.0-dev' into fix/infra-private-import-relative-20260930
fix(config): fence-ignore policy gains D106/B018; pytest run wall calibrated to the real
invocation (#1182)
Merge branch '0.12.0-dev' into fix/docs-fence-policy-20260930
Merge remote-tracking branch 'origin/feat/oud-package-20260930' into
fix/infra-1171-adopt-20260930
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/infra-1171-adopt-20260930
Merge integration tip into docs import policy lane
Merge latest Infra integration into docs artifact lane
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/infra-docs-toc-convergence-20260930
refactor(supervisor): read poll intervals and ps timeout from the constants SSOT (#1183)
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/infra-1144-adopt-20260930
merge: adopt current generated documentation integration
Merge latest Infra integration into docs artifact lane
merge: adopt coordinated packaging lane integration
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/infra-docs-toc-convergence-20260930
fix(docs): regenerate the api-reference counters so make gen is a fixed point (#1181)
Merge 0.12.0-dev into docs artifact lane
chore(gen): land the tip's docs projection fixed point (#1180)
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/infra-docs-toc-convergence-20260930
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/infra-1171-adopt-20260930
Merge branch '0.12.0-dev' into fix/tip-gen-docs-fixed-point-20260930
feat(packaging): adopt integration and declare validated data paths
Merge remote-tracking branch 'origin/fix/infra-upg-staging-mypy-timeout-20260929' into
fix/infra-1167-adopt-20260930
Merge branch '0.12.0-dev' of github.com:flext-sh/flext-infra into
fix/infra-cli-candidate-consumer-20260930
fix(setup): bound private submodule provisioning with explicit Git credentials (#1159)
build(upg): stage the .mise/locks sidecars in the upg lifecycle (template) (#1167)
merge: adopt the current tip into the candidate bootstrap lane (fix-forward)
chore: absorb the integration tip
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/infra-1167-adopt-20260930
fix(release): admit the claude governance manifest beside agents at the sdist root
(#1163)
Merge branch '0.12.0-dev' of github.com:flext-sh/flext-infra into
fix/infra-submodule-setup-20260930
test(resource-limits): run boundary-rejection cases on the integration budget (#1173)
refactor(deps): own the lock integrity gate in code, not the Makefile template (#1165)
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/infra-resource-limit-ssot-20260930
fix(docs): fail audit on findings and parse inline commands by intent (#1157)
Merge remote-tracking branch 'origin/fix/infra-docs-audit-20260930' into
fix/infra-docs-audit-20260930
fix(beads): tolerate the bd gate serialization marker in composed verification (#1175)
Merge branch '0.12.0-dev' of github.com:flext-sh/flext-infra into
fix/infra-docs-audit-20260930
fix(codegen): plan lazy init in each selected repository (#1155)
merge: adopt current infrastructure integration for OUD packaging
Merge branch '0.12.0-dev' of github.com:flext-sh/flext-infra into
fix/infra-lazy-init-multirepo-20260930
fix(infra): provision physical environments beside worktrees (#1147)
fix(refactor): classvar relocation autofix reaches nested constants in canonical
constants.py facades (flext-xwag0) (#1178)
Merge remote-tracking branch 'origin/fix/infra-external-venv-20260930' into
fix/infra-external-venv-20260930
chore: absorb the integration tip (incl. #1170)
Merge branch '0.12.0-dev' of github.com:flext-sh/flext-infra into
fix/infra-external-venv-20260930
Merge branch '0.12.0-dev' into fix/infra-resource-limit-ssot-20260930
Merge branch '0.12.0-dev' into fix/infra-lock-integrity-gate-20260930
fix(mise): pin 2026.9.18 and declare the bootstrap release-age policy (#1174)
Merge branch '0.12.0-dev' of github.com:flext-sh/flext-infra into
fix/infra-lazy-init-multirepo-20260930
Merge branch '0.12.0-dev' into fix/infra-resource-limit-ssot-20260930
Merge branch '0.12.0-dev' into fix/infra-lock-integrity-gate-20260930
Merge branch '0.12.0-dev' of github.com:flext-sh/flext-infra into
fix/infra-docs-quality-d9nzw-20260930
fix(validate): content-only namespace receipt + banned-annotation vocabulary (uno8m
slice) (#1176)
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/infra-resource-limit-ssot-20260930
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/sidecar-lock-cure-20260930
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/infra-1155-adopt-20260930
fix(git-state): guarded worktree checkpoints on the public symlink primitives (#1130)
merge: adopt current flext-infra integration baseline
merge: adopt current 0.12.0-dev tip (e81865432) into the annotations lane
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/infra-resource-limit-ssot-20260930
merge: integrate 0.12.0-dev (through #1170) into the r6 state lane
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/infra-1155-adopt-20260930
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/infra-tip-green-r6-20260929
fix(check): wire the project mypy-budget SSOT into the standalone check path
(flext-siwvh) (#1170)
Merge remote-tracking branch 'origin/0.12.0-dev' into
investigate/infra-suite-profile-20260930
merge: adopt current flext-infra integration baseline
chore: absorb the integration tip
fix(bootstrap): pin the mise release selector to 2026.9.16 (2026.9.17 upstream
regression) (#1168)
Merge branch '0.12.0-dev' into fix/infra-lock-integrity-gate-20260930
merge: integrate current flext-infra baseline
fix(markdown): retire MD077 — a dialect rule the canonical docs formatter cannot satisfy
(#1169)
Merge branch '0.12.0-dev' into fix/infra-lock-integrity-gate-20260930
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/sidecar-lock-cure-20260930
fix(mise): fail loud on an absent or drifted aube sidecar before setup does (#1166)
refactor(ruff): name the exclusion authorities and end the binding ping-pong (#1164)
Merge branch '0.12.0-dev' into fix/infra-docs-audit-20260930
fix(validate): banned-annotation vocabulary across the namespace surface (uno8m slice 1)
(#1117)
Merge branch 'fix/infra-external-venv-20260930' of github.com:flext-sh/flext-infra into
investigate/infra-suite-profile-20260930
merge: reconcile the PR branch state (mise latest revert) into the r2 lane
merge: adopt moved tip into the uno8m annotations lane (r2)
merge: adopt external venv prerequisite and test owner
merge(infra): integrate latest 0.12.0-dev into external environment lane
merge(infra): integrate baseline with external environment fixes
fix(validate): verify a planless layout's on-disk export contract (#1162)
Merge external runtime and no-keyring fixture contracts
Merge real Make hook environment fixture
Merge fail-loud documentation audit owner
Merge lazy-init and bootstrap fixes into private import discovery
Merge selected-repository lazy-init fixture correction
fix(infra): fail loud on a duplicated mise.lock instead of a distant CI failure (#1135)
fix(infra): declare the ai-hub worker ceiling for its suite deadline (#1127)
Merge per-repository lazy-init planning owner
Merge remote-tracking branch 'origin/fix/upg-mise-lock-resilience-20260930' into
fix/upg-mise-lock-resilience-20260930
Merge formatted candidate bootstrap guide
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/upg-mise-lock-resilience-20260930
Merge candidate bootstrap fixture and Makefile phase fixes
Merge external Make environment test cutover
Merge commit '813784755283c5a0c998418f9cb42b04cef24738' into HEAD
Merge Make-only bootstrap rendering before member tooling
Merge branch '0.12.0-dev' into fix/tip-gen-fixed-point-20260929
Merge remote-tracking branch 'origin/0.12.0-dev' into HEAD
Merge external environment test contract for lazy-init validation
docs(registry): the upg verb description covers the verification it now performs (#1151)
Merge commit '99086f2fdf3030933ccca057a0f25ad4b8b074a0' into HEAD
Merge bootstrap topology for incomplete managed gitlinks
Merge branch '0.12.0-dev' into docs/upg-description-covers-verification-20260930
Merge no-keyring bootstrap and candidate setup contracts for lazy-init validation
Merge workspace autofix fixture and private import owner
Merge public enforcement immutability fixture correction
fix(markdown): a hint-only rumdl exit is green, not a tool error (#1160)
Merge remote-tracking branch 'origin/0.12.0-dev' into
docs/upg-description-covers-verification-20260930
Merge bounded Mypy fixture correction for native test progression
Merge candidate bootstrap and no-keyring owner into CLI consumer
Merge candidate bootstrap call site for typed submodule setup
Merge typed submodule setup source into candidate bootstrap
Merge private-import and workspace fixture corrections for lazy-init validation
Merge enforcement fixture correction for lazy-init validation
Merge no-keyring source into bootstrap candidate
Merge physical external environment owner for submodule setup
merge: adopt lazy-init per-repository plan for memory validation
merge: adopt private import fixture repairs for memory validation
Merge runtime and memory contract into enforcement lane
Merge remote-tracking branch 'origin/fix/infra-candidate-bootstrap-20260930' into
fix/infra-cli-candidate-consumer-20260930
Merge resource-limit raw exit contract
Merge resource memory contract into lazy-init lane
Merge physical external environment owner for docs audit
Merge canonical external runtime environment into lazy-init lane
Merge explicit workspace check contract for resource validation
Merge integration baseline for Markdown proof
Merge root check contract correction
fix(repo): generated locks never merge — a textual merge corrupts them (#1149)
Merge external environment source for resource validation
merge: adopt explicit workspace root contract test
merge: adopt integration markdown diagnostics
Merge external physical environment owner
fix(markdown): stop blocking on the formatter hint the fix verb cannot repair (#1148)
Merge integration enforcement fix into candidate lane
merge: adopt integration typing-text owner
merge: adopt integration typing-unifier correction
Merge external environment fixture repair
merge: adopt physical environment fixture correction
merge: adopt physical runtime fixture owner
fix(fixers): fix-enforcement keeps typing text; the typing unifier is not its owner
(#1146)
Merge physical external environment support into candidate lane
Merge integration base into candidate dependency lane
merge: adopt canonical physical environment route
merge: adopt external physical environment owner
fix(git): preserve the index/worktree distinction when copying dirty state (#1145)
fix(models): a conformed ruff list field may be legitimately empty (#1142)
fix(make): an upgrade publishes only after the cycle it changed still passes (#1139)
docs(toolchain): correct the false qlty pin rationale (#1138)
fix(toolchain): make the upg lock write atomic and self-recovering (#1137)
fix(mise): reject a lockfile annotation in a generated .mise.toml selector (#1136)
fix(toolchain): ast\_grep\_version must be an npm specifier, not the aube build id
(#1119)
fix(gen): reclaim interrupted-transaction residue instead of failing forever (#1134)
docs(guides): land the docs fixed point the Docs workflow requires (#1131)
fix(make): make upg assert its own gen fixed point (#1133)
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/infra-gen-projections-tip-20260929
merge(internal): adopt origin/0.12.0-dev into the ai-hub worker-ceiling lane
(fix-forward)
Merge branch '0.12.0-dev' into fix/tip-gen-fixed-point-20260929
fmt-fixes
Merge branch 'fmt-fixes' into fix/infra-tip-green-r6-20260929
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/infra-tip-green-r6-20260929
Merge commit '17a4ffdf833ad0ae93e87b6109bf56e693233f1e' into fmt-fixes
Merge commit 'aa3112d6f2eba9efa8fb6e74b2410bc58820c8b7' into fmt-fixes
Merge commit '810bce9fc8cd07d31d90f4214f822100ff5c6da4' into fmt-fixes
Merge commit '8154d19d0adaa0cc7921dd69ed3684951114d645' into fmt-fixes
Merge commit '2f35573065670d8e1d94bad82315047c4c9d3c2f' into fmt-fixes
wip
Merge remote-tracking branch 'refs/remotes/origin/0.12.0-dev' into 0.12.0-dev
fix(infra): optional mypy cache default + four root-cause repairs in ensure\_ruff
(#1120)
fix(infra): correct ast\_grep\_version, restore missing imports, align set type
merge: adopt current 0.12.0-dev tip into the NS-CONTRACT-001 slice lane
fix(check): mypy budget as project SSOT + mypy returns to CI (operator 2026-09-29)
(#1113)
fix(mise): relock jscpd to a single resolution on the tip (fix-forward) (#1114)
fix(discovery): accept runtime\_root in runtime\_python and re-resolve … (#1082)
Merge branch '0.12.0-dev' into fix/runtime-python-runtime-root-20260928
Fix/mypy supervisor boundary 20260928 (#1081)
merge: adopt 0.12.0-dev into the tip-heal lane (ensure\_ruff resolved on the healed
version)
feat(pytest-runner): tagged PytestWorkerCeiling with absolute or CPU-fraction form
(#1107)
\[WIP\] preserve lane fix/lazy-init-deterministic-order before retirement (#1079)
fix(release): admit the governance agent manifest at the sdist root (#1108)
fix(mise): declare jscpd host-invariant so the lock holds one resolution (#1112)
chore(gen): consume the relock projections (mise 96527ca3 era) (#1109)
fix(deps): bind compose\_per\_file\_ignores as a classmethod (restores gen on the tip)
(#1110)
Merge branch '0.12.0-dev' into fix/ruff-compose-signature-20260929
merge: adopt moved 0.12.0-dev base (PR #1107)
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/member-projections-relock-20260929
fix(ruff): generated-roots owner read + fail-loud exclusions + dead orchestrator export
pruned (flext-x4l60) (#1111)
\[WIP\] merge(integration): adopt #1075 into the r6 lane
merge: adopt 0.12.0-dev (carries the ensure\_ruff binding regression to cure)
fix(infra): restore instance binding on compose\_per\_file\_ignores (#1075)
Merge branch '0.12.0-dev' into fix/lazy-init-deterministic-order
Merge branch '0.12.0-dev' into fix/mypy-supervisor-boundary-20260928
Merge branch '0.12.0-dev' into fix/runtime-python-runtime-root-20260928
Merge branch '0.12.0-dev' into fix/ruff-compose-ignore-binding-20260929
fix(ruff): restore the excluded-roots computation and the static cont… (#1105)
Fix/infra stabilization r5 20260929 (#1106)
Merge branch '0.12.0-dev' into fix/compose-per-file-ignores-signature-20260929
Merge branch '0.12.0-dev' into fix/infra-stabilization-r5-20260929
\[WIP\] preserve dormant worktree dirty state (infra git-owner-refactor… (#1086)
\[WIP\] fix(codemod): make mod verifies rule-test snapshots, never rewrites them
(flext-itpd1.7) (#1103)
Merge branch '0.12.0-dev' into fix/codemod-snapshot-drift-fails-20260929
\[WIP\] fix(fix): make fix never deletes information (flext-itpd1.5) (#1101)
\[WIP\] merge(integration): adopt #1104, #1085 and #1102 into the round-5 lane
\[WIP\] fix(fixers): delete the whole-file regex transformer (flext-itpd1.6) (#1102)
Fix/1043 adopt 20260929 (#1085)
fix(mypy): 120s bound, CI Mypy cache restore/save, red-base codemod and test repairs
(#1104)
\[WIP\] merge(integration): adopt #1098 into the F2 lane
\[WIP\] merge(integration): adopt #1098 into the F1 lane
merge(integration): adopt #1098 into the mypy-bound lane
fix(docs): standalone repositories publish the canonical root MkDocs title (#1098)
\[WIP\] merge(integration): adopt #1100 and #1096 into the round-5 lane
\[WIP\] merge(integration): adopt #1100 and #1096 into the mypy-bound lane
fix(validate): populate\_by\_name on the pytest diag extractor (flext-dw54w residue)
(#1096)
feat(census): apply every classvar\_relocation violation in one pass (#1100)
\[WIP\] merge(integration): adopt de9a46af5 into the round-5 lane
\[WIP\] merge(integration): adopt #1099 into the mypy-bound lane
fix(validate): declared content-only roots skip the namespace layout contract (#1099)
\[WIP\] merge(integration): adopt #1097 into the mypy-bound lane
fix(release): carry the project's prepared dist inputs into the staged source (#1097)
merge: adopt the invest-session preservation of the swept first worktree (content
superseded by the public-rename commits)
fix(codegen): formatter-stable lazy-init mappings; fix/fmt fixed point; fresh-import in
the declared runtime (#1095)
merge(integration): adopt #1092 and the narrowed tuple codemod into the round 3 lane
fix(codemod): rewire typing type tuples only when FlextConstantsGuards owns the name
(#1094)
fix(validate): zero-test projects run to a typed green receipt (6n6u) (#1092)
fix(mypy): key the shared cache by project so relocks stay warm; provision propagation
fixtures once (#1093)
fix(validate): fresh-import usa o interprete do processo com PYTHONPATH (#1091)
merge: adopt current 0.12.0-dev tip into the zero-test contract lane
fix(infra): grouped stabilization — generated .mimosa ignore, one scan-scope owner,
hermetic mirrors, strict config template, latest build backend (#1090)
merge(integration): adopt #1089 #1077 #1078 into the stabilization lane
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/fix-accesso… (#1078)
Merge branch '0.12.0-dev' into fix/fix-accessors-recipe-20260928
Fix/codemod observational findings 20260928 (#1077)
merge(integration): adopt 662accbff (#1073) and 29648e123 (#1087) into the stabilization
lane
Fix/rewire primitives types 20260929 (#1089)
Merge branch '0.12.0-dev' into fix/rewire-primitives-types-20260929
\[WIP\] preserve dormant worktree dirty state (infra-config-j2-strict, … (#1087)
Merge branch '0.12.0-dev' into fix/1043-adopt-20260929
fix(infra): relock onto flext-core d65f7333a, declared ruff exclusions, integrate
784225084 (#1073)
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/cold-mypy-shared-cache-20260929
Merge remote-tracking branch 'infra-origin/0.12.0-dev' into
fix/rewire-primitives-types-20260929
Fix/pyproject scripts conditional (#1072)
Merge branch '0.12.0-dev' into fix/pyproject-scripts-conditional
chore: land pending primary-checkout commits (flext-infra) (#1070)
perf(mypy): share one lock-keyed analysis cache across checkouts (#1069)
refactor(typing): read PRIMITIVES\_TYPES from c (fleet cutover with flext-core#525)
(#1068)
refactor(git): one typed owner for the worktree registry (#1067)
merge: adopt the preserved x44z3 lane over the tool-tables typing fixes
Merge remote-tracking branch 'refs/remotes/origin/0.12.0-dev' into 0.12.0-dev
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/cold-mypy-shared-cache-20260929
Merge branch '0.12.0-dev' of github.com:flext-sh/flext-infra into
refactor/infra-git-owner-flext-law-20260929
Test/extra verb canonical collision 20260929 (#1066)
\[WIP\] preserve abandoned lane cold-mypy-2 before adoption (coordinator) (#1065)
\[WIP\] preserve abandoned lane 6n6u-zero-test before adoption (coordin… (#1064)
Fix/flext t8p7n forbid gate suspension 20260928 (#1063)
Merge branch '0.12.0-dev' into fix/flext-t8p7n-forbid-gate-suspension-20260928
\[WIP\] fix(pyproject): one parent-walking mise.lock reader for the Tap… (#1062)
Adopt/pr938 20260928 (#1061)
\[WIP\] fix(upg): stage uv.lock in a manifest mirror and publish by one… (#1060)
Fix/release notes markdown 9nvu8 (#1059)
refactor(git): one canonical owner per ref fact (flext-law conformance) (#1058)
feat(git): own staged-index probe; generalize git\_is\_ancestor to any pair (#1057)
fix(deps): projections of root-scoped tool lists keep only existing roots (#1043)
\[WIP\] Merge remote fix/pyproject-scripts-conditional into preserved lane
Merge commit '82ffdb7b9c7fee6fd94792dd896ad61d6a6d7606' into fix/1043-adopt-20260929
\[WIP\] Merge 0.12.0-dev into t8p7n lane
fix(setup): provision governed gitlinks in GitHub CI before gen (#1056)
merge: integrate 0.12.0-dev into the PR938 lane
\[WIP\] Merge origin/0.12.0-dev into fix/flext-t8p7n
perf(setup): initialize absent governed gitlinks in parallel (#1055)
merge(0.12.0-dev): adopt the integration tip into fix/pyproject-scripts-conditional
(no-ff)
chore: null-integrate closed PRs (history only, no content change) (#1054)
docs(config): document the flext-infra config singleton (#1053)
chore: null-integrate closed PR #935
(recovery/p0-20260927/flext-work--v8-s0-npm-lock--flext-infra); intent re-landed via
flext-zmzvq
chore: null-integrate closed PR #931
(recovery/p0-20260927/flext-work--facade-alias-inheritance); intent re-landed via
flext-t8p7n
chore: null-integrate closed PR #933
(recovery/p0-20260927/flext-work--infra-config-import); intent re-landed via flext-t8p7n
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/release-notes-markdown-9nvu8
fix(release): seed the internal-versions map from the root lock's git entries (#1048)
test(codegen): guard every declared verb renders an implementation (#1052)
fix(codegen): declare startup-health-episode as a required beads custom type
(flext-1xkn4) (#1050)
refactor(infra): adopt mise version pinning in toolchain models (fix-forward) (#1047)
fix(gates): canonical-alias treats package:false roots as no-policy-owner trees (#1051)
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/beads-config-ssot-1xkn4-20260928
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/release-internal-versions-20260928
fix(ci): cache the Mise tool storage on the member jobs (#1049)
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/beads-config-ssot-1xkn4-20260928
fix(mise): keep github attestation verification for qlty (unbreak consumer setup)
(#1046)
Merge remote-tracking branch 'refs/remotes/origin/0.12.0-dev' into 0.12.0-dev
fix(tip): re-resolve the flext-cli pin and normalize markdown/format drift (#1045)
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/release-internal-versions-20260928
fix(infra): align stale callers with the integration tips (unbreak 0.12.0-dev) (#1041)
\[WIP\] preserve lane fix/infra-zero-test-baseline-20260927 before reti… (#943)
Merge branch '0.12.0-dev' into
recovery/p0-20260927/flext-work--v8-infra-base-reds--flext-infra
Merge remote-tracking branch 'refs/remotes/origin/0.12.0-dev' into 0.12.0-dev
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/release-notes-markdown-9nvu8
fix(pyproject): authenticate taplo through the mise.lock pin, not the selector (#1034)
Merge branch '0.12.0-dev' into fix/t7668-offline-taplo-pin-20260928
fix(gen): canonicalize pyright execution environment order by root (#1039)
merge: adopt current 0.12.0-dev integration tip into boundary-identit… (#1037)
test(release): prove generated release notes prettier-stable (adopts 1f8f14933) (#1031)
fix(discovery): accept the declared runtime\_root in runtime\_python (#1040)
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/release-notes-markdown-9nvu8
Merge remote-tracking branch 'refs/remotes/origin/0.12.0-dev' into 0.12.0-dev
merge: adopt 1f8f14933 — the release-notes markdown cure landed first
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/pyright-env-order-canonical-20260928
fix(check): constrain Mypy supervisor to typed checker requests (#1004)
Merge branch '0.12.0-dev' into fix/mypy-supervisor-boundary-20260928
fix(make): render the declared fix-namespace and fix-accessors verbs (#1030)
merge(infra): adopt 0.12.0-dev into fix/mypy-supervisor-boundary-20260928
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/fix-accessors-recipe-20260928
fix(ci): reuse the tool caches across CI runs, saved even on failure (#1036)
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/fix-accessors-recipe-20260928
chore(config): remove dead extra\_ignored\_patterns overlay field (#1035)
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/cold-mypy-tool-cache-20260928
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/remove-dead-ignored-patterns-20260928
fix(release): escape merged subjects and bound release-note lines (#1029)
Merge remote-tracking branch 'refs/remotes/origin/0.12.0-dev' into 0.12.0-dev
fix(codemod): publish mod rewrites formatter-clean in the same pass (#1032)
fix(runner): one-item xdist dispatch makes the declared max-failures stop immediate at
fleet scale (flext-itpd1.3.7) (#1033)
Merge remote-tracking branch 'origin/0.12.0-dev' into
fix/remove-dead-ignored-patterns-20260928
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/release-notes-markdown-9nvu8
merge(infra): absorb 0.12.0-dev into fix/release-notes-escape-20260928
fix(mod): reach the formatting fixed point on make mod's first pass (#1028)
fix(gen): format TOML with the locked Taplo release (#1027)
fix(semantic-cutover): drop the flattened wrapper docstring at the generator (#1026)
test(census): prove ENFORCE-079 reports and relocates every class constant (#1025)
fix(gates): zero-python topologies pass the python checkers with typed receipts (#1024)
fix(census): honor recorded check-gate suspensions for overlapping rule families
(gc-wisp-d7mnad) (#1023)
fix(conform): attached members of any family render on the workspace line (#1021)
fix(make): build verb respects package:false roots — typed noop instead of uv build
(#1022)
Merge 0.12.0-dev (109e4fc27, #1018 landed) into the kd07c lane
fix(deps): skip flext-managed=false submodules in workspace project enumeration (#1018)
feat(diagnostics): add the profile-test verb for cold-run pytest profiling
(flext-itpd1.3.7) (#1020)
docs(guides): regenerate local-config-overrides through make docs (#1019)
fix(mise): normalize the pre-bake launcher migration (cold-start detection) (#1017)
chore(merge): adopt origin/0.12.0-dev into the deps-managed lane
docs(agents): align the header to the composed-member two-mode standard (decision a)
(#1016)
fix(binding): preserve consumer resolution and environment ownership (#1003)
merge: adopt current 0.12.0-dev integration tip into mise-launcher-migration lane
chore(mise): adopt the mise wave — 9.15 pin + toolchain.mise\_version selector + saga
reconciliation (#1015)
merge: adopt current 0.12.0-dev integration tip into binding-938 lane
refactor(fixers): retire unreachable gate adapter (#998)
fix(validate): fresh-import probes run in the declared target environment (#1013)
merge: adopt mise-version-preserve lane (toolchain.mise\_version selector)
merge: adopt infra-recheck-gates lane (retired saga reconciliation + mise 9.15 bump)
docs(guides): regenerate the execution-context TOC through make docs (#1014)
merge: adopt current 0.12.0-dev integration tip into retire-gate-fixer lane
\[WIP\] merge 0.12.0-dev (4aaed4171) into the fresh-import lane
merge: adopt current 0.12.0-dev integration tip into mypy-supervisor-boundary lane
fix(check): resolve boundary owners from typed project identity (#1010)
merge: adopt current 0.12.0-dev integration tip into boundary-identity lane
fix(conform): keep the attached members in the workspace root group (#1008)
\[WIP\] Merge origin/0.12.0-dev (45e10436d) into fix/workspace-group-drop-20260928
test(docs): update auditor test setup and assertions (#1009)
\[WIP\] Merge origin/0.12.0-dev into fix/workspace-group-drop-20260928
fix(deps): uv.lock written by make upg owns every flext-\* pin (#1007)
merge: adopt current integration before supervisor runtime validation
\[WIP\] reconcile retired saga with current integration tip
fix(codegen): grant ci packages: read only to declared registry consumers (#1006)
\[WIP\] merge 0.12.0-dev (5a0b18e97, #1005 landed) into the upg-stale lane
fix(upg): lock tools from the manifest gen renders so one upg converges (#1005)
\[WIP\] merge fix/upg-lock-order-20260928 (#1005) into the upg-stale lane
Adopt current integration seed and revision owner repairs
merge: adopt current integration for binding validation
fix(codegen): a seed runtime triple starts from the packaged baked copy (#1002)
fix(codegen): bootstrap Mise from the runtime root pin in attached members (flext-305db)
(#999)
Merge integration tip into Mypy supervisor repair lane
fix(infra): resolve the infrastructure source for fully manifest-pinned consumers
(#1000)
merge: integrate current infra baseline into binding recovery
merge: adopt integrated docs fixed point before adapter validation
\[WIP\] merge origin/0.12.0-dev into fix/mise-attached-member-20260928 (flext-305db)
docs(guides): commit the docs formatter fixed point for using-flext-tests (flext-2m968)
(#996)
merge: adopt current integration for gate adapter removal
chore(gen): land the tip generated-surface convergence (gen fixed point) (#995)
fix(infra): regenerate projections after the work saga retirement (flext-2m968) (#994)
\[WIP\] fix(infra): retire the resurrected work saga and repair the tip gates
(flext-2m968) (#993)
\[WIP\] fix(release): select baseline from integration history (#991)
merge: adopt published tip repair without waiving acceptance (flext-pftj2)
fix(infra): restore make gen after the #986/#988/#989 merges (#992)
merge: adopt integration tip into release ancestry lane (flext-pftj2)
\[WIP\] merge origin/0.12.0-dev (#988 #990) into tip-green-5
\[WIP\] merge origin/0.12.0-dev into tip-green-5
fix(constants): import the shared infra constants the workspace owner uses (#990)
\[WIP\] snapshot live edits in the flext-infra primary checkout (#988)
Merge branch '0.12.0-dev' into wip/infra-primary-snapshot-20260928
fix(constants): import the shared infra constants the workspace owner uses (#989)
\[WIP\] adopt unpublished stash 5dacd07325 (flext-infra) (#983)
\[WIP\] adopt unpublished stash 9914c8d341 (flext-infra) (#981)
\[WIP\] merge fix/tip-green-4-20260928 follow-ups into tip-green-5
fix(codegen,gates): unblock make gen and return the codemod gate to the active set
(#979)
\[WIP\] adopt unpublished stash 2fbb50b666 (flext-infra) (#986)
Merge branch '0.12.0-dev' into wip/stash-2fbb50b666-adopt
Merge branch '0.12.0-dev' into wip/infra-primary-snapshot-20260928
Merge branch '0.12.0-dev' into wip/stash-5dacd07325-adopt
\[WIP\] adopt unpublished stash 5bed818f05 (flext-infra) (#982)
Merge branch '0.12.0-dev' into wip/stash-5bed818f05-adopt
Merge branch '0.12.0-dev' into wip/stash-9914c8d341-adopt
fix(config): restore make gen on ab3fb8809 (endpoint origin, testmon cutover, render
kwargs) (#980)
Merge branch '0.12.0-dev' into fix/codemod-infra-gate-warnings-20260928
WIP on new/sync: 470415692 Merge origin/0.12.0-dev: restore make gen + endpoint\_origin
managed\_city
\[WIP\] merge origin/0.12.0-dev (#976 #977 #978) into tip-green-3
fix(infra): restore make gen on the tip after the #945/#959/#970 merges (#975)
Fix/tip green 2 20260928 (#978)
fix(pyproject): keep the 0cdeaf4eb document.py - the drop's caller ha… (#977)
Merge origin/0.12.0-dev: restore make gen + endpoint\_origin managed\_city (#976)
Merge origin/0.12.0-dev: restore make gen + endpoint\_origin managed\_city
WIP on new/sync: 647a45be2 wip
\[WIP\] preserve lane fix/iac-infra-owner residue (flext-itpd1.3.10) (#964)
\[WIP\] preserve lane fix/p0-upg-pin-cutover-20260927 residue (flext-itpd1.3.10) (#961)
Merge branch '0.12.0-dev' into fix/p0-upg-pin-cutover-20260927
\[WIP\] merge fix/tip-green-2-20260928 (owner re-derivations) into tip-green-3
Merge branch '0.12.0-dev' into fix/iac-infra-owner
merge: absorb origin/0.12.0-dev (949 drop #969, tip-green #968) over … (#974)
\[WIP\] preserve flext-infra state from lane flext (#945)
merge: absorb origin/0.12.0-dev (949 drop #969, tip-green #968) over the husk discard
fix(infra): restore make gen and clear tip reds after the preservation merges (#972)
\[WIP\] preserve lane fix/p0-beads-static-identity-20260927 residue (flext-itpd1.3.10)
(#962)
Merge branch '0.12.0-dev' into fix/p0-beads-static-identity-20260927
\[WIP\] preserve lane fix/infra-red-tests-followup residue (flext-itpd1.3.10) (#963)
New/sync (#971)
\[WIP\] merge origin/0.12.0-dev (#959 #965 #967 #970) into tip-green-2
WIP on new/sync: 647a45be2 wip
Fix/tip adopt 959 967 966 (#970)
Merge branch '0.12.0-dev' into new/sync
Merge branch '0.12.0-dev' into fix/tip-adopt-959-967-966
fix(models): restore pre-husk deps\_tool\_config and contexts; unbreak the tip imports
(#965)
fix(infra): restore ToolchainSpec fields for lint/pyrefly green (#959)
fix(codegen): implement the render-artifact protocol the K5 refactor declared (#967)
P0 fix(models): two half-removed owners crashed every flext\_infra import (flext-xsuwg)
(#966)
Merge branch '0.12.0-dev' into fix/flext-infra-lint-pyrefly-toolchain-fields
Merge branch '0.12.0-dev' into fix/husk-phantom-import-20260928
Merge branch '0.12.0-dev' into fix/codegen-render-artifact-protocol
Merge branch '0.12.0-dev' into fix/infra-models-defaults-dangling
Merge remote-tracking branch 'refs/remotes/origin/0.12.0-dev' into 0.12.0-dev
wip
Recovery/p0 20260927/flext n8tk7 0e364848e (#969)
\[WIP\] Preserve isolated infra lifecycle repairs for adoption (#926)
Fix/tip green 20260928 (#968)
Merge branch '0.12.0-dev' into fix/infra-lifecycle-isolated-20260927
\[WIP\] merge #966 fix/infra-models-defaults-dangling into tip adoption lane
\[WIP\] merge #967 fix/codegen-render-artifact-protocol into tip adoption lane
\[WIP\] merge #959 fix/flext-infra-lint-pyrefly-toolchain-fields into tip adoption lane
\[WIP\] preserve never-committed husk content v8-md-converge/flext-infra (#954)
Merge branch '0.12.0-dev' into recovery/p0-20260927/husk-v8-md-converge--flext-infra
\[WIP\] preserve lane fix/post-merge-gen-fixed-point before retirement (#932)
\[WIP\] preserve lane fix/generator-worktree-and-mise-bootstrap before … (#942)
Merge branch '0.12.0-dev' into
recovery/p0-20260927/worktrees--flext-infra-generator-fixes
\[WIP\] preserve lane wip/audit-infra-20260922 before retirement (#930)
\[WIP\] preserve lane fix/zero-red-tests before retirement (#928)
\[WIP\] Preserve abandoned mise launcher-bake slice — the fleet-wide make gen/upg
blocker (flext-itpd1.3.10) (#957)
\[WIP\] preserve never-committed husk content v8-model-helpers/flext-infra (#955)
fix(infra): bake the Mise launchers and complete the cold-start triple (flext-7babo)
(#958)
\[WIP\] preserve never-committed husk content v8-gate-speed/flext-infra (#953)
\[WIP\] preserve lane hotfix/testmon-worker-collection-20260924 before … (#939)
\[WIP\] preserve never-committed husk content v8-testmon/flext-infra (#956)
Merge branch '0.12.0-dev' into recovery/p0-20260927/husk-v8-testmon--flext-infra
\[WIP\] preserve lane fix/docker-ci-selection-20260926 before retirement (#937)
Merge branch '0.12.0-dev' into recovery/p0-20260927/husk-v8-model-helpers--flext-infra
\[WIP\] preserve lane fix/docker-ci-policy-20260926 before retirement (#936)
Merge branch '0.12.0-dev' into
recovery/p0-20260927/flext-worktrees--docker-ci-policy-20260926--flext-infra
\[WIP\] preserve never-committed husk content v8-ci-scope/flext-infra (#952)
Merge branch '0.12.0-dev' into recovery/p0-20260927/husk-v8-ci-scope--flext-infra
\[WIP\] Fix/upg lifecycle hooks (preserved lane; re-evaluate after flext-infra lands)
(#925)
merge: integrate origin/0.12.0-dev into the recovery snapshot lane (flext-n8tk7)
fix(infra): allow manifest-owned dependency pin cutovers (#950)
fix: the renames-tests followup — runner floor, layout spawns, docs scope, modernizer
probe (#947)
Fix/inc429 mise upg projection 20260927 (#951)
merge: align fix/infra-red-tests-followup with 0.12.0-dev (exterminate #944 + Rope cycle
#923)
merge: integrate flext-infra 0.12.0-dev through 84478a207
fix(infra): compose the shared Rope cycle and typed scaffold manifest (#923)
merge: align iac infra owner with 0.12.0-dev and repair runtime gates
fix(docs): stop requiring the generated api-reference surface on package-less scopes
(#948)
fix(runtime): exterminate .flext-runtime, repair tip gen, census K3-K5 to zero (#944)
Merge branch '0.12.0-dev' into fix/iac-infra-owner
Merge origin/0.12.0-dev (65c56b83d, #946) into the infra landing lane
fix(runtime): complete the .flext-runtime extermination and unbreak the 0.12.0-dev tip
(#946)
\[WIP\] Merge #946 runtime-census manifest-name filter (884f159ae) into K5 lane
Merge branch 'fix/infra-exterminate-flext-runtime-20260927' into
fix/infra-red-tests-followup
Merge remote-tracking branch 'origin/fix/infra-red-tests-followup' into
fix/infra-red-tests-followup
Merge branch '0.12.0-dev' into fix/iac-infra-owner
Merge branch '0.12.0-dev' into
recovery/p0-20260927/flext-worktrees--infra-testmon-collection-20260924
Merge branch '0.12.0-dev' into
recovery/p0-20260927/flext-work--audit-infra-20260922--flext-infra
Merge branch '0.12.0-dev' into
recovery/p0-20260927/fleet-closure-lanes--zero-red-tests--flext-infra
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/infra-red-tests-followup
Merge branch '0.12.0-dev' into fix/upg-lifecycle-hooks
Merge branch '0.12.0-dev' into fix/infra-red-tests-followup
\[WIP\] preserve lane fix/config-import-runtime before retirement
Merge origin/0.12.0-dev into fix/infra-exterminate-flext-runtime-20260927
\[WIP\] refactor(census): one owner per module and per fact (K3, ENFORCE-067) (#920)
fix(runtime): exterminate the external .flext-runtime state and restore checkout
environments (#922)
Merge fix/infra-census-k4-stateless-utilities-20260927 (adopt #921) into
fix/infra-exterminate-flext-runtime-20260927
Merge fix/infra-census-k3-one-class-20260927 (adopt #920) into
fix/infra-exterminate-flext-runtime-20260927
Merge branch '0.12.0-dev' into fix/infra-census-k3-one-class-20260927
\[WIP\] refactor(census): rename the 42 forbidden get\_/is\_ accessors (K2) (#918)
\[WIP\] fix(codegen,tests): clear the flext-infra tip test reds at their owners (#919)
merge: synchronize recovery with 0.12.0-dev tip \[WIP\] (#916)
refactor(cli): project-prefix the CLI route and dispatch classes (census K1) (#917)
merge: synchronize recovery with 0.12.0-dev tip \[WIP\]
Fix/infra check green 20260927 (#915)
\[WIP\] merge 0.12.0-dev: adopt the concurrent Beads-participation and namespace line
\[WIP\] fix(check): make check green in CI within 120 s (#913)
Recovery/stabilization 0.12 20260926 (#914)
Fix/namespace product owner 20260926 (#911)
Merge branch '0.12.0-dev' into fix/namespace-product-owner-20260926
Fix/docker ci policy 20260926 (#912)
Recovery/stabilization 0.12 20260926 infra (#910)
Merge branch '0.12.0-dev' into recovery/stabilization-0.12-20260926-infra
\[WIP\] merge 0.12.0-dev into the lane (13 tip commits) (#909)
fix: zero-red convergence — rope fork dc.3, canonical adoption, lifecycle speed (#902)
\[WIP\] merge 0.12.0-dev into the lane (13 tip commits)
Merge origin/0.12.0-dev into fix/zero-red-convergence-20260925
merge: integrate flext-infra 0.12.0-dev tip into stabilization lane
merge: adopt the runtime-census cures from fix/modernizer-probe-merge-20260926
merge: refresh flext-infra integration tip
fix(namespace): facade stem carries the package identity, not the checkout (#908)
fix(gen): isort member order is case-insensitive inside a type group (#907)
fix(pytest): cosmos-docgen ceiling returns to the measured 4 workers (#906)
fix(pytest): cosmos-docgen declares its measured 8-worker ceiling (#905)
feat(pytest): per-project worker ceilings in the tooling SSOT (#904)
fix(docs): prettier never rewraps pandoc-fenced authoring sources (#903)
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/iac-infra-owner
test(modernizer): repair the derived-facade probe left unparsable on the tip (#901)
merge recovery/stabilization-0.12-20260926 (00f7a8ed4): adopt the infra stabilization
line
merge fix/modernizer-probe-parse (#901): adopt its probe assertion; overview from the
corrected generator
WIP on fix/zero-red-convergence-20260925: 3e288f9ce fix(tests): the conform lifecycle
scenarios clone one conformed template
merge(zero-red): adopt canonical a4898b561 per runbook 08
merge: align infra CI repairs with latest 0.12.0-dev tip
Merge origin/0.12.0-dev into fix/iac-infra-owner
Fix/zero red tests (#897)
Merge origin/0.12.0-dev into fix/infra-red-tests-followup
Merge current 0.12.0-dev into namespace product fix
merge: align infra stabilization with 0.12.0-dev tip
Merge the pytest runner serialize-small-selection fix
Merge origin/0.12.0-dev into fix/iac-infra-owner
Merge the layout keep-override test fix
Merge the modernizer and joint-mod test fixes
Merge branch '0.12.0-dev' into fix/zero-red-tests
Fix/zero red convergence 20260925 (#898)
Merge branch '0.12.0-dev' into fix/zero-red-convergence-20260925
\[WIP\] fix: preserve frozen runtime identity and native bootstrap repairs (#899)
Fix/v8 s0 npm lock (#900)
Merge branch '0.12.0-dev' into fix/v8-s0-npm-lock
Merge branch '0.12.0-dev' into fix/frozen-runtime-identity-20260926
Merge branch '0.12.0-dev' into fix/zero-red-tests
chore(merge): adopt the direct integration-tip repairs d6a413f32 and … (#896)
test: repair the rename-campaign tests and the runtime-consumer import probe (#894)
test(container): drop the dependency-injector bridge fixture (#893)
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/iac-infra-owner
Integrate current 0.12.0-dev tip into infra stabilization
merge: align with 0.12.0-dev
Integrate native platform and complete gate stabilization
fix(layout): cosmos-docgen keeps its presentation SSOT roots (#895)
merge generation failure and lease repair
merge dependency floor owner repair
Merge the docs root-scope fix: restore the gen fixed point on the integration tip
Merge pull request #892 from marlonsc/fix/docs-workspace-root-generate-symmetry
merge: adopt canonical 0.12.0-dev tip f06c0d0b into the zero-red convergence lane
Fix/zero red tests (#891)
fix: restore post-#881 integration green (stale merge resolutions, pending infra-dedup
rewrites) (#890)
chore(merge): adopt the direct integration-tip repairs d6a413f32 and bf59a1357
fix(tests): repair tip merge residue and drop the detector import workaround (#889)
chore(merge): integrate origin/0.12.0-dev (#888) into post-881 lane
merge: adopt 0.12.0-dev (infra-dedup test campaign) into the slow-tier lane
Feat/rename campaigns as rule data (#888)
merge: adopt 0.12.0-dev (#884 governed detector) into the slow-tier lane
Fix/infra slow tier green (#887)
chore(merge): adopt the remote base update of the rename-campaigns lane
feat(codemod): ship rename campaigns as make mod rule data (infra-dedup) (#881)
Merge branch '0.12.0-dev' into feat/rename-campaigns-as-rule-data
Fix/zero red tests (#886)
Fix/infra slow tier green (#885)
fix: pyproject generated header + detector consumes governed SSOT (#884)
Merge branch '0.12.0-dev' into feat/rename-campaigns-as-rule-data
chore(merge): integrate origin/0.12.0-dev test-law work into rename-campaigns lane
merge(zero-red): adopt the canonical adjusted integration tip 1b2b15ece
chore(merge): integrate 0.12.0-dev (#883 propagate verb) into pyproject header/detector
SSOT lane
feat(workspace): add the workspace-only propagate verb (one lane per changed member)
(#883)
chore(merge): integrate origin/0.12.0-dev into rename-campaigns lane
test: drive flext-infra's own suite to zero reds on the integration tip (#882)
test: exterminate test-law violations in flext-infra's own suite and repair the reds
they hid (#880)
chore(merge): integrate origin/0.12.0-dev (#877 #878 #879) into test-law lane
refactor(release): one publication lane owner and a collapsed release package (#879)
\[WIP\] merge origin/0.12.0-dev into refactor/release-publication-owner
feat(coverage): remove the coverage floor; coverage is measured, never gated (#877)
fix(codegen): elect lazy-init letters from the project's own facade chain (#878)
feat(codemod): generalize the test-law rule catalog (#875)
Merge origin/0.12.0-dev into feat/release-coverage-floor
\[WIP\] Merge origin/0.12.0-dev (org overlay test isolation #876) into test-law lane
fix(tests): write layout org overlay under tmp\_path, not the installed flext-cli
package (#876)
fix(gates): adopt #869 boundary print detection and repair the integration fixed point
(#874)
Merge 0.12.0-dev into fix/post-merge-green-20260925
fix(codemod): restore the rope lint exemption and loud None guards in… (#873)
Merge branch '0.12.0-dev' into fix/zero-red-tests
Fix/zero red convergence 20260925 (#872)
Merge branch '0.12.0-dev' into fix/zero-red-convergence-20260925
Merge integration into facade alias and development contract lane (#871)
Merge branch '0.12.0-dev' into fix/facade-alias-inheritance
Fix/lazy export collision 20260924 (#870)
Merge branch '0.12.0-dev' into fix/lazy-export-collision-20260924
fix(make): upg passes no empty lockfile platform list to mise (#868)
fix(make): workspace members use the workspace runtime; setup parses on the host make
(#867)
Fix/zero red tests (#866)
Merge branch '0.12.0-dev' into fix/zero-red-tests
Merge remote-tracking branch 'origin/fix/suite-green' into fix/zero-red-tests
fix(make): upg runs the declared pre-/post-upg lifecycle hooks (#858)
Merge branch '0.12.0-dev' into fix/upg-lifecycle-hooks
fix: integrated suite green (suite-green + 861 convergence) (#865)
Merge branch '0.12.0-dev' into fix/suite-green
Merge remote-tracking branch 'origin/fix/rope-fork-pin' into fix/zero-red-tests
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/zero-red-tests
merge(zero-red): adopt the integration tip 6d5e06e5e before the zero-red proof
merge(zero-red): adopt the parallel suite-green convergence lane
fix(gates,codegen): neutral security skip without src; package:false analyzer dirs
(#864)
merge(zero-red): adopt the profile-owned rope pin and restored codegen contracts from
fix/zero-red-tests
merge(zero-red): adopt the rope fork cutover and mod findings from fix/rope-fork-pin
Merge commit '44b3381ea' into fix/suite-green
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/suite-green
fix(codemod): facade-base-by-class-name selects FLEXT family facades only (#863)
Merge strict post-merge gate repairs into upg lifecycle
Merge origin/0.12.0-dev into fix/upg-lifecycle-hooks
Merge origin/0.12.0-dev into fix/upg-lifecycle-hooks; keep the lock law over #860
fix(layout): GEMINI.md is a canonical agent pointer (#862)
merge(0.12.0-dev): adopt the integration tip into the suite-green lane
Merge branch '0.12.0-dev' of github.com:flext-sh/flext-infra into
fix/infra-green-convergence-20260925
fix(toolchain): unlocked fleet mode + stale installer cleanup + tip integration (#860)
Merge origin/0.12.0-dev into fix/upg-lifecycle-hooks
fix(docs): surface validate reasons and honor the workspace-root docs contract (#859)
fix(codegen): drop stale installer projection entries + integrate tip (#856)
Merge remote-tracking branch 'origin/0.12.0-dev' into chore/fleet-integration-20260925
Merge remote-tracking branch 'origin/0.12.0-dev' into 0.12.0-dev
Merge origin/0.12.0-dev into fix/upg-lifecycle-hooks
fix: finish post-merge infra convergence (#857)
Merge remote-tracking branch 'origin/chore/fleet-integration-20260925' into
chore/fleet-integration-20260925
Merge branch '0.12.0-dev' of github.com:flext-sh/flext-infra into
fix/infra-green-convergence-20260925
Merge remote-tracking branch 'origin/0.12.0-dev' into 0.12.0-dev
Fix/post merge green 20260925 (#854)
merge: integrate all pending 0.12.0-dev pull requests (#853)
merge: integrate PR 840 preserved integration guards
merge: integrate PR 850 pydantic-settings update
merge: integrate PR 851 infra green convergence
merge: integrate PR 852 mise activation recovery
Merge branch '0.12.0-dev' into fix/models-facade-base-import
Merge branch '0.12.0-dev' of github.com:flext-sh/flext-infra into
fix/infra-green-convergence-20260925
feat(make): freeze setup installs and centralize lock updates (#845)
fix(infra): converge activation ownership and strict validation (#849)
fix(codegen): align facade imports and generated fixture contracts (#847)
merge: adopt the concurrent fix/models-facade-base-import head into the envrc recovery
Merge branch '0.12.0-dev' into fix/infra-green-convergence-20260925
Merge branch '0.12.0-dev' into fix/models-facade-base-import
Merge branch '0.12.0-dev' into feat/upg-lock-law
fix(check): preserve native failures and typed observations (#848)
fix(infra): reconcile activation history with regenerated artifacts
\[WIP\] Integrate activation ownership with strict test accounting
\[WIP\] Merge validated CI partitions and Sonar source repairs into accounting
\[WIP\] Merge frozen setup and validated gate policy into fixture repair
\[WIP\] Merge frozen setup and truthful gate observations into test accounting
\[WIP\] Merge validated native gate repairs into CI partition
Merge preserved public fixture and declared identity repairs
Merge frozen toolchain and active gate policy into check repair
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/codemod-gate-observational
Merge current integration into frozen toolchain lane
WIP on feat/upg-lock-law: fd51696db \[WIP\] test(upg): assert the committed-lock law on
generated output
merge: integrate current 0.12.0-dev into testmon hotfix
Merge remote-tracking branch 'origin/0.12.0-dev' into 0.12.0-dev
merge: integrate current 0.12.0-dev into testmon hotfix
\[WIP\] fix(codemod): facade-base rewires every letter base of a compos… (#844)
Fix/lazy init mode parity 20260923 (#843)
Merge branch '0.12.0-dev' into fix/lazy-init-mode-parity-20260923
\[WIP\] preserve: workspace-venv-ownership lane uncommitted work (6 paths) (#842)
Merge branch '0.12.0-dev' into fix/workspace-venv-ownership
fix(mise): stop projecting bd/gc into project .mise.toml; ai-hub's global config owns
them (#841)
Fix/phase1 wave generator (#839)
wip: preserve generator ownership and strict gate repairs (#838)
\[WIP\] fix(codegen): quote the mise bootstrap tilde patterns; key conf… (#837)
scratch: nearest-parent election (#836)
Merge branch '0.12.0-dev' into fix/lazy-init-nearest-parent-election
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/lazy-export-collision-20260924
merge: adopt integration repairs before generator validation
fix(gates): keep ast-grep exit semantics in the observational split (#835)
Merge remote-tracking branch 'origin/0.12.0-dev' into 0.12.0-dev
fix(gates): make codemod policy findings observational (#834)
Merge integration into facade alias and development contract lane
fix(codegen): scope fresh-import probes to declared Python packages (#833)
fix(deps): declare pymdown-extensions as a core runtime dependency (#832)
merge: land rope lane generator parity cures and the gen/fix fixed-point fix
(flext-djna9, flext-w2iw4, flext-7gup3, flext-7mo02)
Merge remote-tracking branch 'origin/0.12.0-dev' into recovery/rope-automation-20260921
feat(sonar): sync SonarCloud server-side issue exclusions from the codegen SSOT (#830)
\[WIP\] merge origin/0.12.0-dev into recovery lane (flext-w2iw4)
Merge origin/0.12.0-dev (#828 sonarcloud tests root, #829 facade base) into the
sonarcloud-sync lane
fix(codemod): facades extend the parent by its declared class name (#829)
Merge origin/0.12.0-dev (sonarcloud projector #826/#828, floor writer #827) into the
facade-base lane
fix(codegen): declare the SonarCloud tests root unconditionally (#828)
Merge remote-tracking branch 'origin/0.12.0-dev' into recovery/rope-automation-20260921
fix(codegen): derive the project package name from the manifest, not the directory name
(#825)
fix(deps): write dependency floors to the modernized repository, never the installed
package (#827)
feat(codegen): project .sonarcloud.properties fleet-wide from the SSOT (#826)
Merge remote-tracking branch 'origin/chore/regen-20260923' into
recovery/rope-automation-20260921
wip
Merge remote-tracking branch 'refs/remotes/origin/0.12.0-dev' into 0.12.0-dev
fix(ci): authenticate the Docs workflow toolchain resolution with the job token (#823)
fix(tests): derive the CI workflow contract from the workflow SSOT (#822)
fix(validate): stop the composition-root rule crashing on bare module annotations (#821)
fix(deps): raise the pydantic-settings floor to 2.14.2 (#820)
fix(ci): drop make test from the CI workflow (#819)
Merge PR #818 lane (nearest-parent facets, regression test, pyright fix) into the CI
lane
merge(0.12.0-dev): absorb integration tip 2026-09-23 wave-8 (no-ff)
integrate origin/0.12.0-dev: rope automation wave-6
merge(0.12.0-dev): absorb integration tip 2026-09-23 wave-7 (no-ff)
Rope automation wave-6: generator fixed point + pydantic-settings cure (#816)
Fix/lazy init deterministic order (#817)
chore(gen): land the generator fixed point on 0.12.0-dev (#815)
merge(0.12.0-dev): absorb integration tip 2026-09-23 wave-6 (no-ff)
merge(0.12.0-dev): sync before the plugin cure
merge(0.12.0-dev): absorb #812 lazy-init determinism before re-rendering
fix(ci): refresh the apt index before installing declared system packages (#814)
merge(0.12.0-dev): absorb integration tip 2026-09-23 wave-5 (no-ff)
fix(config): restore the canonical mypy section; deterministic lazy-init order (#812)
merge(0.12.0-dev): absorb mypy warning posture and root-cause holds
merge(0.12.0-dev): sync the determinism branch with the tip
merge(0.12.0-dev): integrate the tip before restoring resolvability
merge(0.12.0-dev): absorb allow\_redefinition restoration + fixes (no-ff)
merge(0.12.0-dev): absorb pydantic-settings hold + strict facade roots + mypy warning
posture (no-ff)
merge(0.12.0-dev): absorb integration tip 2026-09-23 wave-6 (no-ff)
merge(0.12.0-dev): absorb integration tip 2026-09-23 wave-5 (no-ff)
merge(0.12.0-dev): absorb integration tip 2026-09-22 wave-4 (no-ff)
merge: absorb integration execution import repair (#810)
merge(0.12.0-dev): converge python toolchain lane (#809)
Wip/audit infra 20260922 (#808)
chore(gen): project ruff namespace-packages and rope-cured facets (#811)
Merge branch '0.12.0-dev' into wip/audit-infra-20260922
feat(check): warning-gate policy is owned by the checked repository (#807)
Merge the post-merge repair lane (lint/pyright root fixes, test debt, warning posture)
merge(0.12.0-dev): absorb integration tip 2026-09-22 wave-3 (no-ff)
merge(0.12.0-dev): land rope engine cures — lazy-init planner bootstrap exports
merge(0.12.0-dev): absorb gen-fixed-point planner repairs (no-ff)
Merge integration tip 37c348afe (warn posture + rope alignment) into post-merge repair
merge(0.12.0-dev): absorb integration tip 2026-09-22 (no-ff)
Merge remote-tracking branch 'origin/0.12.0-dev' into wip/audit-infra-20260922
merge(0.12.0-dev): absorb rope infra alignment (no-ff)
fix(gates): grade namespace and runtime-census findings as advisory warnings (#806)
Merge remote-tracking branch 'refs/remotes/origin/0.12.0-dev' into 0.12.0-dev
fix(audit): root-cure silent fallbacks, shadowings, bypasses and fake tests
(flext-t5uhw) (#805)
merge(0.12.0-dev): align recovery with integration tip 20260922 (no-ff)
Merge remote-tracking branch 'origin/0.12.0-dev' into wip/audit-infra-20260922
merge: adopt integration tip into codemod rules slice (no-ff)
\[WIP\] Enforce workspace-owned Python environments (#801)
merge: 0.12.0-dev tip into branch (stabilization)
Merge integration tip d74c1f633 (PR #804 merge) into post-merge fixed-point repair
Repair generated Make help, metadata discovery and gate diagnostics (#804)
Merge current integration fixes before producer validation
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/backport-sed-csv-mod
Merge current integration before generated consumer validation
Merge remote-tracking branch 'origin/0.12.0-dev' into recovery/rope-automation-20260921
Merge branch '0.12.0-dev' of github.com:flext-sh/flext-infra into 0.12.0-dev
Merge current integration before generated artifact repair
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/workspace-venv-ownership
fix(gates): preserve parser failures and repair integration type contracts (#802)
Merge current integration before gate repair validation
\[WIP\] reconcile current integration and enforce transactional runtime verification
Merge integrated SccReport and markdown-code fixes
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/workspace-venv-ownership
Merge current integration namespace repair before validation
Merge integration before preserving native gate diagnostics
\[WIP\] merge integration while preserving recovered generator repairs
Integration/knowledge hub fleet 20260922 (#800)
fix(setup): advance Python minor to latest patch (#799)
merge(recovery): converge Rope automation with Python setup
merge: absorb integration execution import repair
merge(0.12.0-dev): converge python toolchain lane
\[WIP\] absorb latest integration owner repairs
Merge remote-tracking branch 'origin/0.12.0-dev' into 0.12.0-dev
Merge remote-tracking branch 'refs/remotes/origin/0.12.0-dev' into 0.12.0-dev
merge(0.12.0-dev): adopt published tip before landing the runtime-model alias fix
merge(0.12.0-dev): integrate concurrent work before landing the conform dedup
Merge remote-tracking branch 'refs/remotes/origin/0.12.0-dev' into 0.12.0-dev
Merge remote-tracking branch 'origin/0.12.0-dev' into 0.12.0-dev
\[WIP\] absorb integration SCC bootstrap repair
Recovery/rope automation 20260921 (#797)
merge(0.12.0-dev): adopt published tip before landing gates fix
\[WIP\] absorb current Infra integration into recovery
fix(codegen): authenticate cached hardlink sources (#796)
fix(conform): plain self in the conform partials; typed receipts docu… (#795)
fix(codegen): wheel force-include skips data dirs already shipped by the package (#794)
fix(security): semgrep remediation infra — tarfile extraction filter + triage +
dependabot cooldown (flext-p57t.12) (#793)
fix(codegen): propagate environment filesystem failures (#792)
fix(ci-template): gen fixed-point step carries the job token (#791)
merge: absorb integration tip (dependabot stagger SSOT)
Merge branch '0.12.0-dev' into fix/semgrep-infra-reval260921
Merge remote-tracking branch 'origin/0.12.0-dev' into 0.12.0-dev
Merge remote-tracking branch 'origin/0.12.0-dev' into 0.12.0-dev
merge: absorb origin 0.12.0-dev (duplicate-content lineages converge)
\[WIP\] absorb current integration into Rope recovery
fix(check): report codemod matches as warnings (#790)
Merge origin/0.12.0-dev into fix/docs-source-state-ci
\[WIP\] Recover Rope and generation automation (#788)
fix(docs): authenticate hardlinked read sources (#789)
\[WIP\] recover codegen residue through current declaration owners
\[WIP\] reconcile recovered Beads marker residue with current codegen owners
\[WIP\] merge recovered generation convergence history into automation recovery
fix(codegen): declaring-owner letters, declaration-first integration (flext-0in0k.9)
fix(codegen): declaring-owner letters, declaration-first integration branch,
one-name-per-line tuples (flext-0in0k.9) (#785)
fix(codegen): render wrapped imports one name per line; four-per-line LOC-cap workaround
dies (flext-5fxu6.4.9) (#783)
\[WIP\] merge origin/0.12.0-dev (ClassVar namespace-holder members, sorted discovery)
into lane/f04-import-renderer-one-per-line
Merge remote-tracking branch 'origin/0.12.0-dev' into HEAD
feat(codemod): ban-numbered-script-all-declaration — numbered scripts publish nothing
(flext-0in0k.3) (#782)
merge: absorb fleet tip into protocol receipt lane
stabilize(0.12): land the flext-infra lane and restore inherited facade letters (#781)
merge: bring the integration branch into the flext-infra lane
fix(codegen): the transaction journal recovers one recorded root, consistently (unblocks
make gen) (#780)
chore(rope): preserve rope-modernize uncommitted edits (follow-up #744) (#765)
fix(codegen,utilities): port the remaining MRO-cutover repairs (repository\_provider,
Make selector, signature-rules loader) (#779)
Merge remote-tracking branch 'origin/0.12.0-dev' into wip/org-layer-restore-20260920
fix(config,models): restore the org layer and collapse the duplicated release family
(blocks gen + ai-hub check) (#778)
merge: integrate 0.12.0-dev (post 775/776/777) into rope-modernize lane (PR #765
adoption)
perf(lazy-init): pack comma entries up to MAX\_LINE\_LENGTH in projections (#777)
Merge branch '0.12.0-dev' into perf/lazy-init-compact-render
Wip/stabilize 0.12 flext infra 20260919 (#776)
Merge branch '0.12.0-dev' into wip/stabilize-0.12-flext-infra-20260919
merge: integrate 0.12.0-dev into rope-modernize preservation lane (PR #765 adoption)
Fix/conform plan base restore (#775)
Merge branch '0.12.0-dev' into fix/conform-plan-base-restore
merge: reconcile mirror lineage with import-fixed lineage (flext-v4fmn)
merge: reconcile both repairs of the models refactor (fix-forward)
merge: bring the integration tip into the lane (fix-forward)
merge: bring this mirror checkout up to the published integration (fix-forward)
merge: adopt the concurrent lane advance (fix-forward)
Merge commit '1fccfca1fd215b761d5f081e5e0faf6802ef3f5a' into 0.12.0-dev
Merge commit '4100745ca894c47ed02128510fcf4e8f82c7b557' into 0.12.0-dev
Merge commit 'be1bbc34023ac2922b0a6b07a13b5b06ed1ae2e4' into 0.12.0-dev
wip
Merge commit 'd03939aea31b672b4c91e6a831222e510a621482' into 0.12.0-dev
Merge commit '4ee955c0b3531882eb6ac9a3364599eb4799f52d' into 0.12.0-dev
Merge remote-tracking branch 'refs/remotes/origin/0.12.0-dev' into 0.12.0-dev
merge: reunite the lane with its published head (fix-forward)
Merge commit 'd84644f0698f06d81f3be10cc3de2865455841a9' into 0.12.0-dev
Merge commit '56ffdb5af1809469a61ebf99995637250fdd7fbb' into 0.12.0-dev
Merge commit '52e84484d71ade3c4295e28597d9667a9fceb3d9' into
wip/stabilize-0.12-flext-infra-20260919
merge: absorb 0.12.0-dev tip (fleet projections + residue adoption) into stabilized
lineage
Merge commit 'd81d0d03dc8501fa9cce76081fc2878923a6b4ad' into 0.12.0-dev
Wip/stabilize 0.12 flext infra 20260919 (#772)
Merge branch '0.12.0-dev' into wip/stabilize-0.12-flext-infra-20260919
refactor(utils): implement semantic cutover module and refactor dispatch
Merge commit '30c82b30f5b4ecf6b660a743014a725da13e70da' into 0.12.0-dev
Merge commit 'ba29d112b8429fb65abffd6e5066c78f75136fa9' into 0.12.0-dev
merge: worktree-fix-hermetic-gate-child-env into 0.12.0-dev (best of both)
merge: adopt parallel lane's convergence of stabilization branch
Merge branch 'stabilize/lazy-init-exports' into 0.12.0-dev
Merge branch 'wip/stabilize-0.12-flext-infra-20260919' into 0.12.0-dev
merge: absorb 0.12.0-dev tip into lazy-init-exports (infra #764)
Merge remote-tracking branch 'refs/remotes/origin/0.12.0-dev' into 0.12.0-dev
\[WIP\] merge(port-now): resgate do kilo-code — fatos de worktree + testes de validate
\[WIP\] merge(port-now): fachada unica do modernizer de deps + familia conform de
pyproject
\[WIP\] merge(port-now): gates rumdl+prettier no markdown SSOT da frota
\[WIP\] merge(port-now): rollback de bootstrap do scaffold + testes de lifecycle
\[WIP\] merge(port-now): gate LAZY\_BOOTSTRAP\_ROOT\_PACKAGE do lazy-init
\[WIP\] merge(port-now): shellcheck de templates + journal de codegen por worktree
merge: absorver origin/0.12.0-dev na lane de estabilização de flext-infra
fix(conform): allow passive bd ledger exports in composed Beads routes (#768)
Merge remote-tracking branch 'origin/0.12.0-dev' into eval/pr-766
Merge remote-tracking branch 'origin/worktree-agent-a446a07f0e7868707' into eval/pr-766
Merge remote-tracking branch 'origin/worktree-agent-a584f133b536d21e8' into eval/pr-761
Merge remote-tracking branch 'origin/stabilize/lazy-init-exports' into eval/pr-764
Merge remote-tracking branch 'origin/fix/codegen-mro-fleet' into eval/pr-763
Merge remote-tracking branch 'origin/worktree-agent-a7e86cd1eba0cd1e6' into eval/pr-762
merge(0.12.0-dev): converge stabilization branch with the tip
Merge remote-tracking branch 'origin/feature/rope-modernize' into eval/pr-760
fix(codegen): render bare internal deps at workspace-context root (#767)
Merge branch '0.12.0-dev' into feature/rope-modernize
Merge remote-tracking branch 'refs/remotes/origin/0.12.0-dev' into 0.12.0-dev
wip
fix(infra): recognize legacy member guide projections; remove merge marker from execute
owner (#752)
Merge branch '0.12.0-dev' into docs/governance-convergence-adopt
fix(check): markdown-code gate default OFF (explicit CHECK\_GATES only) (#753)
Merge branch '0.12.0-dev' into fix/markdown-code-default-off
fix: restore generation and documentation contracts for chart validation (#754)
Merge branch '0.12.0-dev' into fix/dese-provider-contracts
Merge current provider configuration ownership into dese repairs
Merge provider tool provenance repair into dese validation
Merge current provider integration for documentation repair
Merge current provider integration branch into dese repairs
fix(workspace): integrate remote 0.12.0-dev and keep orchestrator fix
Merge remote-tracking branch 'refs/remotes/origin/0.12.0-dev' into 0.12.0-dev
merge: absorb integration tip 385a71212 (governance projection refresh) into
pydantic-protocol-repairs lane
Merge origin/0.12.0-dev into feature/rope-modernize
merge: absorb 0.12.0-dev fixes; reconcile config family, promoted contract and conform
ports
merge: absorb 0.12.0-dev into pydantic-protocol consolidation lane (fix-forward,
hunk-by-hunk)
Merge commit '222994200' into 0.12.0-dev
fixes
fixes
fixes
fix(make): route enforcement through workspace dispatcher (#750)
Merge branch '0.12.0-dev' into fix/workspace-fix-enforcement
\[WIP\] codegen: unblock cosmos consumers (manifest-owned urls, abort-on-failure,
state-dir lease, workflow comments, envrc guard) (#747)
Merge branch '0.12.0-dev' into lane/cosmos-unblock
fix(docs): converge documentation pipeline owners (#746)
Merge branch '0.12.0-dev' into feature/rope-modernize
merge: integrate origin 0.12.0-dev
fix: stabilize 0.12.0-dev utility and layout repairs (#751)
merge: retain strict utility repairs on 0.12.0-dev
fixes
merge: integrate current strict 0.12.0-dev producer tip
Merge fix/generated-guide-ownership into 0.12.0-dev
merge: integrate latest MRO role typing
merge: integrate 0.12.0-dev into documentation lane
merge: adopt documentation pipeline tip
merge: integrate 0.12.0-dev into governance convergence
infra: rope modernize engine + lazy-init one-writer fix (#743)
Merge branch '0.12.0-dev' into feature/rope-modernize
Merge branch 'branch' into feature/rope-modernize
\[WIP\] merge lane/pydantic-protocol-repairs into W-I lane; regenerate lazy maps
(flext-5fxu6.4.15)
\[WIP\] merge lane/pydantic-protocol-repairs checkpoint into W-H worker lane
(flext-5fxu6.4.15)
\[WIP\] merge lane/pydantic-protocol-repairs into W-I worker lane (flext-5fxu6.4.15)
\[WIP\] merge lane/pydantic-protocol-repairs into W-G lane (flext-5fxu6.4.15)
\[WIP\] merge lane/z456w-infra (cosmos-z456w promoted discovery) into lane
(flext-5fxu6.4)
\[WIP\] merge PR #743 feature/rope-modernize into lane (flext-5fxu6.4 S1)
\[WIP\] merge origin/0.12.0-dev into lane/pydantic-protocol-repairs
Merge remote-tracking branch 'origin/0.12.0-dev' into lane/pydantic-protocol-repairs
merge: absorb 0.12.0-dev tip; \_models/codegen.py = integration facade shape
(\_codegen/base.py joins family modules; census/policy/results/session partials
exterminated upstream)
fix(config): canonical Infra owns sed\_patterns (SSOT yaml key validated;
artifact/release duplicate Infra roots remain for later cutover)
merge: absorb promoted-framework-lift (PR #681) into rope-modernize; newest law wins —
HEAD kept for all content conflicts (cooldown/apply exterminations, structlog\<26
rationale), killed files stay dead
Merge remote-tracking branch 'origin/0.12.0-dev' into feature/rope-modernize
merge: absorb 0.12.0-dev tip (mise recovery sha256 identity, ruff fmt) into
rope-modernize lane; gen-side alignment stays exterminated (one writer per destination)
merge: absorb remote lane advances into feature/rope-modernize (fix-forward)
chore(lane): absorb lane remote advances (stabilizer)
Merge branch '0.12.0-dev' into feature/rope-modernize
chore(lane): pull 0.12.0-dev tip (stabilizer sync)
merge: integrate remote advance before renderer gate
merge: renderer bootstrap-owner gate (G1) into 0.12.0-dev
chore(lane): unify optional-city split + toolchain + f4 adoptions into rope-modernize
Merge remote-tracking branch 'origin/0.12.0-dev' into stabilize/lazy-init-exports
chore(adoption): merge f4-infra into rope-modernize lane
chore(adoption): merge fix/toolchain-spec-restore into rope-modernize lane
chore(adoption): merge fix/optional-city-env-source into rope-modernize lane
Merge remote-tracking branch 'refs/remotes/origin/0.12.0-dev' into 0.12.0-dev
merge: integrate remote 0.12.0-dev with alignment crash fix
Merge remote-tracking branch 'refs/remotes/origin/0.12.0-dev' into 0.12.0-dev
Fix/flext 5fxu6 recover interrupted integration (#742)
Merge branch '0.12.0-dev' into fix/flext-5fxu6-recover-interrupted-integration
Fix/flext 5fxu6 generator facades (#741)
Merge branch '0.12.0-dev' into fix/flext-5fxu6-generator-facades
merge: integrate origin/0.12.0-dev (PR 740 mod sed list import) with adoption WIP
af9f4ae34
Feat/mod sed list import (#740)
merge: absorb integration tip 0.12.0-dev into optional-city-env-source
Merge branch '0.12.0-dev' of github.com:flext-sh/flext-infra into 0.12.0-dev
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/codegen-docs-ownership
Merge remote-tracking branch 'origin/0.12.0-dev' into 0.12.0-dev
chore(gen): adopt conditional environment-source projection (#736)
Merge branch '0.12.0-dev' into fix/envrc-optional-environment-sources
fix(docs): import the codegen file plan used by source freezing (#738)
Merge branch '0.12.0-dev' into feat/mod-sed-list-import
Merge branch 'v5-exec' into 0.12.0-dev
Merge remote-tracking branch 'origin/0.12.0-dev' into v5-exec
Merge branch 'v5-exec' into 0.12.0-dev
Merge remote-tracking branch 'refs/remotes/origin/0.12.0-dev' into 0.12.0-dev
Merge remote-tracking branch 'refs/remotes/origin/0.12.0-dev' into v5-exec
\[WIP\] Preserve plan collector and transaction handoff (#733)
Merge branch '0.12.0-dev' into fix/plan-reconciliation-make-contract
fix(envrc): source Gas City environment sources only when they exist (#735)
Merge branch 'fix/workspace-hygiene-0.12.0' into 0.12.0-dev
Merge remote-tracking branch 'origin/bugfix/stabilize-0.12.0' into
fix/workspace-hygiene-0.12.0
merge: adopt central tracker restoration and environment fixes
\[WIP\] Merge current integration environment and Beads contracts
\[WIP\] Merge latest integration runtime and direnv lifecycle fixes
merge: adopt current integration runtime composition
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/workspace-hygiene-0.12.0
\[WIP\] Merge integration tip and reconcile transaction and documentation owners
Merge current integration and preserve shared fixtures and CI command contract
merge: carry docs renderer contract into integration
\[WIP\] Reconcile stabilization contributions and refresh operational handoff
Merge development relative-import repair into stabilization
Merge current integration into collector stabilization
Merge remote-tracking branch 'origin/hotfix/pytest-complete-failure-reporting' into
bugfix/stabilize-0.12.0
\[WIP\] integrate strict docs planning and reconciled test namespaces
\[WIP\] merge Git facade and fixture contributions from PR 723
Merge remote-tracking branch 'refs/remotes/origin/0.12.0-dev' into
bugfix/stabilize-0.12.0
Merge published generation repairs into reconciliation lane
Merge remote-tracking branch 'origin/0.12.0-dev' into
hotfix/pytest-complete-failure-reporting
chore(gitignore): adopt two residue patterns at the owner, reject the third (#726)
\[WIP\] Remove remaining Make effect selectors (#728)
Merge branch '0.12.0-dev' into fix/plan-reconciliation-make-contract
\[WIP\] stabilize generated configuration and absorb checkout changes (#729)
Merge completed operator integration cycle
merge: absorb completed operator integration cycle
Merge remote-tracking branch 'refs/remotes/origin/0.12.0-dev' into
bugfix/stabilize-0.12.0
Merge published integration snapshot into reconciliation
Merge integration and regenerate Make contract documentation
merge: retain exact integration gitlink history
Merge 0.12.0-dev into Make contract reconciliation
merge: absorb published checkout changes for stabilization
merge: absorb published operator checkout for stabilization
Merge remote-tracking branch 'refs/remotes/origin/0.12.0-dev' into 0.12.0-dev
fix(infra): stabilize 0.12.0 bootstrap — no-mode Make, exterminate budget/.gen/ancestry
(#727)
Merge remote-tracking branch 'refs/remotes/origin/0.12.0-dev' into 0.12.0-dev
Merge pull request #725: the fleet commits no uv.lock; setup resolves floors fresh
merge origin/0.12.0-dev into lane-r41: absorb integration
Merge remote-tracking branch 'origin/0.12.0-dev' into
worktree-fix-hermetic-gate-child-env
fix(codegen): the owner declares every table it writes (#722)
Merge branch '0.12.0-dev' into lane-r41
fix(codegen): \`initialize\` requires the environment it runs the toolchain in (#720)
Merge branch '0.12.0-dev' into fix/initialize-requires-environment
fix(models): the field factory moves to its declared owner, typed (#721)
Merge remote-tracking branch 'origin/0.12.0-dev' into
worktree-fix-hermetic-gate-child-env
Merge branch 'fix/flext-5fxu6-generator-facades' into
fix/flext-5fxu6-recover-interrupted-integration
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/flext-5fxu6-generator-facades
Merge pull request #719: declare index-declarations in SARIF and budget (repairs make
check)
merge origin/0.12.0-dev: absorb integration before landing scope-authority fixes
merge origin/0.12.0-dev into lane-r41: absorb integration
WIP on v5-exec: 7c66f4aca Merge remote-tracking branch 'origin/0.12.0-dev' into v5-exec
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/toolchain-spec-restore
feat(gates): an undeclared gitlink fails the gate, fleet-wide (#718)
chore(flext-infra): preserve lane-r41 changes across 2 paths (#716)
chore(flext-infra): preserve wip/duplicate/flext/flext-infra changes across 3 paths
(#715)
chore(flext-infra): preserve constants-remediation-0.12 changes across 1 paths (#714)
merge origin/0.12.0-dev into fix/discovery-honours-manifest-exclusions: absorb
integration
chore(flext-infra): preserve lane-r41 changes across 7 paths (#713)
Merge branch '0.12.0-dev' into lane-r41
fix(gates): tier-whitelist reports every violation, not an aggregate count (#712)
chore(flext-infra): preserve wip/duplicate/flext/flext-infra changes across 0 paths
(#710)
Merge branch '0.12.0-dev' into wip/duplicate/flext/flext-infra
chore(repo): drop the tracked worktree gitlink and adopt fmt output (#709)
\[WIP\] merge origin/0.12.0-dev into lane-r41
Merge remote-tracking branch 'origin/0.12.0-dev' into 0.12.0-dev
Merge commit '3d2ac92c735a52b3089923a90c2496daf71c96d4' into 0.12.0-dev
Merge branch 'fix/untrack-orphan-worktree-gitlink' into 0.12.0-dev
Merge remote-tracking branch 'origin/0.12.0-dev' into
worktree-fix-hermetic-gate-child-env
fix(codemod,models): m is the single owner of ConfigDict; the rule converges every
consumer (#706)
chore(flext-infra): preserve fix/flext-5fxu6-infra-enforcement changes across 3 paths
(#702)
fix(gates): wire the hermetic child env into every gate (#705)
WIP on fix/flext-5fxu6-infra-enforcement: eddcf601d fix: mypy type fixes for
config-loaded values
Merge remote-tracking branch 'origin/0.12.0-dev' into
worktree-fix-hermetic-gate-child-env
Merge commit 'ac681127b' into fix/flext-5fxu6-infra-enforcement
Merge remote-tracking branch 'origin/0.12.0-dev' into 0.12.0-dev
fix(codegen,deps,check): one owner for gitignore sections, pyrefly includes and declared
exception names (#698)
\[WIP\] merge origin/0.12.0-dev into chore/absorb-inflight-20260911b
Merge remote-tracking branch 'origin/0.12.0-dev' into 0.12.0-dev
Merge remote-tracking branch 'origin/0.12.0-dev' into 0.12.0-dev
Merge remote-tracking branch 'origin/0.12.0-dev' into 0.12.0-dev
Fix/green green native validation (#697)
fix(infra): integration checkpoint — make test green, 17/21 check gates, root-cause
fixes X-89..X-119 (#696)
Merge branch '0.12.0-dev' into chore/absorb-inflight-20260911b
fix(codegen): emit the repository-owned extra-verb dispatch block once (#695)
fix(codegen): stabilize byte-exact conformance diagnostics (#694)
\[WIP\] Merge origin/0.12.0-dev into chore/absorb-inflight-20260911b (integration
checkpoint)
\[WIP\] Merge origin/chore/absorb-inflight-20260911b into the lane (adopt concurrent
work, fix-forward)
\[WIP\] fix(infra): absorb in-flight lane — R28 promoted cutover, external-gate markers,
root-relative boundary scope, lazy-init parent resolution (#693)
chore(flext-infra): preserve constants-remediation-0.12 changes across 3 paths (#692)
Merge branch '0.12.0-dev' into constants-remediation-0.12
\[WIP\] Recover aborted-agent codegen/deps round (#642)
Merge branch '0.12.0-dev' into fix/recover-codegen-deps-wip
Merge branch '0.12.0-dev' into chore/absorb-inflight-20260911b
Merge remote-tracking branch 'origin/0.12.0-dev' into 0.12.0-dev
Merge remote-tracking branch 'origin/0.12.0-dev' into 0.12.0-dev
Merge remote-tracking branch 'origin/0.12.0-dev' into 0.12.0-dev
Merge remote-tracking branch 'origin/0.12.0-dev' into 0.12.0-dev
chore: absorb origin/0.12.0-dev into lane (fix-forward, 35 commits)
chore: absorb origin/0.12.0-dev into lane (fix-forward, ancestry gate)
feat(budget): generator projects the budget table from config SSOT (#688)
Merge branch '0.12.0-dev' into fix/budget-gate-generator-provisioning
fix(namespace): land loc-cap SSOT lane absorbed at host retirement (#685)
Merge branch '0.12.0-dev' into fix/namespace-loc-ssot
fix(deps): lower unsatisfiable types-openpyxl floor to published 3.1.5.20260827 (#683)
Merge branch '0.12.0-dev' into fix/types-openpyxl-floor
Release/coherent gen (#690)
Merge branch '0.12.0-dev' into release/coherent-gen
release: single-owner policy render from config (#691)
Merge remote-tracking branch 'origin/0.12.0-dev' into v5-exec
Merge remote-tracking branch 'origin/0.12.0-dev' into v5-exec
refactor: tighten types and error handling in flext\_infra
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/namespace-loc-ssot
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/namespace-loc-ssot
Merge remote-tracking branch 'origin/0.12.0-dev' into fix/namespace-loc-ssot
On 0.12.0-dev: preserved pre-integration WIP: unauthorized managed-file edits +
NS-IMPORT carve-out (fix-forward snapshot)
WIP on 0.12.0-dev: f41875666 fix(deps): structlog floor 25.5.0\<26 for meltano 4.2.2 cap
checkpoint(wip): preserve uncommitted lane state before integration sweep
Merge branch 'integrate/sweep-checks-tests-md' into fix/hq-36xk-version-ssot
Merge branch 'hotfix/gen-extra-paths-fixed-point' into fix/hq-36xk-version-ssot
Merge branch 'fix/devcontainer-render-context' into fix/hq-36xk-version-ssot
Merge branch 'hotfix/repair-committed-conflicts' into fix/hq-36xk-version-ssot
Merge branch 'feature/ehqvu-cosmos-epic-lane' into fix/hq-36xk-version-ssot
Merge branch 'epic/import-monopoly' into fix/hq-36xk-version-ssot
Merge branch 'codex/corrigir-pre-commit-e-pre-push' into fix/hq-36xk-version-ssot
Merge branch 'bugfix/uv-exclude-dependencies-schema' into fix/hq-36xk-version-ssot
Merge branch 'bugfix/pytest-profile-opt-in' into fix/hq-36xk-version-ssot
Merge branch 'bugfix/grpc-pyright-fixed-point' into fix/hq-36xk-version-ssot
Merge branch 'bugfix/external-consumer-lane-provisioning' into fix/hq-36xk-version-ssot
Merge branch 'bugfix/docs-worktree-scan-config-key' into fix/hq-36xk-version-ssot
Merge branch 'bugfix/consumer-declared-provider' into fix/hq-36xk-version-ssot
Merge branch 'bugfix/ci-integration-branch-triggers' into fix/hq-36xk-version-ssot
merge: absorb the moved tip; keep the green bootstrap template (flext-io8wa)
