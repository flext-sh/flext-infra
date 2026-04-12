"""Public tests for docs scope utilities."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests import c, m, u


def test_doc_scope_creation(tmp_path: Path) -> None:
    report_dir = tmp_path / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    scope = m.Infra.DocScope(
        name="flext-a",
        path=tmp_path,
        report_dir=report_dir,
    )

    assert scope.name == "flext-a"
    assert scope.path == tmp_path
    assert scope.report_dir == report_dir


def test_doc_scope_requires_name(tmp_path: Path) -> None:
    report_dir = tmp_path / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    with pytest.raises(Exception):
        m.Infra.DocScope(name="", path=tmp_path, report_dir=report_dir)


def test_build_scopes_returns_root_and_selected_projects(tmp_path: Path) -> None:
    workspace = u.Infra.Tests.create_docs_workspace(
        tmp_path,
        project_names=("flext-a", "flext-b"),
    )

    result = u.Infra.build_scopes(
        workspace,
        projects=["flext-a"],
        output_dir=c.Infra.DEFAULT_DOCS_OUTPUT_DIR,
    )

    assert result.success
    assert [scope.name for scope in result.value] == ["root", "flext-a"]


def test_build_scopes_without_filter_still_returns_root_scope(tmp_path: Path) -> None:
    workspace = u.Infra.Tests.create_docs_workspace(tmp_path)

    result = u.Infra.build_scopes(
        workspace,
        projects=None,
        output_dir=c.Infra.DEFAULT_DOCS_OUTPUT_DIR,
    )

    assert result.success
    assert [scope.name for scope in result.value] == ["root"]


def test_build_scopes_uses_custom_output_dir(tmp_path: Path) -> None:
    workspace = u.Infra.Tests.create_docs_workspace(
        tmp_path,
        project_names=("flext-a",),
    )

    result = u.Infra.build_scopes(
        workspace,
        projects=["flext-a"],
        output_dir=".custom-docs",
    )

    assert result.success
    assert result.value[0].report_dir == workspace / ".custom-docs"
    assert result.value[1].report_dir == workspace / "flext-a/.custom-docs"


def test_build_scopes_skips_missing_projects(tmp_path: Path) -> None:
    workspace = u.Infra.Tests.create_docs_workspace(tmp_path)

    result = u.Infra.build_scopes(
        workspace,
        projects=["flext-missing"],
        output_dir=c.Infra.DEFAULT_DOCS_OUTPUT_DIR,
    )

    assert result.success
    assert [scope.name for scope in result.value] == ["root"]


def test_build_scopes_preserves_discovered_package_name(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    project_root = workspace / "flext-demo"
    package_root = project_root / "src" / "demo_pkg"
    package_root.mkdir(parents=True)
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "pyproject.toml").write_text(
        "[project]\nname='workspace'\n",
        encoding="utf-8",
    )
    (package_root / "__init__.py").write_text("", encoding="utf-8")
    (project_root / "pyproject.toml").write_text(
        "[project]\n"
        "name='flext-demo'\n"
        "dependencies=['flext-core>=0.1.0']\n\n"
        "[tool.hatch.build.targets.wheel]\n"
        "packages=['src/demo_pkg']\n",
        encoding="utf-8",
    )

    result = u.Infra.build_scopes(
        workspace,
        projects=["flext-demo"],
        output_dir=c.Infra.DEFAULT_DOCS_OUTPUT_DIR,
    )

    assert result.success
    assert len(result.value) == 2
    assert result.value[1].package_name == "demo_pkg"
