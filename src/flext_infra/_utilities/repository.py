"""Canonical repository-to-provider resolution utilities."""

from __future__ import annotations


from pathlib import Path
from urllib.parse import quote, unquote, urlsplit, urlunsplit

from flext_core import r
from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.protocols import p
from flext_infra.typings import t

_MINIMUM_ARTIFACT_URL_PARTS = 5
_REPOSITORY_URL_PARTS = 2


class FlextInfraUtilitiesRepository:
    """Resolve provider-owned policy for one governed repository."""

    @staticmethod
    def derived_repository_ref(
        distribution: str,
        *,
        provider: m.Infra.ProviderSpec,
        role: c.Infra.RepositoryRole = c.Infra.RepositoryRole.WORKSPACE_MEMBER,
        checkout: c.Infra.CheckoutKind = c.Infra.CheckoutKind.SUBMODULE,
    ) -> m.Infra.RepositoryRef:
        """Derive one repository reference from generic provider policy.

        flext-infra owns no catalog of the projects it serves, so a governed
        distribution that the live workspace does not declare is still
        resolvable: its canonical source is the provider contract plus its own
        distribution name. Nothing here is looked up; everything is derived.
        """
        return m.Infra.RepositoryRef(
            name=distribution,
            distribution=distribution,
            url=f"{provider.base_url.rstrip('/')}/{distribution}.git",
            path=Path(distribution),
            role=role,
            provider=provider.name,
            checkout=checkout,
            codegen=c.Infra.CodegenKind.CONFORM,
            package=True,
            editable=True,
            read_only=False,
        )

    @staticmethod
    def repository_provider(
        repository: p.Infra.RepositoryRef, providers: t.SequenceOf[m.Infra.ProviderSpec]
    ) -> p.Result[m.Infra.ProviderSpec]:
        """Return the unique typed provider declared by ``repository.provider``."""
        matches = tuple(
            provider for provider in providers if provider.name == repository.provider
        )
        if len(matches) != 1:
            return r[m.Infra.ProviderSpec].fail(
                f"repository provider must resolve exactly once: {repository.provider}"
            )
        return r[m.Infra.ProviderSpec].ok(matches[0])

    @staticmethod
    def resolve_integration_branch(
        workspace: m.Infra.WorkspaceSpec, provider: m.Infra.ProviderSpec
    ) -> str:
        """Return the workspace overlay branch, else the provider catalog branch."""
        if (
            workspace.integration is not None
            and workspace.integration.provider == provider.name
        ):
            integration_branch: str = workspace.integration.branch
            return integration_branch
        provider_branch: str = provider.branch
        return provider_branch

    @staticmethod
    def repository_artifact_authority(
        repository: p.Infra.RepositoryRef,
        provider: m.Infra.ProviderSpec,
        workspace: m.Infra.WorkspaceSpec | None = None,
    ) -> m.Infra.RepositoryArtifactAuthority:
        """Derive the exact GitHub authority and effective ref from repository policy."""
        ref = (
            FlextInfraUtilitiesRepository.resolve_integration_branch(
                workspace, provider
            )
            if workspace is not None
            else provider.branch
        )
        authority = (
            FlextInfraUtilitiesRepository.repository_artifact_authority_from_remote(
                repository.url, ref
            )
        )
        effective_organization = (
            workspace.integration.organization
            if workspace is not None
            and workspace.integration is not None
            and workspace.integration.provider == provider.name
            and workspace.integration.organization is not None
            else provider.organization
        )
        if authority.organization != effective_organization:
            msg = "repository URL organization conflicts with provider policy"
            raise ValueError(msg)
        return authority

    @staticmethod
    def repository_artifact_authority_from_remote(
        remote: str, ref: str
    ) -> m.Infra.RepositoryArtifactAuthority:
        """Derive a validated GitHub artifact authority from remote and ref."""
        parsed = urlsplit(remote.removesuffix(".git"))
        if (
            parsed.scheme != "https"
            or parsed.hostname != "github.com"
            or parsed.port is not None
            or parsed.username is not None
            or parsed.password is not None
        ):
            msg = "repository artifact authority requires canonical GitHub HTTPS URL"
            raise ValueError(msg)
        url_parts = parsed.path.strip("/").split("/")
        if len(url_parts) != _REPOSITORY_URL_PARTS:
            msg = "repository GitHub URL must identify organization/repository"
            raise ValueError(msg)
        organization, repository_name = url_parts
        return m.Infra.RepositoryArtifactAuthority(
            host=parsed.hostname,
            organization=organization,
            repository=repository_name,
            ref=ref,
        )

    @staticmethod
    def repository_artifact_url(reference: m.Infra.RepositoryArtifactReference) -> str:
        """Build one complete percent-encoded GitHub blob or tree URL."""
        authority = reference.authority
        encoded_ref = "/".join(
            quote(part, safe="") for part in authority.ref.split("/")
        )
        encoded_path = "/".join(
            quote(part, safe="") for part in reference.path.split("/")
        )
        fragment = (
            quote(reference.fragment, safe="-._~!$&'()*+,;=:@/?")
            if reference.fragment
            else ""
        )
        url: str = urlunsplit((
            "https",
            authority.host,
            f"/{quote(authority.organization, safe='')}/{quote(authority.repository, safe='')}/{reference.kind}/{encoded_ref}/{encoded_path}",
            "",
            fragment,
        ))
        return url

    @staticmethod
    def repository_artifact_parse(
        value: str, authorities: t.SequenceOf[m.Infra.RepositoryArtifactAuthority]
    ) -> p.Result[m.Infra.RepositoryArtifactReference]:
        """Parse and validate one complete GitHub artifact URL against authorities."""
        parsed = urlsplit(value)
        if (
            parsed.scheme != "https"
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.port is not None
        ):
            return r.fail(
                "repository artifact URL must use credential-free HTTPS without query"
            )
        parts = parsed.path.lstrip("/").split("/")
        if len(parts) < _MINIMUM_ARTIFACT_URL_PARTS:
            return r.fail("repository artifact URL is incomplete")
        organization, repository, kind_raw, *tail = parts
        authority = next(
            (
                item
                for item in authorities
                if item.host == parsed.hostname
                and item.organization == unquote(organization)
                and item.repository == unquote(repository)
            ),
            None,
        )
        if authority is None:
            return r.fail(
                "repository artifact URL uses an unknown repository authority"
            )
        try:
            kind = m.Infra.RepositoryArtifactKind(kind_raw)
        except ValueError:
            return r.fail("repository artifact URL kind must be blob or tree")
        ref_parts = authority.ref.split("/")
        encoded_ref = tail[: len(ref_parts)]
        if [unquote(part) for part in encoded_ref] != ref_parts:
            return r.fail("repository artifact URL uses the wrong configured ref")
        path_parts: list[str] = []
        for encoded_part in tail[len(ref_parts) :]:
            decoded = encoded_part
            for _ in range(3):
                next_value = unquote(decoded)
                if next_value == decoded:
                    break
                decoded = next_value
            if decoded != unquote(encoded_part):
                return r.fail("repository artifact URL path uses noncanonical encoding")
            path_parts.append(decoded)
        if not path_parts or any(
            not part or part in {".", ".."} or "\\" in part or "/" in part
            for part in path_parts
        ):
            return r.fail("repository artifact URL path is not repository-relative")
        reference = m.Infra.RepositoryArtifactReference(
            authority=authority,
            kind=kind,
            path="/".join(path_parts),
            fragment=unquote(parsed.fragment) or None,
        )
        canonical = FlextInfraUtilitiesRepository.repository_artifact_url(reference)
        if canonical.split("#", maxsplit=1)[0] != value.split("#", maxsplit=1)[0]:
            return r.fail("repository artifact URL is not canonical")
        return r.ok(reference)

    @staticmethod
    def gitmodule_branch_is_governed(
        declared_branch: str,
        *,
        provider_branch: str,
        integration_branch: str | None = None,
    ) -> bool:
        """Accept follow-superproject (``.``) or the resolved integration line."""
        if declared_branch == c.Infra.FOLLOW_SUPERPROJECT_BRANCH:
            return True
        if declared_branch == provider_branch:
            return True
        return integration_branch is not None and declared_branch == integration_branch

    @classmethod
    def repository_baseline_branch(
        cls, repository_root: Path, fallback: str | None = None
    ) -> p.Result[str]:
        """Return the integration baseline the repository actually publishes.

        A provider declares one default branch, but managed repositories under
        the same provider legitimately integrate on different branches. The
        baseline is therefore derived from live Git: the published
        remote-tracking integration branch wins.

        ``fallback`` carries the provider default for a repository that cannot
        have published anything yet (project creation). Without it, a checkout
        with no integration branch fails closed instead of guessing.
        """
        from flext_infra.utilities import u

        for candidate in c.Infra.INTEGRATION_BRANCH_PREFERENCE:
            reference = f"refs/remotes/origin/{candidate}"
            resolved = u.Infra.git_ref_exists(
                m.Infra.GitRefRequest(repo_root=repository_root, reference=reference)
            )
            if resolved.success and resolved.value.value:
                return r[str].ok(candidate)
        if fallback:
            return r[str].ok(fallback)
        return r[str].fail(
            "repository publishes no integration branch "
            f"({', '.join(c.Infra.INTEGRATION_BRANCH_PREFERENCE)}): {repository_root}"
        )

    @staticmethod
    def workspace_spec_load(repository_root: Path) -> p.Result[m.Infra.WorkspaceSpec]:
        """Load governed topology and derive observed external Git dependencies."""
        from flext_infra.workspace.detector import FlextInfraWorkspaceDetector

        return FlextInfraWorkspaceDetector.load_workspace_spec(repository_root)

    @staticmethod
    def repository_conform_target(
        repository_root: Path, workspace: m.Infra.WorkspaceSpec | None = None
    ) -> p.Result[m.Infra.RepositoryConformTarget]:
        """Return typed effective policy inferred from live repository topology."""
        from flext_infra.workspace.detector import FlextInfraWorkspaceDetector

        resolved_workspace = workspace
        if resolved_workspace is None:
            loaded = FlextInfraWorkspaceDetector.load_workspace_spec(repository_root)
            if loaded.failure:
                return r[m.Infra.RepositoryConformTarget].fail(
                    loaded.error or "workspace manifest load failed"
                )
            resolved_workspace = loaded.value
        return FlextInfraWorkspaceDetector.conform_target(
            repository_root, resolved_workspace
        )


__all__: tuple[str, ...] = ("FlextInfraUtilitiesRepository",)
