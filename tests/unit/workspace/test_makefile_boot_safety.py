"""Workspace boot safety tests through the generated public Make target."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from flext_tests import tm

from flext_cli import cli
from flext_infra.workspace.workspace_makefile import (
    FlextInfraWorkspaceMakefileGenerator,
)

if TYPE_CHECKING:
    from pathlib import Path


def _write_workspace(tmp_path: Path) -> Path:
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    (workspace_root / "pyproject.toml").write_text(
        "[project]\nname='workspace-root'\nversion='0.1.0'\nrequires-python='>=3.13,<3.14'\n",
        encoding="utf-8",
    )
    (workspace_root / ".gitmodules").write_text(
        '[submodule "demo"]\n\tpath = demo\n\turl = https://example.invalid/demo.git\n',
        encoding="utf-8",
    )
    config_dir = workspace_root / "config"
    config_dir.mkdir()
    (config_dir / "workspace.yaml").write_text(
        (
            "version: 2\n"
            "name: workspace-root\n"
            "repository:\n"
            "  name: workspace-root\n"
            "  distribution: workspace-root\n"
            "  provider: flext-sh\n"
            "  url: https://github.com/flext-sh/workspace-root.git\n"
            "  branch: main\n"
            "  path: .\n"
            "  role: workspace-root\n"
            "  state: active\n"
            "  profile: workspace-root\n"
            "  checkout: root\n"
            "  codegen: conform\n"
            "  package: false\n"
            "  editable: false\n"
            "  read_only: false\n"
            "members: []\n"
            "content_only: []\n"
            "exclusions: []\n"
        ),
        encoding="utf-8",
    )
    (workspace_root / "demo" / ".git").mkdir(parents=True)
    tm.ok(FlextInfraWorkspaceMakefileGenerator().generate(workspace_root))
    return workspace_root


def _write_git_probe(tmp_path: Path) -> tuple[Path, Path]:
    probe_dir = tmp_path / "bin"
    probe_dir.mkdir()
    calls_path = tmp_path / "git-calls.log"
    git_path = probe_dir / "git"
    git_path.write_text(
        (
            "#!/usr/bin/bash\n"
            'printf "%s\\n" "$*" >> "$GIT_CALLS_PATH"\n'
            'if [ "$1" = "config" ]; then\n'
            "  printf 'submodule.demo.path demo\\n'\n"
            "fi\n"
            'if [ "$1" = "-C" ] && [ "$3" = "status" ]; then\n'
            "  printf ' M shared-change.yaml\\n'\n"
            "fi\n"
        ),
        encoding="utf-8",
    )
    git_path.chmod(0o755)
    return probe_dir, calls_path


class TestsFlextInfraWorkspaceBootSafety:
    """Behavior contract for shared-worktree boot preflight."""

    def test_boot_fails_before_submodule_mutation_when_declared_worktree_is_dirty(
        self, tmp_path: Path
    ) -> None:
        """Refuse boot before synchronizing or updating a dirty submodule."""
        workspace_root = _write_workspace(tmp_path)
        probe_dir, calls_path = _write_git_probe(tmp_path)

        outcome = cli.run_raw(
            ["make", "-C", str(workspace_root), "_boot_submodules"],
            env={
                "GIT_CALLS_PATH": str(calls_path),
                "PATH": f"{probe_dir}{os.pathsep}{os.environ['PATH']}",
            },
            remove_env_keys=("MAKEFLAGS", "PROJECT", "PROJECTS", "VERBOSE"),
        )

        process = tm.ok(outcome)
        calls = calls_path.read_text(encoding="utf-8")
        tm.that(process.exit_code, ne=0)
        tm.that(process.stdout + process.stderr, has="demo")
        tm.that(calls, lacks=["submodule sync", "submodule update"])
