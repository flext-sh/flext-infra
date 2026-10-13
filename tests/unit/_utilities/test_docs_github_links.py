"""Public documentation URL behavior from real repository declarations.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests import tm, u


@pytest.fixture
def docs_repository(tmp_path: Path) -> Path:
    """Create a real peripheral Git owner with an explicit integration contract.

    Returns:
        The resulting ``Path``.
    """
    root = tmp_path / "docs-owner"
    root.mkdir()
    u.Tests.initialize_git_repo(
        root,
        origin_url="https://github.com/example-owner/root-docs.git",
    )
    directory = root / "config"
    directory.mkdir(exist_ok=True)
    (directory / "codegen.yaml").write_text(
        "Infra:\n  codegen:\n    repository:\n      integration:\n"
        "        provider: github\n        branch: docs/integration\n",
        encoding="utf-8",
    )
    (root / ".gitmodules").write_text(
        '[submodule "peripheral"]\n'
        "  path = components/peripheral\n"
        "  url = https://github.com/second-owner/peripheral-docs.git\n"
        "  branch = docs/member-line\n",
        encoding="utf-8",
    )
    member = root / "components/peripheral"
    member.mkdir(parents=True)
    (root / "README.md").write_text("Root docs\n", encoding="utf-8")
    (member / "README.md").write_text("Member docs\n", encoding="utf-8")
    return root


class TestsFlextInfraUtilitiesDocsGithubLinks:
    """Exercise Git identity, branch rewriting, and local existence evidence."""

    @staticmethod
    def test_gitmodule_admits_member_without_a_catalog(docs_repository: Path) -> None:
        repos = u.Infra.docs_github_repos(docs_repository)
        tm.that(
            {(repo.organization, repo.repository) for repo in repos},
            eq={("example-owner", "root-docs"), ("second-owner", "peripheral-docs")},
        )
        member = tm.not_none(
            u.Infra.docs_github_repo_lookup(
                "second-owner",
                "peripheral-docs",
                repository_root=docs_repository,
            )
        )
        tm.that(member.branch, eq="docs/member-line")
        tm.that(
            Path(member.local_checkout), eq=docs_repository / "components/peripheral"
        )

    @staticmethod
    def test_canonical_link_round_trip_and_missing_path(docs_repository: Path) -> None:
        repo = tm.not_none(
            u.Infra.docs_github_repo_lookup(
                "example-owner",
                "root-docs",
                repository_root=docs_repository,
            )
        )
        target = tm.not_none(
            u.Infra.docs_canonical_github_url(
                repo.organization,
                repo.repository,
                "README.md",
                repository_root=docs_repository,
            )
        )
        tm.that(
            u.Infra.docs_github_local_path(
                target + "#L1",
                repository_root=docs_repository,
            ),
            eq=docs_repository / "README.md",
        )
        tm.that(
            u.Infra.docs_github_link_issues(
                file="consumer.md",
                line_number=1,
                raw=target,
                target=target,
                repository_root=docs_repository,
            ),
            eq=[],
        )
        missing = tm.not_none(
            u.Infra.docs_canonical_github_url(
                repo.organization,
                repo.repository,
                "absent.md",
                repository_root=docs_repository,
            )
        )
        issues = u.Infra.docs_github_link_issues(
            file="consumer.md",
            line_number=2,
            raw=missing,
            target=missing,
            repository_root=docs_repository,
        )
        tm.that({issue.issue_type for issue in issues}, eq={"broken_github_link"})

    @staticmethod
    def test_wrong_branch_rewrite_preserves_fragment(docs_repository: Path) -> None:
        stale = (
            "https://github.com/example-owner/root-docs/blob/foreign/ref/README.md#L1"
        )
        rewritten = u.Infra.docs_rewrite_github_url(
            stale, repository_root=docs_repository
        )
        repo = tm.not_none(
            u.Infra.docs_github_repo_lookup(
                "example-owner",
                "root-docs",
                repository_root=docs_repository,
            )
        )
        tm.that(rewritten, none=True)
        issues = u.Infra.docs_github_link_issues(
            file="consumer.md",
            line_number=3,
            raw=stale,
            target=stale,
            repository_root=docs_repository,
        )
        tm.that({issue.issue_type for issue in issues}, eq={"wrong_github_branch"})

    @staticmethod
    def test_placeholder_rewrite_uses_real_origin_and_keeps_fragment(
        docs_repository: Path,
    ) -> None:
        repo = tm.not_none(
            u.Infra.docs_github_repo_lookup(
                "example-owner",
                "root-docs",
                repository_root=docs_repository,
            )
        )
        placeholder = next(iter(u.Infra.docs_stale_github_organizations()))
        target = f"https://github.com/{placeholder}/{repo.repository}/blob/{repo.branch}/README.md#L1"
        tm.that(
            u.Infra.docs_rewrite_github_url(target, repository_root=docs_repository),
            eq=f"https://github.com/{repo.organization}/{repo.repository}/blob/{repo.branch}/README.md#L1",
        )

    @staticmethod
    def test_foreign_repository_is_not_fabricated(docs_repository: Path) -> None:
        target = "https://github.com/unrelated-owner/unrelated-repo/blob/main/a.md"
        tm.that(
            u.Infra.docs_github_repo_lookup(
                "unrelated-owner",
                "unrelated-repo",
                repository_root=docs_repository,
            ),
            none=True,
        )
        tm.that(
            u.Infra.docs_rewrite_github_url(target, repository_root=docs_repository),
            none=True,
        )
        tm.that(
            u.Infra.docs_github_link_issues(
                file="consumer.md",
                line_number=4,
                raw=target,
                target=target,
                repository_root=docs_repository,
            ),
            eq=[],
        )

    class TestDocsExpandLocalCheckout:
        """Verify local checkout path expansion."""

        @staticmethod
        def test_empty_path_returns_none() -> None:
            tm.that(u.Infra.docs_expand_local_checkout(""), none=True)

        @staticmethod
        def test_whitespace_path_returns_none() -> None:
            tm.that(u.Infra.docs_expand_local_checkout("   "), none=True)

        @staticmethod
        def test_expand_home_path() -> None:
            result = u.Infra.docs_expand_local_checkout("~/flext")
            tm.that(result, eq=Path("~/flext").expanduser())

        @staticmethod
        def test_expand_absolute_path() -> None:
            checkout = Path.home() / "checkout"
            result = u.Infra.docs_expand_local_checkout(str(checkout))
            tm.that(result, eq=checkout)

    class TestDocsParseGithubDocUrl:
        """Verify GitHub blob/tree URL parsing."""

        @staticmethod
        def test_parse_valid_blob_url() -> None:
            match = u.Infra.docs_parse_github_doc_url(
                "https://github.com/flext-sh/flext/blob/main/README.md",
            )
            tm.that(match is not None, eq=True)
            if match is not None:
                tm.that(match.group("org"), eq="flext-sh")
                tm.that(match.group("repo"), eq="flext")
                tm.that(match.group("kind"), eq="blob")
                tm.that(match.group("refpath"), eq="main/README.md")
                tm.that(match.group("suffix"), none=True)

        @staticmethod
        def test_parse_valid_tree_url() -> None:
            match = u.Infra.docs_parse_github_doc_url(
                "https://github.com/example-org/example-repo/tree/feature-line/src/",
            )
            tm.that(match is not None, eq=True)
            if match is not None:
                tm.that(match.group("kind"), eq="tree")
                tm.that(match.group("refpath"), eq="feature-line/src/")

        @staticmethod
        def test_parse_keeps_fragment_out_of_refpath() -> None:
            match = tm.not_none(
                u.Infra.docs_parse_github_doc_url(
                    "https://github.com/flext-sh/flext/blob/main/README.md#L10",
                ),
            )
            tm.that(match.group("refpath"), eq="main/README.md")
            tm.that(match.group("suffix"), eq="#L10")

        @staticmethod
        def test_parse_keeps_slash_ref_in_refpath() -> None:
            match = tm.not_none(
                u.Infra.docs_parse_github_doc_url(
                    "https://github.com/flext-sh/flext/blob/feature/fix/README.md",
                ),
            )
            tm.that(match.group("refpath"), eq="feature/fix/README.md")

        @staticmethod
        def test_parse_non_github_url_returns_none() -> None:
            tm.that(
                u.Infra.docs_parse_github_doc_url("https://example.com/foo/bar"),
                none=True,
            )

        @staticmethod
        def test_parse_invalid_url_returns_none() -> None:
            tm.that(u.Infra.docs_parse_github_doc_url("not a url"), none=True)

        @staticmethod
        def test_parse_strips_surrounding_whitespace() -> None:
            match = u.Infra.docs_parse_github_doc_url(
                "  https://github.com/flext-sh/flext/blob/main/README.md  ",
            )
            tm.that(match is not None, eq=True)
