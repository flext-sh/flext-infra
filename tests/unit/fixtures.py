"""Pytest fixtures for FLEXT infra tests.

Provides reusable fixtures for creating real project structures using tmp_path.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests import c, m, t, u

_FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


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
    assert parsed.success
    return parsed.value


@pytest.fixture
def tool_config_document() -> m.Infra.ToolConfigDocument:
    return u.Infra.Tests.tool_config_document()


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
    (workspace / c.Infra.PYPROJECT_FILENAME).write_text(
        _modernizer_workspace_pyproject(),
        encoding="utf-8",
    )
    return workspace


@pytest.fixture
def modernizer_workspace_with_projects(modernizer_workspace: Path) -> Path:
    (modernizer_workspace / c.Infra.PYPROJECT_FILENAME).write_text(
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


@pytest.fixture
def rope_workspace(
    tmp_path: Path,
) -> t.Pair[t.Infra.RopeProject, Path]:
    """Create a real rope workspace with semantic-analysis fixtures."""
    workspace_root = tmp_path / "rope_workspace"
    package_root = workspace_root / "src" / "rope_demo"
    package_root.mkdir(parents=True, exist_ok=True)
    (package_root / "__init__.py").write_text("", encoding="utf-8")
    (package_root / "models.py").write_text(
        "from pathlib import Path\n\n"
        "class Animal:\n"
        "    pass\n\n"
        "class Dog(Animal):\n"
        "    home = Path('kennel')\n\n"
        "    @staticmethod\n"
        "    def fetch() -> str:\n"
        "        return 'ball'\n\n"
        "    @classmethod\n"
        "    def breed(cls) -> str:\n"
        "        return cls.__name__\n\n"
        "    def _wag(self) -> str:\n"
        "        return 'wag'\n",
        encoding="utf-8",
    )
    (package_root / "services.py").write_text(
        "from rope_demo.models import Dog\n\n"
        "class Kennel:\n"
        "    def adopt(self) -> Dog:\n"
        "        return Dog()\n",
        encoding="utf-8",
    )

    rope_project = u.Infra.init_rope_project(workspace_root, project_prefix="__never__")
    return rope_project, workspace_root


@pytest.fixture
def models_resource(
    rope_workspace: t.Pair[t.Infra.RopeProject, Path],
) -> t.Infra.RopeResource:
    """Return the Rope resource for the semantic models fixture module."""
    rope_project, workspace_root = rope_workspace
    resource = u.Infra.get_resource_from_path(
        rope_project,
        workspace_root / "src" / "rope_demo" / "models.py",
    )
    assert resource is not None
    return resource


@pytest.fixture
def services_resource(
    rope_workspace: t.Pair[t.Infra.RopeProject, Path],
) -> t.Infra.RopeResource:
    """Return the Rope resource for the semantic services fixture module."""
    rope_project, workspace_root = rope_workspace
    resource = u.Infra.get_resource_from_path(
        rope_project,
        workspace_root / "src" / "rope_demo" / "services.py",
    )
    assert resource is not None
    return resource


__all__: list[str] = [
    "deptry_report_payload",
    "models_resource",
    "modernizer_workspace",
    "modernizer_workspace_with_projects",
    "real_docs_project",
    "real_makefile_project",
    "real_python_package",
    "real_toml_project",
    "real_workspace",
    "rope_workspace",
    "services_resource",
    "tool_config_document",
]
