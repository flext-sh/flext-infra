"""Conform-owned ``[tool.uv]`` rendering for one pyproject document.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from urllib.parse import unquote, urlsplit

from flext_cli import u
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from flext_infra import c, m, p, r, t
from flext_infra._utilities import FlextInfraUtilitiesDependencies
from flext_infra._utilities._pyproject import (
    FlextInfraUtilitiesPyprojectRequirements,
    FlextInfraUtilitiesPyprojectSession,
)
from flext_infra._utilities.dependency_requirements import (
    FlextInfraUtilitiesDependencyRequirements,
)


class FlextInfraUtilitiesPyprojectUvSources(
    FlextInfraUtilitiesPyprojectRequirements,
    FlextInfraUtilitiesPyprojectSession,
):
    """Render the conform-owned ``[tool.uv]`` keys of one pyproject document."""

    @classmethod
    def pyproject_native_resolution_view(
        cls,
        root: m.Infra.UvResolutionProject,
        *,
        members: t.SequenceOf[m.Infra.UvResolutionProject],
        directory: Path,
        policy: m.Infra.MakeUvResolutionSpec,
    ) -> p.Result[t.Cli.TomlDocument]:
        """Project the canonical Make all-groups/all-extras native UV graph.

        The generated non-package project never shares a distribution name
        with an installed project. Native path bindings therefore replace
        Git backedges without replacing any synthetic group requirement.
        Original package metadata and editable declarations remain unchanged.
        """
        if not directory.is_absolute():
            return r[t.Cli.TomlDocument].fail(
                f"resolution view directory is not absolute: {directory}",
            )
        projects = (
            root,
            *sorted(members, key=lambda item: item.repository.distribution),
        )
        names = [
            canonicalize_name(project.repository.distribution) for project in projects
        ]
        if len(names) != len(set(names)):
            return r[t.Cli.TomlDocument].fail(
                "resolution projects have colliding normalized distribution names",
            )
        virtual_name = canonicalize_name(
            root.repository.distribution + policy.virtual_distribution_suffix,
        )
        if virtual_name in names:
            return r[t.Cli.TomlDocument].fail(
                f"resolution distribution collides with a declared project: {virtual_name}",
            )
        root_payload = cls._resolution_project_payload(root)
        root_project = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
            root_payload.get(c.Infra.PROJECT, {}),
        )
        root_tool = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
            root_payload.get(c.Infra.TOOL, {}),
        )
        native_uv: t.JsonDict = deepcopy(
            dict(t.Cli.JSON_MAPPING_ADAPTER.validate_python(root_tool.get("uv", {}))),
        )
        for key in ("workspace", "sources", "package", "dev-dependencies"):
            native_uv.pop(key, None)
        native_uv["package"] = False
        view_project: t.JsonDict = (
            {
                "name": virtual_name,
                "version": root_project["version"],
                "requires-python": root_project["requires-python"],
                "dependencies": [],
                "optional-dependencies": {},
            }
            if root_project
            else {}
        )
        dependencies: list[t.JsonValue] = []
        member_bindings: list[t.JsonValue] = []
        extras: t.JsonDict = {}
        groups: t.JsonDict = {}
        group_metadata: t.JsonDict = {}
        sources: t.JsonDict = {}
        index_entries: t.JsonDict = {}
        overrides = t.Cli.JSON_LIST_ADAPTER.validate_python(
            native_uv.get("override-dependencies", []),
        )
        constraints = list(
            t.Cli.JSON_LIST_ADAPTER.validate_python(
                native_uv.get("constraint-dependencies", []),
            ),
        )
        overridden = set(names)
        retained_overrides = list(overrides)
        explicit_names = {
            FlextInfraUtilitiesDependencies.dep_name(entry)
            for entry in overrides
            if isinstance(entry, str)
        }
        seen_groups: set[str] = set()
        seen_extras: set[str] = set()
        for position, project in enumerate(projects):
            payload = cls._resolution_project_payload(project)
            metadata = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
                payload.get(c.Infra.PROJECT, {}),
            )
            name = canonicalize_name(project.repository.distribution)
            metadata_name = metadata.get("name")
            if (project.repository.package or metadata_name is not None) and (
                not isinstance(metadata_name, str)
                or canonicalize_name(metadata_name) != name
            ):
                return r[t.Cli.TomlDocument].fail(
                    f"resolution project identity differs from its declaration: {project.directory}",
                )
            optional = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
                metadata.get(c.Infra.OPTIONAL_DEPENDENCIES, {}),
            )
            selected_extras = tuple(sorted(optional))
            constraints.extend(
                FlextInfraUtilitiesDependencies.dependency_constraint(
                    requirement,
                    replace_source=True,
                )
                for requirement in cls.document_requirement_lines(
                    project.document
                ).unwrap()
                if FlextInfraUtilitiesDependencies.dep_name(requirement) in overridden
            )
            request = name
            if selected_extras:
                request += f"[{','.join(selected_extras)}]"
            if project.repository.package:
                if position == 0:
                    dependencies.append(request)
                else:
                    member_bindings.append(request)
                if name not in explicit_names:
                    retained_overrides.append(request)
                sources[name] = {
                    "path": project.directory.relative_to(
                        directory,
                        walk_up=True,
                    ).as_posix(),
                    "editable": project.repository.editable,
                }
            tool = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
                payload.get(c.Infra.TOOL, {}),
            )
            project_uv = t.Cli.JSON_MAPPING_ADAPTER.validate_python(tool.get("uv", {}))
            if position == 0 and not project.repository.package:
                for requirement in t.Cli.JSON_LIST_ADAPTER.validate_python(
                    metadata.get(c.Infra.DEPENDENCIES, []),
                ):
                    if not isinstance(requirement, str):
                        return r[t.Cli.TomlDocument].fail(
                            "content-only runtime dependency is not a requirement string",
                        )
                    dependencies.append(
                        cls._resolution_requirement(requirement, project)
                    )
            declared_groups = dict(
                t.Cli.JSON_MAPPING_ADAPTER.validate_python(
                    payload.get(c.Infra.DEPENDENCY_GROUPS, {}),
                ),
            )
            legacy_dev = project_uv.get("dev-dependencies")
            if legacy_dev is not None:
                development = list(
                    t.Cli.JSON_LIST_ADAPTER.validate_python(
                        declared_groups.get("dev", []),
                    ),
                )
                development.extend(t.Cli.JSON_LIST_ADAPTER.validate_python(legacy_dev))
                declared_groups["dev"] = development
            validated_groups = m.Infra.DependencyGroupDeclarations.model_validate(
                {"dependency-groups": declared_groups},
            )
            declared_groups = {
                group: cls.dependency_group_wire(entries)
                for group, entries in validated_groups.dependency_groups.items()
            }
            renamed = {
                canonicalize_name(group): (
                    group
                    if position == 0
                    else f"{name}{policy.member_group_separator}{group}"
                )
                for group in declared_groups
            }
            if len(renamed) != len(declared_groups):
                return r[t.Cli.TomlDocument].fail(
                    f"resolution project has colliding normalized group names: {name}",
                )
            for target in renamed.values():
                normalized = canonicalize_name(target)
                if normalized in seen_groups:
                    return r[t.Cli.TomlDocument].fail(
                        f"resolution dependency-group names collide: {target}",
                    )
                seen_groups.add(normalized)
            project_sources = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
                project_uv.get("sources", {}),
            )
            if position == 0 and not project.repository.package:
                for dependency, raw_sources in project_sources.items():
                    normalized_dependency = canonicalize_name(dependency)
                    if normalized_dependency in overridden:
                        continue
                    entries = (
                        t.Cli.JSON_LIST_ADAPTER.validate_python(raw_sources)
                        if isinstance(raw_sources, list)
                        else [raw_sources]
                    )
                    sources[normalized_dependency] = [
                        cls._resolution_source(
                            t.Cli.JSON_MAPPING_ADAPTER.validate_python(entry),
                            project,
                            directory=directory,
                            group=None,
                        )
                        for entry in entries
                    ]
            for extra, raw_requirements in optional.items():
                target = (
                    extra
                    if position == 0
                    else f"{name}{policy.member_group_separator}{extra}"
                )
                normalized = canonicalize_name(target)
                if normalized in seen_extras:
                    return r[t.Cli.TomlDocument].fail(
                        f"resolution optional-dependency names collide: {target}",
                    )
                seen_extras.add(normalized)
                selected: list[t.JsonValue] = []
                for requirement in t.Cli.JSON_LIST_ADAPTER.validate_python(
                    raw_requirements,
                ):
                    if not isinstance(requirement, str):
                        return r[t.Cli.TomlDocument].fail(
                            "optional dependency is not a requirement string",
                        )
                    selected.append(cls._resolution_requirement(requirement, project))
                extras[target] = selected
                optional_names = {
                    FlextInfraUtilitiesDependencies.dep_name(requirement)
                    for requirement in selected
                    if isinstance(requirement, str)
                }
                for dependency, raw_sources in project_sources.items():
                    dependency_name = canonicalize_name(dependency)
                    if (
                        dependency_name in overridden
                        or dependency_name not in optional_names
                    ):
                        continue
                    entries = (
                        t.Cli.JSON_LIST_ADAPTER.validate_python(raw_sources)
                        if isinstance(raw_sources, list)
                        else [raw_sources]
                    )
                    for raw_source in entries:
                        source = t.Cli.JSON_MAPPING_ADAPTER.validate_python(raw_source)
                        source_extra = source.get("extra", extra)
                        if (
                            "group" in source
                            or not isinstance(source_extra, str)
                            or canonicalize_name(source_extra)
                            != canonicalize_name(extra)
                        ):
                            continue
                        relocated = cls._resolution_source(
                            source,
                            project,
                            directory=directory,
                            group=None,
                        )
                        relocated["extra"] = target
                        added = cls._resolution_add_source(
                            sources, dependency, relocated
                        )
                        if added.failure:
                            return r[t.Cli.TomlDocument].from_failure(added)
            for group, raw_entries in declared_groups.items():
                target = renamed[canonicalize_name(group)]
                rewritten: list[t.JsonValue] = []
                for entry in t.Cli.JSON_LIST_ADAPTER.validate_python(raw_entries):
                    if isinstance(entry, str):
                        rewritten.append(cls._resolution_requirement(entry, project))
                    else:
                        inclusion = m.Infra.DependencyGroupInclude.model_validate(entry)
                        included = inclusion.include_group
                        rewritten.append({
                            "include-group": renamed[canonicalize_name(included)],
                        })
                groups[target] = rewritten
                if position == 0 and not project.repository.package:
                    continue
                group_names = cls._resolution_group_requirement_names(
                    declared_groups,
                    group,
                )
                for dependency, raw_sources in project_sources.items():
                    dependency_name = canonicalize_name(dependency)
                    if (
                        dependency_name in overridden
                        or dependency_name not in group_names
                    ):
                        continue
                    entries = (
                        t.Cli.JSON_LIST_ADAPTER.validate_python(raw_sources)
                        if isinstance(raw_sources, list)
                        else [raw_sources]
                    )
                    for raw_source in entries:
                        source = t.Cli.JSON_MAPPING_ADAPTER.validate_python(raw_source)
                        source_group = source.get("group", group)
                        if (
                            "extra" in source
                            or not isinstance(source_group, str)
                            or canonicalize_name(source_group)
                            != canonicalize_name(group)
                        ):
                            continue
                        relocated = cls._resolution_source(
                            source,
                            project,
                            directory=directory,
                            group=target,
                        )
                        added = cls._resolution_add_source(
                            sources, dependency, relocated
                        )
                        if added.failure:
                            return r[t.Cli.TomlDocument].from_failure(added)
            for group, metadata_value in t.Cli.JSON_MAPPING_ADAPTER.validate_python(
                project_uv.get("dependency-groups", {}),
            ).items():
                if canonicalize_name(group) not in renamed:
                    return r[t.Cli.TomlDocument].fail(
                        f"resolution group metadata has no declaration: {name}:{group}",
                    )
                group_metadata[renamed[canonicalize_name(group)]] = deepcopy(
                    metadata_value
                )
            for raw_index in t.Cli.JSON_LIST_ADAPTER.validate_python(
                project_uv.get("index", []),
            ):
                index = t.Cli.JSON_MAPPING_ADAPTER.validate_python(raw_index)
                identity = index.get("name", "")
                if not isinstance(identity, str):
                    return r[t.Cli.TomlDocument].fail(
                        f"invalid resolution index name: {project.directory}",
                    )
                if identity in index_entries and index_entries[identity] != index:
                    return r[t.Cli.TomlDocument].fail(
                        f"resolution index declarations conflict: {identity}",
                    )
                index_entries[identity] = deepcopy(dict(index))
        if view_project:
            view_project["dependencies"] = dependencies
            view_project["optional-dependencies"] = extras
        binding_requirements = (
            member_bindings if view_project else [*dependencies, *member_bindings]
        )
        if binding_requirements:
            if canonicalize_name(virtual_name) in seen_groups:
                return r[t.Cli.TomlDocument].fail(
                    f"resolution binding group collides with a declaration: {virtual_name}",
                )
            groups[virtual_name] = binding_requirements
        native_uv["sources"] = sources
        native_uv["override-dependencies"] = retained_overrides
        if constraints:
            native_uv["constraint-dependencies"] = constraints
        if group_metadata:
            native_uv["dependency-groups"] = group_metadata
        if index_entries:
            native_uv["index"] = list(index_entries.values())
        view: t.JsonDict = {
            c.Infra.DEPENDENCY_GROUPS: groups,
            c.Infra.TOOL: {"uv": native_uv},
        }
        if view_project:
            view[c.Infra.PROJECT] = view_project
        return r[t.Cli.TomlDocument].ok(u.Cli.toml_document_from_mapping(view))

    @staticmethod
    def _resolution_group_requirement_names(
        groups: t.JsonMapping,
        group: str,
    ) -> t.StrSequence:
        """Identify native source applicability without flattening output groups."""
        normalized = {
            canonicalize_name(name): entries for name, entries in groups.items()
        }
        pending = [canonicalize_name(group)]
        visited: set[str] = set()
        names: set[str] = set()
        while pending:
            selected = pending.pop()
            if selected in visited:
                continue
            visited.add(selected)
            for requirement in t.Cli.JSON_LIST_ADAPTER.validate_python(
                normalized[selected],
            ):
                if isinstance(requirement, str):
                    name = FlextInfraUtilitiesDependencies.dep_name(requirement)
                    if name is not None:
                        names.add(name)
                else:
                    inclusion = m.Infra.DependencyGroupInclude.model_validate(
                        requirement
                    )
                    pending.append(canonicalize_name(inclusion.include_group))
        return tuple(sorted(names))

    @staticmethod
    def _resolution_add_source(
        sources: t.JsonDict,
        dependency: str,
        entry: t.JsonDict,
    ) -> p.Result[bool]:
        """Merge one context-qualified source without hiding source disagreement."""
        name = canonicalize_name(dependency)
        existing = t.Cli.JSON_LIST_ADAPTER.validate_python(sources.get(name, []))
        unscoped = [
            t.Cli.JSON_MAPPING_ADAPTER.validate_python(item)
            for item in existing
            if isinstance(item, Mapping) and "group" not in item and "extra" not in item
        ]
        if unscoped:
            unqualified = dict(entry)
            unqualified.pop("group", None)
            unqualified.pop("extra", None)
            if any(item != unqualified for item in unscoped):
                return r[bool].fail(f"resolution source contexts conflict: {name}")
            return r[bool].ok(value=False)
        if entry in existing:
            return r[bool].ok(value=False)
        sources[name] = [*existing, entry]
        return r[bool].ok(value=True)

    @staticmethod
    def _resolution_project_payload(
        project: m.Infra.UvResolutionProject,
    ) -> t.JsonDict:
        """Detach native metadata without mutating its authenticated document."""
        payload = u.Cli.toml_as_mapping(project.document)
        if payload is None:
            msg = f"resolution input is not a TOML mapping: {project.directory}"
            raise ValueError(msg)
        if not project.directory.is_absolute():
            msg = f"resolution input directory is not absolute: {project.directory}"
            raise ValueError(msg)
        return deepcopy(dict(payload))

    @staticmethod
    def _resolution_requirement(
        requirement: str,
        project: m.Infra.UvResolutionProject,
    ) -> str:
        """Rebase relative direct file references while retaining PEP 508 fields."""
        parsed = Requirement(requirement)
        if parsed.url is None:
            return requirement
        locator = urlsplit(parsed.url)
        if locator.scheme not in {"", "file"}:
            return requirement
        path = Path(unquote(locator.path))
        if path.is_absolute() or locator.netloc:
            return requirement
        parsed.url = (project.directory / path).resolve().as_uri()
        if locator.fragment:
            parsed.url += f"#{locator.fragment}"
        return str(parsed)

    @staticmethod
    def _resolution_source(
        source: t.JsonMapping,
        project: m.Infra.UvResolutionProject,
        *,
        directory: Path,
        group: str | None,
    ) -> t.JsonDict:
        """Relocate one native group source into its generated group context."""
        entry = deepcopy(dict(source))
        path = entry.get("path")
        if isinstance(path, str):
            entry["path"] = (
                (project.directory / path)
                .resolve()
                .relative_to(directory, walk_up=True)
                .as_posix()
            )
        workspace = entry.get("workspace")
        if isinstance(workspace, str):
            entry["workspace"] = (
                (project.directory / workspace)
                .resolve()
                .relative_to(directory, walk_up=True)
                .as_posix()
            )
        if group is not None:
            entry["group"] = group
        return entry

    @classmethod
    def document_requirement_lines(
        cls,
        document: t.Cli.TomlDocument,
    ) -> p.Result[list[str]]:
        """Collect every declared requirement line of one pyproject document.

        Returns:
            The resulting ``p.Result[list[str]]``.

        """
        payload = u.Cli.toml_as_mapping(document)
        if payload is None:
            return r[list[str]].fail("pyproject document is not a TOML mapping")
        requirements: list[str] = []
        project = payload.get(c.Infra.PROJECT)
        if isinstance(project, Mapping):
            for key in (c.Infra.DEPENDENCIES, c.Infra.OPTIONAL_DEPENDENCIES):
                requirements.extend(
                    FlextInfraUtilitiesDependencies.raw_requirement_values(
                        project.get(key),
                    ),
                )
        groups = payload.get(c.Infra.DEPENDENCY_GROUPS)
        if isinstance(groups, Mapping):
            for group in groups.values():
                requirements.extend(
                    FlextInfraUtilitiesDependencies.raw_requirement_values(
                        group,
                    ),
                )
        return r[list[str]].ok(requirements)

    @classmethod
    def active_session_requirements(
        cls,
        document: t.Cli.TomlDocument,
        *,
        environment: t.StrMapping,
    ) -> t.VariadicTuple[str]:
        """Read strictly parsed requirements active on the consumer interpreter.

        Returns:
            The resulting ``t.VariadicTuple[str]``.

        """
        return tuple(
            active
            for item in cls.document_requirement_lines(document).unwrap()
            if (
                active := FlextInfraUtilitiesDependencies.active_requirement(
                    item,
                    environment=environment,
                )
            )
            is not None
        )

    @classmethod
    def direct_source_names(
        cls,
        document: t.Cli.TomlDocument,
    ) -> p.Result[t.VariadicTuple[str]]:
        """Name every requirement taken by direct ``@ source`` reference.

        Forks and local projects reach a project only this way, never from a
        registry, so this is the derived set the supply-chain cooldown skips.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[str]]``.

        """
        lines = cls.document_requirement_lines(document)
        if lines.failure:
            return r[t.VariadicTuple[str]].from_failure(lines)
        return r[t.VariadicTuple[str]].ok(
            tuple(
                sorted({
                    name
                    for item in lines.value
                    if cls._declares_direct_source(item)
                    and (name := FlextInfraUtilitiesDependencies.dep_name(item))
                    is not None
                }),
            ),
        )

    @staticmethod
    def _resolved_uv_table(document: t.Cli.TomlDocument) -> t.Cli.TomlTable:
        """Return the ``[tool.uv]`` table, creating its nesting when absent.

        Returns:
            The resulting ``t.Cli.TomlTable``.

        """
        tool = u.Cli.toml_table_child(document, c.Infra.TOOL)
        if tool is None:
            tool = u.Cli.toml_ensure_table(document, c.Infra.TOOL)
        uv = u.Cli.toml_table_child(tool, "uv")
        return uv if uv is not None else u.Cli.toml_ensure_table(tool, "uv")

    @staticmethod
    def _sync_uv_candidates(
        uv: t.Cli.TomlTable,
        candidate_sources: t.StrMapping,
        requirements: t.StrSequence,
        resolution: m.Infra.UvResolutionSpec,
    ) -> None:
        """Sync the staging candidate pins over every resolved requirement.

        A declared candidate commit replaces every direct and transitive
        requirement for that distribution during staging. The candidate
        manifest owns this temporary pin; the committed lock owns normal
        resolutions when no candidate is declared (flext-oe420).

        Only explicit SSOT overrides and authenticated staging candidates
        belong in package metadata. Local development bindings are owned
        by the generated native resolution view.
        """
        overrides = list(resolution.override_dependencies)
        for name, source in sorted(candidate_sources.items()):
            extras = FlextInfraUtilitiesDependencyRequirements.dependency_extras(
                requirements,
                name,
            )
            overrides.append(f"{name}{extras} @ {source}")
        if overrides:
            u.Cli.toml_sync_string_list(
                uv,
                "override-dependencies",
                overrides,
            )
        else:
            u.Cli.toml_remove_key_if_present(uv, "override-dependencies")

    @staticmethod
    def _sync_uv_constraints(
        uv: t.Cli.TomlTable,
        resolution: m.Infra.UvResolutionSpec,
    ) -> None:
        """Sync the SSOT-rendered constraints, link mode, and banned cooldown keys.

        Constraints are SSOT-rendered: the declared config value is the only
        source, so a removed declaration exterminates the key everywhere and
        no orphan cap can survive without an owner. uv carries no cooldown
        key: `exclude-newer` (any form) is banned (operator 2026-09-16). The
        fleet cooldown lives once in
        codegen.toolchain.dependency_cooldown_days and reaches mise and
        dependabot (operator 2026-10-01). Removed declarations exterminate
        the keys everywhere so no orphan cap survives (flext-gzfd2 class).
        """
        retained_constraints = tuple(
            requirement
            for requirement in resolution.constraint_dependencies
            if FlextInfraUtilitiesDependencies.dep_name(requirement) != "uv"
        )
        if retained_constraints:
            u.Cli.toml_sync_string_list(
                uv,
                "constraint-dependencies",
                retained_constraints,
            )
        else:
            u.Cli.toml_remove_key_if_present(uv, "constraint-dependencies")
        u.Cli.toml_sync_value(uv, "link-mode", resolution.link_mode)
        u.Cli.toml_remove_key_if_present(uv, "exclude-newer")
        u.Cli.toml_remove_key_if_present(uv, "exclude-newer-package")

    @staticmethod
    def _sync_uv_environments(
        uv: t.Cli.TomlTable,
        resolution: m.Infra.UvResolutionSpec,
    ) -> None:
        """Sync the fleet toolchain SSOT environments.

        Environments come from the fleet toolchain SSOT: an empty declaration
        removes the key so uv resolves every environment, and a declared
        sequence skips the splits the fleet does not support (win32 resolves
        meltano's structlog cap against flext-core's floor and is
        unsatisfiable).
        """
        if resolution.environments:
            # Declared as list[JsonValue], not list[str]: `list` is invariant,
            # so the narrower element type is not assignable to the writer's
            # parameter even though every element is a valid JsonValue.
            environments: list[t.JsonValue] = list(resolution.environments)
            u.Cli.toml_sync_value(uv, "environments", environments)
        else:
            u.Cli.toml_remove_key_if_present(uv, "environments")

    @classmethod
    def _sync_uv_sources(
        cls,
        document: t.Cli.TomlDocument,
        *,
        resolution: m.Infra.UvResolutionSpec,
        candidate_sources: t.StrMapping,
        workspace: m.Infra.WorkspaceSpec,
        local_requirements: t.StrSequence,
    ) -> p.Result[bool]:
        """Render the conform-owned ``[tool.uv]`` keys and workspace identity.

        The resolver keys are always declared, so the table always exists and
        never ends empty.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        uv = cls._resolved_uv_table(document)
        members = (
            tuple(member for member in workspace.subprojects if member.package)
            if workspace.repository.role is c.Infra.MakeProfile.WORKSPACE
            else ()
        )
        root_names = (
            (workspace.repository.distribution,) if workspace.repository.package else ()
        )
        local_names = (*root_names, *(member.distribution for member in members))
        conflicting = set(local_names) & candidate_sources.keys()
        if conflicting:
            return r[bool].fail(
                "candidate source overrides local members: "
                + ", ".join(sorted(conflicting)),
            )
        # Authored metadata retains declared policy. Native resolution views own
        # local source overrides and the constraints preserving replaced sources.
        cls._sync_uv_candidates(
            uv,
            candidate_sources,
            local_requirements,
            resolution,
        )
        u.Cli.toml_remove_key_if_present(uv, "required-version")
        cls._sync_uv_constraints(uv, resolution)
        cls._sync_uv_environments(uv, resolution)
        u.Cli.toml_remove_key_if_present(uv, "exclude-dependencies")
        cls._retire_generated_local_sources(
            uv,
            (workspace.repository, *workspace.subprojects),
        )
        return r[bool].ok(value=True)

    @staticmethod
    def _retire_generated_local_sources(
        uv: t.Cli.TomlTable,
        repositories: t.SequenceOf[p.Infra.RepositoryRef],
    ) -> None:
        """Remove only identifiable old generated local bindings.

        Native workspace declarations and custom sources remain owned by
        their author. A source outside the authenticated declarations is
        never inferred to be generated from its name or source type.
        """
        sources = u.Cli.toml_table_child(uv, "sources")
        if sources is None:
            return
        source_names = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
            u.Cli.toml_unwrap_item(sources),
        )
        declared = {canonicalize_name(item.distribution): item for item in repositories}
        has_native_workspace = u.Cli.toml_value(uv, "workspace") is not None
        for source_name, entry in source_names.items():
            repository = declared.get(canonicalize_name(source_name))
            if repository is None or not isinstance(entry, Mapping):
                continue
            generated_path = {
                "path": repository.path.as_posix(),
                "editable": repository.editable,
            }
            generated_self = (
                repository.path == Path()
                and not has_native_workspace
                and entry == {"workspace": True}
            )
            if not has_native_workspace and (entry == generated_path or generated_self):
                u.Cli.toml_remove_key_if_present(sources, source_name)
        if not sources:
            u.Cli.toml_remove_key_if_present(uv, "sources")


__all__: list[str] = ["FlextInfraUtilitiesPyprojectUvSources"]
