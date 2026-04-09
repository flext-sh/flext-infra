"""Tests for FlextInfraPathResolver.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import FlextInfraUtilitiesPaths


class TestFlextInfraPathResolver:
    """Test suite for FlextInfraPathResolver."""

    def test_workspace_root_with_current_directory(self) -> None:
        """Test resolving workspace root from current directory."""
        resolver = FlextInfraUtilitiesPaths()
        result = resolver.workspace_root(".")
        tm.ok(result)
        assert isinstance(result.value, Path)
        assert result.value.is_absolute()

    def test_workspace_root_with_absolute_path(self, tmp_path: Path) -> None:
        """Test resolving workspace root with absolute path."""
        resolver = FlextInfraUtilitiesPaths()
        result = resolver.workspace_root(str(tmp_path))
        tm.ok(result)
        assert isinstance(result.value, Path)
        assert result.value.is_absolute()

    def test_workspace_root_with_path_object(self, tmp_path: Path) -> None:
        """Test resolving workspace root with Path t.NormalizedValue."""
        resolver = FlextInfraUtilitiesPaths()
        result = resolver.workspace_root(tmp_path)
        tm.ok(result)
        assert isinstance(result.value, Path)
        assert result.value == tmp_path.resolve()

    def test_workspace_root_invalid_path(self) -> None:
        """Test workspace root resolution with invalid path."""
        resolver = FlextInfraUtilitiesPaths()
        result = resolver.workspace_root("/nonexistent/path/that/does/not/exist")
        tm.ok(result)

    def test_workspace_root_with_resolve_type_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        resolver = FlextInfraUtilitiesPaths()

        def _raise_type_error(self: Path, strict: bool | None = None) -> Path:
            _ = self
            _ = strict
            msg = "invalid path type"
            raise TypeError(msg)

        result = resolver.workspace_root(".")
        tm.fail(result)
        assert isinstance(result.error, str)
        assert "failed to resolve" in result.error.lower()
