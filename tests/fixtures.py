"""Pytest fixtures for FLEXT infra tests.

Provides reusable fixtures for creating real project structures using tmp_path.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests import c, t, u

_FIXTURES_DIR = Path(__file__).with_name("fixtures")


def _read_fixture(*parts: str) -> str:
    return _FIXTURES_DIR.joinpath(*parts).read_text(encoding="utf-8")


def _modernizer_pyproject(name: str) -> str:
    return f'[project]\nname = "{name}"\nversion = "0.1.0"\n'


def _modernizer_workspace_pyproject(*members: str) -> str:
    base = _modernizer_pyproject("workspace")
    if not members:
        return base
    members_text = ", ".join(f'"{member}"' for member in members)
    return f"{base}\n[tool.uv.workspace]\nmembers = [{members_text}]\n"


@pytest.fixture
def deptry_report_payload() -> t.Cli.JsonPayload:
    parsed = u.Cli.json_parse(_read_fixture("deps", "deptry_report.json"))
    assert parsed is not None
    assert parsed.is_success
    return parsed.value


@pytest.fixture
def real_toml_project(tmp_path: Path) -> Path:
    """Create a real project with valid pyproject.toml."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    pyproject_content = """\
[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"

[project]
name = "test-project"
version = "0.1.0"
description = "Test project"
authors = [{name = "Test", email = "test@example.com"}]
"""
    (project_root / "pyproject.toml").write_text(pyproject_content)
    return project_root


@pytest.fixture
def real_makefile_project(tmp_path: Path) -> Path:
    """Create a real project with valid Makefile."""
    project_root = tmp_path / "makefile_project"
    project_root.mkdir()
    makefile_content = """\
.PHONY: help setup check test

help:
\t@echo "Available targets"

setup:
\t@echo "Setting up"

check:
\t@echo "Checking"

test:
\t@echo "Testing"
"""
    (project_root / "Makefile").write_text(makefile_content)
    return project_root


@pytest.fixture
def real_python_package(tmp_path: Path) -> Path:
    """Create a real Python package with src layout."""
    project_root = tmp_path / "python_package"
    project_root.mkdir()
    src_dir = project_root / "src" / "test_pkg"
    src_dir.mkdir(parents=True)
    (src_dir / "__init__.py").write_text('"""Test package."""\n__version__ = "0.1.0"\n')
    (project_root / "pyproject.toml").write_text(
        '[project]\nname = "test-pkg"\nversion = "0.1.0"\n',
    )
    return project_root


@pytest.fixture
def real_workspace(tmp_path: Path) -> Path:
    """Create a real multi-project workspace."""
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    (workspace_root / "Makefile").write_text(
        ".PHONY: help\nhelp:\n\t@echo 'Workspace'\n",
    )
    (workspace_root / "pyproject.toml").write_text(
        '[project]\nname = "workspace"\nversion = "0.1.0"\n',
    )
    for i in range(1, 4):
        project_dir = workspace_root / f"project_{i}"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").write_text(
            f'[project]\nname = "project-{i}"\nversion = "0.1.0"\n',
        )
        src_dir = project_dir / "src" / f"project_{i}"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text(f'"""Project {i}."""\n')
    return workspace_root


@pytest.fixture
def modernizer_workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / c.Infra.Files.PYPROJECT_FILENAME).write_text(
        _modernizer_workspace_pyproject(),
        encoding="utf-8",
    )
    return workspace


@pytest.fixture
def modernizer_workspace_with_projects(modernizer_workspace: Path) -> Path:
    (modernizer_workspace / c.Infra.Files.PYPROJECT_FILENAME).write_text(
        _modernizer_workspace_pyproject("selected", "ignored"),
        encoding="utf-8",
    )
    _ = u.Infra.Tests.mk_project(
        modernizer_workspace,
        "selected",
        pyproject=_modernizer_pyproject("selected"),
    )
    _ = u.Infra.Tests.mk_project(
        modernizer_workspace,
        "ignored",
        pyproject=_modernizer_pyproject("ignored"),
    )
    return modernizer_workspace


@pytest.fixture
def real_docs_project(tmp_path: Path) -> Path:
    """Create a real project with documentation."""
    project_root = tmp_path / "docs_project"
    project_root.mkdir()
    docs_dir = project_root / "docs"
    docs_dir.mkdir()
    (docs_dir / "README.md").write_text("# Documentation\n")
    (docs_dir / "index.md").write_text("# Index\n")
    (project_root / "README.md").write_text("# Project\n")
    (project_root / "pyproject.toml").write_text(
        '[project]\nname = "docs-project"\nversion = "0.1.0"\n',
    )
    return project_root


__all__ = [
    "deptry_report_payload",
    "modernizer_workspace",
    "modernizer_workspace_with_projects",
    "real_docs_project",
    "real_makefile_project",
    "real_python_package",
    "real_toml_project",
    "real_workspace",
]
