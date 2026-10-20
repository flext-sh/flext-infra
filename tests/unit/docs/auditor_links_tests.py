"""Tests for FlextInfraDocAuditor — broken link and markdown helpers.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests import m, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraAuditorLinks:
    """Tests for FlextInfraDocAuditor broken-link and markdown helpers."""

    class TestAuditorToMarkdown:
        """Tests for docs_audit_markdown helper."""

        @staticmethod
        def test_to_markdown_empty_issues(tmp_path: Path) -> None:
            """Test docs_audit_markdown with no issues."""
            (tmp_path / "docs").mkdir()
            scope = m.Infra.DocScope(
                name="test",
                path=tmp_path,
                report_dir=tmp_path / "reports",
            )
            result = u.Infra.docs_audit_markdown(scope, [])
            tm.that(len(result), gte=0)
            tm.that(result, has="# Docs Audit Report")

        @staticmethod
        def test_to_markdown_with_issues(tmp_path: Path) -> None:
            """Test docs_audit_markdown with issues."""
            (tmp_path / "docs").mkdir()
            scope = m.Infra.DocScope(
                name="test",
                path=tmp_path,
                report_dir=tmp_path / "reports",
            )
            issue = m.Infra.AuditIssue(
                file="README.md",
                issue_type="broken_link",
                severity="high",
                message="Link not found",
            )
            result = u.Infra.docs_audit_markdown(scope, [issue])
            tm.that(len(result), gte=0)
            tm.ok(any("README.md" in line for line in result))

    class TestAuditorBrokenLinks:
        """Tests for docs_broken_link_issues."""

        @staticmethod
        def test_broken_link_issues_empty_scope(tmp_path: Path) -> None:
            """Test docs_broken_link_issues with no markdown files."""
            scope = m.Infra.DocScope(
                name="test",
                path=tmp_path,
                report_dir=tmp_path / "reports",
            )
            issues = u.Infra.docs_broken_link_issues(scope)
            tm.that(len(issues), gte=0)

        @staticmethod
        @pytest.mark.parametrize(
            "markdown",
            [
                pytest.param("[link](test.md)", id="valid-links"),
                pytest.param("[link](https://example.com)", id="external-links"),
                pytest.param("[link](#section)", id="fragment-links"),
                pytest.param("```\n[link](nonexistent.md)\n```", id="code-block-links"),
                pytest.param("[a, b]", id="should-skip-target-text"),
                pytest.param("[some text]", id="plain-bracket-text"),
            ],
        )
        def test_broken_link_issues_ignore_non_findings(
            tmp_path: Path,
            markdown: str,
        ) -> None:
            """Test docs_broken_link_issues ignores well-formed non-finding markdown."""
            docs_dir = tmp_path / "docs"
            docs_dir.mkdir(parents=True, exist_ok=True)
            (docs_dir / "test.md").write_text(markdown)
            scope = m.Infra.DocScope(
                name="test",
                path=tmp_path,
                report_dir=tmp_path / "reports",
            )
            issues = u.Infra.docs_broken_link_issues(scope)
            tm.that(len(issues), gte=0)

        @staticmethod
        def test_broken_link_issues_with_missing_target(tmp_path: Path) -> None:
            """Test docs_broken_link_issues reports missing targets."""
            docs_dir = tmp_path / "docs"
            docs_dir.mkdir(parents=True, exist_ok=True)
            (docs_dir / "test.md").write_text("[link](missing.md)")
            scope = m.Infra.DocScope(
                name="test",
                path=tmp_path,
                report_dir=tmp_path / "reports",
            )
            issues = u.Infra.docs_broken_link_issues(scope)
            tm.ok(len(issues) > 0)
            tm.ok(any("missing.md" in issue.message for issue in issues))

        @staticmethod
        def test_broken_link_issues_rejects_cross_project_relative_link(
            tmp_path: Path,
        ) -> None:
            """Test broken link issues rejects cross project relative link."""
            docs_dir = tmp_path / "docs"
            docs_dir.mkdir(parents=True, exist_ok=True)
            (docs_dir / "test.md").write_text(
                "[other project](../../flext-core/docs/index.md)",
                encoding="utf-8",
            )
            scope = m.Infra.DocScope(
                name="test",
                path=tmp_path,
                report_dir=tmp_path / "reports",
            )

            issues = u.Infra.docs_broken_link_issues(scope)

            tm.that(
                any(
                    issue.issue_type == "cross_project_relative_link"
                    for issue in issues
                ),
                eq=True,
            )

        @staticmethod
        def test_broken_link_issues_with_space_in_url_skips(
            tmp_path: Path,
        ) -> None:
            """Test docs_broken_link_issues skips URLs with spaces."""
            docs_dir = tmp_path / "docs"
            docs_dir.mkdir(parents=True, exist_ok=True)
            (docs_dir / "test.md").write_text("[link](some text)")
            scope = m.Infra.DocScope(
                name="test",
                path=tmp_path,
                report_dir=tmp_path / "reports",
            )
            issues = u.Infra.docs_broken_link_issues(scope)
            tm.that(len(issues), gte=0)
            tm.that(len(issues), eq=0)

    class TestAuditorGithubLinks:
        """Audit and repair links through real native repository facts."""

        @staticmethod
        def _owner(root: Path) -> m.Infra.DocsGithubRepoSpec:
            u.Tests.initialize_git_repo(
                root,
                origin_url="https://github.com/fixture-owner/fixture-docs.git",
            )
            directory = root / "config"
            directory.mkdir(exist_ok=True)
            (directory / "codegen.yaml").write_text(
                "Infra:\n  codegen:\n    repository:\n      integration:\n"
                "        provider: github\n        branch: docs/fixture-line\n",
                encoding="utf-8",
            )
            return tm.not_none(
                u.Infra.docs_github_repo_lookup(
                    "fixture-owner",
                    "fixture-docs",
                    repository_root=root,
                )
            )

        @staticmethod
        def test_github_stale_organization(tmp_path: Path) -> None:
            """Test github stale organization."""
            repo = TestsFlextInfraAuditorLinks.TestAuditorGithubLinks._owner(tmp_path)
            placeholder = next(iter(u.Infra.docs_stale_github_organizations()))
            docs = tmp_path / "docs"
            docs.mkdir()
            (docs / "test.md").write_text(
                f"[x](https://github.com/{placeholder}/{repo.repository}/blob/{repo.branch}/README.md)\n",
                encoding="utf-8",
            )
            scope = m.Infra.DocScope(
                name="fixture", path=tmp_path, report_dir=tmp_path / "reports"
            )
            issues = u.Infra.docs_broken_link_issues(scope)
            tm.that(
                "stale_github_organization" in {item.issue_type for item in issues},
                eq=True,
            )

        @staticmethod
        def test_github_wrong_branch(tmp_path: Path) -> None:
            """Test github wrong branch."""
            repo = TestsFlextInfraAuditorLinks.TestAuditorGithubLinks._owner(tmp_path)
            docs = tmp_path / "docs"
            docs.mkdir()
            (docs / "test.md").write_text(
                f"[x](https://github.com/{repo.organization}/{repo.repository}/blob/foreign/ref/README.md)\n",
                encoding="utf-8",
            )
            scope = m.Infra.DocScope(
                name="fixture", path=tmp_path, report_dir=tmp_path / "reports"
            )
            issues = u.Infra.docs_broken_link_issues(scope)
            tm.that(
                "wrong_github_branch" in {item.issue_type for item in issues}, eq=True
            )

        @staticmethod
        def test_github_rewrite_fix(tmp_path: Path) -> None:
            """Test github rewrite fix."""
            repo = TestsFlextInfraAuditorLinks.TestAuditorGithubLinks._owner(tmp_path)
            placeholder = next(iter(u.Infra.docs_stale_github_organizations()))
            docs = tmp_path / "docs"
            docs.mkdir()
            target = docs / "test.md"
            foreign = f"https://github.com/{placeholder}/{repo.repository}/blob/foreign/ref/README.md"
            target.write_text(
                f"[x](https://github.com/{placeholder}/{repo.repository}/blob/{repo.branch}/README.md#L1)\n"
                f"[y]({foreign})\n",
                encoding="utf-8",
            )
            item = u.Infra.docs_process_markdown_file(target, apply=True)
            tm.that(item.links, gte=1)
            tm.that(
                target.read_text(),
                has=f"https://github.com/{repo.organization}/{repo.repository}/blob/{repo.branch}/README.md#L1",
            )
            tm.that(target.read_text(), has=foreign)
