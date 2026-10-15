"""Public pyproject conformer over the requirement and uv-source owners.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Annotated

from flext_cli import u

from flext_infra import c, m, p, r, t
from flext_infra._utilities import FlextInfraUtilitiesDependencies
from flext_infra._utilities._pyproject import FlextInfraUtilitiesPyprojectUvSources
from flext_infra._utilities._pyproject._requirements_provenance import (
    FlextInfraUtilitiesPyprojectRequirementsProvenance,
)
from flext_infra._utilities._pyproject.overlay import (
    FlextInfraUtilitiesPyprojectOverlay,
)


class FlextInfraUtilitiesPyprojectDocument(FlextInfraUtilitiesPyprojectUvSources):
    """Render root workspace and autonomous library metadata deterministically."""

    class PyprojectConformOptions(m.ImmutableValueModel):
        """Detected integration provenance for internal requirements and dev floors."""

        flext_line: Annotated[
            m.Infra.WorkspaceIntegrationSpec | None,
            m.Field(
                description="Detected provider and branch for internal requirements",
            ),
        ] = None
        repository_root: Annotated[
            Path | None,
            m.Field(description="Canonical root for declared member metadata"),
        ] = None

    @classmethod
    def _parsed_pyproject(
        cls,
        pyproject_content: str,
    ) -> p.Result[t.Triple[t.Cli.TomlDocument, str, t.JsonMapping]]:
        """Parse a source, its distribution identity, and its mapping once.

        Returns:
            The validated document, project name, and metadata mapping.

        """
        result = r[t.Triple[t.Cli.TomlDocument, str, t.JsonMapping]]
        source = u.Cli.toml_parse_text(pyproject_content)
        if source is None:
            return result.fail(
                "pyproject content is not valid TOML",
            )
        project = u.Cli.toml_table_child(source, c.Infra.PROJECT)
        if project is None:
            return result.fail(
                "pyproject content must define [project]",
            )
        project_name_raw = u.Cli.toml_value(project, c.Infra.NAME)
        if not isinstance(project_name_raw, str) or not project_name_raw.strip():
            return result.fail(
                "[project].name must be a non-empty string",
            )
        payload = u.Cli.toml_as_mapping(source)
        if payload is None:
            return result.fail("root metadata is not a TOML mapping")
        return result.ok((source, project_name_raw.strip(), payload))

    @classmethod
    def pyproject_conform(
        cls,
        pyproject_content: str,
        *,
        workspace: m.Infra.WorkspaceSpec,
        required_dev_dependencies: t.StrSequence,
        uv_resolution: m.Infra.UvResolutionSpec,
        options: PyprojectConformOptions | None = None,
    ) -> p.Result[str]:
        """Return canonical TOML with autonomous dependencies and uv policy.

        The workspace manifest owns the topology facts, including the
        namespace production scope its project declares and the members a
        workspace root environment serves. Attached members, of any family,
        render on the workspace's declared integration line; ``options.flext_line``
        is the detected FLEXT integration line whose branch re-renders commit
        residue in the other internal requirements. Without a line, both fail
        loudly. Generated bare dev floors use the same detected provider line as
        the scaffold; CUSTOM requirements never acquire provenance from provider
        policy unless that dependency is a declared floor.

        Returns:
            Canonical TOML with autonomous dependencies and uv policy.

        """
        parsed = cls._parsed_pyproject(pyproject_content)
        if parsed.failure:
            return r[str].from_failure(parsed)
        source, project_name = parsed.value[0], parsed.value[1]
        provenance = options if options is not None else cls.PyprojectConformOptions()
        environment = cls._member_environment_requirements(workspace, provenance)
        if environment.failure:
            return r[str].from_failure(environment)
        member_requests, member_groups, member_requirements = environment.value
        member_groups = cls.active_development_requirements(member_groups)
        custom_groups: t.Pair[t.StrSequence, t.StrSequence] = ((), ())
        if workspace.repository.role == c.Infra.MakeProfile.WORKSPACE:
            custom = cls._sync_root_environment_groups(
                source,
                pyproject_content,
                member_groups,
            )
            if custom.failure:
                return r[str].from_failure(custom)
            custom_groups = custom.value
        cls._sync_dependency_groups(
            source,
            project_name=project_name,
            required_dev_dependencies=required_dev_dependencies,
        )
        cls._sync_member_environment_dev(
            source,
            (*member_requests, *member_groups, *member_requirements),
        )
        requirement_sources = cls._normalized_requirement_sources(
            source,
            project_name,
            workspace,
            required_dev_dependencies,
            provenance,
        )
        if requirement_sources.failure:
            return r[str].from_failure(requirement_sources)
        (
            local_requirements,
            declared_sources,
            candidate_sources,
        ) = requirement_sources.value
        if workspace.repository.role == c.Infra.MakeProfile.WORKSPACE:
            owned = cls._sync_root_environment_provenance(
                source,
                custom_groups,
                FlextInfraUtilitiesPyprojectRequirementsProvenance(
                    declared_sources=declared_sources,
                    candidate_sources=candidate_sources,
                    family_line=provenance.flext_line.branch
                    if provenance.flext_line
                    else None,
                ),
            )
            if owned.failure:
                return r[str].from_failure(owned)
        cls._remove_legacy_tooling(source)
        return cls._synced_conform_tables(
            source,
            uv_resolution=uv_resolution,
            candidate_sources=candidate_sources,
            local_requirements=(*local_requirements, *member_requirements),
            workspace=workspace,
        ).flat_map(lambda _synced: cls._render_pyproject(source))

    @classmethod
    def _normalized_requirement_sources(
        cls,
        source: t.Cli.TomlDocument,
        project_name: str,
        workspace: m.Infra.WorkspaceSpec,
        required_dev_dependencies: t.StrSequence,
        provenance: PyprojectConformOptions,
    ) -> p.Result[t.Triple[t.StrSequence, t.StrMapping, t.StrMapping]]:
        """Resolve declared origins before normalizing development requirements.

        Returns:
            Local requirements and source mappings, or the original failure.

        """
        local = cls.document_requirement_lines(source)
        if local.failure:
            return r[t.Triple[t.StrSequence, t.StrMapping, t.StrMapping]].from_failure(
                local,
            )
        origins = cls._declared_requirement_sources(
            source,
            project_name=project_name,
            workspace=workspace,
            required_dev_dependencies=required_dev_dependencies,
            flext_line=provenance.flext_line,
        )
        if origins.failure:
            return r[t.Triple[t.StrSequence, t.StrMapping, t.StrMapping]].from_failure(
                origins,
            )
        declared, candidates = origins.value
        normalized = cls._normalize_requirements(
            source,
            declared_sources=declared,
            candidate_sources=candidates,
            family_line=provenance.flext_line.branch
            if provenance.flext_line is not None
            else None,
        )
        if normalized.failure:
            return r[t.Triple[t.StrSequence, t.StrMapping, t.StrMapping]].from_failure(
                normalized,
            )
        return r[t.Triple[t.StrSequence, t.StrMapping, t.StrMapping]].ok(
            (local.value, declared, candidates),
        )

    @staticmethod
    def _sync_member_environment_dev(
        source: t.Cli.TomlDocument,
        requirements: t.StrSequence,
    ) -> None:
        """Retain marker variants when merging selected member requirements."""
        groups = u.Cli.toml_ensure_table(source, c.Infra.DEPENDENCY_GROUPS)
        dev = u.Cli.toml_as_string_list(u.Cli.toml_value(groups, str(c.Infra.DEV)))
        u.Cli.toml_sync_string_list(
            groups,
            str(c.Infra.DEV),
            sorted({*dev, *requirements}),
        )

    @classmethod
    def _sync_root_environment_groups(
        cls,
        source: t.Cli.TomlDocument,
        original: str,
        member_groups: t.StrSequence,
    ) -> p.Result[t.Pair[t.StrSequence, t.StrSequence]]:
        """Retain custom development groups before adding current member requirements.

        Returns:
            Custom DEV and CODEGEN requirements, or the original parse failure.

        """
        payload = u.Cli.toml_as_mapping(source)
        if payload is None:
            return r[t.Pair[t.StrSequence, t.StrSequence]].fail(
                "root metadata is not a TOML mapping",
            )
        groups = u.Cli.toml_ensure_table(source, c.Infra.DEPENDENCY_GROUPS)
        retained: t.MutableMappingKV[str, t.StrSequence] = {}
        for group in (str(c.Infra.DEV), c.Infra.DependencyGroup.CODEGEN):
            custom = FlextInfraUtilitiesPyprojectOverlay.custom_dev_additions(
                payload,
                original,
                group=group,
            )
            if custom.failure:
                return r[t.Pair[t.StrSequence, t.StrSequence]].from_failure(custom)
            retained[group] = cls.active_development_requirements(custom.value)
            values = retained[group]
            if group == c.Infra.DependencyGroup.CODEGEN:
                values = tuple(sorted({*values, *member_groups}))
            u.Cli.toml_sync_string_list(groups, group, values)
        return r[t.Pair[t.StrSequence, t.StrSequence]].ok(
            (retained[str(c.Infra.DEV)], retained[c.Infra.DependencyGroup.CODEGEN]),
        )

    @classmethod
    def _sync_root_environment_provenance(
        cls,
        source: t.Cli.TomlDocument,
        custom_groups: t.Pair[t.StrSequence, t.StrSequence],
        context: FlextInfraUtilitiesPyprojectRequirementsProvenance,
    ) -> p.Result[bool]:
        """Tag derived occurrences after normalizing their declared origins.

        Returns:
            Success after publication to the document, or the original failure.

        """
        for group, custom in zip(
            (str(c.Infra.DEV), c.Infra.DependencyGroup.CODEGEN),
            custom_groups,
            strict=True,
        ):
            normalized_custom: t.MutableSequenceOf[str] = []
            for value in custom:
                canonical = cls._canonical_requirement(value, provenance=context)
                if canonical.failure:
                    return r[bool].from_failure(canonical)
                normalized_custom.append(canonical.value)
            FlextInfraUtilitiesPyprojectOverlay.sync_member_dev_provenance(
                source,
                custom=normalized_custom,
                group=group,
            )
        return r[bool].ok(value=True)

    @staticmethod
    def _member_environment_requirements(
        workspace: m.Infra.WorkspaceSpec,
        options: PyprojectConformOptions,
    ) -> p.Result[t.Triple[t.StrSequence, t.StrSequence, t.StrSequence]]:
        """Retain all declared member extras and groups in the root environment.

        Args:
            workspace: Declared members and their integration contract.
            options: Canonical repository root and conformance provenance.

        Returns:
            Member requests, dependency groups, and declared requirements.
        """
        result = r[t.Triple[t.StrSequence, t.StrSequence, t.StrSequence]]
        members = (
            tuple(member for member in workspace.subprojects if member.package)
            if workspace.repository.role == c.Infra.MakeProfile.WORKSPACE
            else ()
        )
        if not members:
            return result.ok(((), (), ()))
        if options.repository_root is None or workspace.integration is None:
            return result.fail(
                "member provisioning requires repository root and integration",
            )
        requests: list[str] = []
        groups: list[str] = []
        requirements: list[str] = []
        for member in members:
            path = options.repository_root / member.path / c.PYPROJECT_FILENAME
            parsed = FlextInfraUtilitiesPyprojectDocument._member_requirements(
                path, member.distribution
            )
            if parsed.failure:
                return result.from_failure(parsed)
            metadata, declared = parsed.value
            extras = (
                f"[{','.join(sorted(metadata.optional_dependencies))}]"
                if metadata.optional_dependencies
                else ""
            )
            requests.append(
                f"{member.distribution}{extras} @ "
                f"git+{member.url}@{workspace.integration.branch}",
            )
            for entries in metadata.dependency_groups.values():
                groups.extend(entry for entry in entries if isinstance(entry, str))
            requirements.extend(declared)
        return result.ok((tuple(requests), tuple(groups), tuple(requirements)))

    @staticmethod
    def _member_requirements(
        path: Path,
        distribution: str,
    ) -> p.Result[t.Pair[m.Infra.DepsToml.MemberRequirements, t.StrSequence]]:
        """Parse a member's dependency declarations once at the TOML boundary.

        Returns:
            Validated metadata and its complete requirement lines.
        """
        result = r[t.Pair[m.Infra.DepsToml.MemberRequirements, t.StrSequence]]
        document = u.Cli.toml_read_document(path)
        if document.failure:
            return result.from_failure(document)
        payload = u.Cli.toml_as_mapping(document.value)
        if payload is None:
            return result.fail(f"member metadata is not a TOML mapping: {path}")
        project = payload.get(c.Infra.PROJECT)
        if not isinstance(project, Mapping):
            return result.fail(
                f"member metadata identity differs from declaration: {path}",
            )
        parsed = u.validate_value(
            m.Infra.DepsToml.MemberRequirements,
            {
                "name": project.get(c.Infra.NAME),
                "dependencies": project.get(c.Infra.DEPENDENCIES, ()),
                "optional_dependencies": project.get(c.Infra.OPTIONAL_DEPENDENCIES, {}),
                "dependency_groups": payload.get(c.Infra.DEPENDENCY_GROUPS, {}),
            },
        )
        if parsed.failure:
            return result.from_failure(parsed)
        if parsed.value.name != distribution:
            return result.fail(
                f"member metadata identity differs from declaration: {path}",
            )
        declared = FlextInfraUtilitiesPyprojectUvSources.document_requirement_lines(
            document.value,
        ).unwrap()
        return result.ok((parsed.value, declared))

    @staticmethod
    def _declared_floor_sources(
        workspace: m.Infra.WorkspaceSpec,
        *,
        project_name: str,
        requirements: t.StrSequence,
        flext_line: m.Infra.WorkspaceIntegrationSpec | None,
    ) -> p.Result[t.StrMapping]:
        """Derive member sources and provider provenance only for generated floors.

        Returns:
            Declared sources, or the missing provider URL failure.

        """
        declared_sources = (
            {
                member.distribution: f"git+{member.url}@{workspace.integration.branch}"
                for member in workspace.subprojects
            }
            if workspace.integration is not None
            else {}
        )
        if flext_line is not None:
            floors = {
                name
                for requirement in requirements
                if (name := FlextInfraUtilitiesDependencies.dep_name(requirement))
                and name not in {project_name, *declared_sources}
                and name.startswith("flext-")
                and requirement.strip() == name
            }
            if floors and flext_line.base_url is None:
                return r[t.StrMapping].fail(
                    "detected FLEXT line carries no provider base URL",
                )
            declared_sources.update({
                name: f"git+{flext_line.base_url}/{name}.git@{flext_line.branch}"
                for name in floors
            })
        return r[t.StrMapping].ok(declared_sources)

    @staticmethod
    def _render_pyproject(source: t.Cli.TomlDocument) -> p.Result[str]:
        """Serialize the conformed document and validate the rendered TOML.

        Returns:
            Rendered TOML, or the original invalid-render failure.

        """
        original = u.Cli.toml_dumps(source)
        payload = u.Cli.toml_as_mapping(source)
        if payload is None:
            return r[str].fail("canonical pyproject document is not a TOML mapping")
        tool = u.Cli.toml_mapping_child(payload, c.Infra.TOOL)
        if tool is not None:
            uv = u.Cli.toml_mapping_child(tool, "uv")
            if uv is not None:
                payload = u.json_mapping_adapter().validate_python({
                    **payload,
                    c.Infra.TOOL: {
                        **tool,
                        "uv": {key: uv[key] for key in sorted(uv)},
                    },
                })
        normalized = u.Cli.toml_document_from_mapping(payload)
        groups = u.Cli.toml_table_child(source, c.Infra.DEPENDENCY_GROUPS)
        if groups is not None:
            for group in (str(c.Infra.DEV), c.Infra.DependencyGroup.CODEGEN):
                if u.Cli.toml_value(groups, group) is None:
                    continue
                custom = FlextInfraUtilitiesPyprojectOverlay.custom_dev_additions(
                    payload,
                    original,
                    group=group,
                )
                if custom.failure:
                    return r[str].from_failure(custom)
                FlextInfraUtilitiesPyprojectOverlay.sync_member_dev_provenance(
                    normalized,
                    custom=custom.value,
                    group=group,
                )
        rendered = u.Cli.toml_dumps(normalized)
        if u.Cli.toml_parse_text(rendered) is None:
            return r[str].fail("canonical pyproject rendering produced invalid TOML")
        return r[str].ok(rendered)

    @classmethod
    def _declared_requirement_sources(
        cls,
        source: t.Cli.TomlDocument,
        *,
        project_name: str,
        workspace: m.Infra.WorkspaceSpec,
        required_dev_dependencies: t.StrSequence,
        flext_line: m.Infra.WorkspaceIntegrationSpec | None,
    ) -> p.Result[t.Pair[t.StrMapping, t.StrMapping]]:
        """Return the declared and candidate Git sources of internal requirements.

        Workspace members render on the declared integration line; generated
        bare ``flext-*`` dev floors render on the detected FLEXT line; candidate
        dependencies must be declared requirements.

        Returns:
            The declared and candidate requirement sources.

        """
        declared = cls._declared_floor_sources(
            workspace,
            project_name=project_name,
            requirements=required_dev_dependencies,
            flext_line=flext_line,
        )
        if declared.failure:
            return r[t.Pair[t.StrMapping, t.StrMapping]].from_failure(declared)
        declared_sources = declared.value
        candidate_sources = {
            item.distribution: f"git+{item.url}@{item.commit}"
            for item in workspace.candidate_dependencies
        }
        unused_candidates = sorted(
            candidate_sources.keys()
            - set(FlextInfraUtilitiesDependencies.declared_dependency_names(source)),
        )
        if unused_candidates:
            return r[t.Pair[t.StrMapping, t.StrMapping]].fail(
                "candidate dependencies are not declared requirements: "
                + ", ".join(unused_candidates),
            )
        return r[t.Pair[t.StrMapping, t.StrMapping]].ok(
            (declared_sources, candidate_sources),
        )

    @classmethod
    def _synced_conform_tables(
        cls,
        source: t.Cli.TomlDocument,
        *,
        uv_resolution: m.Infra.UvResolutionSpec,
        candidate_sources: t.StrMapping,
        local_requirements: t.StrSequence,
        workspace: m.Infra.WorkspaceSpec,
    ) -> p.Result[bool]:
        """Sync the canonical typecheck, namespace, uv, and provenance tables.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        cls._remove_legacy_tooling(source)
        typecheck_paths = cls._sync_typecheck_paths(source)
        if typecheck_paths.failure:
            return r[bool].from_failure(typecheck_paths)
        namespace_scope = cls._sync_namespace_scope(
            source,
            workspace.project.namespace_scan_dirs
            if workspace.project is not None
            else None,
        )
        if namespace_scope.failure:
            return r[bool].from_failure(namespace_scope)
        sources_result = cls._sync_uv_sources(
            source,
            resolution=uv_resolution,
            candidate_sources=candidate_sources,
            workspace=workspace,
            local_requirements=local_requirements,
        )
        if sources_result.failure:
            return r[bool].from_failure(sources_result)
        provenance_result = cls._validate_dependency_provenance(
            source,
            workspace=workspace,
        )
        if provenance_result.failure:
            return r[bool].from_failure(provenance_result)
        return r[bool].ok(value=True)

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
        document: t.Cli.TomlDocument,
        namespace_scan_dirs: t.StrSequence | None,
    ) -> p.Result[bool]:
        """Sync ``[tool.flext.namespace].scan_dirs`` from the project SSOT.

        ``None`` or an empty sequence leaves the section untouched: projects
        without a declared scope keep the dynamic every-root behavior. A
        non-empty sequence is the workspace manifest's production scope.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if not namespace_scan_dirs:
            return r[bool].ok(value=True)
        namespace = u.Cli.toml_ensure_path(document, c.Infra.CONFORM_NAMESPACE_TABLE)
        u.Cli.toml_sync_string_list(namespace, "scan_dirs", list(namespace_scan_dirs))
        return r[bool].ok(value=True)

    @staticmethod
    def _sync_typecheck_paths(document: t.Cli.TomlDocument) -> p.Result[bool]:
        """Remove checkout-absolute type checker interpreter pins.

        Search paths belong to FlextInfraExtraPathsManager. Top-level
        ``venv`` / ``venvPath`` belong to deps modernize (root vs child
        runtime). Conform must not strip those or gen oscillates.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        tool = u.Cli.toml_table_child(document, c.Infra.TOOL)
        if tool is None:
            return r[bool].ok(value=True)
        pyrefly = u.Cli.toml_table_child(tool, c.Infra.PYREFLY)
        if pyrefly is not None:
            u.Cli.toml_remove_key_if_present(pyrefly, "python-interpreter-path")

        pyright = u.Cli.toml_table_child(tool, c.Infra.PYRIGHT)
        if pyright is None:
            return r[bool].ok(value=True)

        # venv / venvPath are owned by deps modernize (workspace vs child
        # runtime). Conform only strips checkout-absolute interpreter pins.
        interpreter_keys = ("pythonPath", "pythonInterpreterPath")
        for key in interpreter_keys:
            u.Cli.toml_remove_key_if_present(pyright, key)
        raw_environments = u.Cli.json_as_sequence(
            u.Cli.toml_value(pyright, "executionEnvironments"),
        )
        normalized_environments: t.JsonValueList = []
        for index, environment in enumerate(raw_environments):
            if not isinstance(environment, Mapping):
                return r[bool].fail(
                    f"tool.pyright.executionEnvironments[{index}] must be a mapping",
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
                pyright,
                "executionEnvironments",
                normalized_environments,
            )
        return r[bool].ok(value=True)


__all__: list[str] = ["FlextInfraUtilitiesPyprojectDocument"]
