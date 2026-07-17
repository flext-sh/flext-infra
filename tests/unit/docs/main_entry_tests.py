"""Public CLI routing tests for docs commands."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from flext_tests import tm

from flext_infra import docs_main, main as infra_main
from tests import u


class TestsDocsCli:
    """Verify docs commands through their public CLI entry points."""

    @staticmethod
    def _workspace(tmp_path: Path, *, fixable: bool = False) -> Path:
        workspace: Path = u.Tests.create_docs_workspace(
            tmp_path, project_names=("flext-a", "flext-b"), include_fixable_link=fixable
        )
        return workspace

    def test_requires_subcommand(self) -> None:
        """Return the usage exit code when docs has no subcommand."""
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
    def test_help_routes(self, argv: list[str]) -> None:
        """Expose help successfully for every public docs route."""
        tm.that(infra_main(argv), eq=0)

    def test_package_entrypoint_routes_through_docs_group(self) -> None:
        """Route the package entry point through the public docs command group."""
        tm.that(docs_main(["--help"]), eq=0)
        tm.that(docs_main(["audit", "--help"]), eq=0)
        tm.that(docs_main([]), eq=1)

    def test_audit_projects_filter_writes_selected_reports(
        self, tmp_path: Path
    ) -> None:
        """Write audit reports only for explicitly selected projects."""
        workspace = self._workspace(tmp_path)

        tm.that(
            infra_main([
                "docs",
                "audit",
                "--workspace",
                str(workspace),
                "--projects",
                "flext-a",
            ]),
            eq=0,
        )
        tm.that((workspace / ".reports/docs/audit-report.md").exists(), eq=True)
        tm.that((workspace / "flext-a/.reports/docs/audit-report.md").exists(), eq=True)
        tm.that(
            (workspace / "flext-b/.reports/docs/audit-report.md").exists(), eq=False
        )

    def test_fix_generate_and_build_use_public_routes(self, tmp_path: Path) -> None:
        """Run fix, generate, and build through their public command routes."""
        workspace = self._workspace(tmp_path, fixable=True)

        tm.that(
            infra_main(["docs", "fix", "--workspace", str(workspace), "--apply"]), eq=0
        )
        tm.that((workspace / "docs/README.md").read_text(), has="guides/setup.md")
        tm.that(
            infra_main([
                "docs",
                "generate",
                "--workspace",
                str(workspace),
                "--apply",
                "--projects",
                "flext-a",
            ]),
            eq=0,
        )
        tm.that((workspace / ".reports/docs/generate-report.md").exists(), eq=True)
        tm.that(
            (workspace / "flext-a/.reports/docs/generate-report.md").exists(), eq=True
        )
        tm.that(
            (workspace / "flext-b/.reports/docs/generate-report.md").exists(), eq=False
        )

        build_workspace = u.Tests.create_docs_workspace(tmp_path / "build-root")
        tm.that(
            infra_main(["docs", "build", "--workspace", str(build_workspace)]), eq=0
        )
        tm.that((build_workspace / ".reports/docs/build-report.md").exists(), eq=True)
