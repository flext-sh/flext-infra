"""Single-rule Git workspace mode detection.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, override
from urllib.parse import urlparse

from flext_core import r
from flext_infra import c, config, m, u
from flext_infra.base import s

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraWorkspaceDetector(s[c.Infra.WorkspaceMode]):
    """Classify one repository from its own Git topology.

    SINGLE RULE: a repository declaring ``.gitmodules`` is a workspace;
    a repository without it is standalone. No registry, member mapping,
    parent lookup, manifest file, or attachment marker participates.
    """

    @staticmethod
    def repository_is_governed(
        repository: m.Infra.RepositoryRef, provider: m.Infra.ProviderSpec
    ) -> bool:
        """Require provider key, host, and organization to agree exactly."""
        if repository.provider != provider.name:
            return False
        provider_url = urlparse(provider.base_url)
        repository_url = urlparse(repository.url)
        provider_path = provider_url.path.strip("/")
        repository_path = repository_url.path.strip("/")
        # CI remotes often omit the ``.git`` suffix; compare on a canonical form.
        repository_name = repository_path.removeprefix(
            f"{provider.organization}/"
        ).removesuffix(".git")
        canonical_path = f"{provider.organization}/{repository_name}.git"
        actual_path = (
            repository_path
            if repository_path.endswith(".git")
            else f"{repository_path}.git"
        )
        return (
            provider_url.scheme == repository_url.scheme
            and provider_url.netloc == repository_url.netloc
            and provider_path == provider.organization
            and bool(repository_name)
            and actual_path == canonical_path
        )

    @classmethod
    def load_workspace_spec(
        cls, repository_root: Path, *, project_metadata: p.ProjectMetadata | None = None
    ) -> p.Result[m.Infra.WorkspaceSpec]:
        """Derive the workspace spec from live Git and project metadata.

        Topology comes from ``.gitmodules`` and identity comes from
        ``pyproject.toml``.
        """
        return cls._derive_workspace_spec(
            repository_root, project_metadata=project_metadata
        )

    @classmethod
    def _derive_workspace_spec(
        cls, repository_root: Path, *, project_metadata: p.ProjectMetadata | None = None
    ) -> p.Result[m.Infra.WorkspaceSpec]:
        """Derive the spec from the repository itself, never from a registry.

        Operator law: flext-infra owns generic conform behaviour and must not
        carry a catalog of the projects it serves. Identity comes from the
        repository's ``pyproject.toml``. ``.gitmodules`` is deliberately not
        parsed here: its presence classifies topology but cannot create
        relationships or policy. Nothing is looked up in a registry.
        """
        resolved_metadata = project_metadata
        if resolved_metadata is None:
            metadata = u.read_project_metadata(repository_root)
            if metadata.failure:
                return r[m.Infra.WorkspaceSpec].fail(
                    metadata.error
                    or (
                        "cannot derive workspace spec without metadata: "
                        f"{repository_root}"
                    )
                )
            resolved_metadata = metadata.value
        origin = cls._git_origin_url(repository_root)
        if origin.failure:
            return r[m.Infra.WorkspaceSpec].fail(
                origin.error or f"unable to read Git origin: {repository_root}"
            )
        provider = cls._declared_provider_for_url(origin.value)
        if provider is None:
            return r[m.Infra.WorkspaceSpec].fail(
                f"repository origin has no declared provider: {origin.value}"
            )
        project_name = resolved_metadata.project.name
        local_repository = m.Infra.RepositoryRef(
            name=project_name,
            distribution=project_name,
            url=origin.value,
            path=Path(),
            provider=provider.name,
        )
        project_spec = cls._project_spec(resolved_metadata, origin.value, provider)
        return r[m.Infra.WorkspaceSpec].ok(
            m.Infra.WorkspaceSpec(repository=local_repository, project=project_spec)
        )

    @staticmethod
    def _project_spec(
        metadata: p.ProjectMetadata, origin: str, provider: m.Infra.ProviderSpec
    ) -> m.Infra.ProjectSpec:
        """Project the canonical metadata object into the codegen contract."""
        project_name = metadata.project.name
        package_name = metadata.package_name
        class_stem = metadata.class_stem
        derived_ns = class_stem.removeprefix("Flext")
        project_namespace = derived_ns or class_stem
        alias = u.Infra.package_alias(package_name=package_name)
        authors = tuple(metadata.project.authors)
        first_author = authors[0] if authors else None
        author_name = first_author.name if first_author else "FLEXT Team"
        author_email = first_author.email if first_author else "team@flext.dev"
        urls = metadata.project.urls
        homepage = (
            urls.homepage if urls and urls.homepage else origin.removesuffix(".git")
        )
        documentation = urls.documentation if urls and urls.documentation else homepage
        description = (
            metadata.project.description
            or f"{class_stem} — FLEXT typed integration package"
        )
        upstream = (
            "flext_cli"
            if any(
                dependency.startswith(("flext-cli", "flext_cli"))
                for dependency in metadata.project.dependencies
            )
            else "flext_core"
        )
        return m.Infra.ProjectSpec(
            package_name=package_name,
            class_stem=class_stem,
            namespace=project_namespace,
            constant_name=project_name,
            namespace_attribute=alias,
            alias=alias,
            environment_prefix=f"{package_name.upper()}_",
            description=description,
            version=metadata.project.version,
            license="MIT",
            author_name=author_name,
            author_email=author_email,
            upstream=upstream,
            homepage=homepage
            or f"https://github.com/{provider.organization}/{project_name}",
            documentation=documentation
            or f"https://github.com/{provider.organization}/{project_name}",
            year=2026,
        )

    @staticmethod
    def _git_origin_url(repository_root: Path) -> p.Result[str]:
        """Read the repository's own declared origin without substitution."""
        result = u.Infra.git_remote_url(
            m.Infra.GitRemoteUrlRequest(repo_root=repository_root, remote="origin")
        )
        if result.failure:
            return r[str].fail(
                result.error or f"unable to read Git origin: {repository_root}"
            )
        origin = result.value.text.strip()
        if not origin:
            return r[str].fail(f"repository has no Git origin: {repository_root}")
        return r[str].ok(origin)

    @staticmethod
    def _declared_provider_for_url(url: str) -> m.Infra.ProviderSpec | None:
        """Return the declared provider owning ``url``, or ``None`` if ungoverned.

        Providers are generic policy (host, organization, integration branch)
        and remain flext-infra's to own. Which projects exist under them is
        not, so the match is made against the URL the repository itself
        declares.
        """
        parsed = urlparse(url)
        for provider in config.Infra.codegen.providers:
            provider_url = urlparse(provider.base_url)
            if (
                provider_url.scheme == parsed.scheme
                and provider_url.netloc == parsed.netloc
                and parsed.path.strip("/").startswith(f"{provider.organization}/")
            ):
                return provider
        return None

    @classmethod
    def _repository_mode(cls, repository_root: Path) -> p.Result[c.Infra.WorkspaceMode]:
        """Classify the repository by its own `.gitmodules` presence."""
        return r[c.Infra.WorkspaceMode].ok(
            c.Infra.WorkspaceMode.WORKSPACE
            if (repository_root / c.Infra.GITMODULES).is_file()
            else c.Infra.WorkspaceMode.STANDALONE
        )

    @classmethod
    def conform_target(
        cls, repository_root: Path, *, project_metadata: p.ProjectMetadata | None = None
    ) -> p.Result[m.Infra.RepositoryConformTarget]:
        """Derive the sole conformance target from live Git and typed identity."""
        resolved_root = repository_root.expanduser().resolve()
        workspace_result = cls.load_workspace_spec(
            resolved_root, project_metadata=project_metadata
        )
        if workspace_result.failure:
            return r[m.Infra.RepositoryConformTarget].fail(
                workspace_result.error or "unable to load governing workspace"
            )
        resolved_workspace = workspace_result.value
        repository = resolved_workspace.repository
        resolved_metadata = project_metadata
        if resolved_metadata is None:
            metadata = u.read_project_metadata(resolved_root)
            if metadata.failure:
                return r[m.Infra.RepositoryConformTarget].fail(
                    metadata.error
                    or f"unable to read project metadata: {resolved_root}"
                )
            resolved_metadata = metadata.value
        canonical_project_name = resolved_metadata.project.name
        if canonical_project_name != repository.distribution:
            return r[m.Infra.RepositoryConformTarget].fail(
                "project metadata and repository identity differ: "
                f"{canonical_project_name} != {repository.distribution}"
            )
        providers = tuple(
            item
            for item in config.Infra.codegen.providers
            if item.name == repository.provider
        )
        if len(providers) != 1:
            return r[m.Infra.RepositoryConformTarget].fail(
                f"repository provider must resolve exactly once: {repository.provider}"
            )
        provider = providers[0]
        if not cls.repository_is_governed(repository, provider):
            return r[m.Infra.RepositoryConformTarget].fail(
                f"repository is an external or fork URL: {repository.url}"
            )
        mode_result = cls().detect(resolved_root)
        if mode_result.failure:
            return r[m.Infra.RepositoryConformTarget].fail(
                mode_result.error or "unable to infer repository topology"
            )
        managed_result = u.Infra.tool_flext_declared(resolved_root)
        if managed_result.failure:
            return r[m.Infra.RepositoryConformTarget].fail(
                managed_result.error
                or f"managed declaration resolution failed: {resolved_root}"
            )
        return r[m.Infra.RepositoryConformTarget].ok(
            m.Infra.RepositoryConformTarget(
                repository=repository,
                root=resolved_root,
                topology=mode_result.value,
                managed=managed_result.value,
                canonical_project_name=canonical_project_name,
                ci_enabled=True,
            )
        )

    def detect(self, project_root: Path) -> p.Result[c.Infra.WorkspaceMode]:
        """Detect mode from this repository's `.gitmodules` presence alone."""
        try:
            resolved_project_root = project_root.resolve()
        except c.EXC_OS_RUNTIME_TYPE as exc:
            return r[c.Infra.WorkspaceMode].fail_op("Workspace detection", exc)
        return self._repository_mode(resolved_project_root)

    @override
    def execute(self) -> p.Result[c.Infra.WorkspaceMode]:
        """Execute the workspace detection flow."""
        return self.detect(self.workspace_root)


__all__: list[str] = ["FlextInfraWorkspaceDetector"]
