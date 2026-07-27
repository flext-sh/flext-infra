"""Verify generated workspace-root Make behavior across orchestration seams."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from flext_tests import tm

from flext_cli import cli
from flext_infra import c, config, m, u
from flext_infra.workspace.orchestrator import FlextInfraOrchestratorService
from flext_infra.workspace.workspace_makefile import (
    FlextInfraWorkspaceMakefileGenerator,
)

if TYPE_CHECKING:
    from flext_cli import p as cli_p
    from flext_infra import p


def _write_workspace(tmp_path: Path) -> tuple[Path, tuple[str, ...]]:
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    root_repository = next(
        repository
        for repository in config.Infra.codegen.repositories
        if repository.role is c.Infra.RepositoryRole.WORKSPACE_ROOT
        and repository.provider == config.Infra.codegen.providers[0].name
    )
    members = tuple(
        repository
        for repository in config.Infra.codegen.repositories
        if repository.role is c.Infra.RepositoryRole.WORKSPACE_MEMBER
        and repository.provider == root_repository.provider
    )[:2]
    project_names = tuple(member.path.as_posix() for member in members)
    (workspace_root / "pyproject.toml").write_text(
        "[project]\n"
        f"name = '{root_repository.distribution}'\n"
        "version = '0.1.0'\n\n"
        "[tool.flext.workspace]\n"
        f"members = {list(project_names)!r}\n",
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
        (project_root / "pyproject.toml").write_text(
            f"[project]\nname = '{project_name}'\nversion = '0.1.0'\n", encoding="utf-8"
        )
    tm.ok(FlextInfraWorkspaceMakefileGenerator().generate(workspace_root))
    return workspace_root, project_names


def _write_child_makefile(project_root: Path, *, exit_code: int) -> None:
    (project_root / "Makefile").write_text(
        "SHELL := /bin/sh\n"
        ".PHONY: check test\n"
        "check test:\n"
        "\t@printf 'project=%s verb=%s gates=%s uv_project=%s uv_env=%s "
        "venv=%s fail_fast=%s\\n' '$(notdir $(CURDIR))' '$@' "
        "'$(CHECK_GATES)' '$(UV_PROJECT)' '$(UV_PROJECT_ENVIRONMENT)' "
        "'$(VIRTUAL_ENV)' '$(FAIL_FAST)'\n"
        f"\t@exit {exit_code}\n",
        encoding="utf-8",
    )


def _write_fake_uv(bin_root: Path, log_path: Path) -> None:
    bin_root.mkdir()
    (bin_root / "uv").write_text(
        "#!/bin/sh\n"
        f"printf '%s|%s|%s|%s\\n' \"$UV_PROJECT\" \"$UV_PROJECT_ENVIRONMENT\" "
        f"\"$VIRTUAL_ENV\" \"$*\" >> {log_path}\n",
        encoding="utf-8",
    )
    (bin_root / "uv").chmod(0o755)


class TestsWorkspaceRootMakeContract:
    def test_workspace_root_make_template_is_owned_by_typed_config(self) -> None:
        make_entries = tuple(
            entry
            for entry in config.Infra.codegen.templates.entries
            if entry.destination == c.Infra.MAKEFILE_FILENAME
        )

        tm.that(make_entries, len=1)
        tm.that(make_entries[0].profiles, has=c.Infra.MakeProfile.WORKSPACE_ROOT)

    def test_generated_make_selects_manifest_projects_and_forwards_gates(
        self, tmp_path: Path
    ) -> None:
        workspace_root, project_names = _write_workspace(tmp_path)

        process: cli_p.Cli.CommandOutput = tm.ok(
            cli.run_raw([
                "make",
                "-C",
                str(workspace_root),
                "--dry-run",
                "check",
                f"PROJECT={project_names[0]}",
                "CHECK_GATES=lint,pyrefly",
            ])
        )
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0)
        tm.that(output, has=f"--projects {project_names[0]}")
        tm.that(output, has='--make-arg "CHECK_GATES=lint,pyrefly"')
        tm.that(output, lacks=f"--projects {project_names[1]}")

    def test_workspace_root_setup_owns_environment_and_uses_venv_directory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        workspace_root, _ = _write_workspace(tmp_path)
        fake_bin = tmp_path / "bin"
        uv_log = tmp_path / "uv.log"
        _write_fake_uv(fake_bin, uv_log)
        monkeypatch.setenv(
            "PATH", f"{fake_bin}{os.pathsep}{os.environ.get('PATH', '')}"
        )
        monkeypatch.setenv("UV_PROJECT", str(tmp_path / "hostile-project"))
        monkeypatch.setenv(
            "UV_PROJECT_ENVIRONMENT", str(tmp_path / "hostile-venv")
        )
        monkeypatch.setenv("VIRTUAL_ENV", str(tmp_path / "hostile-venv"))

        process: cli_p.Cli.CommandOutput = tm.ok(
            cli.run_raw(
                [
                    "make",
                    "-C",
                    str(workspace_root),
                    "setup",
                    "WHAT=environment",
                ]
            )
        )

        tm.that(process.exit_code, eq=0)
        calls = uv_log.read_text(encoding="utf-8").splitlines()
        expected_environment = str(workspace_root / ".venv")
        for call in calls:
            project, environment, virtual_env, arguments = call.split("|", 3)
            tm.that(project, eq=str(workspace_root))
            tm.that(environment, eq=expected_environment)
            tm.that(virtual_env, eq=expected_environment)
            if "--python" in arguments:
                tm.that(arguments, lacks=".venv/bin/python")
                tm.that(arguments, has=f"--python {expected_environment}")

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
