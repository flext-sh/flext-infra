"""Public CLI routing tests for docs commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flext_infra import docs_main, main as infra_main
from tests import u
from flext_tests import tm

if TYPE_CHECKING:
    from pathlib import Path


def _workspace(tmp_path: Path, *, fixable: bool = False) -> Path:
    workspace: Path = u.Tests.create_docs_workspace(
        tmp_path, project_names=("flext-a", "flext-b"), include_fixable_link=fixable
    )
    return workspace


def test_docs_cli_requires_subcommand() -> None:
    tm.that(infra_main(["docs"]), eq=1)


@pytest.mark.parametrize(
    "argv",
    [
        ["docs", "--help"],
        ["docs", "audit", "--help"],
        ["docs", "build", "--help"],
        ["docs", "fix", "--help"],
        ["docs", "generate", "--help"],
        ["docs", "serve", "--help"],
        ["docs", "validate", "--help"],
    ],
)
def test_docs_cli_help_routes(argv: list[str]) -> None:
    tm.that(infra_main(argv), eq=0)


def test_flext_docs_entrypoint_routes_through_docs_group() -> None:
    # NOTE (multi-agent): S0 motor entrypoint — proves `flext-docs` == `flext-infra docs`
    # via the package-root lazy export (mro-3o9s).
    tm.that(docs_main(["--help"]), eq=0)
    tm.that(docs_main(["audit", "--help"]), eq=0)
    tm.that(docs_main([]), eq=1)


def test_docs_cli_audit_projects_filter_writes_only_selected_reports(
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path)

    assert (
        infra_main([
            "docs",
            "audit",
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


def test_docs_cli_fix_generate_and_build_use_public_routes(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path, fixable=True)

    assert infra_main(["docs", "fix", "--workspace", str(workspace), "--apply"]) == 0
    tm.that((workspace / "docs/README.md").read_text(), has="guides/setup.md")
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
    assert (workspace / ".reports/docs/generate-report.md").exists()
    assert (workspace / "flext-a/.reports/docs/generate-report.md").exists()
    assert not (workspace / "flext-b/.reports/docs/generate-report.md").exists()

    build_workspace = u.Tests.create_docs_workspace(tmp_path / "build-root")
    tm.that(infra_main(["docs", "build", "--workspace", str(build_workspace)]), eq=0)
    assert (build_workspace / ".reports/docs/build-report.md").exists()
