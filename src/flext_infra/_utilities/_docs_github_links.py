"""GitHub cross-repo doc URL policy for the flext-infra docs engine.

Resolves repository identity and branch facts from native Git declarations.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlsplit

from flext_infra import FlextInfraConfig, c, config, m, t
from flext_infra._utilities.git import FlextInfraUtilitiesGit
from flext_infra._utilities._git.remote import FlextInfraUtilitiesGitRemote
from flext_infra._utilities.repository import FlextInfraUtilitiesRepository
from flext_infra._utilities.project_managed_artifacts import (
    FlextInfraUtilitiesProjectManagedArtifacts,
)

# Concrete-owner imports: this module resolves during the root's lazy ``u``
# export, when the root namespace is still initializing — a root from-import
# would re-enter the partial namespace and fail.


class FlextInfraUtilitiesDocsGithubLinks:
    """Governed GitHub URL helpers for docs audit and fix."""

    @staticmethod
    def _config() -> FlextInfraConfig:

        return config

    @staticmethod
    def docs_github_repos(
        repository_root: Path,
    ) -> t.VariadicTuple[m.Infra.DocsGithubRepoSpec]:
        """Derive typed GitHub repositories from origin and .gitmodules.

        Returns:
            Declared URL, branch and exact local checkout facts.

        """
        root = (
            FlextInfraUtilitiesGit
            .git_repository_root(
                m.Infra.GitRepoRequest(repo_root=repository_root),
            )
            .unwrap()
            .repository_root
        )
        identity = FlextInfraUtilitiesGit.git_identity(
            m.Infra.GitRepoRequest(repo_root=root),
        ).unwrap()
        if identity.superproject_root is not None:
            root = identity.superproject_root
            identity = FlextInfraUtilitiesGit.git_identity(
                m.Infra.GitRepoRequest(repo_root=root),
            ).unwrap()
        inputs = FlextInfraUtilitiesProjectManagedArtifacts.load_codegen_inputs(
            root
        ).unwrap()
        integration = FlextInfraUtilitiesRepository.resolve_integration_branch(
            root,
            policy_branch=inputs.spec.branch_policy.integration_branch,
            inputs=inputs,
        ).unwrap()
        declarations: list[t.Triple[str, str, Path]] = []
        if identity.origin_remote is not None:
            declarations.append(
                (
                    identity.origin_remote,
                    integration,
                    root,
                ),
            )
        members = FlextInfraUtilitiesGit.git_submodule_declarations(
            root,
        ).unwrap()
        for member in members:
            branch = integration if member.branch == "." else member.branch
            if not branch:
                message = f"documentation Git declaration has no branch: {member.path}"
                raise ValueError(message)
            declarations.append((member.url, branch, root / member.path))
        repositories: list[m.Infra.DocsGithubRepoSpec] = []
        for url, branch, checkout in declarations:
            canonical = FlextInfraUtilitiesGitRemote.canonical_origin_remote(url)
            if canonical.startswith("git@github.com:"):
                path = canonical.removeprefix("git@github.com:")
            else:
                parsed = urlsplit(canonical)
                if parsed.hostname != "github.com":
                    continue
                path = parsed.path.strip("/")
            pieces = path.removesuffix(".git").split("/")
            if len(pieces) != 2 or not all(pieces):
                message = (
                    f"GitHub declaration must name one owner and repository: {url}"
                )
                raise ValueError(message)
            organization, repository = pieces
            repositories.append(
                m.Infra.DocsGithubRepoSpec(
                    organization=organization,
                    repository=repository,
                    branch=branch,
                    local_checkout=str(checkout),
                ),
            )
        return tuple(repositories)

    @staticmethod
    def docs_stale_github_organizations() -> frozenset[str]:
        """Placeholder organizations that must not appear in doc URLs.

        Returns:
            The resulting ``frozenset[str]``.

        """
        return frozenset(
            FlextInfraUtilitiesDocsGithubLinks._config().Infra.codegen.make.docs.stale_github_organizations,
        )

    @staticmethod
    def docs_github_repo_lookup(
        organization: str,
        repository: str,
        *,
        repository_root: Path,
    ) -> m.Infra.DocsGithubRepoSpec | None:
        """Find one governed repo by organization and repository name.

        Returns:
            The resulting ``m.Infra.DocsGithubRepoSpec | None``.

        """
        for repo in FlextInfraUtilitiesDocsGithubLinks.docs_github_repos(
            repository_root
        ):
            if repo.organization == organization and repo.repository == repository:
                return repo
        return None

    @staticmethod
    def docs_expand_local_checkout(path: str) -> Path | None:
        """Expand ``~`` local_checkout paths; empty means no local check.

        Returns:
            The resulting ``Path | None``.

        """
        value = path.strip()
        if not value:
            return None
        return Path(value).expanduser()

    @staticmethod
    def docs_parse_github_doc_url(target: str) -> re.Match[str] | None:
        """Parse a github.com blob/tree documentation URL.

        Returns:
            The resulting ``re.Match[str] | None``.

        """
        return c.Infra.DOCS_GITHUB_BLOB_TREE_RE.match(target.strip())

    @staticmethod
    def docs_github_governed_path(refpath: str, branch: str) -> str | None:
        """Return the path after ``branch`` when ``refpath`` starts with it.

        Git refs may contain ``/`` (``feature/fix``), so a URL alone cannot say
        where the ref ends. Only the governed branch is a trusted boundary; any
        other ref is unresolvable and yields ``None``.

        Returns:
            The path after ``branch`` when ``refpath`` starts with it.

        """
        prefix = f"{branch}/"
        if not refpath.startswith(prefix):
            return None
        return refpath[len(prefix) :]

    @staticmethod
    def docs_canonical_github_url(
        organization: str,
        repository: str,
        path: str,
        *,
        is_dir: bool = False,
        repository_root: Path,
    ) -> str | None:
        """Build a canonical GitHub URL for a governed repository path.

        Returns:
            The resulting ``str | None``.

        """
        repo = FlextInfraUtilitiesDocsGithubLinks.docs_github_repo_lookup(
            organization,
            repository,
            repository_root=repository_root,
        )
        if repo is None:
            return None
        kind = "tree" if is_dir else "blob"
        return (
            f"https://github.com/{repo.organization}/{repo.repository}/"
            f"{kind}/{repo.branch}/{path}"
        )

    @staticmethod
    def docs_rewrite_github_url(
        target: str,
        *,
        repository_root: Path,
    ) -> str | None:
        """Rewrite a stale org placeholder when the ref is the governed branch.

        A different ref is never rewritten: refs may contain ``/``, so its
        extent (and thus the path) is undecidable from the URL alone. Any
        ``?query``/``#fragment`` suffix is carried over unchanged.

        Returns:
            The resulting ``str | None``.

        """
        match = FlextInfraUtilitiesDocsGithubLinks.docs_parse_github_doc_url(target)
        if match is None:
            stale = FlextInfraUtilitiesDocsGithubLinks.docs_stale_github_organizations()
            for org in stale:
                needle = f"https://github.com/{org}/"
                if target.startswith(needle):
                    # Cannot rewrite without knowing the real org/repo.
                    return None
            return None
        org = match.group("org")
        repository = match.group("repo")
        refpath = match.group("refpath")
        suffix = match.group("suffix") or ""
        kind = match.group("kind")
        stale = FlextInfraUtilitiesDocsGithubLinks.docs_stale_github_organizations()
        lookup_org = org
        if org in stale:
            matches = tuple(
                repo
                for repo in FlextInfraUtilitiesDocsGithubLinks.docs_github_repos(
                    repository_root,
                )
                if repo.repository == repository
            )
            if len(matches) != 1:
                return None
            lookup_org = matches[0].organization
        repo = FlextInfraUtilitiesDocsGithubLinks.docs_github_repo_lookup(
            lookup_org,
            repository,
            repository_root=repository_root,
        )
        if repo is None:
            return None
        path = FlextInfraUtilitiesDocsGithubLinks.docs_github_governed_path(
            refpath,
            repo.branch,
        )
        # A foreign ref has no decidable ref/path boundary: the audit reports it
        # as a wrong branch, and no rewrite is guessed.
        if path is None or org == repo.organization:
            return None
        return (
            f"https://github.com/{repo.organization}/{repo.repository}/"
            f"{kind}/{repo.branch}/{path}{suffix}"
        )

    @staticmethod
    def docs_github_local_path(
        target: str,
        *,
        repository_root: Path,
    ) -> Path | None:
        """Resolve a governed GitHub URL to a local checkout path when configured.

        Returns:
            The resulting ``Path | None``.

        """
        match = FlextInfraUtilitiesDocsGithubLinks.docs_parse_github_doc_url(target)
        if match is None:
            return None
        org = match.group("org")
        repository = match.group("repo")
        if org in FlextInfraUtilitiesDocsGithubLinks.docs_stale_github_organizations():
            return None
        repo = FlextInfraUtilitiesDocsGithubLinks.docs_github_repo_lookup(
            org,
            repository,
            repository_root=repository_root,
        )
        if repo is None:
            return None
        governed_path = FlextInfraUtilitiesDocsGithubLinks.docs_github_governed_path(
            match.group("refpath"),
            repo.branch,
        )
        if governed_path is None:
            return None
        root = FlextInfraUtilitiesDocsGithubLinks.docs_expand_local_checkout(
            repo.local_checkout,
        )
        if root is None:
            return None
        return FlextInfraUtilitiesDocsGithubLinks._github_member_path(
            root,
            governed_path,
        )

    @staticmethod
    def _github_member_path(
        root: Path,
        path: str,
    ) -> Path:
        """Join one local checkout root with its governed relative path.

        Returns:
            The resulting ``Path``.

        """
        return root / path

    @staticmethod
    def docs_github_link_issues(
        *,
        file: str,
        line_number: int,
        raw: str,
        target: str,
        repository_root: Path,
    ) -> t.SequenceOf[m.Infra.AuditIssue]:
        """Emit audit issues for stale or locally-missing GitHub doc URLs.

        Returns:
            The resulting ``t.SequenceOf[m.Infra.AuditIssue]``.

        """
        issues: list[m.Infra.AuditIssue] = []
        match = FlextInfraUtilitiesDocsGithubLinks.docs_parse_github_doc_url(target)
        if match is None:
            return issues
        org = match.group("org")
        if org in FlextInfraUtilitiesDocsGithubLinks.docs_stale_github_organizations():
            issues.append(
                m.Infra.AuditIssue(
                    file=file,
                    issue_type="stale_github_organization",
                    severity="high",
                    message=(
                        f"line {line_number}: placeholder GitHub organization "
                        f"must be rewritten -> {raw}"
                    ),
                ),
            )
            return issues
        repository = match.group("repo")
        repo = FlextInfraUtilitiesDocsGithubLinks.docs_github_repo_lookup(
            org,
            repository,
            repository_root=repository_root,
        )
        if (
            repo is not None
            and FlextInfraUtilitiesDocsGithubLinks.docs_github_governed_path(
                match.group("refpath"),
                repo.branch,
            )
            is None
        ):
            issues.append(
                m.Infra.AuditIssue(
                    file=file,
                    issue_type="wrong_github_branch",
                    severity="high",
                    message=(
                        f"line {line_number}: GitHub branch must be "
                        f"{repo.branch} -> {raw}"
                    ),
                ),
            )
        local = FlextInfraUtilitiesDocsGithubLinks.docs_github_local_path(
            target,
            repository_root=repository_root,
        )
        if local is not None and not local.exists():
            issues.append(
                m.Infra.AuditIssue(
                    file=file,
                    issue_type="broken_github_link",
                    severity="high",
                    message=(
                        f"line {line_number}: governed GitHub path missing locally "
                        f"({local}) -> {raw}"
                    ),
                ),
            )
        return issues


__all__: list[str] = ["FlextInfraUtilitiesDocsGithubLinks"]
