"""Public pyproject conformer over the requirement and uv-source owners.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from base64 import urlsafe_b64encode
from collections.abc import Mapping
from json import dumps
from pathlib import Path
from sys import prefix
from typing import Annotated

from flext_cli import u

from flext_infra import c, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesDependencies,
    FlextInfraUtilitiesDependencyRequirements,
    FlextInfraUtilitiesGit,
)
from flext_infra._utilities._pyproject import FlextInfraUtilitiesPyprojectUvSources
from flext_infra._utilities._pyproject._requirements_provenance import (
    FlextInfraUtilitiesPyprojectRequirementsProvenance,
)
from flext_infra._utilities._pyproject.overlay import (
    FlextInfraUtilitiesPyprojectOverlay,
)
from flext_infra.workspace import FlextInfraWorkspaceEnvironmentProvenance


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
        member_declarations: Annotated[
            t.VariadicTuple[m.Cli.AtomicFileState] | None,
            m.Field(
                description="Pre-render captured member declarations in declared order"
            ),
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
        environment = cls._member_environment_requirements(
            source,
            workspace,
            provenance,
        )
        if environment.failure:
            return r[str].from_failure(environment)
        member_requests, member_groups, member_requirements = environment.value
        member_groups = cls.active_development_requirements(member_groups)
        origins = cls._declared_requirement_sources(
            project_name=project_name,
            workspace=workspace,
            required_dev_dependencies=required_dev_dependencies,
            flext_line=provenance.flext_line,
        )
        if origins.failure:
            return r[str].from_failure(origins)
        declared_sources, candidate_sources = origins.value
        source_context = FlextInfraUtilitiesPyprojectRequirementsProvenance(
            declared_sources=declared_sources,
            candidate_sources=candidate_sources,
            family_line=provenance.flext_line.branch
            if provenance.flext_line is not None
            else None,
        )
        custom_groups: t.Pair[
            t.SequenceOf[str | m.Infra.DependencyGroupInclude],
            t.SequenceOf[str | m.Infra.DependencyGroupInclude],
        ] = ((), ())
        if workspace.repository.role == c.Infra.MakeProfile.WORKSPACE:
            custom = cls._sync_root_environment_groups(
                source,
                pyproject_content,
                member_groups,
            )
            if custom.failure:
                return r[str].from_failure(custom)
            custom_groups = custom.value
        grouped = cls._sync_dependency_groups(
            source,
            project_name=project_name,
            required_dev_dependencies=required_dev_dependencies,
            provenance=source_context,
        )
        if grouped.failure:
            return r[str].from_failure(grouped)
        cls._sync_member_environment_dev(
            source,
            (*member_requests, *member_groups, *member_requirements),
        )
        requirement_sources = cls._normalized_requirement_sources(
            source,
            source_context,
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
                source_context,
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
        provenance: FlextInfraUtilitiesPyprojectRequirementsProvenance,
    ) -> p.Result[t.Triple[t.StrSequence, t.StrMapping, t.StrMapping]]:
        """Validate composed declarations before applying the one source context.

        Returns:
            Local requirements and source mappings, or the original failure.

        """
        local = cls.document_requirement_lines(source)
        if local.failure:
            return r[t.Triple[t.StrSequence, t.StrMapping, t.StrMapping]].from_failure(
                local,
            )
        unused_candidates = sorted(
            provenance.candidate_sources.keys()
            - set(FlextInfraUtilitiesDependencies.declared_dependency_names(source)),
        )
        if unused_candidates:
            return r[t.Triple[t.StrSequence, t.StrMapping, t.StrMapping]].fail(
                "candidate dependencies are not declared requirements: "
                + ", ".join(unused_candidates),
            )
        normalized = cls._normalize_requirements(
            source,
            declared_sources=provenance.declared_sources,
            candidate_sources=provenance.candidate_sources,
            family_line=provenance.family_line,
        )
        if normalized.failure:
            return r[t.Triple[t.StrSequence, t.StrMapping, t.StrMapping]].from_failure(
                normalized,
            )
        return r[t.Triple[t.StrSequence, t.StrMapping, t.StrMapping]].ok(
            (local.value, provenance.declared_sources, provenance.candidate_sources),
        )

    @classmethod
    def _sync_member_environment_dev(
        cls,
        source: t.Cli.TomlDocument,
        requirements: t.StrSequence,
    ) -> None:
        """Retain marker variants when merging selected member requirements."""
        groups = u.Cli.toml_ensure_table(source, c.Infra.DEPENDENCY_GROUPS)
        dev_name = cls.dependency_group_name(tuple(groups), str(c.Infra.DEV))
        dev = cls.read_dependency_group(groups, dev_name)
        existing = frozenset(entry for entry in dev if isinstance(entry, str))
        additions = tuple(sorted(set(requirements) - existing))
        u.Cli.toml_sync_value(
            groups,
            dev_name,
            cls.dependency_group_wire((*dev, *additions)),
        )

    @classmethod
    def _sync_root_environment_groups(
        cls,
        source: t.Cli.TomlDocument,
        original: str,
        member_groups: t.StrSequence,
    ) -> p.Result[
        t.Pair[
            t.SequenceOf[str | m.Infra.DependencyGroupInclude],
            t.SequenceOf[str | m.Infra.DependencyGroupInclude],
        ]
    ]:
        """Retain custom development groups before adding current member requirements.

        Returns:
            Custom DEV and CODEGEN requirements, or the original parse failure.

        """
        result_type = r[
            t.Pair[
                t.SequenceOf[str | m.Infra.DependencyGroupInclude],
                t.SequenceOf[str | m.Infra.DependencyGroupInclude],
            ]
        ]
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
            authored_name = cls.dependency_group_name(tuple(groups), str(group))
            custom = FlextInfraUtilitiesPyprojectOverlay.custom_dev_additions(
                payload,
                original,
                group=group,
            )
            if custom.failure:
                return result_type.from_failure(custom)
            retained[group] = cls.merge_dependency_group_entries((), custom.value)
            values = retained[group]
            if group == c.Infra.DependencyGroup.CODEGEN:
                values = cls.merge_dependency_group_entries(
                    tuple(sorted(set(member_groups))),
                    values,
                )
            u.Cli.toml_sync_value(
                groups,
                authored_name,
                cls.dependency_group_wire(values),
            )
        return result_type.ok(
            (retained[str(c.Infra.DEV)], retained[c.Infra.DependencyGroup.CODEGEN]),
        )

    @classmethod
    def _sync_root_environment_provenance(
        cls,
        source: t.Cli.TomlDocument,
        custom_groups: t.Pair[
            t.SequenceOf[str | m.Infra.DependencyGroupInclude],
            t.SequenceOf[str | m.Infra.DependencyGroupInclude],
        ],
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
    def _member_environment_requirements(
        source: t.Cli.TomlDocument,
        workspace: m.Infra.WorkspaceSpec,
        options: PyprojectConformOptions,
    ) -> p.Result[t.Triple[t.StrSequence, t.StrSequence, t.StrSequence]]:
        """Retain all declared member extras and groups in the root environment.

        Args:
            source: Parsed root requirements before environment composition.
            workspace: The workspace specification containing subprojects and
                integration details.
            options: The options for pyproject conformity, including repository
                root and other settings.

        Returns:
            A result containing a triple of string sequences representing the
                member environment requirements.
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
        declared_lines = (
            FlextInfraUtilitiesPyprojectDocument.document_requirement_lines(source)
        )
        if declared_lines.failure:
            return result.from_failure(declared_lines)
        requests: list[str] = []
        groups: list[str] = []
        requirements: list[str] = []
        declarations = options.member_declarations
        if declarations is not None and len(declarations) != len(members):
            return result.fail(
                "captured member declarations differ from declared members"
            )
        for index, member in enumerate(members):
            if declarations is None:
                declaration = (
                    FlextInfraUtilitiesPyprojectDocument.member_project_declaration(
                        options.repository_root,
                        member,
                    )
                )
                if declaration.failure:
                    return result.from_failure(declaration)
                state = declaration.value
            else:
                state = declarations[index]
            parsed = (
                FlextInfraUtilitiesPyprojectDocument.member_declaration_requirements(
                    state,
                    member.distribution,
                )
            )
            if parsed.failure:
                return result.from_failure(parsed)
            metadata, declared = parsed.value
            name = FlextInfraUtilitiesDependencies.dep_name(member.distribution)
            if name is None:
                return result.fail(
                    f"member distribution is not a requirement name: {member.distribution}",
                )
            explicit = tuple(
                line
                for line in declared_lines.value
                if FlextInfraUtilitiesDependencies.dep_name(line) == name
                and FlextInfraUtilitiesPyprojectDocument._declares_direct_source(line)
            )
            extras = FlextInfraUtilitiesDependencyRequirements.dependency_extras(
                (
                    *explicit,
                    *(
                        f"{member.distribution}[{extra}]"
                        for extra in metadata.optional_dependencies
                    ),
                ),
                name,
            )
            if explicit:
                for line in explicit:
                    origin = FlextInfraUtilitiesPyprojectDocument._parsed_canonical_provenance(
                        line,
                    )
                    if origin.failure:
                        return result.from_failure(origin)
                    _head, marker, (url, reference) = origin.value
                    request = f"{member.distribution}{extras} @ git+{url}@{reference}"
                    requests.append(
                        f"{request}; {marker[1]}" if marker[0] else request,
                    )
            else:
                requests.append(
                    f"{member.distribution}{extras} @ "
                    f"git+{member.url}@{workspace.integration.branch}",
                )
            for entries in metadata.dependency_groups.values():
                groups.extend(entry for entry in entries if isinstance(entry, str))
            requirements.extend(declared)
        return result.ok((tuple(requests), tuple(groups), tuple(requirements)))

    @staticmethod
    def member_project_declaration(
        repository_root: Path,
        repository: m.Infra.RepositoryRef,
        *,
        lock_state: m.Cli.AtomicFileState | None = None,
    ) -> p.Result[m.Cli.AtomicFileState]:
        """Elect the authenticated live or installed producer declaration."""
        result = r[m.Cli.AtomicFileState]
        matches = u.installed_distributions(name=repository.distribution)
        if len(matches) != 1:
            return result.fail(
                "member declaration needs one installed distribution: "
                f"{repository.distribution}",
            )
        distribution = matches[0]
        raw = distribution.read_text(c.Infra.DISTRIBUTION_DIRECT_URL_FILE)
        if raw is None:
            return result.fail(
                "member declaration lacks PEP 610 provenance: "
                f"{repository.distribution}",
            )
        receipt = r[m.Infra.DirectUrlReceipt].create_from_callable(
            lambda: m.Infra.DirectUrlReceipt.model_validate_json(raw, strict=True),
        )
        if receipt.failure:
            return result.from_failure(receipt)
        if receipt.value.dir_info is not None and receipt.value.dir_info.editable:
            if not repository.editable:
                return result.fail(
                    "member editable installation differs from declaration: "
                    f"{repository.distribution}",
                )
            authenticated = (
                FlextInfraWorkspaceEnvironmentProvenance.validate_editable_installation(
                    repository,
                    repository_root,
                    distribution,
                    receipt.value,
                )
            )
            if authenticated.failure:
                return result.from_failure(authenticated)
            return u.Cli.atomic_read_binary_file_state(
                repository_root / repository.path / c.PYPROJECT_FILENAME,
                required=True,
            )
        if lock_state is None:
            lock_read = u.Cli.atomic_read_binary_file_state(
                repository_root / c.Infra.UV_LOCK_FILENAME,
                required=True,
            )
            if lock_read.failure:
                return result.from_failure(lock_read)
            lock_state = lock_read.value
        if (
            lock_state.path != (repository_root / c.Infra.UV_LOCK_FILENAME).resolve()
            or lock_state.content is None
        ):
            return result.fail("member artifact needs its captured root lock")
        locked_document = u.Cli.toml_parse_text(
            lock_state.content.decode(c.DEFAULT_ENCODING),
        )
        if locked_document is None:
            return result.fail("captured member artifact lock is invalid TOML")
        locked_payload = u.Cli.toml_as_mapping(locked_document)
        if locked_payload is None:
            return result.fail("captured member artifact lock is not a mapping")
        locked = r[m.Infra.LockedEnvironment].create_from_callable(
            lambda: m.Infra.LockedEnvironment.model_validate_json(
                dumps(locked_payload),
            ),
        )
        if locked.failure:
            return result.from_failure(locked)
        candidates = tuple(
            item
            for item in locked.value.package
            if FlextInfraUtilitiesDependencies.dep_name(item.name)
            == FlextInfraUtilitiesDependencies.dep_name(repository.distribution)
            and item.version == distribution.version
        )
        if len(candidates) != 1 or candidates[0].source.git is None:
            return result.fail(
                "member declaration requires its installed locked Git artifact: "
                f"{repository.distribution}",
            )
        origin = FlextInfraWorkspaceEnvironmentProvenance.locked_origin_verdict(
            repository.distribution,
            candidates[0],
            raw,
        )
        if origin.failure:
            return result.from_failure(origin)
        if FlextInfraUtilitiesGit.git_remote_identity(
            receipt.value.url
        ) != FlextInfraUtilitiesGit.git_remote_identity(repository.url):
            return result.fail(
                "member artifact origin differs from declared repository: "
                f"{repository.distribution}",
            )
        files = distribution.files
        if files is None:
            return result.fail(
                f"member artifact has no RECORD inventory: {repository.distribution}",
            )
        resources = tuple(item for item in files if item.name == c.PYPROJECT_FILENAME)
        if len(resources) != 1:
            return result.fail(
                "member artifact needs one packaged producer declaration: "
                f"{repository.distribution}; publish its generated wheel first",
            )
        resource = resources[0]
        path = Path(str(distribution.locate_file(resource))).resolve()
        if not path.is_relative_to(Path(prefix).resolve()):
            return result.fail(
                "member declaration escapes its installed environment: "
                f"{repository.distribution}",
            )
        captured = u.Cli.atomic_read_binary_file_state(path, required=True)
        if captured.failure:
            return result.from_failure(captured)
        state = captured.value
        if (
            state.content is None
            or resource.hash is None
            or resource.hash.mode != "sha256"
            or resource.size != len(state.content)
            or resource.hash.value
            != urlsafe_b64encode(
                bytes.fromhex(u.Cli.sha256_bytes(state.content)),
            )
            .rstrip(b"=")
            .decode("ascii")
        ):
            return result.fail(
                "member producer declaration differs from its RECORD: "
                f"{repository.distribution}",
            )
        producer = FlextInfraUtilitiesPyprojectDocument._parsed_pyproject(
            state.content.decode(c.DEFAULT_ENCODING),
        )
        if producer.failure:
            return result.from_failure(producer)
        document, name, _payload = producer.value
        force_include = u.Cli.toml_table_path(
            document,
            ("tool", "hatch", "build", "targets", "wheel", "force-include"),
        )
        if (
            FlextInfraUtilitiesDependencies.dep_name(name)
            != FlextInfraUtilitiesDependencies.dep_name(repository.distribution)
            or force_include is None
            or u.Cli.toml_value(force_include, c.PYPROJECT_FILENAME)
            != resource.as_posix()
        ):
            return result.fail(
                "packaged declaration differs from its producer build contract: "
                f"{repository.distribution}",
            )
        return result.ok(state)

    @staticmethod
    def member_declaration_requirements(
        state: m.Cli.AtomicFileState,
        distribution: str,
    ) -> p.Result[t.Pair[m.Infra.DepsToml.MemberRequirements, t.StrSequence]]:
        """Parse complete member requirements from the exact captured declaration."""
        result = r[t.Pair[m.Infra.DepsToml.MemberRequirements, t.StrSequence]]
        path = state.path
        if state.content is None:
            return result.fail(f"member declaration has no captured bytes: {path}")
        parsed_document = FlextInfraUtilitiesPyprojectDocument._parsed_pyproject(
            state.content.decode(c.DEFAULT_ENCODING),
        )
        if parsed_document.failure:
            return result.from_failure(parsed_document)
        document, _name, payload = parsed_document.value
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
        if FlextInfraUtilitiesDependencies.dep_name(
            parsed.value.name,
        ) != FlextInfraUtilitiesDependencies.dep_name(distribution):
            return result.fail(
                f"member metadata identity differs from declaration: {path}",
            )
        declared = FlextInfraUtilitiesPyprojectUvSources.document_requirement_lines(
            document,
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
        """Derive governed defaults for source-less members and generated floors.

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
