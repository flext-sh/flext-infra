"""Autonomous library pyproject conformance through the flext-cli TOML facade."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from typing import TYPE_CHECKING

from flext_cli import r, u

from flext_infra import m
from flext_infra.constants import c
from flext_infra.typings import t

from .._utilities.dependencies import FlextInfraUtilitiesDependencies
from .._utilities.repository import FlextInfraUtilitiesRepository

if TYPE_CHECKING:
    from collections.abc import Iterator

    from flext_infra.protocols import p


class FlextInfraUtilitiesPyprojectConform:
    """Render root workspace and autonomous library metadata deterministically."""

    # This pure renderer replaces the mutating dependency path-sync command;
    # codegen is the only public orchestrator.

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

    @classmethod
    def _parsed_pyproject(
        cls, pyproject_content: str
    ) -> p.Result[t.Pair[t.Cli.TomlDocument, str]]:
        """Parse one pyproject source and return it with its declared project name."""
        source = u.Cli.toml_parse_text(pyproject_content)
        if source is None:
            return r[t.Pair[t.Cli.TomlDocument, str]].fail(
                "pyproject content is not valid TOML"
            )
        project = u.Cli.toml_table_child(source, c.Infra.PROJECT)
        if project is None:
            return r[t.Pair[t.Cli.TomlDocument, str]].fail(
                "pyproject content must define [project]"
            )
        project_name_raw = u.Cli.toml_value(project, c.Infra.NAME)
        if not isinstance(project_name_raw, str) or not project_name_raw.strip():
            return r[t.Pair[t.Cli.TomlDocument, str]].fail(
                "[project].name must be a non-empty string"
            )
        return r[t.Pair[t.Cli.TomlDocument, str]].ok((source, project_name_raw.strip()))

    @classmethod
    def _declared_uv_constraint_dependencies(
        cls, document: t.Cli.TomlDocument
    ) -> t.SequenceOf[str]:
        """Return the document-declared ``[tool.uv] constraint-dependencies``."""
        tool = u.Cli.toml_table_child(document, c.Infra.TOOL)
        if tool is None:
            return ()
        uv = u.Cli.toml_table_child(tool, "uv")
        if uv is None:
            return ()
        declared = u.Cli.toml_value(uv, "constraint-dependencies")
        return tuple(u.Cli.toml_as_string_list(declared))

    @classmethod
    def _rendered_conformed_document(
        cls,
        document: t.Cli.TomlDocument,
        *,
        project_name: str,
        workspace: p.Infra.WorkspaceSpec,
        workspace_mode: c.Infra.MakeProfile,
        invalid_render_error: str,
    ) -> p.Result[str]:
        """Validate dependency provenance, then render canonical TOML.

        ``invalid_render_error`` carries the only difference between the two
        public conformers: the message each reports for an unparsable render.
        """
        provenance_result = cls._validate_dependency_provenance(
            document,
            project_name=project_name,
            workspace=workspace,
            workspace_mode=workspace_mode,
        )
        if provenance_result.failure:
            return r[str].from_failure(provenance_result)
        rendered = u.Cli.toml_dumps(document)
        if u.Cli.toml_parse_text(rendered) is None:
            return r[str].fail(invalid_render_error)
        return r[str].ok(rendered)

    @classmethod
    def pyproject_conform(
        cls,
        pyproject_content: str,
        *,
        workspace: p.Infra.WorkspaceSpec,
        workspace_mode: c.Infra.MakeProfile,
        toolchain: p.Infra.ToolchainSpec,
        required_dev_dependencies: t.StrSequence,
        uv_link_mode: str | None = None,
        uv_exclude_dependencies: t.SequenceOf[p.Model] = (),
        namespace_scan_dirs: t.StrSequence | None = None,
    ) -> p.Result[str]:
        """Return canonical TOML with autonomous dependencies and root workspace."""
        parsed = cls._parsed_pyproject(pyproject_content)
        if parsed.failure:
            return r[str].from_failure(parsed)
        source, project_name = parsed.value
        cls._sync_dependency_groups(
            source,
            project_name=project_name,
            workspace=workspace,
            workspace_mode=workspace_mode,
            required_dev_dependencies=required_dev_dependencies,
        )
        normalized = cls._normalize_requirements(
            source,
            project_name=project_name,
            workspace=workspace,
            workspace_mode=workspace_mode,
            canonicalize_all=True,
        )
        if normalized.failure:
            return r[str].from_failure(normalized)
        cls._remove_legacy_tooling(source)
        typecheck_paths = cls._sync_typecheck_paths(source)
        if typecheck_paths.failure:
            return r[str].from_failure(typecheck_paths)
        namespace_scope = cls._sync_namespace_scope(source, namespace_scan_dirs)
        if namespace_scope.failure:
            return r[str].from_failure(namespace_scope)
        sources_result = cls._sync_uv_sources(
            source,
            project_name=project_name,
            workspace=workspace,
            workspace_mode=workspace_mode,
            link_mode=uv_link_mode or toolchain.uv_link_mode,
            exclude_dependencies=uv_exclude_dependencies,
            uv_environments=toolchain.uv_environments,
            constraint_dependencies=toolchain.uv_constraint_dependencies,
        )
        if sources_result.failure:
            return r[str].from_failure(sources_result)
        return cls._rendered_conformed_document(
            source,
            project_name=project_name,
            workspace=workspace,
            workspace_mode=workspace_mode,
            invalid_render_error=(
                "canonical pyproject rendering produced invalid TOML"
            ),
        )

    @classmethod
    def pyproject_dependencies_conform(
        cls,
        pyproject_content: str,
        *,
        workspace: p.Infra.WorkspaceSpec,
        workspace_mode: c.Infra.MakeProfile,
    ) -> p.Result[str]:
        """Conform only internal requirements and their root workspace overlay."""
        parsed = cls._parsed_pyproject(pyproject_content)
        if parsed.failure:
            return r[str].from_failure(parsed)
        source, project_name = parsed.value
        provenance_result = cls._validate_dependency_provenance(
            source,
            project_name=project_name,
            workspace=workspace,
            workspace_mode=workspace_mode,
        )
        if provenance_result.failure:
            return r[str].from_failure(provenance_result)
        workspace_context_root = cls._is_workspace_context_root(
            project_name=project_name,
            workspace=workspace,
            workspace_mode=workspace_mode,
        )
        if workspace_context_root:
            sources_result = cls._validate_root_uv_sources(source, workspace=workspace)
            if sources_result.failure:
                return r[str].from_failure(sources_result)
        normalized = cls._normalize_requirements(
            source,
            project_name=project_name,
            workspace=workspace,
            workspace_mode=workspace_mode,
            canonicalize_all=False,
        )
        if normalized.failure:
            return r[str].from_failure(normalized)
        cls._sync_workspace_dependency_group(
            source,
            project_name=project_name,
            workspace=workspace,
            workspace_mode=workspace_mode,
        )
        # On the dependency-only surface the declared document constraints are
        # the SSOT: they flow through the same uv-pin filter as the toolchain
        # path so a legacy `uv` cap is removed and every other constraint is
        # preserved verbatim.
        sources_result = (
            r[bool].ok(True)
            if workspace_context_root
            else cls._sync_uv_sources(
                source,
                project_name=project_name,
                workspace=workspace,
                workspace_mode=workspace_mode,
                constraint_dependencies=cls._declared_uv_constraint_dependencies(
                    source
                ),
            )
        )
        if sources_result.failure:
            return r[str].from_failure(sources_result)
        return cls._rendered_conformed_document(
            source,
            project_name=project_name,
            workspace=workspace,
            workspace_mode=workspace_mode,
            invalid_render_error="dependency conformance produced invalid TOML",
        )

    @classmethod
    def _normalize_requirements(
        cls,
        document: t.Cli.TomlDocument,
        *,
        project_name: str,
        workspace: p.Infra.WorkspaceSpec,
        workspace_mode: c.Infra.MakeProfile,
        canonicalize_all: bool,
    ) -> p.Result[bool]:
        """Render internal requirements for root workspace or detached operation."""
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
            canonicalize_all=canonicalize_all,
            revisions=workspace.project.dependency_revisions
            if workspace.project
            else {},
            workspace_dependencies=workspace_dependencies,
        )
        if normalized.failure:
            return normalized
        for section, group_name in cls.requirement_group_fields(document, project):
            group_result = cls._normalize_requirement_field(
                section,
                group_name,
                canonicalize_all=canonicalize_all,
                revisions=workspace.project.dependency_revisions
                if workspace.project
                else {},
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
        canonicalize_all: bool,
        revisions: t.StrMapping,
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
                item, revisions=revisions, workspace_dependencies=workspace_dependencies
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
        revisions: t.StrMapping,
        workspace_dependencies: frozenset[str],
    ) -> p.Result[str]:
        """Render one internal requirement from its own declared Git source.

        The requirement line is the only authority for an internal
        dependency's canonical URL and branch: it is parsed and canonicalized
        (transport scheme only), never rewritten from provider policy. The
        workspace manifest may pin the ref to an explicit immutable revision —
        a declared SHA, never an invented default. A source-less internal
        dependency that the active workspace overlay does not own is a loud
        failure.
        """
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
        source = FlextInfraUtilitiesRepository.declared_git_source(requirement)
        if source.failure:
            return r[str].from_failure(source)
        url, declared_ref = source.value
        if not url:
            return r[str].fail(
                "internal flext dependency declares no direct git source and "
                f"is not a workspace dependency: {dependency_name}"
            )
        ref = str(revisions.get(dependency_name, declared_ref))
        # The declared source stays authoritative under a workspace root too:
        # uv replaces it there with the root ``workspace = true`` overlay, and
        # a member ``[tool.uv.sources]`` git entry is rejected by uv itself,
        # so the inline form is the only valid dual-context declaration.
        inline = f"{head} @ git+{url}@{ref}"
        return r[str].ok(
            f"{inline}; {marker_text}" if separator and marker_text else inline
        )

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
        # Otherwise stale member pins override the declared fleet floor. One
        # exception is structural: a bare internal floor name carries no Git
        # source and no version to enforce, so a live requirement that declares
        # its own direct source is the authority for that dependency and the
        # floor yields to it.
        live_dev = u.Cli.toml_as_string_list(u.Cli.toml_value(groups, str(c.Infra.DEV)))
        sourced_live_names = {
            name
            for requirement in live_dev
            if (name := FlextInfraUtilitiesDependencies.dep_name(requirement))
            and cls._declares_direct_source(requirement)
        }
        required_dev = tuple(
            requirement
            for requirement in required_dev_dependencies
            if FlextInfraUtilitiesDependencies.dep_name(requirement) != project_name
            and not cls._floor_yields_to_declared_source(
                requirement, sourced_live_names
            )
        )
        dev = [*required_dev, *live_dev, *optional_dev]
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

    @staticmethod
    def _declares_direct_source(requirement: str) -> bool:
        """Whether one requirement line declares a direct ``@ source``."""
        return "@" in requirement.partition(";")[0]

    @staticmethod
    def _floor_yields_to_declared_source(
        requirement: str, sourced_live_names: frozenset[str] | set[str]
    ) -> bool:
        """Whether a bare internal floor name must yield to a declared source."""
        name = FlextInfraUtilitiesDependencies.dep_name(requirement)
        return (
            name is not None
            and name.startswith("flext-")
            and not FlextInfraUtilitiesPyprojectConform._declares_direct_source(
                requirement
            )
            and name in sourced_live_names
        )

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

    @staticmethod
    def _is_topology_repository_root(
        *, project_name: str, workspace: p.Infra.WorkspaceSpec
    ) -> bool:
        """Identify the real multi-project root, not an autonomous repository."""
        return bool(workspace.subprojects) and (
            project_name == workspace.repository.distribution
        )

    @classmethod
    def _is_workspace_context_root(
        cls,
        *,
        project_name: str,
        workspace: p.Infra.WorkspaceSpec,
        workspace_mode: c.Infra.MakeProfile,
    ) -> bool:
        """Identify the root only when the active topology is a workspace."""
        return (
            workspace_mode is c.Infra.MakeProfile.WORKSPACE
            and cls._is_topology_repository_root(
                project_name=project_name, workspace=workspace
            )
        )

    @staticmethod
    def _remove_legacy_tooling(document: t.Cli.TomlDocument) -> None:
        """Delete legacy packaging owners superseded by canonical conformance.

        The ``[tool.flext]`` table is preserved because it carries project-local
        tooling policy unrelated to repository topology.
        """
        tool = u.Cli.toml_table_child(document, c.Infra.TOOL)
        if tool is None:
            return
        u.Cli.toml_remove_key_if_present(tool, c.Infra.POETRY)

    @staticmethod
    def _sync_namespace_scope(
        document: t.Cli.TomlDocument, namespace_scan_dirs: t.StrSequence | None
    ) -> p.Result[bool]:
        """Sync ``[tool.flext.namespace].scan_dirs`` from the project SSOT.

        ``None`` or an empty sequence leaves the section untouched: projects
        without a declared scope keep the dynamic every-root behavior. A
        non-empty sequence is the workspace manifest's production scope
        (cosmos-3flk9 decision A).
        """
        if not namespace_scan_dirs:
            return r[bool].ok(True)
        namespace = u.Cli.toml_ensure_path(document, c.Infra.CONFORM_NAMESPACE_TABLE)
        u.Cli.toml_sync_string_list(namespace, "scan_dirs", list(namespace_scan_dirs))
        return r[bool].ok(True)

    @staticmethod
    def _sync_typecheck_paths(document: t.Cli.TomlDocument) -> p.Result[bool]:
        """Remove checkout-absolute type checker interpreter pins.

        Search paths belong to FlextInfraExtraPathsManager. Top-level
        ``venv`` / ``venvPath`` belong to deps modernize (root vs child
        runtime). Conform must not strip those or gen oscillates.
        """
        tool = u.Cli.toml_table_child(document, c.Infra.TOOL)
        if tool is None:
            return r[bool].ok(True)
        pyrefly = u.Cli.toml_table_child(tool, c.Infra.PYREFLY)
        if pyrefly is not None:
            u.Cli.toml_remove_key_if_present(pyrefly, "python-interpreter-path")

        pyright = u.Cli.toml_table_child(tool, c.Infra.PYRIGHT)
        if pyright is None:
            return r[bool].ok(True)

        # venv / venvPath are owned by deps modernize (workspace vs child
        # runtime). Conform only strips checkout-absolute interpreter pins.
        interpreter_keys = ("pythonPath", "pythonInterpreterPath")
        for key in interpreter_keys:
            u.Cli.toml_remove_key_if_present(pyright, key)
        raw_environments = u.Cli.json_as_sequence(
            u.Cli.toml_value(pyright, "executionEnvironments")
        )
        normalized_environments: t.JsonValueList = []
        for index, environment in enumerate(raw_environments):
            if not isinstance(environment, Mapping):
                return r[bool].fail(
                    f"tool.pyright.executionEnvironments[{index}] must be a mapping"
                )
            mapping = t.Cli.JSON_MAPPING_ADAPTER.validate_python(environment)
            normalized: t.JsonDict = dict(mapping)
            root = normalized.get("root")
            normalized[c.Infra.EXTRA_PATHS] = ["src"] if root == "src" else [".", "src"]
            for key in ("venv", "venvPath", "pythonPath", "pythonInterpreterPath"):
                normalized.pop(key, None)
            normalized_environments.append(normalized)
        if raw_environments:
            u.Cli.toml_sync_value(
                pyright, "executionEnvironments", normalized_environments
            )
        return r[bool].ok(True)

    @classmethod
    def _document_requirement_lines(
        cls, document: t.Cli.TomlDocument
    ) -> p.Result[list[str]]:
        """Collect every declared requirement line of one pyproject document."""
        payload = u.Cli.toml_as_mapping(document)
        if payload is None:
            return r[list[str]].fail("pyproject document is not a TOML mapping")
        requirements: list[str] = []
        project = payload.get(c.Infra.PROJECT)
        if isinstance(project, Mapping):
            for key in (c.Infra.DEPENDENCIES, c.Infra.OPTIONAL_DEPENDENCIES):
                requirements.extend(cls.raw_requirement_values(project.get(key)))
        groups = payload.get(c.Infra.DEPENDENCY_GROUPS)
        if isinstance(groups, Mapping):
            for group in groups.values():
                requirements.extend(cls.raw_requirement_values(group))
        return r[list[str]].ok(requirements)

    @classmethod
    def _dependency_overrides(
        cls, workspace: p.Infra.WorkspaceSpec, *, requirements: t.SequenceOf[str]
    ) -> p.Result[t.VariadicTuple[str]]:
        """Render declared immutable revisions as uv override-dependencies.

        A manifest-declared revision pins one external provider-owned
        dependency to an explicit SHA. The URL is still detected — from that
        dependency's own declared direct Git source in the same document —
        so a pin without a declared source fails loudly instead of borrowing
        an URL from any catalog.
        """
        revisions: t.StrMapping = (
            workspace.project.dependency_revisions if workspace.project else {}
        )
        members = {member.distribution for member in workspace.subprojects}
        declared: dict[str, str] = {}
        for requirement in requirements:
            name = FlextInfraUtilitiesDependencies.dep_name(requirement)
            if name in revisions:
                declared[name] = requirement
        overrides: list[str] = []
        for name in sorted(revisions):
            if name in members or not name.startswith("flext-"):
                return r[tuple[str, ...]].fail(
                    f"dependency revision must name an external provider dependency: {name}"
                )
            source = FlextInfraUtilitiesRepository.declared_git_source(
                declared.get(name, name)
            )
            if source.failure:
                return r[tuple[str, ...]].from_failure(source)
            url, _ref = source.value
            if not url:
                return r[tuple[str, ...]].fail(
                    "pinned dependency declares no direct git source to detect "
                    f"its URL from: {name}"
                )
            overrides.append(f"{name} @ git+{url}@{revisions[name]}")
        return r[tuple[str, ...]].ok(tuple(overrides))

    @classmethod
    def _sync_uv_sources(
        cls,
        document: t.Cli.TomlDocument,
        *,
        project_name: str,
        workspace: p.Infra.WorkspaceSpec,
        workspace_mode: c.Infra.MakeProfile,
        link_mode: str | None = None,
        constraint_dependencies: t.SequenceOf[str] | None = None,
        exclude_dependencies: t.SequenceOf[p.Model] | None = None,
        uv_environments: t.StrSequence | None = None,
    ) -> p.Result[bool]:
        """Keep managed uv sources only as the root local-workspace overlay."""
        repository_root = cls._is_workspace_context_root(
            project_name=project_name,
            workspace=workspace,
            workspace_mode=workspace_mode,
        )
        declared_requirements = cls._document_requirement_lines(document)
        if declared_requirements.failure:
            return r[bool].from_failure(declared_requirements)
        overrides = cls._dependency_overrides(
            workspace, requirements=declared_requirements.value
        )
        if overrides.failure:
            return r[bool].from_failure(overrides)
        tool = u.Cli.toml_table_child(document, c.Infra.TOOL)
        if tool is None:
            if (
                not repository_root
                and link_mode is None
                and not exclude_dependencies
                and not constraint_dependencies
                and not overrides.value
            ):
                return r[bool].ok(True)
            tool = u.Cli.toml_ensure_table(document, c.Infra.TOOL)
        uv = u.Cli.toml_table_child(tool, "uv")
        if uv is None:
            if (
                not repository_root
                and link_mode is None
                and not exclude_dependencies
                and not constraint_dependencies
                and not overrides.value
            ):
                return r[bool].ok(True)
            uv = u.Cli.toml_ensure_table(tool, "uv")
        if overrides.value:
            u.Cli.toml_sync_string_list(uv, "override-dependencies", overrides.value)
        else:
            u.Cli.toml_remove_key_if_present(uv, "override-dependencies")
        u.Cli.toml_remove_key_if_present(uv, "required-version")
        # Constraints are SSOT-rendered: the declared config value is the only
        # source, so a removed declaration exterminates the key everywhere and
        # no orphan cap can survive without an owner (flext-gzfd2 class).
        selected_constraints = tuple(constraint_dependencies or ())
        retained_constraints = tuple(
            requirement
            for requirement in selected_constraints
            if FlextInfraUtilitiesDependencies.dep_name(requirement) != "uv"
        )
        if retained_constraints:
            u.Cli.toml_sync_string_list(
                uv, "constraint-dependencies", retained_constraints
            )
        else:
            u.Cli.toml_remove_key_if_present(uv, "constraint-dependencies")
        if link_mode is not None:
            u.Cli.toml_sync_value(uv, "link-mode", link_mode)
        # The supply-chain cooldown was exterminated fleet-wide (flext-fphyv):
        # uv resolves every version published up to now. Removed declarations
        # exterminate the keys everywhere so no orphan cap survives without an
        # owner (flext-gzfd2 class).
        u.Cli.toml_remove_key_if_present(uv, "exclude-newer")
        u.Cli.toml_remove_key_if_present(uv, "exclude-newer-package")
        # Environments come from the fleet toolchain SSOT: an empty declaration
        # removes the key so uv resolves every environment, and a declared
        # sequence skips the splits the fleet does not support (win32 resolves
        # meltano's structlog cap against flext-core's floor and is
        # unsatisfiable).
        if uv_environments is not None and uv_environments:
            # Declared as list[JsonValue], not list[str]: `list` is invariant,
            # so the narrower element type is not assignable to the writer's
            # parameter even though every element is a valid JsonValue.
            environments: list[t.JsonValue] = list(uv_environments)
            u.Cli.toml_sync_value(uv, "environments", environments)
        elif uv_environments is not None:
            u.Cli.toml_remove_key_if_present(uv, "environments")
        # Project is a flext-infra routing key only; uv scoped form is
        # {package={name, version?}, dependencies=[...]} (uv settings docs).
        # Emit on every owning pyproject so standalone CI clones resolve;
        # do not gate on owns_uv_root_policy (that stripped member excludes).
        if exclude_dependencies is not None:
            exclude_payload = list(
                t.Cli.JSON_LIST_ADAPTER.validate_python([
                    {
                        key: value
                        for key, value in item.model_dump(
                            mode="json", exclude_none=True
                        ).items()
                        if key != "project"
                    }
                    for item in exclude_dependencies
                ])
            )
            if exclude_payload:
                u.Cli.toml_sync_value(uv, "exclude-dependencies", exclude_payload)
            else:
                u.Cli.toml_remove_key_if_present(uv, "exclude-dependencies")
        member_paths = tuple(member.path.as_posix() for member in workspace.subprojects)
        # Only an actual multi-project owner declares a uv workspace. A leaf
        # can also be a composed member; inserting an empty workspace there
        # breaks execution from the parent with uv's nested-workspace error.
        if repository_root and member_paths:
            workspace_table = u.Cli.toml_table_child(uv, "workspace")
            if workspace_table is None:
                workspace_table = u.Cli.toml_ensure_table(uv, "workspace")
            u.Cli.toml_sync_string_list(workspace_table, "members", member_paths)
        else:
            u.Cli.toml_remove_key_if_present(uv, "workspace")
        sources = u.Cli.toml_table_child(uv, "sources")
        if sources is None and repository_root:
            sources = u.Cli.toml_ensure_table(uv, "sources")
        if sources is None:
            if not repository_root and not tuple(uv):
                u.Cli.toml_remove_key_if_present(tool, "uv")
            return r[bool].ok(True)
        workspace_names = {member.distribution for member in workspace.subprojects}
        for source_name in tuple(sources):
            # Member documents resolve internal siblings through the direct
            # Git requirement; a git [tool.uv.sources] entry on a workspace
            # member is rejected by uv itself, and only the root carries the
            # workspace overlay.
            if source_name.startswith("flext-") and (
                not repository_root or source_name not in workspace_names
            ):
                u.Cli.toml_remove_key_if_present(sources, source_name)
        if repository_root:
            for member in workspace.subprojects:
                u.Cli.toml_sync_mapping_table(
                    sources, member.distribution, {"workspace": True}
                )
        elif not tuple(sources):
            u.Cli.toml_remove_key_if_present(uv, "sources")
        if not repository_root and not tuple(uv):
            u.Cli.toml_remove_key_if_present(tool, "uv")
        return r[bool].ok(True)

    @staticmethod
    def raw_requirement_values(raw: object) -> list[str]:
        """Collect raw requirement strings from a dependencies value or group table.

        ``project.dependencies`` is one array while ``optional-dependencies``
        and ``dependency-groups`` are tables of arrays; this is the single
        owner of that shape for read-only requirement scans.
        """
        if isinstance(raw, Mapping):
            values: list[str] = []
            for group in raw.values():
                values.extend(
                    FlextInfraUtilitiesPyprojectConform.raw_requirement_values(group)
                )
            return values
        if isinstance(raw, (list, tuple)):
            return [item for item in raw if isinstance(item, str)]
        return []

    @staticmethod
    def _resolved_root_sources(
        *, workspace: p.Infra.WorkspaceSpec
    ) -> MutableMapping[str, MutableMapping[str, t.JsonValue]]:
        """Resolve the workspace source overlay from the declared topology."""
        return {
            member.distribution: {"workspace": True} for member in workspace.subprojects
        }

    @classmethod
    def _validate_root_uv_sources(
        cls, document: t.Cli.TomlDocument, *, workspace: p.Infra.WorkspaceSpec
    ) -> p.Result[bool]:
        """Validate the root overlay without rewriting out-of-order TOML tables."""
        payload = u.Cli.toml_as_mapping(document)
        if payload is None:
            return r[bool].fail("pyproject document is not a TOML mapping")
        tool = payload.get(c.Infra.TOOL)
        if not isinstance(tool, Mapping):
            return r[bool].fail("root pyproject must define [tool]")
        uv = tool.get("uv")
        if not isinstance(uv, Mapping):
            return r[bool].fail("root pyproject must define [tool.uv]")
        declared_requirements = cls._document_requirement_lines(document)
        if declared_requirements.failure:
            return r[bool].from_failure(declared_requirements)
        overrides = cls._dependency_overrides(
            workspace, requirements=declared_requirements.value
        )
        if overrides.failure:
            return r[bool].from_failure(overrides)
        declared = u.Cli.toml_as_string_list(uv.get("override-dependencies"))
        if tuple(declared) != overrides.value:
            return r[bool].fail("root dependency overrides differ from workspace SSOT")
        uv_workspace = uv.get("workspace")
        if not isinstance(uv_workspace, Mapping):
            return r[bool].fail("root pyproject must define [tool.uv.workspace]")
        validated_members = u.validate_value(
            t.Infra.STR_SEQ_ADAPTER, uv_workspace.get("members"), strict=True
        )
        if validated_members.failure:
            return r[bool].fail_op(
                "validate root uv workspace package entries", validated_members.error
            )
        members = validated_members.value
        expected_members = tuple(
            member.path.as_posix() for member in workspace.subprojects
        )
        if tuple(members) != expected_members:
            return r[bool].fail(
                "root uv workspace package entries differ from workspace SSOT"
            )
        sources = uv.get("sources")
        if not isinstance(sources, Mapping):
            return r[bool].fail("root pyproject must define [tool.uv.sources]")
        expected_sources = cls._resolved_root_sources(workspace=workspace)
        if tuple(sources) != tuple(expected_sources):
            return r[bool].fail("root uv workspace sources differ from workspace SSOT")
        for source_name, expected_source in expected_sources.items():
            source = sources.get(source_name)
            if (
                not isinstance(source, Mapping)
                or tuple(source) != tuple(expected_source)
                or dict(source) != expected_source
            ):
                return r[bool].fail(
                    f"root uv workspace sources differ from workspace SSOT: {source_name}"
                )
        return r[bool].ok(True)

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
        payload = u.Cli.toml_as_mapping(document)
        if payload is None:
            return r[bool].fail("pyproject document is not a TOML mapping")
        member_names = frozenset(
            member.distribution for member in workspace.subprojects
        )
        raw_values: list[str] = []
        project = payload.get(c.Infra.PROJECT)
        if not isinstance(project, Mapping):
            return r[bool].fail("pyproject content must define [project]")
        workspace_context_root = cls._is_workspace_context_root(
            project_name=project_name,
            workspace=workspace,
            workspace_mode=workspace_mode,
        )
        for key in (c.Infra.DEPENDENCIES, c.Infra.OPTIONAL_DEPENDENCIES):
            value = project.get(key)
            if isinstance(value, Mapping):
                for group in value.values():
                    raw_values.extend(u.Cli.toml_as_string_list(group))
            else:
                raw_values.extend(u.Cli.toml_as_string_list(value))
        groups = payload.get(c.Infra.DEPENDENCY_GROUPS)
        if isinstance(groups, Mapping):
            for group in groups.values():
                raw_values.extend(u.Cli.toml_as_string_list(group))
        for requirement in raw_values:
            dependency_name = FlextInfraUtilitiesDependencies.dep_name(requirement)
            if dependency_name not in member_names:
                continue
            # Root documents express the workspace overlay; publishable
            # members keep the direct Git requirement so the same metadata
            # resolves standalone. uv replaces it with the root workspace
            # source when resolving the composed tree.
            has_direct_source = "@" in requirement.partition(";")[0]
            if workspace_context_root and has_direct_source:
                return r[bool].fail(
                    "workspace dependency declares a conflicting direct source: "
                    f"{dependency_name}"
                )
            # Standalone provenance is manifest-owned: [tool.uv.sources] is
            # rendered from the workspace member URL, so the requirement line
            # stays a plain distribution name and the manifest URL must be
            # HTTPS (fail-closed against ssh/file:// provenance).
            member = next(
                (
                    item
                    for item in workspace.subprojects
                    if item.distribution == dependency_name
                ),
                None,
            )
            if member is not None and not member.url.startswith("https://"):
                return r[bool].fail(
                    "internal dependency manifest provenance must be HTTPS: "
                    f"{dependency_name} ({member.url})"
                )
        return r[bool].ok(True)

    @classmethod
    def overlay_preserved(
        cls,
        rendered: str,
        live: str | None,
        *,
        preserve_project_keys: t.StrSequence | None = None,
        managed_tool_tables: t.StrSequence | None = None,
    ) -> p.Result[str]:
        """Keep live CUSTOM project keys and unmanaged tool tables."""
        if preserve_project_keys is not None and managed_tool_tables is not None:
            project_keys = preserve_project_keys
            tool_tables = managed_tool_tables
        else:
            from flext_infra import config as infra_config

            spec: m.Infra.ManagedFileSpec | None = next(
                (
                    item
                    for item in infra_config.Infra.codegen.managed_files
                    if item.path.as_posix() == c.Infra.PYPROJECT_FILENAME
                ),
                None,
            )
            if spec is None:
                return r[str].fail("pyproject.toml is missing from managed_files")
            project_keys = (
                spec.preserve_project_keys
                if preserve_project_keys is None
                else preserve_project_keys
            )
            tool_tables = (
                spec.managed_tool_tables
                if managed_tool_tables is None
                else managed_tool_tables
            )
        rendered_payload = u.Cli.toml_mapping_from_text(rendered)
        # An absent live file takes the same canonicalization path as a present
        # one: the projection is the parse-merge-dump form, so first publication
        # and every later conform produce byte-identical output (fixed point).
        empty_payload: t.JsonMapping = {}
        live_payload = (
            u.Cli.toml_mapping_from_text(live) if live is not None else empty_payload
        )
        if rendered_payload is None:
            return r[str].fail("rendered pyproject is not valid TOML")
        if live_payload is None:
            return r[str].fail("live pyproject is not valid TOML")
        merged = dict(rendered_payload)
        project = dict(u.Cli.toml_mapping_child(merged, c.Infra.PROJECT) or {})
        live_project = u.Cli.toml_mapping_child(live_payload, c.Infra.PROJECT) or {}
        for key in project_keys:
            if key in live_project:
                if key == c.Infra.DEPENDENCIES:
                    validated_required = u.validate_value(
                        t.Infra.STR_SEQ_ADAPTER, project.get(key, []), strict=True
                    )
                    if validated_required.failure:
                        return r[str].fail_op(
                            "validate runtime dependencies", validated_required.error
                        )
                    validated_custom = u.validate_value(
                        t.Infra.STR_SEQ_ADAPTER, live_project[key], strict=True
                    )
                    if validated_custom.failure:
                        return r[str].fail_op(
                            "validate runtime dependencies", validated_custom.error
                        )
                    required = validated_required.value
                    custom = validated_custom.value
                    owned_names = {
                        FlextInfraUtilitiesDependencies.dep_name(item)
                        for item in required
                    }
                    # Profiles own same-name requirements. CUSTOM requirements
                    # retain full specs, including distinct markers for one name.
                    project[key] = [
                        *dict.fromkeys((
                            *required,
                            *(
                                item
                                for item in custom
                                if FlextInfraUtilitiesDependencies.dep_name(item)
                                not in owned_names
                            ),
                        ))
                    ]
                else:
                    project[key] = live_project[key]
        merged[c.Infra.PROJECT] = project
        # Preserve project dev additions before conformance reapplies fleet floors.
        groups = dict(u.Cli.toml_mapping_child(merged, c.Infra.DEPENDENCY_GROUPS) or {})
        live_groups = (
            u.Cli.toml_mapping_child(live_payload, c.Infra.DEPENDENCY_GROUPS) or {}
        )
        if str(c.Infra.DEV) in live_groups:
            groups[str(c.Infra.DEV)] = live_groups[str(c.Infra.DEV)]
            merged[c.Infra.DEPENDENCY_GROUPS] = groups
        tool = dict(u.Cli.toml_mapping_child(merged, c.Infra.TOOL) or {})
        live_tool = u.Cli.toml_mapping_child(live_payload, c.Infra.TOOL) or {}
        managed = frozenset(tool_tables)
        tool.update({
            key: value for key, value in live_tool.items() if key not in managed
        })
        merged[c.Infra.TOOL] = tool
        return r[str].ok(u.Cli.toml_dumps(u.Cli.toml_document_from_mapping(merged)))


__all__: list[str] = ["FlextInfraUtilitiesPyprojectConform"]
