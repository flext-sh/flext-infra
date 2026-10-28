"""Public workspace Make contracts and canonical regeneration ownership.

Conform generates every profile's Makefile. The declared approval lifecycle,
test runner and public contract descriptions retain their canonical owners.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import config
from flext_infra.codegen import FlextInfraCodegenConform
from tests import c, m, tm, u


class TestsFlextInfraCodegenRepositoryRootScope:
    """Tests for ``FlextInfraCodegenRepositoryRootScope``."""

    @staticmethod
    @pytest.mark.parametrize(
        ("project_name", "authored_root"),
        [("flext-alpha", "automation"), ("flext-beta", "quality_tools")],
    )
    def test_pyproject_generation_retains_owned_python_scope(
        tmp_path: Path,
        project_name: str,
        authored_root: str,
    ) -> None:
        """The generated Pyright projection retains authored scopes at fixed point."""
        u.Tests.copy_tracked_mise_seeds(tmp_path)
        root = u.Tests.mk_project(
            tmp_path,
            project_name,
            pyproject=f"[project]\nname='{project_name}'\nversion='0.1.0'\n",
        )
        project = u.Tests.project_spec(project_name)
        roots = (
            config.Infra.tooling.tools.pyright.path_rules.source_dir,
            "docs",
            "scripts",
            "examples",
            authored_root,
        )
        for relative in roots:
            directory = root / relative / project.package_name
            directory.mkdir(parents=True, exist_ok=True)
            (directory / "__init__.py").write_text("", encoding="utf-8")
        repository = u.Tests.repository_ref(project_name).model_copy(
            update={"role": c.Infra.MakeProfile.STANDALONE},
        )
        request = u.Tests.conform_request(
            root,
            what=c.Infra.CodegenConformSurface.PYPROJECT,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.CHECK,
        )
        service = FlextInfraCodegenConform.Generate(
            repository_root=root,
            state=m.Infra.CodegenConformState(
                repository_root=root,
                request=request,
                initial_workspace=u.Tests.workspace_spec(repository, project=project),
            ),
        )
        first_plan = tm.ok(service.plan(request))
        first = next(
            item for item in first_plan.files if item.path.name == c.PYPROJECT_FILENAME
        )
        rendered = u.Tests.codegen_file_text(first)
        pyright = u.Tests.toml_table_at(rendered, "tool", "pyright")
        includes = frozenset(u.Tests.toml_strings(pyright["include"]))
        tm.ok(frozenset(roots).issubset(includes))
        tm.that(
            frozenset(
                str(u.Tests.toml_mapping(env)["root"])
                for env in u.Tests.toml_list(pyright["executionEnvironments"])
            ),
            eq=includes,
        )
        published = root / c.PYPROJECT_FILENAME
        published.write_bytes(tm.not_none(first.desired_content))
        published.chmod(tm.not_none(first.desired_mode))
        second_plan = tm.ok(service.plan(request))
        second = next(
            item for item in second_plan.files if item.path.name == c.PYPROJECT_FILENAME
        )
        tm.that(second.desired_content, eq=first.desired_content)
        tm.fail(u.Infra.codegen_file_requires_effect(second))

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
        tm.ok(
            FlextInfraCodegenConform.Generate(
                repository_root=root,
                state=m.Infra.CodegenConformState(
                    repository_root=root,
                    request=request,
                ),
            ).execute()
        )
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

    def test_check_projection_runs_one_public_process(
        self,
        tmp_path: Path,
    ) -> None:
        """The rendered check recipe is one unmasked public CLI invocation."""
        root = self._render_root_makefile(tmp_path)
        rendered = (root / c.Infra.MAKEFILE_FILENAME).read_text(
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        recipe = rendered.split(
            "\n_builtin_check_all: _builtin_require_environment\n", 1
        )[1].split("\n\n", 1)[0]
        tm.that(
            recipe,
            eq=f"\t@$(PROJECT_FLEXT_INFRA) {c.Infra.CLI_GROUP_WORKSPACE} "
            f'{c.Infra.VERB_CHECK} --repository-root "$(PROJECT_ROOT)"',
        )
        tm.that(rendered, lacks=["verify-clean --repo-root", "capture-gate"])

    def test_normal_test_verbs_admit_only_incremental_execution(
        self,
        tmp_path: Path,
    ) -> None:
        """`make test` stays bounded; `test-file` runs one complete file phase.

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
        tm.that(recipe.count("-m flext_infra._pytest.entry"), eq=1)
        tm.that(
            recipe,
            lacks=["_pytest_entry slow", "file-slow", "_pytest_entry full"],
        )
        tm.that(
            recipe,
            has=f'{cache.database_environment_variable}="$$database"',
        )
        tm.that(recipe, has="$(PYTEST_BOUNDED)")
        file_recipe = rendered.split("_builtin_test_file_all:", 1)[1].split("\n\n", 1)[
            0
        ]
        tm.that(file_recipe.count("-m flext_infra._pytest.entry file"), eq=1)
        tm.that(file_recipe, lacks="$(PYTEST_BOUNDED)")
        tm.that(
            file_recipe.count(f'export {c.Infra.PYTEST_ENV_TARGET_FILE}="$(FILE)";'),
            eq=1,
        )
        tm.that(
            file_recipe,
            has=f'{cache.database_environment_variable}="$$database"',
        )
        full_recipe = rendered.split("_builtin_test_full_all:", 1)[1].split("\n\n", 1)[
            0
        ]
        tm.that(full_recipe.count("-m flext_infra._pytest.entry full"), eq=1)
        tm.that(full_recipe, lacks="$(PYTEST_BOUNDED)")
        tm.that(
            full_recipe.count(f'export {c.Infra.PYTEST_ENV_TARGET_FILE}="$(FILE)";'),
            eq=1,
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
        tm.that(expanded.stdout, has="-m flext_infra._pytest.entry profile")
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
        tm.ok(rendered.endswith("\n"))
        tm.fail(rendered.endswith("\n\n"))

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
            tm.ok(u.Cli.process_succeeded(execution.outcome))
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
        tm.ok(u.Cli.process_succeeded(execution.outcome))
        tm.that(
            execution.stdout + execution.stderr,
            has=f"{c.Infra.CLI_GROUP_WORKSPACE} propagate",
        )

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
            FlextInfraCodegenConform.Generate(
                repository_root=repository_root,
                state=m.Infra.CodegenConformState(
                    repository_root=repository_root,
                    request=request,
                    initial_workspace=workspace,
                ),
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
