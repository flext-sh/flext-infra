"""Canonical workspace formatter tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import config, u
from flext_infra.workspace.formatter import FlextInfraWorkspaceFormatter
from flext_tests import tm


class TestsWorkspaceFormatter:
    """Prove formatting uses only Git-owned files and typed steps."""

    def test_select_files_includes_tracked_and_nonignored_dirty_only(
        self, tmp_path: Path
    ) -> None:
        """Ignored files and unrelated languages never reach a formatter."""
        tm.ok(u.Cli.run_raw(["git", "init"], cwd=tmp_path))
        (tmp_path / ".gitignore").write_text("ignored.py\n", encoding="utf-8")
        tracked = tmp_path / "tracked.py"
        dirty = tmp_path / "dirty.py"
        ignored = tmp_path / "ignored.py"
        markdown = tmp_path / "README.md"
        for path in (tracked, dirty, ignored, markdown):
            path.write_text("import os\n", encoding="utf-8")
        tm.ok(
            u.Cli.run_raw(
                ["git", "add", ".gitignore", "tracked.py", "README.md"], cwd=tmp_path
            )
        )
        step = next(
            item
            for item in config.Infra.codegen.formatters
            if item.name == "python-imports"
        )

        selected = FlextInfraWorkspaceFormatter.select_files(tmp_path, step)

        tm.that(selected, eq=(dirty, tracked))
        tm.that(selected, lacks=ignored)
        tm.that(selected, lacks=markdown)

    def test_native_formatter_runs_through_the_explicit_mise_gateway(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Native formatters do not depend on a caller shell's activated PATH."""
        mise = tmp_path / "mise"
        mise.touch()
        monkeypatch.setenv("FLEXT_INFRA_MISE", str(mise))
        step = next(
            item
            for item in config.Infra.codegen.formatters
            if item.name == "go"
        )

        command = FlextInfraWorkspaceFormatter.command_for_step(
            step, (Path("example.go"),), apply=False
        )

        tm.that(
            command,
            eq=(str(mise), "exec", "--", "gofmt", "-d", "example.go"),
        )


__all__: list[str] = ["TestsWorkspaceFormatter"]
