"""Workspace policy and repository identity derived from typed SSOTs.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from flext_core import r
from flext_infra import c, config, m, u

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraWorkspaceGovernanceMixin:
    """Own repository identity, policy overlays, and conform routing."""

    @staticmethod
    def _declares_attached_standalone(repository_root: Path) -> p.Result[bool]:
        """Read the ``[tool.flext.workspace] attached`` opt-in marker."""
        metadata = u.read_project_metadata(repository_root)
        if metadata.failure:
            return r[bool].ok(False)
        return r[bool].ok(metadata.value.flext.workspace.attached)

    @staticmethod
    def persistent_state_artifacts(
        make_profile: c.Infra.MakeProfile,
    ) -> tuple[m.Infra.CodegenArtifactSpec, ...]:
        """Project persistent-state artifacts owned by one Make profile."""
        if make_profile is not c.Infra.MakeProfile.WORKSPACE_ROOT:
            return ()
        persistent = c.Infra.PERSISTENT_STATE_ARTIFACT_NAMES
        return tuple(
            artifact
            for artifact in config.Infra.codegen.artifacts
            if artifact.name in persistent
        )

    @staticmethod
    def _repository_is_governed(
        repository: m.Infra.RepositoryRef, provider: m.Infra.ProviderSpec
    ) -> bool:
        """Require provider key, host, organization, and URL shape to agree."""
        provider_url = urlparse(provider.base_url)
        repository_url = urlparse(repository.url)
        provider_path = provider_url.path.strip("/")
        repository_path = repository_url.path.strip("/")
        repository_name = repository_path.removeprefix(
            f"{provider.organization}/"
        ).removesuffix(".git")
        return all(
            (
                repository.provider == provider.name,
                provider_url.scheme == repository_url.scheme,
                provider_url.netloc == repository_url.netloc,
                provider_path == provider.organization,
                bool(repository_name),
                repository_path
                == f"{provider.organization}/{repository_name}.git",
            )
        )

    @staticmethod
    def _declared_provider_for_url(url: str) -> m.Infra.ProviderSpec | None:
        """Return the configured provider owning ``url`` when one matches."""
        parsed = urlparse(url)
        return next(
            (
                provider
                for provider in config.Infra.codegen.providers
                if all(
                    (
                        urlparse(provider.base_url).scheme == parsed.scheme,
                        urlparse(provider.base_url).netloc == parsed.netloc,
                        parsed.path.strip("/").startswith(
                            f"{provider.organization}/"
                        ),
                    )
                )
            ),
            None,
        )

    @classmethod
    def _provider_for_url(cls, url: str) -> m.Infra.ProviderSpec:
        """Resolve the configured provider owning ``url`` or the SSOT default."""
        provider = cls._declared_provider_for_url(url)
        if provider is not None:
            return provider
        return config.Infra.codegen.default_provider_spec

    @staticmethod
    def _git_origin_url(repository_root: Path) -> p.Result[str]:
        """Read the declared origin, proving its absence before returning empty."""
        remotes = u.Cli.capture([c.Infra.GIT, "remote"], cwd=repository_root)
        if remotes.failure:
            return r[str].fail(r.require_error(remotes))
        if "origin" not in remotes.value.splitlines():
            return r[str].ok("")
        captured = u.Cli.capture(
            [c.Infra.GIT, "remote", "get-url", "origin"], cwd=repository_root
        )
        if captured.failure:
            return r[str].fail(r.require_error(captured))
        origin = captured.value.strip()
        if not origin:
            return r[str].fail(f"Git origin URL is empty: {repository_root}")
        return r[str].ok(origin)

    @staticmethod
    def resolve_workspace_root(repository_root: Path) -> p.Result[Path]:
        """Resolve the manifest owner for a repository or attached member."""
        resolved_root = repository_root.expanduser().resolve()
        superproject = u.Cli.capture(
            [c.Infra.GIT, "rev-parse", "--show-superproject-working-tree"],
            cwd=resolved_root,
        )
        if superproject.failure:
            inside_work_tree = u.Cli.capture(
                [c.Infra.GIT, "rev-parse", "--is-inside-work-tree"],
                cwd=resolved_root,
            )
            if inside_work_tree.failure or inside_work_tree.value.strip() != "true":
                return r[Path].ok(resolved_root)
            return r[Path].fail(
                superproject.error or "unable to resolve Git superproject"
            )
        owner = Path(superproject.value).resolve() if superproject.value else resolved_root
        return r[Path].ok(owner)

    @staticmethod
    def workspace_analysis_exclusion_paths(
        workspace: m.Infra.WorkspaceSpec,
    ) -> tuple[Path, ...]:
        """Return ordered, unique paths excluded from static analysis."""
        declared = (
            *workspace.external_dependency_paths,
            *(exclusion.path for exclusion in workspace.exclusions),
        )
        return tuple(dict.fromkeys(declared))

    @classmethod
    def _unmanifested_repository_is_governed(cls, repository_root: Path) -> bool:
        """Classify a manifestless project only from its own typed identity."""
        metadata = u.read_project_metadata(repository_root)
        if metadata.failure:
            return False
        origin = cls._git_origin_url(repository_root)
        if origin.failure:
            return False
        return all(
            (
                bool(origin.value),
                cls._declared_provider_for_url(origin.value) is not None,
            )
        )

    @classmethod
    def analysis_exclusion_paths(
        cls, repository_root: Path
    ) -> p.Result[tuple[Path, ...]]:
        """Return typed analysis exclusions for a governed repository."""
        manifest_path = cls._manifest_path(repository_root)
        if not manifest_path.is_file() and not cls._unmanifested_repository_is_governed(
            repository_root
        ):
            return r[tuple[Path, ...]].ok(())
        workspace = cls.load_workspace_spec(repository_root)
        if workspace.failure:
            return r[tuple[Path, ...]].fail(
                workspace.error
                or f"unable to load workspace spec: {repository_root}"
            )
        return r[tuple[Path, ...]].ok(
            cls.workspace_analysis_exclusion_paths(workspace.value)
        )

    @staticmethod
    def _validate_local_repository(
        repository: m.Infra.RepositoryRef,
    ) -> p.Result[bool]:
        """Validate immutable relation metadata for a local manifest owner."""
        return (
            r[m.Infra.RepositoryRef]
            .ok(repository)
            .filter(lambda item: item.path.as_posix() == ".")
            .map_error(lambda _: "local repository manifest path must be '.'")
            .flat_map(
                lambda item: r[m.Infra.RepositoryRef]
                .ok(item)
                .filter(lambda value: value.state is c.Infra.RepositoryState.ACTIVE)
                .map_error(lambda _: "local repository must have active state")
            )
            .flat_map(
                lambda item: r[m.Infra.RepositoryRef]
                .ok(item)
                .filter(
                    lambda value: value.role
                    in {
                        c.Infra.RepositoryRole.WORKSPACE_ROOT,
                        c.Infra.RepositoryRole.WORKSPACE_MEMBER,
                        c.Infra.RepositoryRole.STANDALONE,
                    }
                )
                .map_error(
                    lambda _: (
                        "unsupported local repository role: "
                        f"{item.role.value}"
                    )
                )
            )
            .flat_map(
                lambda item: r[m.Infra.RepositoryRef]
                .ok(item)
                .filter(lambda value: not value.read_only)
                .map_error(lambda _: "local repository cannot be read-only")
            )
            .map(lambda _: True)
        )

    @classmethod
    def _resolved_workspace(
        cls,
        governing_root: Path,
        supplied: m.Infra.WorkspaceSpec | None,
    ) -> p.Result[m.Infra.WorkspaceSpec]:
        """Use the supplied typed workspace or load its canonical owner."""
        if supplied is not None:
            return r[m.Infra.WorkspaceSpec].ok(supplied)
        loaded = cls.load_workspace_spec(governing_root)
        if loaded.failure:
            return r[m.Infra.WorkspaceSpec].fail(
                loaded.error or "unable to load governing workspace"
            )
        return loaded

    @staticmethod
    def _conform_repository(
        resolved_root: Path,
        governing_root: Path,
        workspace: m.Infra.WorkspaceSpec,
    ) -> p.Result[m.Infra.RepositoryRef]:
        """Resolve exactly one mutable repository from the governing workspace."""
        if resolved_root == governing_root:
            return r[m.Infra.RepositoryRef].ok(workspace.repository)
        try:
            relative_path = resolved_root.relative_to(governing_root)
        except ValueError as exc:
            return r[m.Infra.RepositoryRef].fail_op(
                "Conformance target resolution", exc
            )
        matches = tuple(item for item in workspace.members if item.path == relative_path)
        if len(matches) != 1:
            return r[m.Infra.RepositoryRef].fail(
                "attached repository is an external read-only dependency, "
                f"not one governed member: {relative_path.as_posix()}"
            )
        return r[m.Infra.RepositoryRef].ok(matches[0])

    @classmethod
    def _validated_conform_identity(
        cls, root: Path, repository: m.Infra.RepositoryRef
    ) -> p.Result[str]:
        """Validate project metadata and provider ownership for one repository."""
        if repository.read_only:
            return r[str].fail(
                f"repository is an external read-only dependency: {repository.name}"
            )
        metadata = u.read_project_metadata(root)
        if metadata.failure:
            return r[str].fail(
                metadata.error or f"unable to read project metadata: {root}"
            )
        canonical_name = metadata.value.project.name
        if canonical_name != repository.distribution:
            return r[str].fail(
                "project metadata and repository identity differ: "
                f"{canonical_name} != {repository.distribution}"
            )
        providers = tuple(
            provider
            for provider in config.Infra.codegen.providers
            if provider.name == repository.provider
        )
        if len(providers) != 1:
            return r[str].fail(
                f"repository provider must resolve exactly once: {repository.provider}"
            )
        if not cls._repository_is_governed(repository, providers[0]):
            return r[str].fail(
                f"repository is an external or fork URL: {repository.url}"
            )
        return r[str].ok(canonical_name)

    @staticmethod
    def _repository_overlay(
        workspace: m.Infra.WorkspaceSpec, project_name: str
    ) -> p.Result[m.Infra.RepositoryPolicyOverlaySpec]:
        """Resolve at most one policy overlay for a canonical project name."""
        overlays = tuple(
            item
            for item in workspace.repository_policy_overlays
            if item.project == project_name
        )
        if len(overlays) > 1:
            return r[m.Infra.RepositoryPolicyOverlaySpec].fail(
                f"repository policy overlay is duplicated: {project_name}"
            )
        overlay = (
            overlays[0]
            if overlays
            else m.Infra.RepositoryPolicyOverlaySpec(project=project_name)
        )
        return r[m.Infra.RepositoryPolicyOverlaySpec].ok(overlay)

    @staticmethod
    def _make_profile(mode: c.Infra.WorkspaceMode) -> c.Infra.MakeProfile:
        """Map detected topology to its canonical Make profile."""
        return {
            c.Infra.WorkspaceMode.WORKSPACE: c.Infra.MakeProfile.WORKSPACE_ROOT,
            c.Infra.WorkspaceMode.WORKSPACE_MEMBER: c.Infra.MakeProfile.WORKSPACE_MEMBER,
            c.Infra.WorkspaceMode.STANDALONE: c.Infra.MakeProfile.STANDALONE,
        }[mode]

    @staticmethod
    def _beads_enabled(
        transaction_worktree: bool,
        make_profile: c.Infra.MakeProfile,
        overlay: m.Infra.RepositoryPolicyOverlaySpec,
    ) -> bool:
        """Derive Beads ownership from topology and the typed policy overlay."""
        return any(
            (
                transaction_worktree,
                make_profile is c.Infra.MakeProfile.WORKSPACE_ROOT,
                all(
                    (
                        make_profile is c.Infra.MakeProfile.STANDALONE,
                        overlay.beads_enabled,
                    )
                ),
            )
        )

    @classmethod
    def _conform_target_for_repository(
        cls,
        resolved_root: Path,
        governing_root: Path,
        workspace: m.Infra.WorkspaceSpec,
        repository: m.Infra.RepositoryRef,
    ) -> p.Result[m.Infra.RepositoryConformTarget]:
        """Materialize a conform target after repository selection."""
        identity = cls._validated_conform_identity(resolved_root, repository)
        if identity.failure:
            return r[m.Infra.RepositoryConformTarget].fail(identity.error)
        overlay = cls._repository_overlay(workspace, identity.value)
        if overlay.failure:
            return r[m.Infra.RepositoryConformTarget].fail(overlay.error)
        mode = cls().detect(resolved_root)
        if mode.failure:
            return r[m.Infra.RepositoryConformTarget].fail(
                mode.error or "unable to infer repository topology"
            )
        primary_root = u.Infra.git_primary_worktree_root(resolved_root)
        if primary_root.failure:
            return r[m.Infra.RepositoryConformTarget].fail(
                primary_root.error or "unable to resolve primary worktree"
            )
        make_profile = cls._make_profile(mode.value)
        transaction_worktree = primary_root.value != resolved_root
        attached_standalone = all(
            (
                mode.value is c.Infra.WorkspaceMode.WORKSPACE_MEMBER,
                resolved_root == governing_root,
            )
        )
        return r[m.Infra.RepositoryConformTarget].ok(
            m.Infra.RepositoryConformTarget(
                repository=repository,
                root=resolved_root,
                make_profile=make_profile,
                beads_enabled=cls._beads_enabled(
                    transaction_worktree, make_profile, overlay.value
                ),
                attached_standalone=attached_standalone,
                routing_only=any((transaction_worktree, attached_standalone)),
                canonical_project_name=identity.value,
                baseline_branch=repository.branch,
                ci_enabled=overlay.value.ci_enabled,
                external_dependency_paths=workspace.external_dependency_paths,
                technical_branch_patterns=(
                    config.Infra.codegen.branch_policy.technical_branch_patterns
                ),
                governed_branch_patterns=(
                    config.Infra.codegen.governed_branch_patterns
                ),
            )
        )

    @classmethod
    def _conform_target_for_workspace(
        cls,
        resolved_root: Path,
        governing_root: Path,
        workspace: m.Infra.WorkspaceSpec,
    ) -> p.Result[m.Infra.RepositoryConformTarget]:
        """Select and validate the repository owned by one workspace."""
        repository = cls._conform_repository(
            resolved_root, governing_root, workspace
        )
        if repository.failure:
            return r[m.Infra.RepositoryConformTarget].fail(repository.error)
        return cls._conform_target_for_repository(
            resolved_root, governing_root, workspace, repository.value
        )

    @classmethod
    def conform_target(
        cls,
        repository_root: Path,
        workspace_spec: m.Infra.WorkspaceSpec | None = None,
    ) -> p.Result[m.Infra.RepositoryConformTarget]:
        """Derive the sole conformance target from live Git and typed identity."""
        resolved_root = repository_root.expanduser().resolve()
        governing_root = cls.resolve_workspace_root(resolved_root)
        if governing_root.failure:
            return r[m.Infra.RepositoryConformTarget].fail(
                governing_root.error or "unable to resolve governing root"
            )
        workspace = cls._resolved_workspace(governing_root.value, workspace_spec)
        if workspace.failure:
            return r[m.Infra.RepositoryConformTarget].fail(workspace.error)
        return cls._conform_target_for_workspace(
            resolved_root, governing_root.value, workspace.value
        )


__all__: list[str] = ["FlextInfraWorkspaceGovernanceMixin"]
