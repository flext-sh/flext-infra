"""Verify generated workspace Make behavior across orchestration seams."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_infra import config
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_infra.workspace.orchestrator import FlextInfraOrchestratorService
from flext_tests import tm

from tests import c, m, p, u
from tests.unit.workspace.worktree_fixture import WorktreeFixture


def _write_workspace(tmp_path: Path) -> tuple[Path, tuple[str, ...]]:
    repository_root = tmp_path / "workspace"
    repository_root.mkdir()
    root_repository = u.Tests.repository_ref("fixture-workspace")
    subprojects = tuple(
        u.Tests.repository_ref(name, path=Path(name))
        for name in ("fixture-member-one", "fixture-member-two")
    )
    project_names = tuple(project.path.as_posix() for project in subprojects)
    root_package = (
        repository_root / "src" / root_repository.distribution.replace("-", "_")
    )
    root_package.mkdir(parents=True)
    (root_package / "__init__.py").write_text("", encoding="utf-8")
    (repository_root / "pyproject.toml").write_text(
        f"[project]\nname = '{root_repository.distribution}'\nversion = '0.1.0'\n",
        encoding="utf-8",
    )
    u.Tests.write_beads_project(
        repository_root,
        workspace=root_repository.name,
        database=root_repository.name,
        issue_prefix=root_repository.name,
    )
    u.Tests.initialize_git_repo(repository_root, origin_url=root_repository.url)
    u.Tests.git_bootstrap(
        repository_root, ("config", "remote.origin.skipDefaultUpdate", "true")
    )
    for project_name in project_names:
        project_root = repository_root / project_name
        WorktreeFixture.initialize_governed_project(
            project_root,
            project_name,
            workspace=f"{project_name}-workspace",
            database=f"{project_name}-database",
            issue_prefix=f"{project_name}-prefix",
        )
    gitmodules_path = WorktreeFixture.write_gitmodules(repository_root, project_names)
    protected_paths = {
        gitmodules_path,
        repository_root / "config" / "beads.yaml",
        *(repository_root / name / "config" / "beads.yaml" for name in project_names),
    }
    # These tests assert what the generated Makefile contains, so the public
    # planning surface provides the exact artifacts without writing the fixture.
    # Generation is runtime-independent and never invokes tracker services.
    planned = tm.ok(
        FlextInfraCodegenConform().plan(
            m.Infra.CodegenConformRequest(
                root=repository_root,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.CHECK,
            )
        )
    )
    tm.that(
        tuple(
            item.path
            for item in planned.files
            if item.path in protected_paths and item.changed
        ),
        empty=True,
    )
    for planned_file in planned.files:
        if planned_file.path in protected_paths:
            continue
        planned_file.path.parent.mkdir(parents=True, exist_ok=True)
        planned_file.path.write_text(planned_file.rendered, encoding="utf-8")
    for project_name in project_names:
        _write_child_makefile(repository_root / project_name, exit_code=0)
    return repository_root, project_names


def _write_child_makefile(project_root: Path, *, exit_code: int) -> None:
    (project_root / "Makefile").write_text(
        "SHELL := /bin/sh\n"
        ".PHONY: setup check test\n"
        "setup:\n"
        "\t@true\n"
        "check test:\n"
        "\t@printf 'project=%s verb=%s gates=%s uv_project=%s uv_env=%s "
        "venv=%s fail_fast=%s\\n' '$(notdir $(CURDIR))' '$@' "
        "'$(CHECK_GATES)' '$(UV_PROJECT)' '$(UV_PROJECT_ENVIRONMENT)' "
        "'$(VIRTUAL_ENV)' '$(FAIL_FAST)'\n"
        f"\t@exit {exit_code}\n",
        encoding="utf-8",
    )


class TestsRepositoryRootMakeContract:
    def test_repository_root_make_template_is_owned_by_typed_config(self) -> None:
        make_entries = tuple(
            entry
            for entry in config.Infra.codegen.templates.entries
            if entry.destination == c.Infra.MAKEFILE_FILENAME
        )

        tm.that(make_entries, len=1)
        tm.that(make_entries[0].profiles, has=c.Infra.MakeProfile.WORKSPACE)

    def test_generated_make_exposes_only_public_conform(self, tmp_path: Path) -> None:
        """Route the sole public conformance verb to the internal CLI.

        Which verb carries conformance is config-owned: it is declared in
        make.verbs and is `gen` today. The contract is that the declared verb
        reaches `codegen conform`, and that no second public entry point does.
        """
        repository_root, _ = _write_workspace(tmp_path)
        declared = {verb.name for verb in config.Infra.codegen.make.verbs}
        tm.that(declared, has="gen")

        generated: p.Cli.CommandOutput = tm.ok(
            u.Tests.run_isolated_make(
                ["-C", str(repository_root), "--dry-run", "gen", "WHAT=check"],
                cwd=repository_root,
            )
        )
        retired: p.Cli.CommandOutput = tm.ok(
            u.Tests.run_isolated_make(
                ["-C", str(repository_root), "--dry-run", "codegen"],
                cwd=repository_root,
            )
        )
        output = generated.stdout + generated.stderr

        tm.that(generated.exit_code, eq=0, msg=output)
        tm.that(output, has="_builtin_gen_$what")
        tm.that(output, lacks="_serialized_")
        tm.that(output, lacks="serialize-make")
        tm.that(declared, lacks="codegen")
        tm.that(retired.exit_code, ne=0)

    def test_generated_make_routes_fmt_apply_to_selected_project(
        self, tmp_path: Path
    ) -> None:
        repository_root, project_names = _write_workspace(tmp_path)

        process: p.Cli.CommandOutput = tm.ok(
            u.Tests.run_isolated_make(
                [
                    "-C",
                    str(repository_root),
                    "--dry-run",
                    "_builtin_fmt_apply",
                    f"PROJECT={project_names[0]}",
                    "APPLY=Y",
                ],
                cwd=repository_root,
            )
        )
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0, msg=output)
        tm.that(output, has="--verb fmt")
        tm.that(output, has=f"--projects {project_names[0]}")
        tm.that(output, has='--make-arg "APPLY=Y"')
        tm.that(output, lacks=f"--projects {project_names[1]}")
        tm.that(output, lacks="ruff check --fix")

    def test_generated_make_routes_fixable_gates_through_checker(
        self, tmp_path: Path
    ) -> None:
        """The public fix verb reaches every gate that advertises a fixer."""
        repository_root, _project_names = _write_workspace(tmp_path)

        process: p.Cli.CommandOutput = tm.ok(
            u.Tests.run_isolated_make(
                [
                    "-C",
                    str(repository_root),
                    "--dry-run",
                    "_builtin_fix_apply",
                    "PROJECT=.",
                    "APPLY=Y",
                ],
                cwd=repository_root,
            )
        )
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0, msg=output)
        tm.that(output, has="ruff check --fix")
        tm.that(output, has="check run --workspace")
        tm.that(output, has='--gates "markdown,smells"')
        tm.that(output, has="--fix")

    def test_generated_make_routes_file_and_match_only_to_owning_project(
        self, tmp_path: Path
    ) -> None:
        repository_root, project_names = _write_workspace(tmp_path)
        owner = project_names[0]
        selected = f"{owner}/tests/unit/test_selected.py"

        process: p.Cli.CommandOutput = tm.ok(
            u.Tests.run_isolated_make(
                [
                    "-C",
                    str(repository_root),
                    "--dry-run",
                    "_builtin_test_all",
                    f"FILE={selected}",
                    "MATCH=selected_case",
                ],
                cwd=repository_root,
            )
        )
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0, msg=output)
        tm.that(output, has=f"--projects {owner}")
        tm.that(output, has="--file")
        tm.that(output, has="--match")

    def test_generated_make_forwards_root_file_with_member_selection(
        self, tmp_path: Path
    ) -> None:
        """Run a root-owned test locally without recursively orchestrating root."""
        repository_root, project_names = _write_workspace(tmp_path)
        selected = "tests/unit/test_provider_contract.py"

        process: p.Cli.CommandOutput = tm.ok(
            u.Tests.run_isolated_make(
                [
                    "-C",
                    str(repository_root),
                    "--dry-run",
                    "_builtin_test_all",
                    f"FILE={selected}",
                ],
                cwd=repository_root,
            )
        )
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0, msg=output)
        tm.that(output, has="python -m flext_infra._pytest_entry")
        tm.that(output, has="--file")
        for project_name in project_names:
            tm.that(output, lacks=f"--projects {project_name}")

    def test_generated_make_default_test_fans_out_to_every_member(
        self, tmp_path: Path
    ) -> None:
        """Default test covers the publishing root and every declared member."""
        repository_root, project_names = _write_workspace(tmp_path)

        process: p.Cli.CommandOutput = tm.ok(
            u.Tests.run_isolated_make(
                ["-C", str(repository_root), "--dry-run", "_builtin_test_all"],
                cwd=repository_root,
            )
        )
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0, msg=output)
        tm.that(output, has="python -m flext_infra._pytest_entry")
        for project_name in project_names:
            tm.that(output, has=f"--projects {project_name}")

    def test_generated_make_default_check_covers_publishing_root(
        self, tmp_path: Path
    ) -> None:
        """Default check validates root sources before orchestrating members."""
        repository_root, project_names = _write_workspace(tmp_path)

        process: p.Cli.CommandOutput = tm.ok(
            u.Tests.run_isolated_make(
                ["-C", str(repository_root), "--dry-run", "_builtin_check_all"],
                cwd=repository_root,
            )
        )
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0, msg=output)
        tm.that(output, has='check run --workspace "')
        tm.that(output, has="--projects .")
        for project_name in project_names:
            tm.that(output, has=f"--projects {project_name}")

        generated_makefile = (repository_root / "Makefile").read_text(encoding="utf-8")
        check_recipe = generated_makefile.split(
            "_builtin_check_all: _builtin_require_environment", 1
        )[1].split("_builtin_check_lint:", 1)[0]
        tm.that(
            check_recipe,
            has=(
                "\tfi; \\\n"
                '\tif [ "$(REPOSITORY_ROOT_PACKAGE)" = "Y" ] && '
                '[ -n "$(SELECTED_ROOT_PROJECT)" ]; then \\\n'
            ),
        )

    def test_repository_root_setup_owns_environment_and_uses_venv_directory(
        self, tmp_path: Path
    ) -> None:
        """Setup provisions the root environment through the caller's uv.

        Setup is provision-only: it creates the workspace venv and syncs
        dependencies with the uv the caller already has on PATH. The previous
        expectation (curl-downloaded mise, then `mise install uv@`, then a
        conform pass, then sync) modelled a bootstrap pipeline the setup
        cutover removed, and it drove real network and real builds from a unit
        test. A fake uv records the invocation, so the contract is observed
        without provisioning anything.
        """
        repository_root, _ = _write_workspace(tmp_path)
        setup_log = tmp_path / "setup.log"
        fake_bin = tmp_path / "fake" / "bin"
        fake_bin.mkdir(parents=True)
        fake_uv = fake_bin / "uv"
        fake_uv.write_text(
            "#!/bin/sh\n"
            'printf "uv|%s|%s|%s|%s\\n" "${UV_PROJECT:-}" '
            '"${UV_PROJECT_ENVIRONMENT:-}" "${VIRTUAL_ENV:-}" "$*" '
            f">> '{setup_log}'\n"
            "exit 0\n",
            encoding="utf-8",
        )
        fake_uv.chmod(0o755)

        process: p.Cli.CommandOutput = tm.ok(
            u.Tests.run_isolated_make(
                [
                    "-C",
                    str(repository_root),
                    "--dry-run",
                    "_builtin_setup_environment",
                    f"UV={fake_uv}",
                ],
                cwd=repository_root,
            )
        )

        output = process.stdout + process.stderr
        tm.that(process.exit_code, eq=0, msg=output)
        expected_environment = str(repository_root / ".venv")
        # The root owns its own environment: the venv lives beside it and the
        # sync targets the repository root, never an ambient caller project.
        tm.that(output, has=f'venv "{expected_environment}"')
        tm.that(output, has=f'sync --project "{repository_root}"')
        tm.that(output, has=f'pip check --python "{expected_environment}"')

    def test_orchestrator_sanitizes_child_env_and_forwards_gates(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository_root, project_names = _write_workspace(tmp_path)
        for project_name in project_names:
            _write_child_makefile(repository_root / project_name, exit_code=0)
        hostile_root = tmp_path / "hostile-worktree"
        hostile_venv = hostile_root / ".venv"
        monkeypatch.chdir(repository_root)
        monkeypatch.setenv("UV_PROJECT", str(hostile_root))
        monkeypatch.setenv("UV_PROJECT_ENVIRONMENT", str(hostile_venv))
        monkeypatch.setenv("VIRTUAL_ENV", str(hostile_venv))
        monkeypatch.setenv("PYTHONPATH", str(hostile_root / "src"))

        result = FlextInfraOrchestratorService(verb="check").orchestrate(
            project_names, "check", make_args=("CHECK_GATES=lint,pyrefly",)
        )

        tm.ok(result, len=2)
        outputs: tuple[p.Cli.CommandOutput, ...] = tuple(result.unwrap())
        for output in outputs:
            child_log = Path(output.stdout).read_text(encoding="utf-8")
            tm.that(child_log, has="gates=lint,pyrefly")
            tm.that(child_log, lacks=str(hostile_root))

    def test_orchestrator_fail_fast_preserves_child_exit_and_skips_remaining(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository_root, project_names = _write_workspace(tmp_path)
        _write_child_makefile(repository_root / project_names[0], exit_code=23)
        _write_child_makefile(repository_root / project_names[1], exit_code=0)
        monkeypatch.chdir(repository_root)

        result = FlextInfraOrchestratorService(verb="test").orchestrate(
            project_names, "test", fail_fast=True
        )

        tm.fail(result, has="orchestration completed with failures: 1")
        first_log = (
            repository_root
            / ".reports"
            / "workspace"
            / "test"
            / f"{project_names[0]}.log"
        )
        second_log = first_log.with_name(f"{project_names[1]}.log")
        tm.that(first_log.read_text(encoding="utf-8"), has="fail_fast=1")
        tm.that(second_log.exists(), eq=False)
