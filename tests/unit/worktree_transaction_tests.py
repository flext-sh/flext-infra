"""Behavior tests for bounded worktree transactions.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import m, u as infra_u
from flext_infra import main as infra_main
from tests import t, u


class TestWorktreeTransactionScope:
    """Prove selected transactions exclude unrelated dirty repository state."""

    def test_selected_repository_excludes_unselected_dirty_state(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Materialize the workspace once while validating only the selection."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        (workspace / "pyproject.toml").write_text(
            '[project]\nname = "workspace"\nversion = "0.1.0"\n', encoding="utf-8"
        )
        u.Tests.initialize_git_repo(workspace)

        for repository_name in ("flext-selected", "flext-unselected"):
            repository = tmp_path / f"{repository_name}-source"
            package = repository / "src" / repository_name.replace("-", "_")
            package.mkdir(parents=True)
            (repository / "pyproject.toml").write_text(
                (f'[project]\nname = "{repository_name}"\nversion = "0.1.0"\n'),
                encoding="utf-8",
            )
            init_content = ""
            if repository_name == "flext-selected":
                init_content = '''# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Selected package.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_core.lazy import (
    build_lazy_import_map as _build_lazy_import_map,
    install_lazy_exports as _install_lazy_exports,
)


_LAZY_MODULES: dict[str, tuple[str, ...]] = {}


_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}


_LAZY_IMPORTS = _build_lazy_import_map(
    _LAZY_MODULES,
    alias_groups=_LAZY_ALIAS_GROUPS,
    sort_keys=False,
)

__all__: tuple[str, ...] = ()


_install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    public_exports=__all__,
)
'''
            package.joinpath("__init__.py").write_text(init_content, encoding="utf-8")
            u.Tests.initialize_git_repo(repository)
            tm.ok(
                u.Cli.run_checked(
                    [
                        "git",
                        "-c",
                        "protocol.file.allow=always",
                        "submodule",
                        "add",
                        str(repository),
                        repository_name,
                    ],
                    cwd=workspace,
                )
            )

        tm.ok(u.Cli.run_checked(["git", "add", "-A"], cwd=workspace))
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-m", "add transaction fixtures"], cwd=workspace
            )
        )
        unselected_init = (
            workspace / "flext-unselected" / "src" / "flext_unselected" / "__init__.py"
        )
        unselected_init.write_text(
            'raise RuntimeError("unselected dirty state must not be imported")\n',
            encoding="utf-8",
        )
        status_before = infra_u.Infra.git_capture(workspace, ("status", "--short"))
        tm.ok(status_before)

        # NOTE (multi-agent): the transaction keeps one complete semantic workspace,
        # but selected repositories alone own dirty snapshots and validation.
        request = m.Infra.WorktreeTransactionRequest(
            workspace_root=workspace,
            command=(
                "codegen",
                "init",
                "--workspace",
                str(workspace),
                "--projects",
                "flext-selected",
                "--apply",
            ),
            selected_repositories=("flext-selected",),
            apply_patch=False,
            timeout_seconds=60,
        )
        result = infra_u.Infra.execute_worktree_transaction(request)

        tm.ok(result)
        tm.that(
            result.value.breakage_detected,
            eq=False,
            msg=infra_u.Infra.render_worktree_transaction_report(result.value),
        )
        tm.that(
            tuple(repository.relative_path for repository in result.value.repositories),
            eq=("flext-selected",),
        )
        # NOTE (multi-agent, mro-wkii.17.26.2.10 / agent: codex): an
        # idempotence gate must prove the first complete plan is already empty.
        tm.that(
            tuple(repository.patch for repository in result.value.repositories),
            eq=(b"",),
        )
        first_command_output = result.value.command_output.stdout
        tm.that(first_command_output.count("rope: opening workspace at"), eq=1)
        tm.that(first_command_output.count("rope: indexed "), eq=1)
        cli_exit = infra_main([
            "codegen",
            "init",
            "--workspace",
            str(workspace),
            "--projects",
            "flext-selected",
            "--check",
        ])
        tm.that(cli_exit, eq=0)
        status_after = infra_u.Infra.git_capture(workspace, ("status", "--short"))
        tm.ok(status_after)
        tm.that(status_after.value, eq=status_before.value)
        tm.that(tuple((workspace / ".worktrees").glob("transaction-*")), eq=())
        progress_output = capsys.readouterr().out
        tm.that(progress_output, contains="materializing flext-selected")
        tm.that(progress_output, contains="repository deltas")
        tm.that(progress_output, contains="cleaning up")
        # NOTE (multi-agent, mro-wkii.17.26.2.10 / agent: codex): the CLI
        # transaction independently owns one complete Rope workspace and index.
        tm.that(progress_output.count("rope: opening workspace at"), eq=1)
        tm.that(progress_output.count("rope: indexed "), eq=1)


__all__: t.StrSequence = []
