"""Public pyproject conformer over the requirement and uv-source owners.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated

from flext_cli import u
from packaging.utils import canonicalize_name

from flext_infra import c, config, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesDependencies,
    FlextInfraUtilitiesProjectManagedArtifacts,
    FlextInfraUtilitiesPyproject,
)
from flext_infra._utilities._pyproject import (
    FlextInfraUtilitiesPyprojectOverlay,
    FlextInfraUtilitiesPyprojectUvSources,
)
from flext_infra._utilities._pyproject._requirements_provenance import (
    FlextInfraUtilitiesPyprojectRequirementsProvenance,
)


class FlextInfraUtilitiesPyprojectDocument(FlextInfraUtilitiesPyprojectUvSources):
    """Render root workspace and autonomous library metadata deterministically."""

    type _CustomGroupsPair = t.Pair[
        t.SequenceOf[str | m.Infra.DependencyGroupInclude],
        t.SequenceOf[str | m.Infra.DependencyGroupInclude],
    ]
    type _ConformedProvenance = t.Triple[
        t.Cli.TomlDocument,
        str,
        FlextInfraUtilitiesPyprojectRequirementsProvenance,
    ]

    class PyprojectConformOptions(m.ImmutableValueModel):
        """Detected integration provenance for internal requirements and dev floors."""

        flext_line: Annotated[
            m.Infra.WorkspaceIntegrationSpec | None,
            m.Field(
                description="Detected provider and branch for internal requirements",
            ),
        ] = None

    @classmethod
    def parsed_pyproject(
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
        retain their authored source refs. Generated bare dev floors use the
        detected provider line in ``options.flext_line``, like the scaffold;
        CUSTOM requirements never acquire provenance from provider policy unless
        that dependency is a declared floor or native source.

        Returns:
            Canonical TOML with autonomous dependencies and uv policy.

        """
        prepared = cls._conformed_provenance(
            pyproject_content,
            workspace=workspace,
            required_dev_dependencies=required_dev_dependencies,
            options=options,
        )
        if prepared.failure:
            return r[str].from_failure(prepared)
        source, project_name, source_context = prepared.value
        custom_groups = cls._workspace_custom_groups(
            source,
            pyproject_content=pyproject_content,
            workspace=workspace,
        )
        if custom_groups.failure:
            return r[str].from_failure(custom_groups)
        grouped = cls._sync_dependency_groups(
            source,
            project_name=project_name,
            required_dev_dependencies=required_dev_dependencies,
            provenance=source_context,
        )
        if grouped.failure:
            return r[str].from_failure(grouped)
        requirement_sources = cls._normalized_requirement_sources(
            source,
            source_context,
        )
        if requirement_sources.failure:
            return r[str].from_failure(requirement_sources)
        (
            local_requirements,
            _superseded_sources,
            candidate_sources,
        ) = requirement_sources.value
        if workspace.repository.role == c.Infra.MakeProfile.WORKSPACE:
            owned = cls._sync_root_environment_provenance(
                source,
                custom_groups.value,
                source_context,
            )
            if owned.failure:
                return r[str].from_failure(owned)
        cls._remove_legacy_tooling(source)
        return cls._synced_conform_tables(
            source,
            uv_resolution=uv_resolution,
            candidate_sources=candidate_sources,
            local_requirements=local_requirements,
            workspace=workspace,
        ).flat_map(lambda _synced: cls._render_pyproject(source))

    @classmethod
    def _conformed_provenance(
        cls,
        pyproject_content: str,
        *,
        workspace: m.Infra.WorkspaceSpec,
        required_dev_dependencies: t.StrSequence,
        options: PyprojectConformOptions | None,
    ) -> p.Result[_ConformedProvenance]:
        """Parse the source and compose its declared requirement provenance.

        Returns:
            The parsed document, its project name, the composed requirement
            provenance.

        """
        result = r[FlextInfraUtilitiesPyprojectDocument._ConformedProvenance]
        parsed = cls.parsed_pyproject(pyproject_content)
        if parsed.failure:
            return result.from_failure(parsed)
        source, project_name = parsed.value[0], parsed.value[1]
        provenance = options if options is not None else cls.PyprojectConformOptions()
        origins = cls._declared_requirement_sources(
            project_name=project_name,
            workspace=workspace,
            required_dev_dependencies=required_dev_dependencies,
            flext_line=provenance.flext_line,
        )
        if origins.failure:
            return result.from_failure(origins)
        declared_sources, candidate_sources = origins.value
        tool = u.Cli.toml_mapping_child(parsed.value[2], c.Infra.TOOL)
        uv = u.Cli.toml_mapping_child(tool, "uv") if tool is not None else None
        native_sources = (
            u.Cli.toml_mapping_child(uv, "sources") if uv is not None else None
        )
        source_context = FlextInfraUtilitiesPyprojectRequirementsProvenance(
            declared_sources=declared_sources,
            candidate_sources=candidate_sources,
            native_sources=(
                tuple(canonicalize_name(name) for name in native_sources)
                if native_sources is not None
                else ()
            ),
        )
        return result.ok((
            source,
            project_name,
            source_context,
        ))

    @classmethod
    def _workspace_custom_groups(
        cls,
        source: t.Cli.TomlDocument,
        *,
        pyproject_content: str,
        workspace: m.Infra.WorkspaceSpec,
    ) -> p.Result[_CustomGroupsPair]:
        """Synchronize root environment groups for workspace-role repositories.

        Returns:
            The synchronized custom group pair, empty outside the workspace role.

        """
        if workspace.repository.role != c.Infra.MakeProfile.WORKSPACE:
            return r[FlextInfraUtilitiesPyprojectDocument._CustomGroupsPair].ok((
                (),
                (),
            ))
        return cls._sync_root_environment_groups(
            source,
            pyproject_content,
        )

    @classmethod
    def _normalized_requirement_sources(
        cls,
        source: t.Cli.TomlDocument,
        provenance: FlextInfraUtilitiesPyprojectRequirementsProvenance,
    ) -> p.Result[t.Triple[t.StrSequence, t.StrMapping, t.StrMapping]]:
        """Validate composed declarations before applying the one source context.

        Returns:
            Local requirements and source mappings, or the original failure.

        """
        result_type = r[t.Triple[t.StrSequence, t.StrMapping, t.StrMapping]]
        local = cls.document_requirement_lines(source)
        if local.failure:
            return result_type.from_failure(
                local,
            )
        unused_candidates = sorted(
            provenance.candidate_sources.keys()
            - set(FlextInfraUtilitiesDependencies.declared_dependency_names(source)),
        )
        if unused_candidates:
            return result_type.fail(
                "candidate dependencies are not declared requirements: "
                + ", ".join(unused_candidates),
            )
        normalized = cls._normalize_requirements(
            source,
            declared_sources=provenance.declared_sources,
            candidate_sources=provenance.candidate_sources,
            native_sources=provenance.native_sources,
        )
        if normalized.failure:
            return result_type.from_failure(
                normalized,
            )
        return result_type.ok(
            (local.value, provenance.declared_sources, provenance.candidate_sources),
        )

    @classmethod
    def _sync_root_environment_groups(
        cls,
        source: t.Cli.TomlDocument,
        original: str,
    ) -> p.Result[_CustomGroupsPair]:
        """Retain authored groups while removing identified generated additions.

        Returns:
            Custom DEV and CODEGEN requirements, or the original parse failure.

        """
        result_type = r[FlextInfraUtilitiesPyprojectDocument._CustomGroupsPair]
        payload = u.Cli.toml_as_mapping(source)
        if payload is None:
            return result_type.fail(
                "root metadata is not a TOML mapping",
            )
        groups = u.Cli.toml_ensure_table(source, c.Infra.DEPENDENCY_GROUPS)
        retained: t.MutableMappingKV[
            str, t.SequenceOf[str | m.Infra.DependencyGroupInclude]
        ] = {}
        for group in (str(c.Infra.DEV), c.Infra.DependencyGroup.CODEGEN):
            authored_name = FlextInfraUtilitiesPyproject.dependency_group_name(
                groups, str(group)
            )
            custom = FlextInfraUtilitiesPyproject.custom_dev_additions(
                payload,
                original,
                group=group,
            )
            if custom.failure:
                return result_type.from_failure(custom)
            retained[group] = cls.merge_dependency_group_entries((), custom.value)
            u.Cli.toml_sync_value(
                groups,
                authored_name,
                FlextInfraUtilitiesPyproject.dependency_group_wire(retained[group]),
            )
        return result_type.ok(
            (retained[str(c.Infra.DEV)], retained[c.Infra.DependencyGroup.CODEGEN]),
        )

    @classmethod
    def _sync_root_environment_provenance(
        cls,
        source: t.Cli.TomlDocument,
        custom_groups: _CustomGroupsPair,
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
            normalized_custom: t.MutableSequenceOf[
                str | m.Infra.DependencyGroupInclude
            ] = []
            for value in custom:
                if not isinstance(value, str):
                    normalized_custom.append(value)
                    continue
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
    def _declared_floor_sources(
        workspace: m.Infra.WorkspaceSpec,
        *,
        project_name: str,
        requirements: t.StrSequence,
        flext_line: m.Infra.WorkspaceIntegrationSpec | None,
    ) -> p.Result[t.StrMapping]:
        """Derive governed source defaults solely for generated bare floors.

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
                custom = FlextInfraUtilitiesPyproject.custom_dev_additions(
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
        *,
        project_name: str,
        workspace: m.Infra.WorkspaceSpec,
        required_dev_dependencies: t.StrSequence,
        flext_line: m.Infra.WorkspaceIntegrationSpec | None,
    ) -> p.Result[t.Pair[t.StrMapping, t.StrMapping]]:
        """Return the declared and candidate Git sources of internal requirements.

        Explicit requirement URLs and refs remain authoritative. Source-less
        members use their governed workspace line; generated bare ``flext-*``
        floors use the detected FLEXT line. Candidate dependencies must be
        declared requirements.

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
        project = u.Cli.toml_table_child(source, c.Infra.PROJECT)
        optional = (
            u.Cli.toml_table_child(project, c.Infra.OPTIONAL_DEPENDENCIES)
            if project is not None
            else None
        )
        deptry = u.Cli.toml_ensure_path(source, (c.Infra.TOOL, c.Infra.DEPTRY))
        u.Cli.toml_sync_string_list(
            deptry,
            "optional_dependencies_dev_groups",
            [
                group
                for group in (
                    FlextInfraUtilitiesProjectManagedArtifacts.native_tool_setting(
                        config.Infra.tooling,
                        c.Infra.DEPTRY,
                        "optional_dependencies_dev_groups",
                        t.StrSequence,
                    )
                )
                if optional is not None and group in optional
            ],
        )
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
        cls._sync_project_documentation(source, workspace.project)
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
    def _sync_project_documentation(
        document: t.Cli.TomlDocument,
        project: m.Infra.ProjectSpec | None,
    ) -> None:
        """Resolve the sole project declaration through the owned leaf policy."""
        FlextInfraUtilitiesPyprojectDocument._sync_documentation_language(
            document,
            project.documentation_language if project is not None else "en",
        )

    @classmethod
    def project_documentation_metadata(
        cls,
        source: str,
        project: m.Infra.ProjectSpec | None,
    ) -> p.Result[str]:
        """Project only documentation metadata without conformance planning.

        Returns:
            Strictly validated metadata, retaining exact unchanged source bytes.

        """
        payload = u.Cli.toml_mapping_from_text(source)
        if payload is None:
            return r[str].fail("invalid documentation pyproject TOML")
        validated = r[u.PyprojectDocument].create_from_callable(
            partial(u.PyprojectDocument.model_validate, payload)
        )
        if validated.failure:
            return r[str].from_failure(validated)
        document = u.Cli.toml_parse_text(source)
        if document is None:
            return r[str].fail("invalid documentation pyproject document")
        before = u.Cli.toml_dumps(document)
        cls._sync_project_documentation(document, project)
        projected = u.Cli.toml_dumps(document)
        if projected == before:
            return r[str].ok(source)
        desired = u.Cli.toml_mapping_from_text(projected)
        checked = r[u.PyprojectDocument].create_from_callable(
            partial(u.PyprojectDocument.model_validate, desired)
        )
        if checked.failure:
            return r[str].from_failure(checked)
        return r[str].ok(projected)

    @staticmethod
    def _sync_documentation_language(
        document: t.Cli.TomlDocument,
        language: t.Infra.DocumentationLanguage,
    ) -> None:
        """Project one owned leaf without taking over CUSTOM documentation policy."""
        tool = u.Cli.toml_table_child(document, c.Infra.TOOL)
        flext = u.Cli.toml_table_child(tool, "flext") if tool is not None else None
        docs = u.Cli.toml_table_child(flext, "docs") if flext is not None else None
        if language == "en":
            if docs is not None:
                u.Cli.toml_remove_key_if_present(docs, "documentation_language")
            return
        if docs is None:
            docs = u.Cli.toml_ensure_path(document, (c.Infra.TOOL, "flext", "docs"))
        if u.Cli.toml_value(docs, "documentation_language") == language:
            return
        docs["documentation_language"] = language

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

        Search paths belong to the analyzer phase. Preserve its member-local
        execution environments and their order through full generation.

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

        # Environment selection is owned by Make and the opened editor folder.
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
            mapping = u.json_mapping_adapter().validate_python(environment)
            normalized: t.JsonDict = dict(mapping)
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
