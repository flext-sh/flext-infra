"""Public workspace Make contracts and canonical regeneration ownership.

Conform generates every profile's Makefile. The declared approval lifecycle,
test runner and public contract descriptions retain their canonical owners.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from flext_infra import config
from flext_infra.codegen import FlextInfraCodegenConform
from tests import c, m, p, t, tm, u


class TestsFlextInfraCodegenRepositoryRootScope:
    """Tests for ``FlextInfraCodegenRepositoryRootScope``."""

    @staticmethod
    @pytest.mark.slow
    def test_selected_member_mod_text_owns_its_real_workspace_scope(
        tmp_path: Path,
    ) -> None:
        """A generated member Makefile rewrites its member from workspace CWD."""
        root = tmp_path / "scope-workspace"
        member = u.Tests.WorktreeFixture.governed_workspace_with_member(root)
        request = u.Tests.conform_request(
            root,
            what=c.Infra.CodegenConformSurface.MAKEFILE,
            scope=c.Infra.CodegenConformScope.ALL,
            mode=c.Infra.CodegenConformMode.APPLY,
        )
        tm.ok(FlextInfraCodegenConform(repository_root=root, request=request).execute())
        for verb in ("upg", "setup"):
            provisioned = tm.ok(u.Tests.run_isolated_make([verb], cwd=root))
            tm.that(
                u.Cli.process_succeeded(provisioned.outcome),
                eq=True,
                msg=provisioned.stdout + provisioned.stderr,
            )
        sentinel = root / "scope_sentinel.py"
        selected = member / "scope_selected.py"
        original = 'value = "scope_before"\n'
        tm.ok(u.Cli.atomic_write_text_file(sentinel, original))
        tm.ok(u.Cli.atomic_write_text_file(selected, original))
        for project in (root, member):
            relative = sentinel.name if project == root else selected.name
            tm.ok(
                u.Cli.atomic_write_text_file(
                    project / c.Infra.CODEMOD_TEXT_RULES_RELPATH,
                    "rules:\n"
                    "  - id: private-scope-contract\n"
                    f"    include: ['{relative}']\n"
                    "    find: 'scope_before'\n"
                    "    replace: 'scope_after'\n",
                )
            )
        result = tm.ok(
            u.Tests.run_isolated_make(
                [
                    "-f",
                    str((member / c.Infra.MAKEFILE_FILENAME).relative_to(root)),
                    "mod-text",
                ],
                cwd=root,
            )
        )
        tm.that(
            u.Cli.process_succeeded(result.outcome),
            eq=True,
            msg=result.stdout + result.stderr,
        )
        tm.that(selected.read_text(encoding="utf-8"), eq='value = "scope_after"\n')
        tm.that(sentinel.read_text(encoding="utf-8"), eq=original)

    @staticmethod
    def _recorded_activation_env(tmp_path: Path) -> t.Pair[t.StrMapping, Path]:
        """Record the local-context activation instead of entering a host shell.

        ``make upg`` is a local verb (CI forbids resolution), so its lifecycle
        activates through ``direnv exec``. A dry run still executes that ``+``
        line; real direnv would load the fixture's ``.envrc`` and resolve tools
        through host Mise shims. The recorded invocation proves the activation
        contract (``direnv exec <root> ... _activated-<verb>``) without
        depending on host state.

        Returns:
            The PATH overlay and the invocation log of the recorded direnv.

        """
        bin_dir = tmp_path / "recorded-bin"
        log = u.Tests.cli_shim(bin_dir, c.Infra.CLI_DIRENV)
        return {"PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}"}, log

    def test_pre_commit_displays_the_canonical_contract(self, tmp_path: Path) -> None:
        """The real Make consumer exposes the configured CI validation contract."""
        root = self._render_root_makefile(tmp_path)
        result = tm.ok(
            u.Cli.run(
                [c.Infra.MAKE, "OPTIONS=Y", "pre-commit"],
                cwd=root,
            ),
        )
        contract = next(
            verb
            for verb in config.Infra.codegen.make.verbs
            if verb.name == "pre-commit"
        )
        tm.that(result.exit_code, eq=0)
        tm.that(result.stdout, has=contract.description)

    def test_verify_clean_projection_uses_the_public_git_service(
        self,
        tmp_path: Path,
    ) -> None:
        """The rendered recipe retains audits and propagates the public CLI exit."""
        root = self._render_root_makefile(tmp_path)
        rendered = (root / c.Infra.MAKEFILE_FILENAME).read_text(
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        recipe = rendered.split("\n_builtin-verify-clean:", 1)[1].split(
            "\n_builtin-docs:",
            1,
        )[0]
        tm.that(recipe, has=["codegen conform", "docs audit"])
        tm.that(
            recipe.splitlines()[-1],
            eq=f"\t@$(PROJECT_FLEXT_INFRA) {c.Infra.CLI_GROUP_WORKSPACE} "
            'verify-clean --repo-root "$(PROJECT_ROOT)"',
        )
        tm.that(recipe, lacks=["diff --exit-code", "||", "\t-", "\t@-"])

    def test_normal_test_verbs_admit_only_incremental_execution(
        self,
        tmp_path: Path,
    ) -> None:
        """`make test` stays one incremental phase; `test-file` runs its file whole.

        `make test` runs in CI and pre-commit, so slow-marked items stay out of
        it (operator 2026-10-01: nothing slow in CI or pre-commit). `test-file`
        is the sole single-file path and runs only locally, so its one ``file``
        entry runs the complete declared file once, including slow items;
        a file whose items are all slow-marked never ends the verb
        with zero executed tests. Neither recipe appends the full suite.
        """
        root = self._render_root_makefile(tmp_path)
        rendered = (root / c.Infra.MAKEFILE_FILENAME).read_text(
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        cache = config.Infra.codegen.make.testmon_cache
        recipe = rendered.split("_builtin_test_all:", 1)[1].split("\n\n", 1)[0]
        tm.that(recipe.count("-m flext_infra._pytest_entry"), eq=1)
        tm.that(
            recipe,
            lacks=["_pytest_entry slow", "file-slow", "_pytest_entry full"],
        )
        tm.that(
            recipe,
            has=f'{cache.database_environment_variable}="$$database"',
        )

    def test_file_profile_does_not_execute_bounded_tests(self, tmp_path: Path) -> None:
        """A selected profile reaches profiling without a bounded test preflight."""
        root = self._render_root_makefile(tmp_path)
        selected = "tests/requested.py"
        expanded = tm.ok(
            u.Tests.run_isolated_make(
                ["--dry-run", "_builtin-profile-test", f"FILE={selected}"],
                cwd=root,
            ),
        )
        tm.that(
            u.Cli.process_succeeded(expanded.outcome),
            eq=True,
            msg=expanded.stdout + expanded.stderr,
        )
        tm.that(
            expanded.stdout,
            has=f'export {c.Infra.PYTEST_ENV_TARGET_FILE}="{selected}";',
        )
        tm.that(expanded.stdout, has="-m flext_infra._pytest_entry profile")
        tm.that(
            expanded.stdout,
            lacks=["_pytest_entry file;", "_pytest_entry file-slow;"],
        )

    @staticmethod
    def test_conform_owns_repository_root_makefile() -> None:
        """The single Makefile render entry includes the workspace profile."""
        makefile_entries = tuple(
            entry
            for entry in config.Infra.codegen.templates.entries
            if entry.destination == c.Infra.MAKEFILE_FILENAME
        )
        tm.that(makefile_entries, len=1)
        tm.that(makefile_entries[0].profiles, has=c.Infra.MakeProfile.WORKSPACE)

    def test_repository_root_projection_uses_workspace_profile(
        self,
        tmp_path: Path,
    ) -> None:
        """The workspace projection has one local body per verb and no fan-out."""
        repository_root = self._render_root_makefile(tmp_path)
        rendered = (repository_root / c.Infra.MAKEFILE_FILENAME).read_text(
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        tm.that(rendered, lacks=["orchestrate", "GITHUB_ACTIONS", "_builtin-self-"])
        tm.that(rendered, has="MAKE_PROFILE := workspace")
        tm.that(
            rendered,
            has="PROJECT_FLEXT_INFRA := $(PROJECT_INFRA_RUN) -m flext_infra",
        )
        tm.that(rendered.endswith("\n"), eq=True)
        tm.that(rendered.endswith("\n\n"), eq=False)

    def test_repository_root_gate_verbs_evaluate_only_the_root(
        self,
        tmp_path: Path,
    ) -> None:
        """Generated workspace check/test run the root's own gates and tests."""
        repository_root = self._render_root_makefile(tmp_path)
        expected = {
            c.Infra.VERB_CHECK: "check run --repository-root",
            c.Infra.VERB_TEST: "_pytest_entry",
        }
        for verb, local_body in expected.items():
            execution = tm.ok(
                u.Cli.run_raw(
                    [c.Infra.MAKE, "--dry-run", f"_builtin-{verb}"],
                    cwd=repository_root,
                    options=m.Cli.ProcessOptions(remove_env_keys=("MAKEFLAGS",)),
                ),
            )
            tm.that(u.Cli.process_succeeded(execution.outcome), eq=True)
            output = execution.stdout + execution.stderr
            tm.that(output, has=local_body)
            tm.that(output, lacks="--verb")

    def test_repository_root_declares_member_propagation(self, tmp_path: Path) -> None:
        """The workspace profile declares propagate through the workspace CLI."""
        repository_root = self._render_root_makefile(tmp_path)
        execution = tm.ok(
            u.Cli.run_raw(
                [c.Infra.MAKE, "--dry-run", "_builtin-propagate"],
                cwd=repository_root,
                options=m.Cli.ProcessOptions(remove_env_keys=("MAKEFLAGS",)),
            ),
        )
        tm.that(u.Cli.process_succeeded(execution.outcome), eq=True)
        tm.that(
            execution.stdout + execution.stderr,
            has=f"{c.Infra.CLI_GROUP_WORKSPACE} propagate",
        )

    def test_repository_root_upg_profiles_canonical_modernization(
        self,
        tmp_path: Path,
    ) -> None:
        """Generated upg renders the exact lock-upgrade and modernizer invocation.

        ``upg`` bootstraps Mise (network) and then dispatches its lifecycle; the
        dry run enters that lifecycle directly, and its recursive ``+``
        activation re-enters the checkout through ``direnv exec``.
        """
        repository_root, activations, execution = self._run_upg_lifecycle(
            tmp_path,
        )

        tm.that(
            u.Cli.process_succeeded(execution.outcome),
            eq=True,
            msg=execution.stdout + execution.stderr,
        )
        rendered = execution.stdout + execution.stderr
        tm.that(rendered, has="deps modernize")
        tm.that(rendered, has="--apply --rewrite-constraints")
        tm.that(rendered, has="lock --project")
        tm.that(rendered, has="--upgrade --refresh")
        tm.that(
            activations.read_text(encoding="utf-8"),
            has=f"exec {repository_root} ",
        )

    def test_repository_root_upg_locks_tools_from_the_rendered_manifest(
        self,
        tmp_path: Path,
    ) -> None:
        """One ``make upg`` lifecycle relocks the tools between gen's halves.

        The render half of ``gen`` writes the tool manifests of the upgraded
        generator; the single ``_upg_lifecycle`` re-resolves mise.lock from
        that rendered manifest (``mise lock --bump``) and installs it before
        gen's activation half demands the pinned Mise release, then checks
        uv.lock before post-upg.
        """
        _, activations, execution = self._run_upg_lifecycle(
            tmp_path,
        )
        tm.that(
            activations.read_text(encoding="utf-8"),
            has=["_activated-gen", "_upg_activated"],
        )
        tm.that(
            u.Cli.process_succeeded(execution.outcome),
            eq=True,
            msg=execution.stdout + execution.stderr,
        )
        steps = execution.stdout.splitlines()
        expected_steps = (
            "--upgrade --refresh",
            "lock --bump",
            "install --locked --yes",
            "deps modernize",
            "_builtin-gen",
            "_activated-gen",
        )
        for needle in expected_steps:
            tm.that(
                execution.stdout,
                has=needle,
                msg=execution.stdout + execution.stderr,
            )
        positions = [
            next(i for i, step in enumerate(steps) if needle in step)
            for needle in expected_steps
        ]
        tm.that(positions, eq=sorted(positions))
        # uv.lock resolves twice (flext-5kqsx): the upgrade selects the newest
        # generator, and the relock resolves the pyproject that generator's
        # render half projected, so a requirement only the upgraded generator
        # declares reaches the lock in the same run. The check follows the
        # final resolution and precedes the tool relock.
        locks = [i for i, step in enumerate(steps) if "lock --project" in step]
        tm.that(len(locks), eq=2)
        upgrade_lock, final_lock = locks
        tm.that(steps[upgrade_lock], has="--upgrade")
        tm.that(steps[final_lock], lacks="--upgrade")
        rendered = next(i for i, s in enumerate(steps) if "_builtin-gen" in s)
        lock_check = max(i for i, s in enumerate(steps) if "lock --check" in s)
        tool_lock = next(i for i, s in enumerate(steps) if "lock --bump" in s)
        # C19: the upgraded Mise is relocked and installed before the
        # resolution renders; the 5kqsx double resolution keeps the upgraded
        # generator's lock before the render and the final relock after it.
        tm.that(tool_lock < rendered, eq=True)
        tm.that(upgrade_lock < rendered < final_lock < lock_check, eq=True)
        tm.that(execution.stdout + execution.stderr, has="_upg_activated")

    @staticmethod
    def _publish_on_gen(root: Path, published: str) -> None:
        """Declare a gen producer that publishes *published* as the Makefile.

        The ``+`` prefix runs it under ``--dry-run`` as conform runs for real:
        the producer half of ``gen`` rewrites the Makefile that ``upg`` parsed.
        """
        (root / "published.mk").write_text(published, encoding="utf-8")
        (root / c.Infra.CUSTOM_MAKE_FILENAME).write_text(
            ".PHONY: _custom-gen\n"
            "_custom-gen:\n"
            '\t+@cp "$(PROJECT_ROOT)/published.mk" "$(SELF_MAKEFILE)"\n',
            encoding="utf-8",
        )

    def test_upg_hands_off_to_the_published_generation(self, tmp_path: Path) -> None:
        """A Makefile published by gen is finished by a fresh `make upg` on it.

        Premise (F1, ai-hub consumer proof 2026-10-09): an upgrade re-entered
        `$(SELF_MAKE) _builtin_require_mise` after gen had published a newer
        Makefile that no longer defined it. The next generation here defines
        none of this generation's private targets, only the public `upg`.
        """
        root = self._render_root_makefile(tmp_path)
        self._publish_on_gen(
            root,
            ".PHONY: upg\n"
            "upg:\n"
            "\t+@printf 'next-generation upg handoff=%s\\n' \"$(UPG_HANDOFF)\"\n",
        )

        execution = tm.ok(
            u.Tests.run_isolated_make(
                ["--dry-run", "_upg_lifecycle"],
                cwd=root,
            ),
        )

        output = execution.stdout + execution.stderr
        tm.that(u.Cli.process_succeeded(execution.outcome), eq=True, msg=output)
        tm.that(output, has="next-generation upg handoff=Y")
        tm.that(output, lacks=["No rule to make target", "_upg_activated"])

    def test_upg_handoff_fails_loud_when_gen_is_not_a_fixed_point(
        self,
        tmp_path: Path,
    ) -> None:
        """A second publication inside the hand-off stops instead of recursing."""
        root = self._render_root_makefile(tmp_path)
        current = (root / c.Infra.MAKEFILE_FILENAME).read_text(encoding="utf-8")
        self._publish_on_gen(root, current + "\n# republished\n")

        execution = tm.ok(
            u.Tests.run_isolated_make(
                ["--dry-run", "_upg_lifecycle", "UPG_HANDOFF=Y"],
                cwd=root,
            ),
        )

        tm.that(u.Cli.process_succeeded(execution.outcome), eq=False)
        tm.that(execution.stderr, has="gen is not a fixed point")

    def test_upg_names_no_private_target_after_gen_publishes(
        self,
        tmp_path: Path,
    ) -> None:
        """After gen publishes, the lifecycle re-enters only `upg` or its converge."""
        root = self._render_root_makefile(tmp_path)
        rendered = (root / c.Infra.MAKEFILE_FILENAME).read_text(encoding="utf-8")
        lifecycle = rendered.split("\n_upg_lifecycle: _builtin_setup_submodules\n", 1)[
            1
        ]
        after_publish = lifecycle.split("$(call RUN_PUBLIC_PRODUCE,gen)\n", 1)[1]
        recipe = after_publish.split("\n\n", 1)[0]
        reentries = {
            line.split("$(SELF_MAKE)", 1)[1].split()[0].rstrip(";")
            for line in recipe.splitlines()
            if "$(SELF_MAKE)" in line
        }
        tm.that(reentries, eq={"_upg_converge"})
        tm.that(recipe, has='-f "$(SELF_MAKEFILE)" upg UPG_HANDOFF=Y')
        tm.that(recipe, has='"$(SELF_MAKEFILE_DIGEST)"')

    @staticmethod
    def _render_root_makefile(tmp_path: Path) -> Path:
        """Render base/Makefile.j2 from a typed workspace fixture.

        Returns:
            The resulting ``Path``.

        """
        repository = u.Tests.repository_ref("workspace-fixture")
        workspace = u.Tests.workspace_spec(
            repository,
            project=u.Tests.project_spec(repository.name),
        )
        # The bootstrap projection refreshes the dispatcher of an existing
        # checkout: the root is a Git repository (the workspace profile resolves
        # itself through Git), even when it carries no topology yet.
        repository_root = u.Tests.git_repository(tmp_path, "workspace")
        request = u.Tests.conform_request(
            repository_root,
            what=c.Infra.CodegenConformSurface.MAKEFILE,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.CHECK,
        )
        plan: m.Infra.CodegenPlan = tm.ok(
            FlextInfraCodegenConform(
                repository_root=repository_root,
                request=request,
                initial_workspace=workspace,
            ).plan(request),
        )
        makefile_plans = tuple(
            fp for fp in plan.files if Path(fp.path).name == c.Infra.MAKEFILE_FILENAME
        )
        tm.that(makefile_plans, len=1)
        makefile_path = repository_root / c.Infra.MAKEFILE_FILENAME
        tm.not_none(makefile_plans[0].desired_content)
        makefile_path.write_text(
            u.Tests.codegen_file_text(makefile_plans[0]),
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        return repository_root

    @classmethod
    def _run_upg_lifecycle(
        cls,
        tmp_path: Path,
    ) -> t.Triple[Path, Path, p.Cli.CommandOutput]:
        """Render the workspace root and dry-run the canonical ``upg`` lifecycle.

        Every ``upg`` recipe assertion shares the same premise: a rendered
        workspace Makefile whose ``_upg_lifecycle`` re-enters through the
        recorded direnv activation. Running the isolated dry run once keeps the
        two tests on a single owner.

        Returns:
            The repository root, the recorded activation log, and the dry-run
            output.

        """
        repository_root = cls._render_root_makefile(tmp_path)
        env, activations = cls._recorded_activation_env(tmp_path)
        execution = tm.ok(
            u.Tests.run_isolated_make(
                ["--dry-run", "_upg_lifecycle"],
                cwd=repository_root,
                env=env,
            ),
        )
        return repository_root, activations, execution
