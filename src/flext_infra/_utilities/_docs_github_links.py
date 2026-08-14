"""GitHub cross-repo doc URL policy for the flext-infra docs engine.

Resolves governed org/repo/ref maps from the repository artifact catalog and
rewrites stale placeholder organizations / wrong working-line branches.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra import config, m, t
from flext_infra._utilities.repository import FlextInfraUtilitiesRepository


class FlextInfraUtilitiesDocsGithubLinks:
    """Governed GitHub URL helpers for docs audit and fix."""

    @staticmethod
    def docs_github_repos() -> tuple[m.Infra.RepositoryArtifactAuthoritySpec, ...]:
        """Return the typed GitHub repo map from make.docs SSOT."""
        return config.Infra.codegen.repository_artifact_authorities

    @staticmethod
    def docs_stale_github_organizations() -> frozenset[str]:
        """Placeholder organizations that must not appear in doc URLs."""
        return frozenset(config.Infra.codegen.make.docs.stale_github_organizations)

    @staticmethod
    def docs_github_repo_lookup(
        organization: str, repository: str
    ) -> m.Infra.RepositoryArtifactAuthoritySpec | None:
        """Find one governed repo by organization and repository name."""
        for repo in FlextInfraUtilitiesDocsGithubLinks.docs_github_repos():
            if repo.organization == organization and repo.repository == repository:
                return repo
        return None

    @staticmethod
    def docs_artifact_authorities() -> tuple[m.Infra.RepositoryArtifactAuthority, ...]:
        """Return explicit configured documentation artifact authorities."""
        return tuple(
            m.Infra.RepositoryArtifactAuthority(
                host="github.com",
                organization=repo.organization,
                repository=repo.repository,
                ref=repo.ref,
            )
            for repo in FlextInfraUtilitiesDocsGithubLinks.docs_github_repos()
        )

    @staticmethod
    def docs_canonical_github_url(
        organization: str, repository: str, path: str, *, is_dir: bool = False
    ) -> str | None:
        """Build a canonical GitHub URL for a governed repository path."""
        repo = FlextInfraUtilitiesDocsGithubLinks.docs_github_repo_lookup(
            organization, repository
        )
        if repo is None:
            return None
        if path.startswith(("/", "\\")):
            return None
        normalized_path = path.rstrip("/")
        if not normalized_path:
            return None
        try:
            reference = m.Infra.RepositoryArtifactReference(
                authority=m.Infra.RepositoryArtifactAuthority(
                    host="github.com",
                    organization=repo.organization,
                    repository=repo.repository,
                    ref=repo.ref,
                ),
                kind=(
                    m.Infra.RepositoryArtifactKind.TREE
                    if is_dir
                    else m.Infra.RepositoryArtifactKind.BLOB
                ),
                path=normalized_path,
            )
        except ValueError:
            return None
        built = FlextInfraUtilitiesRepository.repository_artifact_parse(
            FlextInfraUtilitiesRepository.repository_artifact_url(reference),
            (reference.authority,),
        )
        return (
            FlextInfraUtilitiesRepository.repository_artifact_url(built.value)
            if built.success
            else None
        )

    @staticmethod
    def docs_rewrite_github_url(target: str) -> str | None:
        """Return the canonical equivalent when one configured URL is noncanonical."""
        authorities = FlextInfraUtilitiesDocsGithubLinks.docs_artifact_authorities()
        parsed = FlextInfraUtilitiesRepository.repository_artifact_parse(
            target, authorities
        )
        if parsed.success:
            canonical = FlextInfraUtilitiesRepository.repository_artifact_url(
                parsed.value
            )
            return canonical if canonical != target else None
        return None

    @staticmethod
    def docs_github_link_issues(
        *, file: str, line_number: int, raw: str, target: str
    ) -> t.SequenceOf[m.Infra.AuditIssue]:
        """Emit audit issues for unconfigured or non-canonical GitHub doc URLs."""
        if not target.startswith("https://github.com/"):
            return ()
        parsed = FlextInfraUtilitiesRepository.repository_artifact_parse(
            target, FlextInfraUtilitiesDocsGithubLinks.docs_artifact_authorities()
        )
        if parsed.success:
            return ()
        return (
            m.Infra.AuditIssue(
                file=file,
                issue_type="invalid_github_artifact_reference",
                severity="high",
                message=f"line {line_number}: {parsed.error} -> {raw}",
            ),
        )


__all__: list[str] = ["FlextInfraUtilitiesDocsGithubLinks"]
