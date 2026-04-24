"""Tests for public workspace path resolution utilities."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import u


class TestFlextInfraPathResolver:
    """Verify workspace path resolution through the public utility."""

    def test_resolve_workspace_root_with_current_directory(self) -> None:
        result = u.Infra.resolve_workspace_root_or_cwd(None)
        tm.that(result.is_absolute(), eq=True)

    def test_resolve_workspace_root_with_absolute_path(self, tmp_path: Path) -> None:
        result = u.Infra.resolve_workspace_root_or_cwd(tmp_path)
        tm.that(result.is_absolute(), eq=True)

    def test_resolve_workspace_root_returns_resolved_path(self, tmp_path: Path) -> None:
        result = u.Infra.resolve_workspace_root_or_cwd(tmp_path)
        tm.that(result, eq=tmp_path.resolve())

    def test_resolve_workspace_root_with_none_uses_cwd(self) -> None:
        result = u.Infra.resolve_workspace_root_or_cwd(None)
        tm.that(result, eq=Path.cwd().resolve())

    def test_resolve_workspace_root_with_file_returns_parent(
        self, tmp_path: Path
    ) -> None:
        file_path = tmp_path / "some_file.txt"
        file_path.write_text("", encoding="utf-8")
        result = u.Infra.resolve_workspace_root_or_cwd(file_path)
        tm.that(result, eq=tmp_path.resolve())
