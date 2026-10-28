"""Public functional contract for new and existing project conformance.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import config
from tests import c, m, t, tm, u


@pytest.mark.slow
class TestsFlextInfraScriptDispatchMakefile:
    """Prove per-repo extra verbs and script-dispatch WHAT normalization."""

    @staticmethod
    def _render_root_makefile(
        tmp_path: Path,
        *,
        extra_verbs: tuple[m.Infra.MakeVerbSpec, ...],
        script_dispatch: m.Infra.ScriptDispatchSpec | None,
    ) -> str:
        # The engine is consumer-agnostic, so this fixture models a
        # neutral downstream root and takes its provider from the engine's own
        # configured provider catalog instead of naming a real consumer.
        provider = u.Tests.provider()
        root_repository = m.Infra.RepositoryRef(
            name="demo-root",
            distribution="demo-root",
            url=f"{provider.base_url}/demo-root.git",
            path=Path(),
            # Script dispatch is a generic capability: exercise it on standalone.
            role=c.Infra.MakeProfile.STANDALONE,
            provider=provider.name,
            kind=c.Infra.ProjectKind.INTERNAL_FLEXT,
            codegen=c.Infra.CodegenKind.CONFORM,
            package=False,
            editable=False,
            read_only=False,
            extra_verbs=extra_verbs,
            script_dispatch=script_dispatch,
        )
        workspace = u.Tests.workspace_spec(
            root_repository,
            project=u.Tests.project_spec("demo-root"),
        )
        root = tmp_path / root_repository.name
        root.mkdir()
        u.Tests.initialize_git_repo(root, origin_url=root_repository.url)
        rendered: str = u.Tests.conform_makefile_text(
            root,
            workspace,
        )
        return rendered

    def test_script_dispatch_repo_routes_extra_verbs_and_normalizes_what(
        self,
        tmp_path: Path,
    ) -> None:
        """Extra verbs join PUBLIC_VERBS and dispatch through the dispatcher."""
        rendered = self._render_root_makefile(
            tmp_path,
            extra_verbs=(
                m.Infra.MakeVerbSpec(
                    name="incidente",
                    description="Dispatch incidente through the dispatcher.",
                ),
                m.Infra.MakeVerbSpec(
                    name="charts",
                    description="Dispatch charts through the dispatcher.",
                ),
            ),
            script_dispatch=m.Infra.ScriptDispatchSpec(
                dispatcher="scripts/dispatch.py",
                roots=("scripts", "apps/demo-app/scripts"),
            ),
        )
        # Extra verbs are public targets the dispatcher can reach.
        tm.ok("incidente" in rendered)
        tm.ok("charts" in rendered)
        # Each extra verb gets a _builtin-<verb> target that dispatches through
        # the repo's declared dispatcher.
        tm.ok("_builtin-incidente:" in rendered)
        tm.ok("_builtin-charts:" in rendered)
        # It forwards to the declared dispatcher through uv, not a raw builtin.
        tm.ok("scripts/dispatch.py" in rendered)
        # Script dispatch roots are recorded for operator visibility.
        tm.ok("apps/demo-app/scripts" in rendered)

    def test_extra_verb_dispatch_target_is_emitted_exactly_once(
        self,
        tmp_path: Path,
    ) -> None:
        """Every extra verb owns one public recipe; a second one is a Make warning.

        Two integrations of the same dispatch block once rendered every extra
        verb twice, and GNU Make reported ``overriding recipe for target`` on
        each parse of the consumer's Makefile.
        """
        rendered = self._render_root_makefile(
            tmp_path,
            extra_verbs=(
                m.Infra.MakeVerbSpec(name="deploy", description="Publish the runtime."),
            ),
            script_dispatch=None,
        )
        makefile = tmp_path / "demo-root" / c.Infra.MAKEFILE_FILENAME
        makefile.write_text(rendered, encoding=c.DEFAULT_ENCODING)
        observed = tm.ok(
            u.Cli.run(
                (
                    c.Infra.MAKE,
                    "--no-print-directory",
                    "--dry-run",
                    "--print-data-base",
                    "--eval=__flext_fixture_probe__:",
                    "__flext_fixture_probe__",
                ),
                cwd=makefile.parent,
            ),
        )
        deploy_targets = [
            line for line in observed.stdout.splitlines() if line.startswith("deploy:")
        ]
        tm.that(len(deploy_targets), eq=1)
        tm.that(observed.stderr, lacks="overriding recipe for target")

    def test_dispatch_routes_custom_what_before_allowlist(self, tmp_path: Path) -> None:
        """Custom ``_custom_<verb>`` handlers bypass the builtin allowlist.

        ai-hub and other projects extend ``run`` / ``check`` via custom.mk. The
        continuous Makefile RUN_PUBLIC macro discovers those handlers and
        dispatches them instead of falling through to _builtin-<verb>.
        """
        rendered = self._render_root_makefile(
            tmp_path,
            extra_verbs=(),
            script_dispatch=None,
        )
        # RUN_PUBLIC checks CUSTOM_DECLARED_TARGETS first and calls _custom-$(1)
        # when it exists, falling back to _builtin-$(1).
        tm.ok("define RUN_PUBLIC" in rendered)
        tm.ok("_custom-$(1)" in rendered)
        tm.ok("_builtin-$(1)" in rendered)

    def test_repo_without_script_dispatch_omits_script_routing(
        self,
        tmp_path: Path,
    ) -> None:
        """A repo with no script dispatch omits every script-routing projection."""
        rendered = self._render_root_makefile(
            tmp_path,
            extra_verbs=(),
            script_dispatch=None,
        )
        # No script routing leaks into non-opted-in repositories.
        tm.fail("tr '-' '_'" in rendered)
        tm.fail("scripts/dispatch.py" in rendered)

    def test_gen_replaces_codegen_as_the_single_conform_verb(
        self,
        tmp_path: Path,
    ) -> None:
        """``make gen`` is THE conform verb; ``codegen`` no longer exists.

        The convergence spine fuses codegen+conform under the
        single short ``gen`` verb: one verb, one meaning. The old ``codegen``
        Make verb is fully replaced across config, rendered handlers, and the
        regeneration header.
        """
        make_config = config.Infra.codegen.make
        verb_names = {verb.name for verb in make_config.verbs}
        tm.ok("gen" in verb_names)
        tm.fail("codegen" in verb_names)
        gen = next(verb for verb in make_config.verbs if verb.name == "gen")
        # WHAT selectors were exterminated: one verb, one meaning, declared once.
        gen_fields = type(gen).model_fields
        tm.fail("default_what" in gen_fields)
        tm.fail("_apply_flag_exterminated" in gen_fields)
        tm.ok("initialize" in verb_names)
        tm.fail("serialization" in type(make_config).model_fields)
        rendered = self._render_root_makefile(
            tmp_path,
            extra_verbs=(),
            script_dispatch=None,
        )
        public_line = next(
            line for line in rendered.splitlines() if line.startswith("PUBLIC_VERBS :=")
        )
        tm.ok(" gen" in public_line)
        tm.fail(" codegen" in public_line)
        tm.fail("_DEFAULT_gen" in rendered)
        # S1 (operator law 2026-09-14): gen dispatches unconditionally to
        # _builtin_gen_all; there is no CHECK_ONLY selector, no separate
        # check-mode recipe, and no `conform` verb left at all.
        tm.ok("_builtin-gen: _builtin_gen_all" in rendered)
        tm.fail("_builtin-conform" in rendered)
        tm.fail("_builtin_gen_check" in rendered)
        tm.fail("_builtin_gen_apply" in rendered)
        tm.ok("_builtin_gen_init:" in rendered)
        tm.ok("_builtin_gen_all:" in rendered)
        tm.fail("_builtin_codegen_check" in rendered)
        tm.fail("_builtin_codegen_apply" in rendered)
        builtin_line = next(
            line
            for line in rendered.splitlines()
            if line.startswith("BUILTIN_VERBS :=")
        )
        tm.ok(" gen" in builtin_line)
        tm.fail(" codegen" in builtin_line)
        phony_line = next(
            line
            for line in rendered.splitlines()
            if line.startswith(".PHONY:") and "_builtin_gen_" in line
        )
        tm.that(phony_line, eq=".PHONY: _builtin_gen_init _builtin_gen_all")
        # The handler delegates the entire publication to the generation pipeline.
        gen_all_body = rendered.split("_builtin_gen_all:", 1)[1].split("\n\n", 1)[0]
        tm.that(gen_all_body.count("codegen generate"), eq=1)
        tm.that(gen_all_body, has="$(PROJECT_FLEXT_INFRA)")
        tm.that(
            gen_all_body,
            lacks=[
                "_builtin_require_environment",
                "$(FLEXT_INFRA_BOOTSTRAP)",
                "codegen conform",
                "codegen init",
                "deps modernize",
                "--mode apply",
                "--mode check",
            ],
        )
        tm.that(
            gen_all_body,
            lacks=["codegen lazy-init", "docs generate", "_generated_docs"],
        )
        tm.fail("define _generated_docs" in rendered)
        gen_init_body = rendered.split("_builtin_gen_init:", 1)[1].split("\n\n", 1)[0]
        tm.that(gen_init_body.count("codegen init"), eq=1)
        tm.that(
            gen_init_body,
            has=[
                'set -- --kind "$$KIND";',
                'codegen init --repository-root "$(PROJECT_ROOT)" "$$@"',
            ],
        )
        tm.that(gen_init_body, lacks=["codegen conform", "REPOSITORY_ROOT", "bd"])
        # The regeneration contract published on every projection speaks gen.
        tm.ok("# @flext-regenerate: make gen" in rendered)
        # The custom-surface policy names gen (not codegen) for hooks/handlers.
        handler_policies: t.MutableMappingKV[str, m.Infra.CustomHandlerPolicy] = dict(
            config.Infra.codegen.make.custom_handler_policies,
        )
        for policy in handler_policies.values():
            tm.ok("|gen|" in policy.target_pattern)
            tm.fail("|codegen|" in policy.target_pattern)

    def test_make_initialize_requires_its_provisioned_interpreter(
        self,
        tmp_path: Path,
    ) -> None:
        """The public initializer validates the pinned toolchain before effects."""
        rendered = self._render_root_makefile(
            tmp_path,
            extra_verbs=(),
            script_dispatch=None,
        )
        root = tmp_path / "declared-target"
        package = root / "src" / "demo_root"
        package.mkdir(parents=True)
        makefile = root / c.Infra.MAKEFILE_FILENAME
        makefile.write_text(rendered, encoding="utf-8")
        # Every public verb except help/clean/upg requires the Mise pin
        # (db516968e); seed it so the run reaches the interpreter check.
        u.Tests.copy_tracked_mise_seeds(root)
        u.Tests.initialize_git_repo(root)
        invoked = u.Tests.run_isolated_make(
            ["--no-print-directory", "-f", str(makefile), "initialize"],
            cwd=root,
        )

        tm.ok(invoked)
        tm.fail(u.Cli.process_succeeded(invoked.value.outcome))
        tm.that(
            invoked.value.stderr,
            has=["missing environment interpreter", "make setup creates it"],
        )
        tm.fail((package / c.Infra.INIT_PY).exists())

    def test_work_lifecycle_is_not_projected(self, tmp_path: Path) -> None:
        """Gas City owns lanes; generated repositories expose no second lifecycle."""
        make_config = config.Infra.codegen.make
        verb_names = {verb.name for verb in make_config.verbs}
        tm.fail("work" in verb_names)
        rendered = self._render_root_makefile(
            tmp_path,
            extra_verbs=(),
            script_dispatch=None,
        )
        public_line = next(
            line for line in rendered.splitlines() if line.startswith("PUBLIC_VERBS :=")
        )
        tm.fail(" work" in public_line)
        tm.that(rendered, lacks="_builtin_work_")
        tm.that(rendered, lacks="workspace work")

    def test_profile_test_verb_profiles_the_canonical_pytest_entry(
        self,
        tmp_path: Path,
    ) -> None:
        """profile-test profiles the entry and its central collection children.

        Cold-run diagnosis (flext-itpd1.3.7) needs the same persistent testmon
        database guard and environment as the bounded gate, but the diagnostic
        omits the outer PYTEST_BOUNDED wrapper, not the runner's own deadline.
        """
        rendered = self._render_root_makefile(
            tmp_path,
            extra_verbs=(),
            script_dispatch=None,
        )
        tm.that(
            rendered,
            has=[
                "_builtin-profile-test: _builtin_require_environment\n",
                "_builtin-profile-test-report: _builtin_require_environment\n",
            ],
        )
        profile_test = rendered.split("_builtin-profile-test:", 1)[1].split(
            "\n\n",
            1,
        )[0]
        gate_runner = rendered.split("_builtin_test_all:", 1)[1].split("\n\n", 1)[0]
        datafile = config.Infra.codegen.make.testmon_cache.database_environment_variable
        # The diagnostic reuses the canonical runner's testmon database guard
        # and exports the same database environment.
        tm.that(profile_test, has='database="$(FLEXT_PYTEST_TESTMON_DATABASE)";')
        tm.that(profile_test, has=f'{datafile}="$$database"')
        # The thin entry delegates profiling to the execution adapter.
        tm.that(profile_test, has="-m flext_infra._pytest.entry profile")
        tm.that(profile_test, lacks="import cProfile")
        tm.that(profile_test, has="$(PROFILE_REPORTS_DIR)/pytest.pstats")
        # Only the bounded gate adds the outer hard wall clock wrapper.
        tm.that(profile_test, lacks="PYTEST_BOUNDED")
        tm.that(gate_runner, has="PYTEST_BOUNDED")
        report = rendered.split("_builtin-profile-test-report:", 1)[1].split(
            "\n\n",
            1,
        )[0]
        tm.that(report, has="flext_infra._cprofile.entry")
        tm.that(report, has="$(PROFILE_REPORTS_DIR)/pytest.pstats")
        tm.that(report, has="$(PROFILE_REPORTS_DIR)/pytest.pstats.json")

    def test_profile_mod_report_uses_the_selected_project_root(
        self,
        tmp_path: Path,
    ) -> None:
        """The report adapter runs in the selected Makefile's root, not caller CWD."""
        rendered = self._render_root_makefile(
            tmp_path,
            extra_verbs=(),
            script_dispatch=None,
        )
        report = rendered.split("_builtin-profile-mod-report:", 1)[1].split(
            "\n\n",
            1,
        )[0]
        tm.that(
            report,
            has=(
                '\t@cd "$(PROJECT_ROOT)" || exit $$?; \\\n'
                "\t\t$(PROJECT_INFRA_RUN) -m flext_infra._cprofile.entry \\\n"
                '\t\t"$(PROFILE_REPORTS_DIR)/mod.pstats"'
            ),
        )

    def test_test_verbs_share_the_persistent_testmon_database(
        self,
        tmp_path: Path,
    ) -> None:
        """Public test verbs share one guarded persistent testmon execution path.

        The persistent database is keyed by the declared distribution, so
        every checkout of a project shares one testmon history. Complete
        validation runs incremental then complete through one unbounded
        ``full`` entry, also used by the shipped test-full command.
        """
        rendered = self._render_root_makefile(
            tmp_path,
            extra_verbs=(),
            script_dispatch=None,
        )
        cache = config.Infra.codegen.make.testmon_cache
        public_verbs = (
            next(
                line
                for line in rendered.splitlines()
                if line.startswith("PUBLIC_VERBS :=")
            )
            .split(":=", 1)[1]
            .split()
        )
        expected_verbs = [
            verb.name
            for verb in config.Infra.codegen.make.verbs
            if c.Infra.MakeProfile.STANDALONE in verb.profiles
        ]
        tm.that(public_verbs, eq=expected_verbs)
        tm.that(public_verbs, has="tests")
        tm.that(
            rendered,
            has=[
                ".PHONY: $(PUBLIC_VERBS) $(addprefix _builtin-,$(PUBLIC_VERBS))",
                "_builtin-test: _builtin_test_all\n",
                "_builtin-tests: _builtin_test_full_all\n",
                "_builtin-test-full: _builtin_test_full_all\n",
            ],
        )
        database_line = next(
            line
            for line in rendered.splitlines()
            if line.startswith("override FLEXT_PYTEST_TESTMON_DATABASE")
        )
        tm.that(rendered, has="PROJECT_NAME := demo-root\n")
        tm.that(
            database_line,
            has=(
                f"/{cache.external_storage_directory}/$(PROJECT_NAME)/"
                f"{cache.database_filename}"
            ),
        )
        tm.that(database_line, lacks="PROJECT_ROOT")
        incremental = rendered.split("_builtin_test_all:", 1)[1].split("\n\n", 1)[0]
        full = rendered.split("_builtin_test_full_all:", 1)[1].split("\n\n", 1)[0]
        tm.that(
            incremental,
            has=[
                "PYTEST_BOUNDED",
                f'{cache.database_environment_variable}="$$database"',
            ],
        )
        tm.that(full.count("-m flext_infra._pytest.entry"), eq=1)
        tm.ok(full.rstrip().endswith("-m flext_infra._pytest.entry full"))
        tm.that(full, lacks="PYTEST_BOUNDED")
        tm.that(
            full,
            has=[
                "_builtin_require_environment",
                'if [ -n "$(strip $(FILE))" ]; then',
                'export FLEXT_PYTEST_TARGET_FILE="$(FILE)";',
                f'{cache.database_environment_variable}="$$database"',
            ],
        )

    # A test asserting a downstream consumer's verbs from this
    # engine's catalog was removed. The engine is consumer-agnostic: a consumer
    # declares extra_verbs/script_dispatch in its own typed repository input. The
    # generic capability stays covered by the fixture-driven cases below.
    @pytest.mark.parametrize(
        "script_dispatch",
        [
            None,
            m.Infra.ScriptDispatchSpec(
                dispatcher="scripts/dispatch.py",
                roots=("scripts",),
            ),
        ],
    )
    def test_lint_and_type_paths_scan_every_configured_analyzer_dir(
        self,
        tmp_path: Path,
        script_dispatch: m.Infra.ScriptDispatchSpec | None,
    ) -> None:
        """Every repo scans the configured analyzer dirs present in its checkout.

        examples/ and scripts/ are first-class code under the same gates as
        src/, so the scanned set is the tooling SSOT, independent of script
        dispatch; the Makefile keeps only the directories that exist.
        """
        rendered = self._render_root_makefile(
            tmp_path,
            extra_verbs=(),
            script_dispatch=script_dispatch,
        )
        env_dirs = " ".join(config.Infra.tooling.tools.pyright.path_rules.env_dirs)
        tm.ok(f"for directory in {env_dirs}; do" in rendered)
        tm.ok("MYPY_PATHS := $(RUFF_PATHS)" in rendered)

    def test_every_pytest_verb_declares_the_project_scratch_root(
        self,
        tmp_path: Path,
    ) -> None:
        """Every pytest-running verb declares the project scratch root.

        The fleet's test law rejects a test scratch under /tmp: the caller of
        pytest must declare a project scratch root through TMPDIR (cosmos-charts
        CI run 37235165752 died in pytest_configure on an inherited /tmp). The
        Makefile verb is that caller, so each pytest verb renders ONE shared
        declaration next to its testmon database guard. The storage law places
        that root under the user home keyed by the absolute checkout
        (config make.pytest_scratch), never beside the checkout: inside a
        workspace the checkout's parent is the superproject tree, where Git
        refuses every fixture repository a test creates. The transient sandbox
        resolves the standard temp triplet inside it and is deleted when the
        recipe shell exits.
        """
        rendered = self._render_root_makefile(
            tmp_path,
            extra_verbs=(),
            script_dispatch=None,
        )
        scratch = config.Infra.codegen.make.pytest_scratch
        tm.that(
            rendered,
            has=(
                f"$({scratch.user_home_environment_variable})/"
                f"{scratch.home_relative_directory}/"
                f"{scratch.state_directory_name}$(PROJECT_ROOT)/{scratch.namespace}"
            ),
        )
        verbs = (
            "_builtin_test_all:",
            "_builtin_test_full_all:",
            "_builtin_test_file_all:",
            "_builtin-profile-test:",
        )
        bodies = {
            verb: rendered.split(verb, 1)[1].split("\n\n", 1)[0] for verb in verbs
        }
        sandbox = 'scratch="$$(mktemp -d "$$scratch_root/pytest.XXXXXX")"'
        for body in bodies.values():
            tm.that(
                body,
                has=[
                    'scratch_root="$(FLEXT_PYTEST_SCRATCH_ROOT)"',
                    sandbox,
                    'mkdir -p "$$scratch/tmp"',
                    "export TMPDIR TMP TEMP",
                    "trap 'find \"$$scratch\" -depth -delete' EXIT",
                ],
            )
            # The pytest entry runs after the declaration in the same shell.
            tm.that(
                body.index("export TMPDIR TMP TEMP") < body.index("_pytest_entry"),
                eq=True,
            )
            # No verb owns a private variant of the shared fragment.
            tm.that(body.count(sandbox), eq=1)
        # The declaration is ONE rendered fragment across the four verbs.
        tm.that(rendered.count(sandbox), eq=len(verbs))
        # Never beside the checkout (inside a workspace that is another
        # repository's tree), never under /tmp, never a durable in-tree scratch.
        tm.that(rendered, lacks=["project_parent", ".test-tmp", "PROJECT_SCRATCH"])
        tm.that(rendered, lacks='TMPDIR="$$test_tmp"')
