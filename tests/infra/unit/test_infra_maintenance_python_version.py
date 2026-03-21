"""Tests for FlextInfraPythonVersionEnforcer.

Tests Python version enforcement with real pyproject.toml and tmp_path.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import override

import pytest
from flext_tests import u

from flext_infra.workspace.maintenance.python_version import (
    FlextInfraPythonVersionEnforcer,
)

_MINOR: int = sys.version_info.minor
_BAD: int = _MINOR + 1


def _ws(root: Path, *, minor: int = _MINOR) -> Path:
    """Create workspace root with required markers."""
    root.mkdir(exist_ok=True)
    (root / ".git").mkdir(exist_ok=True)
    (root / "Makefile").touch()
    (root / "pyproject.toml").write_text(
        f'requires-python = ">=3.{minor}"\n',
        encoding="utf-8",
    )
    return root


def _proj(root: Path, name: str, *, minor: int = _MINOR) -> Path:
    """Create a sub-project inside workspace."""
    proj = root / name
    proj.mkdir(exist_ok=True)
    (proj / ".git").mkdir(exist_ok=True)
    (proj / "Makefile").touch()
    (proj / "src").mkdir(exist_ok=True)
    (proj / "pyproject.toml").write_text(
        f'requires-python = ">=3.{minor}"\n',
        encoding="utf-8",
    )
    return proj


def _svc(ws: Path) -> FlextInfraPythonVersionEnforcer:
    """Create enforcer bound to given workspace."""

    class _TestEnforcer(FlextInfraPythonVersionEnforcer):
        @override
        def _workspace_root_from_file(self, file: str | Path) -> Path:
            _ = file
            return ws

    return _TestEnforcer()


class TestEnforcerExecute:
    """Tests for execute() with real workspace structures."""

    def test_check_only_success(self, tmp_path: Path) -> None:
        u.Tests.Matchers.ok(
            _svc(_ws(tmp_path / "ws")).execute(check_only=True, verbose=False), eq=0
        )

    def test_enforce_mode(self, tmp_path: Path) -> None:
        u.Tests.Matchers.ok(
            _svc(_ws(tmp_path / "ws")).execute(check_only=False, verbose=False), eq=0
        )

    def test_verbose_mode(self, tmp_path: Path) -> None:
        svc = _svc(_ws(tmp_path / "ws"))
        u.Tests.Matchers.ok(svc.execute(check_only=True, verbose=True))
        u.Tests.Matchers.that(svc.verbose, eq=True)

    def test_failure_on_workspace_mismatch(self, tmp_path: Path) -> None:
        u.Tests.Matchers.fail(
            _svc(_ws(tmp_path / "ws", minor=_BAD)).execute(check_only=True)
        )

    def test_failure_on_project_mismatch(self, tmp_path: Path) -> None:
        ws = _ws(tmp_path / "ws")
        _proj(ws, "project-a", minor=_BAD)
        u.Tests.Matchers.fail(_svc(ws).execute(check_only=True, verbose=False))

    def test_empty_workspace(self, tmp_path: Path) -> None:
        u.Tests.Matchers.ok(_svc(_ws(tmp_path / "ws")).execute(check_only=True))


class TestReadRequiredMinor:
    """Tests for _read_required_minor()."""

    @pytest.fixture
    def enforcer(self) -> FlextInfraPythonVersionEnforcer:
        return FlextInfraPythonVersionEnforcer()

    def test_from_pyproject(
        self,
        enforcer: FlextInfraPythonVersionEnforcer,
        tmp_path: Path,
    ) -> None:
        ws = _ws(tmp_path / "ws")
        u.Tests.Matchers.that(enforcer._read_required_minor(ws), eq=_MINOR)

    def test_fallback_to_13(
        self,
        enforcer: FlextInfraPythonVersionEnforcer,
        tmp_path: Path,
    ) -> None:
        d = tmp_path / "empty"
        d.mkdir()
        u.Tests.Matchers.that(enforcer._read_required_minor(d), eq=13)

    def test_malformed_pyproject(
        self,
        enforcer: FlextInfraPythonVersionEnforcer,
        tmp_path: Path,
    ) -> None:
        d = tmp_path / "bad"
        d.mkdir()
        (d / "pyproject.toml").write_text("# No field\n", encoding="utf-8")
        u.Tests.Matchers.that(enforcer._read_required_minor(d), eq=13)


class TestWorkspaceRoot:
    """Tests for _workspace_root_from_file()."""

    @pytest.fixture
    def enforcer(self) -> FlextInfraPythonVersionEnforcer:
        return FlextInfraPythonVersionEnforcer()

    def test_success(
        self,
        enforcer: FlextInfraPythonVersionEnforcer,
        tmp_path: Path,
    ) -> None:
        ws = _ws(tmp_path / "ws")
        f = ws / "src" / "module.py"
        f.parent.mkdir(parents=True)
        f.touch()
        resolved = enforcer._workspace_root_from_file(f)
        u.Tests.Matchers.that(str(resolved.resolve()), eq=str(ws.resolve()))

    def test_not_found(
        self,
        enforcer: FlextInfraPythonVersionEnforcer,
        tmp_path: Path,
    ) -> None:
        f = tmp_path / "orphan.py"
        f.touch()
        with pytest.raises(RuntimeError, match="workspace root not found"):
            enforcer._workspace_root_from_file(f)


class TestEnsurePythonVersionFile:
    """Tests for _ensure_python_version_file()."""

    @pytest.fixture
    def enforcer(self) -> FlextInfraPythonVersionEnforcer:
        return FlextInfraPythonVersionEnforcer()

    def test_mismatch_check_mode(
        self,
        enforcer: FlextInfraPythonVersionEnforcer,
        tmp_path: Path,
    ) -> None:
        p = tmp_path / "proj"
        p.mkdir()
        (p / "pyproject.toml").write_text(
            f'requires-python = ">=3.{_BAD}"\n',
            encoding="utf-8",
        )
        enforcer.check_only = True
        u.Tests.Matchers.that(
            enforcer._ensure_python_version_file(p, required_minor=_MINOR),
            eq=False,
        )

    def test_match(
        self,
        enforcer: FlextInfraPythonVersionEnforcer,
        tmp_path: Path,
    ) -> None:
        p = tmp_path / "proj"
        p.mkdir()
        (p / "pyproject.toml").write_text(
            f'requires-python = ">=3.{_MINOR}"\n',
            encoding="utf-8",
        )
        enforcer.check_only = True
        enforcer.verbose = False
        u.Tests.Matchers.that(
            enforcer._ensure_python_version_file(p, required_minor=_MINOR), eq=True
        )

    def test_enforce_mode_mismatch(
        self,
        enforcer: FlextInfraPythonVersionEnforcer,
        tmp_path: Path,
    ) -> None:
        p = tmp_path / "proj"
        p.mkdir()
        (p / "pyproject.toml").write_text(
            f'requires-python = ">=3.{_BAD}"\n',
            encoding="utf-8",
        )
        enforcer.check_only = False
        u.Tests.Matchers.that(
            enforcer._ensure_python_version_file(p, required_minor=_MINOR),
            eq=False,
        )


class TestDiscoverProjects:
    """Tests for _discover_projects()."""

    def test_empty_dir_returns_empty(self, tmp_path: Path) -> None:
        d = tmp_path / "empty"
        d.mkdir()
        enforcer = FlextInfraPythonVersionEnforcer()
        u.Tests.Matchers.that(enforcer._discover_projects(d), eq=[])
