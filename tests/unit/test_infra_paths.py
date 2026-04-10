"""Tests for public workspace path resolution."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import FlextInfraUtilitiesPaths


class TestFlextInfraPathResolver:
    """Verify workspace path resolution through the public utility."""

    def test_workspace_root_with_current_directory(self) -> None:
        resolver = FlextInfraUtilitiesPaths()
        result = resolver.workspace_root(".")
        tm.ok(result)
        tm.that(isinstance(result.value, Path), eq=True)
        tm.that(result.value.is_absolute(), eq=True)

    def test_workspace_root_with_absolute_path(self, tmp_path: Path) -> None:
        resolver = FlextInfraUtilitiesPaths()
        result = resolver.workspace_root(str(tmp_path))
        tm.ok(result)
        tm.that(isinstance(result.value, Path), eq=True)
        tm.that(result.value.is_absolute(), eq=True)

    def test_workspace_root_with_path_object(self, tmp_path: Path) -> None:
        resolver = FlextInfraUtilitiesPaths()
        result = resolver.workspace_root(tmp_path)
        tm.ok(result)
        tm.that(isinstance(result.value, Path), eq=True)
        tm.that(result.value, eq=tmp_path.resolve())

    def test_workspace_root_invalid_path(self) -> None:
        resolver = FlextInfraUtilitiesPaths()
        result = resolver.workspace_root("/nonexistent/path/that/does/not/exist")
        tm.ok(result)

    def test_workspace_root_with_invalid_string_path(self) -> None:
        resolver = FlextInfraUtilitiesPaths()
        result = resolver.workspace_root("\0")
        tm.fail(result)
        tm.that(isinstance(result.error, str), eq=True)
        tm.that("failed to resolve" in (result.error or "").lower(), eq=True)
