"""Tests for the workspace root Make contract and orchestration report.

Covers the single generation owner of the root Makefile, the deterministic
per-project orchestration report, and preservation of the child exit code.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from flext_tests import tm

from flext_infra import c, config
from flext_infra.workspace.orchestrator import FlextInfraOrchestratorService
from flext_infra.workspace.workspace_makefile import (
    FlextInfraWorkspaceMakefileGenerator,
)

if TYPE_CHECKING:
    from flext_infra import p


def _write_workspace(tmp_path: Path) -> tuple[Path, tuple[str, ...]]:
    workspace_root = tmp_path / "workspace"
    project_names = ("project-a", "project-b")
    workspace_root.mkdir()
    (workspace_root / "pyproject.toml").write_text(
        "[project]\nname='workspace-root'\nversion='0.1.0'\n"
        "[tool.flext.workspace]\nmembers=['project-a', 'project-b']\n",
        encoding="utf-8",
    )
    config_dir = workspace_root / "config"
    config_dir.mkdir()
    members = "".join(
        f"\n  - name: {name}\n"
        f"    distribution: {name}\n"
        "    provider: flext-sh\n"
        f"    url: https://github.com/flext-sh/{name}.git\n"
        "    branch: main\n"
        f"    path: {name}\n"
        "    role: workspace-member\n"
        "    state: active\n"
        "    profile: workspace-member\n"
        "    checkout: submodule\n"
        "    codegen: conform\n"
        "    package: true\n"
        "    editable: true\n"
        "    read_only: false"
        for name in project_names
    )
    (config_dir / "workspace.yaml").write_text(
        "version: 2\nname: workspace-root\nrepository:\n"
        "  name: workspace-root\n  distribution: workspace-root\n"
        "  provider: flext-sh\n"
        "  url: https://github.com/flext-sh/workspace-root.git\n"
        "  branch: main\n  path: .\n  role: workspace-root\n"
        "  state: active\n  profile: workspace-root\n  checkout: root\n"
        "  codegen: conform\n  package: false\n  editable: false\n"
        f"  read_only: false\nmembers:{members}\n"
        "content_only: []\nexclusions: []\n",
        encoding="utf-8",
    )
    for name in project_names:
        project_root = workspace_root / name
        project_root.mkdir()
        (project_root / "pyproject.toml").write_text(
            f"[project]\nname='{name}'\nversion='0.1.0'\n", encoding="utf-8"
        )
    tm.ok(FlextInfraWorkspaceMakefileGenerator().generate(workspace_root))
    return workspace_root, project_names


def _write_child_makefile(project_root: Path, *, exit_code: int) -> None:
    (project_root / "Makefile").write_text(
        "SHELL := /bin/sh\n"
        ".PHONY: check test\n"
        "check test:\n"
        "\t@printf 'project=%s verb=%s gates=%s uv_project=%s uv_env=%s venv=%s\\n' "
        "'$(notdir $(CURDIR))' '$@' '$(CHECK_GATES)' '$(UV_PROJECT)' "
        "'$(UV_PROJECT_ENVIRONMENT)' '$(VIRTUAL_ENV)'\n"
        f"\t@exit {exit_code}\n",
        encoding="utf-8",
    )


class TestsWorkspaceRootMakeContract:
    def test_workspace_root_make_has_one_generation_owner(self) -> None:
        make_entries = tuple(
            entry
            for entry in config.Infra.codegen.templates.entries
            if entry.destination == c.Infra.MAKEFILE_FILENAME
        )

        tm.that(make_entries, len=1)
        tm.that(make_entries[0].profiles, lacks=c.Infra.MakeProfile.WORKSPACE_ROOT)

    def test_generated_make_selects_manifest_projects_and_forwards_gates(
        self, tmp_path: Path
    ) -> None:
        workspace_root, project_names = _write_workspace(tmp_path)

        outcome = FlextInfraWorkspaceMakefileGenerator().generate(
            workspace_root, apply=False
        )
        makefile = (workspace_root / "Makefile").read_text(encoding="utf-8")

        tm.ok(outcome, eq=False)
        tm.that(makefile, has="ALL_PROJECTS :=")
        tm.that(makefile, has="SELECTED_PROJECTS :=")
        tm.that(makefile, has='--make-arg "CHECK_GATES=$(CHECK_GATES)"')
        for project_name in project_names:
            tm.that(makefile, has=project_name)

    def test_orchestrator_uses_workspace_environment_and_reports_deterministically(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
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

        result = FlextInfraOrchestratorService(verb="check").orchestrate(
            project_names, "check", make_args=("CHECK_GATES=lint,pyrefly",)
        )
        output = capsys.readouterr().out

        outputs: tuple[p.Cli.CommandOutput, ...] = tuple(tm.ok(result, len=2))
        tm.that([item.exit_code for item in outputs], eq=[0, 0])
        tm.that(output, has="scope=workspace")
        tm.that(output, has="projects=project-a,project-b")
        tm.that(output, has="gates=lint,pyrefly")
        tm.that(output, has="[1/2] START project-a check")
        # mro-9v0d: duration is inherently variable, so the per-project line is
        # matched by pattern. tm.that has no regex parameter (verified against
        # the matcher model and its full history), so the search is explicit.
        tm.that(
            bool(
                re.search(
                    r"\[1/2\] PASS project-a check exit=0 duration=\d+\.\d{2}s",
                    output,
                )
            ),
            eq=True,
        )
        tm.that(output, has="[2/2] START project-b check")
        tm.that(
            bool(
                re.search(
                    r"\[2/2\] PASS project-b check exit=0 duration=\d+\.\d{2}s",
                    output,
                )
            ),
            eq=True,
        )
        tm.that(output, has="summary scope=workspace verb=check total=2 passed=2 failed=0 skipped=0")
        tm.that(output, lacks=[str(hostile_root), "wait:"])

    def test_orchestrator_fail_fast_preserves_child_exit_and_diagnostics(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        workspace_root, project_names = _write_workspace(tmp_path)
        _write_child_makefile(workspace_root / project_names[0], exit_code=23)
        _write_child_makefile(workspace_root / project_names[1], exit_code=0)
        monkeypatch.chdir(workspace_root)

        result = FlextInfraOrchestratorService(verb="test").orchestrate(
            project_names, "test", fail_fast=True
        )
        output = capsys.readouterr().out

        failure = tm.fail(result, has="exit code 23")
        tm.that(failure, has="project-a")
        tm.that(output, has="[1/2] FAIL project-a test exit=23")
        tm.that(output, lacks="[2/2] START")
        tm.that(output, has="summary scope=workspace verb=test total=2 passed=0 failed=1 skipped=1 exit=23")
        tm.that(output, lacks="wait:")
