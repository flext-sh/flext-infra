"""Verify generated workspace-root Make behavior across orchestration seams."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from flext_infra import c, config, m, u
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_infra.workspace.orchestrator import FlextInfraOrchestratorService
from flext_tests import tm
from tests import u as test_u

if TYPE_CHECKING:
    from flext_cli import p as cli_p
    from flext_infra import p


def _write_workspace(tmp_path: Path) -> tuple[Path, tuple[str, ...]]:
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    # The fixture declares the synthetic topology it needs; flext-infra owns
    # no catalog of real projects to borrow rows from.
    root_repository = test_u.Tests.repository_ref("fixture-workspace")
    members = tuple(
        test_u.Tests.repository_ref(
            name, path=Path(name), role=c.Infra.RepositoryRole.WORKSPACE_MEMBER
        )
        for name in ("fixture-member-one", "fixture-member-two")
    )
    project_names = tuple(member.path.as_posix() for member in members)
    root_package = (
        workspace_root / "src" / root_repository.distribution.replace("-", "_")
    )
    root_package.mkdir(parents=True)
    (root_package / "__init__.py").write_text("", encoding="utf-8")
    (workspace_root / "pyproject.toml").write_text(
        f"[project]\nname = '{root_repository.distribution}'\nversion = '0.1.0'\n",
        encoding="utf-8",
    )
    manifest = m.Infra.WorkspaceSpec(
        version=c.Infra.WORKSPACE_MANIFEST_VERSION,
        name=root_repository.name,
        repository=root_repository,
        members=members,
    )
    tm.ok(
        u.Cli.yaml_dump(
            workspace_root / "config" / "workspace.yaml",
            manifest.model_dump(mode="json", exclude_none=True),
        )
    )
    for project_name in project_names:
        project_root = workspace_root / project_name
        project_root.mkdir(parents=True)
        package_root = project_root / "src" / project_name.replace("-", "_")
        package_root.mkdir(parents=True)
        (package_root / "__init__.py").write_text("", encoding="utf-8")
        (project_root / "pyproject.toml").write_text(
            f"[project]\nname = '{project_name}'\nversion = '0.1.0'\n", encoding="utf-8"
        )
    # Seed the declared provider URL as origin so workspace discovery resolves
    # this fixture as a provider-governed checkout; the helper owns the fake
    # baseline ref, and real ancestry is exercised elsewhere.
    test_u.Tests.initialize_git_repo(workspace_root, origin_url=root_repository.url)
    # mro-z89e.2.2: seed a minimal .gitmodules so the conform detector sees the
    # declared members as governed submodules; the real setup/Gitlink lifecycle is
    # covered by tests/unit/codegen/test_workspace_root_setup_submodules.py.
    gitmodules_path = workspace_root / ".gitmodules"
    provider = config.Infra.codegen.providers[0]
    gitmodules_lines = []
    for member in members:
        section_name = member.name.replace("-", "_")
        gitmodules_lines.extend([
            f'[submodule "{section_name}"]\n',
            f"\tpath = {member.path.as_posix()}\n",
            f"\turl = {member.url}\n",
            f"\tbranch = {provider.branch}\n",
        ])
    gitmodules_path.write_text("".join(gitmodules_lines), encoding="utf-8")
    tm.ok(u.Cli.run_checked(["git", "add", ".gitmodules"], cwd=workspace_root))
    tm.ok(
        u.Cli.run_checked(
            ["git", "commit", "-m", "seed fixture gitmodules"], cwd=workspace_root
        )
    )
    # These tests assert what the GENERATED Makefile contains, so only the
    # rendered artifacts are needed. Running the apply path additionally drove
    # the Beads lifecycle, which inspects a live Dolt tracker: a unit test then
    # depended on an external service and failed on any machine without it.
    # Planning renders the same files and touches no tracker.
    planned = tm.ok(
        FlextInfraCodegenConform().plan(
            m.Infra.CodegenConformRequest(
                root=workspace_root,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.CHECK,
            )
        )
    )
    for planned_file in planned.files:
        planned_file.path.parent.mkdir(parents=True, exist_ok=True)
        planned_file.path.write_text(planned_file.rendered, encoding="utf-8")
    # mro-z89e.2.2: this fixture validates the environment/toolchain contract,
    # not Gitlink reconciliation. The generated .gitmodules would classify the
    # plain member directories as managed submodules and fail the setup
    # preflight; Gitlink behavior is covered by
    # tests/unit/codegen/test_workspace_root_setup_submodules.py.
    (workspace_root / ".gitmodules").unlink(missing_ok=True)
    for project_name in project_names:
        _write_child_makefile(workspace_root / project_name, exit_code=0)
    return workspace_root, project_names


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


class TestsWorkspaceRootMakeContract:
    def test_workspace_root_make_template_is_owned_by_typed_config(self) -> None:
        make_entries = tuple(
            entry
            for entry in config.Infra.codegen.templates.entries
            if entry.destination == c.Infra.MAKEFILE_FILENAME
        )

        tm.that(make_entries, len=1)
        tm.that(make_entries[0].profiles, has=c.Infra.MakeProfile.WORKSPACE_ROOT)

    def test_generated_make_exposes_only_public_conform(self, tmp_path: Path) -> None:
        """Route the sole public conformance verb to the internal CLI.

        Which verb carries conformance is config-owned: it is declared in
        make.verbs and is `gen` today. The contract is that the declared verb
        reaches `codegen conform`, and that no second public entry point does.
        """
        workspace_root, _ = _write_workspace(tmp_path)
        declared = {verb.name for verb in config.Infra.codegen.make.verbs}
        tm.that(declared, has="gen")

        generated: cli_p.Cli.CommandOutput = tm.ok(
            test_u.Tests.run_isolated_make(
                ["-C", str(workspace_root), "--dry-run", "gen", "WHAT=check"],
                cwd=workspace_root,
            )
        )
        retired: cli_p.Cli.CommandOutput = tm.ok(
            test_u.Tests.run_isolated_make(
                ["-C", str(workspace_root), "--dry-run", "codegen"], cwd=workspace_root
            )
        )
        output = generated.stdout + generated.stderr

        tm.that(generated.exit_code, eq=0, msg=output)
        tm.that(output, has='--verb "gen"')
        tm.that(declared, lacks="codegen")
        tm.that(retired.exit_code, ne=0)

    def test_generated_setup_runs_its_lifecycle_hooks(self, tmp_path: Path) -> None:
        """``setup`` must fire pre-/post-setup like every other public verb.

        The generated ``setup`` short-circuited straight to
        ``_builtin_setup_environment``, bypassing ``_dispatch`` — so a project
        declaring ``post-setup`` in ``custom.mk`` (the only sanctioned extension
        surface) had that hook silently never execute.
        """
        workspace_root, _project_names = _write_workspace(tmp_path)
        (workspace_root / c.Infra.CUSTOM_MAKE_FILENAME).write_text(
            ".PHONY: post-setup\npost-setup:\n\t@echo POST_SETUP_HOOK_RAN\n",
            encoding="utf-8",
        )

        process: cli_p.Cli.CommandOutput = tm.ok(
            test_u.Tests.run_isolated_make(
                ["-C", str(workspace_root), "--dry-run", "setup"], cwd=workspace_root
            )
        )
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0, msg=output)
        tm.that(output, has="post-setup", msg=output)

    def test_generated_make_selects_manifest_projects_and_forwards_gates(
        self, tmp_path: Path
    ) -> None:
        workspace_root, project_names = _write_workspace(tmp_path)

        process: cli_p.Cli.CommandOutput = tm.ok(
            test_u.Tests.run_isolated_make(
                [
                    "-C",
                    str(workspace_root),
                    "--dry-run",
                    "_builtin_check_all",
                    f"PROJECT={project_names[0]}",
                    "CHECK_GATES=lint,pyrefly",
                ],
                cwd=workspace_root,
            )
        )
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0, msg=output)
        tm.that(output, has=f"--projects {project_names[0]}")
        tm.that(output, has='--make-arg "CHECK_GATES=lint,pyrefly"')
        tm.that(output, lacks=f"--projects {project_names[1]}")

    def test_generated_make_routes_fmt_apply_to_selected_project(
        self, tmp_path: Path
    ) -> None:
        """Apply formatting only in the selected workspace member."""
        workspace_root, project_names = _write_workspace(tmp_path)

        process: cli_p.Cli.CommandOutput = tm.ok(
            test_u.Tests.run_isolated_make(
                [
                    "-C",
                    str(workspace_root),
                    "--dry-run",
                    "_builtin_fmt_apply",
                    f"PROJECT={project_names[0]}",
                    "APPLY=Y",
                ],
                cwd=workspace_root,
            )
        )
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0, msg=output)
        tm.that(output, has="--verb fmt")
        tm.that(output, has=f"--projects {project_names[0]}")
        tm.that(output, has='--make-arg "WHAT=apply"')
        tm.that(output, has='--make-arg "APPLY=Y"')
        tm.that(output, lacks=f"--projects {project_names[1]}")
        tm.that(output, lacks="ruff check --fix")

    def test_generated_make_routes_file_and_match_only_to_owning_project(
        self, tmp_path: Path
    ) -> None:
        workspace_root, project_names = _write_workspace(tmp_path)
        owner = project_names[0]
        selected = f"{owner}/tests/unit/test_selected.py"

        process: cli_p.Cli.CommandOutput = tm.ok(
            test_u.Tests.run_isolated_make(
                [
                    "-C",
                    str(workspace_root),
                    "--dry-run",
                    "_builtin_test_all",
                    f"FILE={selected}",
                    "MATCH=selected_case",
                ],
                cwd=workspace_root,
            )
        )
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0, msg=output)
        tm.that(output, has=f"--projects {owner}")
        tm.that(output, has="--file")
        tm.that(output, has="--match")

    def test_generated_make_routes_root_file_only_to_workspace_root(
        self, tmp_path: Path
    ) -> None:
        """Keep provider-owned root tests in the root project execution lane."""
        workspace_root, _ = _write_workspace(tmp_path)
        selected = "tests/unit/test_provider_contract.py"

        process: cli_p.Cli.CommandOutput = tm.ok(
            test_u.Tests.run_isolated_make(
                [
                    "-C",
                    str(workspace_root),
                    "--dry-run",
                    "_builtin_test_all",
                    f"FILE={selected}",
                ],
                cwd=workspace_root,
            )
        )
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0, msg=output)
        # The root project is in the forwarded selection and the typed FILE
        # selector travels with it. Which project owns the file is decided by
        # the orchestrator (_select_file_owner), not by this Make recipe, so
        # this boundary asserts forwarding rather than owner filtering.
        tm.that(output, has="--projects .")
        tm.that(output, has="--file")

    def test_generated_make_default_test_includes_root_and_every_member(
        self, tmp_path: Path
    ) -> None:
        """Run provider root tests alongside every configured workspace member."""
        workspace_root, project_names = _write_workspace(tmp_path)

        process: cli_p.Cli.CommandOutput = tm.ok(
            test_u.Tests.run_isolated_make(
                ["-C", str(workspace_root), "--dry-run", "_builtin_test_all"],
                cwd=workspace_root,
            )
        )
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0, msg=output)
        tm.that(output, has="--projects .")
        for project_name in project_names:
            tm.that(output, has=f"--projects {project_name}")

    def test_generated_make_exposes_typed_docs_lifecycle(self, tmp_path: Path) -> None:
        workspace_root, project_names = _write_workspace(tmp_path)
        docs = config.Infra.codegen.make.docs
        invocation_log = workspace_root / "docs.log"
        test_u.Tests.write_executable(
            workspace_root / ".venv" / "bin" / "python",
            (
                "#!/bin/sh\n"
                "verb=''\n"
                "previous=''\n"
                'for argument in "$@"; do\n'
                '  if [ "$previous" = "--verb" ]; then verb="$argument"; fi\n'
                '  previous="$argument"\n'
                "done\n"
                'if [ -n "$verb" ]; then exec make --no-print-directory "_serialized_${verb}"; fi\n'
                f'printf "%s\\n" "$*" >> "{invocation_log}"\n'
            ),
        )
        uv = workspace_root / "bin" / "uv"
        test_u.Tests.write_executable(uv, "#!/bin/sh\nexit 0\n")

        for action in docs.actions:
            invocation_log.write_text("", encoding="utf-8")
            process: cli_p.Cli.CommandOutput = tm.ok(
                test_u.Tests.run_isolated_make(
                    [
                        "-C",
                        str(workspace_root),
                        "docs",
                        f"WHAT={action}",
                        f"PROJECTS={project_names[0]}",
                        f"UV={uv}",
                    ],
                    cwd=workspace_root,
                )
            )
            tm.that(process.exit_code, eq=0, msg=process.stdout + process.stderr)
            output = invocation_log.read_text(encoding="utf-8")
            expected_actions = (
                tuple(item for item in docs.actions if item != docs.default_action)
                if action == docs.default_action
                else (action,)
            )
            for expected_action in expected_actions:
                tm.that(output, has=f"docs {expected_action}")
            tm.that(output, has=f"--output-dir {workspace_root / docs.reports_dir}")
            tm.that(output, has=f"--projects {project_names[0]}")
            tm.that(output, lacks=f"--projects {project_names[1]}")
            if action in docs.mutable_actions:
                tm.that(output, has="--check")
                tm.that(output, lacks="--apply")
                invocation_log.write_text("", encoding="utf-8")
                applied = tm.ok(
                    test_u.Tests.run_isolated_make(
                        [
                            "-C",
                            str(workspace_root),
                            "docs",
                            f"WHAT={action}",
                            "APPLY=Y",
                            f"PROJECTS={project_names[0]}",
                            f"UV={uv}",
                        ],
                        cwd=workspace_root,
                    )
                )
                tm.that(applied.exit_code, eq=0, msg=applied.stdout + applied.stderr)
                applied_output = invocation_log.read_text(encoding="utf-8")
                tm.that(applied_output, has="--apply")
                tm.that(applied_output, lacks="--check")
            elif action != docs.default_action:
                tm.that(output, lacks="--apply")
                tm.that(output, lacks="--check")

        invalid = tm.ok(
            test_u.Tests.run_isolated_make(
                ["-C", str(workspace_root), "docs", "WHAT=not-a-docs-action"],
                cwd=workspace_root,
            )
        )
        tm.that(invalid.exit_code, ne=0)

    def test_workspace_root_setup_owns_environment_and_uses_venv_directory(
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
        workspace_root, _ = _write_workspace(tmp_path)
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

        process: cli_p.Cli.CommandOutput = tm.ok(
            test_u.Tests.run_isolated_make(
                [
                    "-C",
                    str(workspace_root),
                    "--dry-run",
                    "_builtin_setup_environment",
                    f"UV={fake_uv}",
                ],
                cwd=workspace_root,
            )
        )

        output = process.stdout + process.stderr
        tm.that(process.exit_code, eq=0, msg=output)
        expected_environment = str(workspace_root / ".venv")
        # The root owns its own environment: the venv lives beside it and the
        # sync targets the workspace root, never an ambient caller project.
        tm.that(output, has=f'venv --clear "{expected_environment}"')
        tm.that(output, has=f'sync --project "{workspace_root}"')
        tm.that(output, has=f'pip check --python "{expected_environment}"')

    def test_orchestrator_sanitizes_child_env_and_forwards_gates(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        workspace_root, project_names = _write_workspace(tmp_path)
        for project_name in project_names:
            _write_child_makefile(workspace_root / project_name, exit_code=0)
        hostile_root = tmp_path / "hostile-worktree"
        hostile_venv = hostile_root / ".venv"
        monkeypatch.chdir(workspace_root)
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
        workspace_root, project_names = _write_workspace(tmp_path)
        _write_child_makefile(workspace_root / project_names[0], exit_code=23)
        _write_child_makefile(workspace_root / project_names[1], exit_code=0)
        monkeypatch.chdir(workspace_root)

        result = FlextInfraOrchestratorService(verb="test").orchestrate(
            project_names, "test", fail_fast=True
        )

        tm.fail(result, has="orchestration completed with failures: 1")
        first_log = (
            workspace_root
            / ".reports"
            / "workspace"
            / "test"
            / f"{project_names[0]}.log"
        )
        second_log = first_log.with_name(f"{project_names[1]}.log")
        tm.that(first_log.read_text(encoding="utf-8"), has="fail_fast=1")
        tm.that(second_log.exists(), eq=False)
