"""Public entrypoint tests for ``FlextInfraDocAuditor.main``."""

from __future__ import annotations

from pathlib import Path

from flext_infra import FlextInfraDocAuditor
from tests import u


def test_auditor_main_help_exits_zero() -> None:
    assert FlextInfraDocAuditor.main(["--help"]) == 0


def test_auditor_main_writes_reports_for_selected_project(tmp_path: Path) -> None:
    workspace = u.Infra.Tests.create_docs_workspace(
        tmp_path,
        project_names=("flext-a", "flext-b"),
    )

    assert (
        FlextInfraDocAuditor.main([
            "--workspace",
            str(workspace),
            "--projects",
            "flext-a",
        ])
        == 0
    )
    assert (workspace / ".reports/docs/audit-report.md").exists()
    assert (workspace / "flext-a/.reports/docs/audit-report.md").exists()
    assert not (workspace / "flext-b/.reports/docs/audit-report.md").exists()


def test_auditor_main_strict_failure_returns_one(tmp_path: Path) -> None:
    workspace = u.Infra.Tests.create_docs_workspace(tmp_path)
    (workspace / "docs/README.md").write_text(
        "# Docs\n\n[Broken](missing.md)\n",
        encoding="utf-8",
    )

    assert FlextInfraDocAuditor.main(["--workspace", str(workspace), "--strict"]) == 1
