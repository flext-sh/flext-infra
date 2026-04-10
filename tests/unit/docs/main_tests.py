"""Public validation-flow tests for the docs CLI."""

from __future__ import annotations

from pathlib import Path

from flext_infra import main as infra_main
from tests import u


def test_docs_cli_validate_fails_before_generation(tmp_path: Path) -> None:
    workspace = u.Infra.Tests.create_docs_workspace(
        tmp_path,
        project_names=("flext-a",),
    )

    assert (
        infra_main([
            "docs",
            "validate",
            "--workspace",
            str(workspace),
            "--projects",
            "flext-a",
        ])
        == 1
    )
    assert (workspace / ".reports/docs/validate-report.md").exists()
    assert (workspace / "flext-a/.reports/docs/validate-report.md").exists()


def test_docs_cli_validate_apply_passes_after_generate_apply(tmp_path: Path) -> None:
    workspace = u.Infra.Tests.create_docs_workspace(
        tmp_path,
        project_names=("flext-a",),
    )

    assert (
        infra_main([
            "docs",
            "generate",
            "--workspace",
            str(workspace),
            "--apply",
            "--projects",
            "flext-a",
        ])
        == 0
    )
    assert (
        infra_main([
            "docs",
            "validate",
            "--workspace",
            str(workspace),
            "--apply",
            "--projects",
            "flext-a",
        ])
        == 0
    )
    assert (workspace / ".reports/docs/validate-report.md").exists()
    assert (workspace / "flext-a/.reports/docs/validate-report.md").exists()
    assert (workspace / "flext-a/TODOS.md").exists()
