"""Internal requirement rendering and workspace dependency-group policy."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_cli import r, u

from flext_infra.constants import c
from flext_infra.typings import t

from ..dependencies import FlextInfraUtilitiesDependencies
from ..repository import FlextInfraUtilitiesRepository

if TYPE_CHECKING:
    from collections.abc import Iterator

    from flext_infra.models import m
    from flext_infra.protocols import p


class FlextInfraUtilitiesPyprojectRequirements:
    """Render internal requirements for the active workspace topology."""

    @staticmethod
    def requirement_group_fields(
        document: t.Cli.TomlDocument, project: t.Cli.TomlTable
    ) -> Iterator[t.Pair[t.Cli.TomlTable, str]]:
        """Yield ``(section, group_name)`` for every declared requirement group.

        Optional dependencies hang off ``[project]`` while dependency groups hang
        off the document root; this is the single owner of that traversal for
        every requirement rewriter.
        """
        for section_name in (c.Infra.OPTIONAL_DEPENDENCIES, c.Infra.DEPENDENCY_GROUPS):
            parent = (
                project if section_name == c.Infra.OPTIONAL_DEPENDENCIES else document
            )
            section = u.Cli.toml_table_child(parent, section_name)
            if section is None:
                continue
            for group_name in tuple(section):
                yield section, group_name

    @staticmethod
    def _is_workspace_context_root(
        *,
        project_name: str,
        workspace: p.Infra.WorkspaceSpec,
        workspace_mode: c.Infra.MakeProfile,
    ) -> bool:
        """Identify the real multi-project root only under a workspace topology."""
        return (
            workspace_mode is c.Infra.MakeProfile.WORKSPACE
            and bool(workspace.subprojects)
            and project_name == workspace.repository.distribution
        )

    @classmethod
    def _normalize_requirements(
        cls,
        document: t.Cli.TomlDocument,
        *,
        project_name: str,
        providers: t.SequenceOf[m.Infra.ProviderSpec],
        workspace: p.Infra.WorkspaceSpec,
        workspace_mode: c.Infra.MakeProfile,
        canonicalize_all: bool,
    ) -> p.Result[bool]:
        """Render internal requirements for root workspace or detached operation."""
        available = (workspace.repository, *workspace.subprojects)
        # Only the root expresses the active workspace overlay in its own
        # requirements. A publishable project keeps its configured Git source
        # so the same pyproject remains resolvable in a standalone checkout; uv
        # replaces it with workspace=true from the workspace root.
        workspace_dependencies = (
            frozenset(project.distribution for project in workspace.subprojects)
            if cls._is_workspace_context_root(
                project_name=project_name,
                workspace=workspace,
                workspace_mode=workspace_mode,
            )
            else frozenset()
        )
        project = u.Cli.toml_ensure_table(document, c.Infra.PROJECT)
        normalized = cls._normalize_requirement_field(
            project,
            c.Infra.DEPENDENCIES,
            repositories=available,
            providers=providers,
            canonicalize_all=canonicalize_all,
            workspace_dependencies=workspace_dependencies,
        )
        if normalized.failure:
            return normalized
        for section, group_name in cls.requirement_group_fields(document, project):
            group_result = cls._normalize_requirement_field(
                section,
                group_name,
                repositories=available,
                providers=providers,
                canonicalize_all=canonicalize_all,
                workspace_dependencies=workspace_dependencies,
            )
            if group_result.failure:
                return group_result
        return r[bool].ok(True)

    @classmethod
    def _normalize_requirement_field(
        cls,
        container: t.Cli.TomlDocument | t.Cli.TomlTable,
        key: str,
        *,
        repositories: t.SequenceOf[p.Infra.RepositoryRef],
        providers: t.SequenceOf[m.Infra.ProviderSpec],
        canonicalize_all: bool,
        workspace_dependencies: frozenset[str],
    ) -> p.Result[bool]:
        """Normalize one dependency array and fail on model-less entries."""
        raw_value = u.Cli.toml_value(container, key)
        if raw_value is None:
            return r[bool].ok(True)
        raw_items = u.Cli.json_as_sequence(raw_value)
        validated_items = u.validate_value(
            t.Infra.STR_SEQ_ADAPTER, raw_items, strict=True
        )
        if validated_items.failure:
            return r[bool].fail_op(
                f"validate dependency group {key}", validated_items.error
            )
        items = validated_items.value
        normalized_items: t.MutableSequenceOf[str] = []
        for item in items:
            normalized = cls._canonical_requirement(
                item,
                repositories=repositories,
                providers=providers,
                workspace_dependencies=workspace_dependencies,
            )
            if normalized.failure:
                return r[bool].from_failure(normalized)
            normalized_items.append(normalized.value)
        canonical = tuple(dict.fromkeys(normalized_items))
        if canonicalize_all:

            def requirement_key(requirement: str) -> t.Pair[str, str]:
                name = FlextInfraUtilitiesDependencies.dep_name(requirement) or ""
                return name, requirement

            canonical = tuple(sorted(canonical, key=requirement_key))
        u.Cli.toml_sync_string_list(container, key, canonical)
        return r[bool].ok(True)

    @classmethod
    def _canonical_requirement(
        cls,
        requirement: str,
        *,
        repositories: t.SequenceOf[p.Infra.RepositoryRef],
        providers: t.SequenceOf[m.Infra.ProviderSpec],
        workspace_dependencies: frozenset[str],
    ) -> p.Result[str]:
        """Render one internal requirement from its local topology reference."""
        dependency_name = FlextInfraUtilitiesDependencies.dep_name(requirement)
        if dependency_name is None or not dependency_name.startswith("flext-"):
            return r[str].ok(requirement.strip())
        requirement_part, separator, marker = requirement.partition(";")
        head_match = c.Infra.PEP621_REQUIREMENT_HEAD_RE.match(requirement_part.strip())
        if head_match is None:
            return r[str].fail(f"invalid internal requirement: {requirement}")
        head = head_match.group("head").strip()
        marker_text = marker.strip()
        if dependency_name in workspace_dependencies:
            if "@" in requirement_part:
                return r[str].fail(
                    "workspace dependency declares a conflicting direct source: "
                    f"{dependency_name}"
                )
            return r[str].ok(
                f"{head}; {marker_text}" if separator and marker_text else head
            )
        reference_result = cls._repository_reference(
            dependency_name, repositories=repositories, providers=providers
        )
        if reference_result.failure:
            return r[str].from_failure(reference_result)
        reference = reference_result.value
        provider = FlextInfraUtilitiesRepository.repository_provider(
            reference, providers
        )
        if provider.failure:
            return r[str].from_failure(provider)
        # Publishable members keep the direct Git requirement with the
        # configured branch: uv accepts the same metadata standalone and, under
        # a workspace root, the root ``workspace = true`` source overlay
        # replaces it at resolution time. A member ``[tool.uv.sources]`` git
        # entry is rejected by uv itself ("workspace member ... references a
        # Git in tool.uv.sources"), so the inline form is the only valid
        # dual-context declaration; branch refs re-resolve on every upgrade
        # (root and member locks resolve the same branch at different tips).
        branch = provider.value.branch
        inline = f"{head} @ git+{reference.url}@{branch}"
        return r[str].ok(
            f"{inline}; {marker_text}" if separator and marker_text else inline
        )

    @staticmethod
    def _repository_reference(
        distribution: str,
        *,
        repositories: t.SequenceOf[p.Infra.RepositoryRef],
        providers: t.SequenceOf[m.Infra.ProviderSpec],
    ) -> p.Result[p.Infra.RepositoryRef]:
        """Return one unambiguous reference for a distribution.

        A distribution the workspace does not declare is still resolvable: its
        canonical source is the provider contract plus its own name. That is
        derived from generic policy, never from a catalog of projects that
        flext-infra is forbidden to own.
        """
        matches = tuple(
            repository
            for repository in repositories
            if repository.distribution == distribution
        )
        if not matches:
            return r.ok(
                FlextInfraUtilitiesRepository.derived_repository_ref(
                    distribution, provider=providers[0]
                )
            )
        reference = matches[0]
        if any(
            item.url != reference.url or item.provider != reference.provider
            for item in matches[1:]
        ):
            return r.fail(
                f"repository catalog conflicts for distribution: {distribution}"
            )
        return r.ok(reference)

    @classmethod
    def _sync_dependency_groups(
        cls,
        document: t.Cli.TomlDocument,
        *,
        project_name: str,
        workspace: p.Infra.WorkspaceSpec,
        workspace_mode: c.Infra.MakeProfile,
        required_dev_dependencies: t.StrSequence,
    ) -> None:
        """Migrate optional dev dependencies and normalize declared groups."""
        project = u.Cli.toml_ensure_table(document, c.Infra.PROJECT)
        groups = u.Cli.toml_ensure_table(document, c.Infra.DEPENDENCY_GROUPS)
        optional = u.Cli.toml_table_child(project, c.Infra.OPTIONAL_DEPENDENCIES)
        optional_dev: t.StrSequence = ()
        if optional is not None:
            optional_dev = u.Cli.toml_as_string_list(
                u.Cli.toml_value(optional, str(c.Infra.DEV))
            )
        # SSOT required floors win over existing same-name pins: dedupe_specs
        # keeps the first occurrence, so toolchain floors must lead the merge.
        # Otherwise stale member pins override the declared fleet floor.
        required_dev = tuple(
            requirement
            for requirement in required_dev_dependencies
            if FlextInfraUtilitiesDependencies.dep_name(requirement) != project_name
        )
        dev = [
            *required_dev,
            *u.Cli.toml_as_string_list(u.Cli.toml_value(groups, str(c.Infra.DEV))),
            *optional_dev,
        ]
        if dev:
            u.Cli.toml_sync_string_list(
                groups,
                str(c.Infra.DEV),
                FlextInfraUtilitiesDependencies.dedupe_specs(tuple(dev)),
            )
        else:
            u.Cli.toml_remove_key_if_present(groups, str(c.Infra.DEV))

        codegen = u.Cli.toml_as_string_list(u.Cli.toml_value(groups, "codegen"))
        if codegen:
            u.Cli.toml_sync_string_list(
                groups,
                "codegen",
                FlextInfraUtilitiesDependencies.dedupe_specs(tuple(codegen)),
            )
        else:
            u.Cli.toml_remove_key_if_present(groups, "codegen")
        cls._sync_workspace_dependency_group(
            document,
            project_name=project_name,
            workspace=workspace,
            workspace_mode=workspace_mode,
        )

        if optional is not None:
            u.Cli.toml_remove_key_if_present(optional, str(c.Infra.DEV))
            if not tuple(optional):
                u.Cli.toml_remove_key_if_present(project, c.Infra.OPTIONAL_DEPENDENCIES)

    @classmethod
    def _sync_workspace_dependency_group(
        cls,
        document: t.Cli.TomlDocument,
        *,
        project_name: str,
        workspace: p.Infra.WorkspaceSpec,
        workspace_mode: c.Infra.MakeProfile,
    ) -> None:
        """Keep the generated workspace dependency group only at the root."""
        repository_root = cls._is_workspace_context_root(
            project_name=project_name,
            workspace=workspace,
            workspace_mode=workspace_mode,
        )
        groups = u.Cli.toml_table_child(document, c.Infra.DEPENDENCY_GROUPS)
        if groups is None:
            if not repository_root:
                return
            # The root dependency overlay is complete even when an older
            # pyproject has no groups table yet.
            groups = u.Cli.toml_ensure_table(document, c.Infra.DEPENDENCY_GROUPS)
        if repository_root:
            u.Cli.toml_sync_string_list(
                groups,
                "workspace",
                tuple(
                    sorted(project.distribution for project in workspace.subprojects)
                ),
            )
            return
        u.Cli.toml_remove_key_if_present(groups, "workspace")

    @classmethod
    def _validate_dependency_provenance(
        cls,
        document: t.Cli.TomlDocument,
        *,
        project_name: str,
        workspace: p.Infra.WorkspaceSpec,
        workspace_mode: c.Infra.MakeProfile,
    ) -> p.Result[bool]:
        """Require one internal dependency provenance for the active topology."""
        payload = u.Cli.toml_as_mapping(document) or {}
        project = u.Cli.toml_mapping_child(payload, c.Infra.PROJECT)
        if project is None:
            return r[bool].fail("pyproject content must define [project]")
        members = {member.distribution: member for member in workspace.subprojects}
        workspace_context_root = cls._is_workspace_context_root(
            project_name=project_name,
            workspace=workspace,
            workspace_mode=workspace_mode,
        )
        optional = u.Cli.toml_mapping_child(project, c.Infra.OPTIONAL_DEPENDENCIES)
        groups = u.Cli.toml_mapping_child(payload, c.Infra.DEPENDENCY_GROUPS)
        requirements = (
            *u.Cli.toml_as_string_list(project.get(c.Infra.DEPENDENCIES)),
            *(
                requirement
                for table in (optional or {}, groups or {})
                for group in table.values()
                for requirement in u.Cli.toml_as_string_list(group)
            ),
        )
        for requirement in requirements:
            member = members.get(
                FlextInfraUtilitiesDependencies.dep_name(requirement) or ""
            )
            if member is None:
                continue
            # Root documents express the workspace overlay; publishable
            # members keep the direct Git requirement so the same metadata
            # resolves standalone. uv replaces it with the root workspace
            # source when resolving the composed tree.
            if workspace_context_root and "@" in requirement.partition(";")[0]:
                return r[bool].fail(
                    "workspace dependency declares a conflicting direct source: "
                    f"{member.distribution}"
                )
            # Standalone provenance is catalog-owned: the catalog URL must be
            # HTTPS (fail-closed against ssh/file:// provenance).
            if not member.url.startswith("https://"):
                return r[bool].fail(
                    "internal dependency catalog provenance must be HTTPS: "
                    f"{member.distribution} ({member.url})"
                )
        return r[bool].ok(True)


__all__: list[str] = ["FlextInfraUtilitiesPyprojectRequirements"]
