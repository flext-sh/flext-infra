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

    assert result.is_success
    assert [scope.name for scope in result.value] == ["root", "flext-a"]


def test_build_scopes_without_filter_still_returns_root_scope(tmp_path: Path) -> None:
    workspace = u.Infra.Tests.create_docs_workspace(tmp_path)

    result = u.Infra.build_scopes(
        workspace,
        projects=None,
        output_dir=c.Infra.DEFAULT_DOCS_OUTPUT_DIR,
    )

    assert result.is_success
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

    assert result.is_success
    assert result.value[0].report_dir == workspace / ".custom-docs"
    assert result.value[1].report_dir == workspace / "flext-a/.custom-docs"


def test_build_scopes_skips_missing_projects(tmp_path: Path) -> None:
    workspace = u.Infra.Tests.create_docs_workspace(tmp_path)

    result = u.Infra.build_scopes(
        workspace,
        projects=["flext-missing"],
        output_dir=c.Infra.DEFAULT_DOCS_OUTPUT_DIR,
    )

    assert result.is_success
    assert [scope.name for scope in result.value] == ["root"]
