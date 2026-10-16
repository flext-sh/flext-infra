"""Conform-owned ``[tool.uv]`` rendering for one pyproject document.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableSet
from copy import deepcopy
from pathlib import Path
from typing import ClassVar
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


class _ResolutionViewState(m.ArbitraryTypesModel):
    """Mutable accumulator for one native resolution view projection."""

    model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
        extra="forbid",
        arbitrary_types_allowed=True,
    )

    directory: Path = m.Field(
        description="Generated view root resolving member relative paths.",
    )
    policy: m.Infra.MakeUvResolutionSpec = m.Field(
        description="Declared resolution policy owning member naming.",
    )
    native_uv: t.MutableJsonMapping = m.Field(
        description="Detached root ``[tool.uv]`` table under projection.",
    )
    view_project: t.MutableJsonMapping = m.Field(
        description="Generated virtual project table, empty when absent.",
    )
    dependencies: t.MutableJsonList = m.Field(
        description="Root dependency requests in declaration order.",
    )
    member_bindings: t.MutableJsonList = m.Field(
        description="Member dependency requests in declaration order.",
    )
    extras: t.MutableJsonMapping = m.Field(
        description="View optional-dependency groups by target name.",
    )
    groups: t.MutableJsonMapping = m.Field(
        description="View dependency groups by target name.",
    )
    group_metadata: t.MutableJsonMapping = m.Field(
        description="Renamed group metadata keyed by target name.",
    )
    sources: t.MutableJsonMapping = m.Field(
        description="Context-qualified source entries by dependency name.",
    )
    index_entries: t.MutableJsonMapping = m.Field(
        description="Conflict-checked index declarations by identity.",
    )
    constraints: t.MutableJsonList = m.Field(
        description="Constraints preserving replaced local sources.",
    )
    retained_overrides: t.MutableJsonList = m.Field(
        description="Declared overrides with member requests appended.",
    )
    overridden: MutableSet[str] = m.Field(
        description="Canonical member names already natively bound.",
    )
    seen_groups: MutableSet[str] = m.Field(
        description="Normalized group names already claimed.",
    )
    seen_extras: MutableSet[str] = m.Field(
        description="Normalized extra names already claimed.",
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

        Returns:
            The resulting ``p.Result[t.Cli.TomlDocument]``.

        """
        validated = cls._validated_resolution_projects(
            root, members, directory=directory, policy=policy
        )
        if validated.failure:
            return r[t.Cli.TomlDocument].from_failure(validated)
        projects, virtual_name = validated.value
        state = cls._resolution_view_state(
            root, projects, virtual_name, directory=directory, policy=policy
        )
        for position, project in enumerate(projects):
            projected = cls._resolution_project_view(state, project, position)
            if projected.failure:
                return r[t.Cli.TomlDocument].from_failure(projected)
        bound = cls._resolution_bound_groups(state, virtual_name)
        if bound.failure:
            return r[t.Cli.TomlDocument].from_failure(bound)
        native_uv = state.native_uv
        native_uv["sources"] = dict(state.sources)
        native_uv["override-dependencies"] = list(state.retained_overrides)
        if state.constraints:
            native_uv["constraint-dependencies"] = list(state.constraints)
        if state.group_metadata:
            native_uv["dependency-groups"] = dict(state.group_metadata)
        if state.index_entries:
            native_uv["index"] = list(state.index_entries.values())
        view: t.JsonDict = {
            c.Infra.DEPENDENCY_GROUPS: dict(state.groups),
            c.Infra.TOOL: {"uv": dict(native_uv)},
        }
        if state.view_project:
            view[c.Infra.PROJECT] = dict(state.view_project)
        return r[t.Cli.TomlDocument].ok(u.Cli.toml_document_from_mapping(view))

    @staticmethod
    def _resolution_bound_groups(
        state: _ResolutionViewState,
        virtual_name: str,
    ) -> p.Result[bool]:
        """Bind the virtual project tables and the synthetic member group.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if state.view_project:
            state.view_project["dependencies"] = list(state.dependencies)
            state.view_project["optional-dependencies"] = dict(state.extras)
        binding_requirements = (
            list(state.member_bindings)
            if state.view_project
            else [*state.dependencies, *state.member_bindings]
        )
        if binding_requirements:
            if canonicalize_name(virtual_name) in state.seen_groups:
                return r[bool].fail(
                    f"resolution binding group collides with a declaration:"
                    f" {virtual_name}",
                )
            state.groups[virtual_name] = binding_requirements
        return r[bool].ok(value=True)

    @classmethod
    def _validated_resolution_projects(
        cls,
        root: m.Infra.UvResolutionProject,
        members: t.SequenceOf[m.Infra.UvResolutionProject],
        *,
        directory: Path,
        policy: m.Infra.MakeUvResolutionSpec,
    ) -> p.Result[t.Pair[list[m.Infra.UvResolutionProject], str]]:
        """Validate the resolution roster and elect the virtual distribution.

        Returns:
            The ordered projects and the virtual distribution name.

        """
        failure = r[t.Pair[list[m.Infra.UvResolutionProject], str]]
        if not directory.is_absolute():
            return failure.fail(
                f"resolution view directory is not absolute: {directory}",
            )
        projects = [
            root,
            *sorted(members, key=lambda item: item.repository.distribution),
        ]
        names = [
            canonicalize_name(project.repository.distribution) for project in projects
        ]
        if len(names) != len(set(names)):
            return failure.fail(
                "resolution projects have colliding normalized distribution names",
            )
        virtual_name = canonicalize_name(
            root.repository.distribution + policy.virtual_distribution_suffix,
        )
        if virtual_name in names:
            return failure.fail(
                f"resolution distribution collides with a declared project:"
                f" {virtual_name}",
            )
        return failure.ok((
            projects,
            virtual_name,
        ))

    @classmethod
    def _resolution_view_state(
        cls,
        root: m.Infra.UvResolutionProject,
        projects: t.SequenceOf[m.Infra.UvResolutionProject],
        virtual_name: str,
        *,
        directory: Path,
        policy: m.Infra.MakeUvResolutionSpec,
    ) -> _ResolutionViewState:
        """Detach the root metadata and scaffold the projection accumulators.

        Returns:
            The resolution view state seeded from the root project.

        """
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
        overrides = t.Cli.JSON_LIST_ADAPTER.validate_python(
            native_uv.get("override-dependencies", []),
        )
        constraints = list(
            t.Cli.JSON_LIST_ADAPTER.validate_python(
                native_uv.get("constraint-dependencies", []),
            ),
        )
        return _ResolutionViewState(
            directory=directory,
            policy=policy,
            native_uv=native_uv,
            view_project=view_project,
            dependencies=[],
            member_bindings=[],
            extras={},
            groups={},
            group_metadata={},
            sources={},
            index_entries={},
            constraints=constraints,
            retained_overrides=list(overrides),
            overridden={
                canonicalize_name(project.repository.distribution)
                for project in projects
            },
            seen_groups=set(),
            seen_extras=set(),
        )

    @classmethod
    def _resolution_project_view(
        cls,
        state: _ResolutionViewState,
        project: m.Infra.UvResolutionProject,
        position: int,
    ) -> p.Result[bool]:
        """Collect one project's contributions into the resolution view state.

        Returns:
            The resulting ``p.Result[bool]``.

        """
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
            return r[bool].fail(
                f"resolution project identity differs from its declaration:"
                f" {project.directory}",
            )
        optional = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
            metadata.get(c.Infra.OPTIONAL_DEPENDENCIES, {}),
        )
        root = position == 0
        cls._resolution_project_constraints(state, project)
        cls._resolution_project_request(state, project, optional, name, root=root)
        tool = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
            payload.get(c.Infra.TOOL, {}),
        )
        project_uv = t.Cli.JSON_MAPPING_ADAPTER.validate_python(tool.get("uv", {}))
        if root and not project.repository.package:
            failed = cls._resolution_root_dependencies(state, project, metadata)
            if failed.failure:
                return failed
        declared_groups = cls._resolution_declared_groups(payload, project_uv)
        renamed = cls._resolution_group_targets(state, declared_groups, name, root=root)
        if renamed.failure:
            return r[bool].from_failure(renamed)
        project_sources = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
            project_uv.get("sources", {}),
        )
        if root and not project.repository.package:
            cls._resolution_root_project_sources(state, project, project_sources)
        resolved = cls._resolution_extra_requirements(
            state, project, optional, name, root=root
        )
        if resolved.failure:
            return r[bool].from_failure(resolved)
        phases: t.VariadicTuple[
            t.Pair[str, t.SequenceOf[t.Triple[str, t.StrSequence, str]]]
        ] = (
            (
                "extra",
                [
                    (target, tuple(optional_names), extra)
                    for extra, (target, optional_names) in resolved.value.items()
                ],
            ),
            (
                "group",
                []
                if root and not project.repository.package
                else [
                    (
                        renamed.value[canonicalize_name(group)],
                        cls._resolution_group_requirement_names(declared_groups, group),
                        group,
                    )
                    for group in declared_groups
                ],
            ),
        )
        for qualifier, context_list in phases:
            relocated = cls._resolution_context_sources(
                state,
                project,
                project_sources,
                context_list,
                qualifier=qualifier,
            )
            if relocated.failure:
                return relocated
        cls._resolution_group_entries(state, project, declared_groups, renamed.value)
        return cls._resolution_project_exports(
            state, project, project_uv, renamed.value, name
        )

    @classmethod
    def _resolution_project_exports(
        cls,
        state: _ResolutionViewState,
        project: m.Infra.UvResolutionProject,
        project_uv: t.JsonMapping,
        renamed: t.MappingKV[str, str],
        name: str,
    ) -> p.Result[bool]:
        """Export renamed group metadata and merged index declarations.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        failed = cls._resolution_group_metadata(state, project_uv, renamed, name)
        if failed.failure:
            return failed
        return cls._resolution_index_entries(state, project, project_uv)

    @classmethod
    def _resolution_project_constraints(
        cls,
        state: _ResolutionViewState,
        project: m.Infra.UvResolutionProject,
    ) -> None:
        """Extend the state constraints over the project's overridden demands."""
        state.constraints.extend(
            FlextInfraUtilitiesDependencies.dependency_constraint(
                requirement,
                replace_source=True,
            )
            for requirement in cls.document_requirement_lines(project.document).unwrap()
            if FlextInfraUtilitiesDependencies.dep_name(requirement) in state.overridden
        )

    @staticmethod
    def _resolution_explicit_overrides(
        state: _ResolutionViewState,
    ) -> set[str]:
        """Name the distributions explicitly pinned by declared overrides.

        Returns:
            The canonical dependency names of the declared override entries.

        """
        return {
            name
            for entry in t.Cli.JSON_LIST_ADAPTER.validate_python(
                state.native_uv.get("override-dependencies", []),
            )
            if isinstance(entry, str)
            and (name := FlextInfraUtilitiesDependencies.dep_name(entry)) is not None
        }

    @classmethod
    def _resolution_project_request(
        cls,
        state: _ResolutionViewState,
        project: m.Infra.UvResolutionProject,
        optional: t.JsonMapping,
        name: str,
        *,
        root: bool,
    ) -> None:
        """Record one project's dependency request and native path binding."""
        selected_extras = tuple(sorted(optional))
        request = name
        if selected_extras:
            request += f"[{','.join(selected_extras)}]"
        if project.repository.package:
            if root:
                state.dependencies.append(request)
            else:
                state.member_bindings.append(request)
            if name not in cls._resolution_explicit_overrides(state):
                state.retained_overrides.append(request)
            state.sources[name] = {
                "path": project.directory.relative_to(
                    state.directory,
                    walk_up=True,
                ).as_posix(),
                "editable": project.repository.editable,
            }

    @classmethod
    def _resolution_root_dependencies(
        cls,
        state: _ResolutionViewState,
        project: m.Infra.UvResolutionProject,
        metadata: t.JsonMapping,
    ) -> p.Result[bool]:
        """Collect the root content-only project's runtime dependencies.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        for requirement in t.Cli.JSON_LIST_ADAPTER.validate_python(
            metadata.get(c.Infra.DEPENDENCIES, []),
        ):
            if not isinstance(requirement, str):
                return r[bool].fail(
                    "content-only runtime dependency is not a requirement string",
                )
            state.dependencies.append(cls._resolution_requirement(requirement, project))
        return r[bool].ok(value=True)

    @classmethod
    def _resolution_declared_groups(
        cls,
        payload: t.JsonDict,
        project_uv: t.JsonMapping,
    ) -> t.JsonDict:
        """Merge legacy dev dependencies and wire the declared groups.

        Returns:
            The project's declared groups in their view-level wire form.

        """
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
        return {
            group: cls.dependency_group_wire(entries)
            for group, entries in validated_groups.dependency_groups.items()
        }

    @classmethod
    def _resolution_group_targets(
        cls,
        state: _ResolutionViewState,
        declared_groups: t.JsonDict,
        name: str,
        *,
        root: bool,
    ) -> p.Result[dict[str, str]]:
        """Rename the declared groups and refuse target collisions.

        Returns:
            The declared groups mapped to their view-level target names.

        """
        renamed: dict[str, str] = {
            canonicalize_name(group): (
                group if root else f"{name}{state.policy.member_group_separator}{group}"
            )
            for group in declared_groups
        }
        if len(renamed) != len(declared_groups):
            return r[dict[str, str]].fail(
                f"resolution project has colliding normalized group names: {name}",
            )
        for target in renamed.values():
            normalized = canonicalize_name(target)
            if normalized in state.seen_groups:
                return r[dict[str, str]].fail(
                    f"resolution dependency-group names collide: {target}",
                )
            state.seen_groups.add(normalized)
        return r[dict[str, str]].ok(renamed)

    @classmethod
    def _resolution_root_project_sources(
        cls,
        state: _ResolutionViewState,
        project: m.Infra.UvResolutionProject,
        project_sources: t.JsonMapping,
    ) -> None:
        """Relocate the root content-only project's declared sources."""
        for dependency, raw_sources in project_sources.items():
            normalized_dependency = canonicalize_name(dependency)
            if normalized_dependency in state.overridden:
                continue
            entries = (
                t.Cli.JSON_LIST_ADAPTER.validate_python(raw_sources)
                if isinstance(raw_sources, list)
                else [raw_sources]
            )
            state.sources[normalized_dependency] = [
                cls._resolution_source(
                    t.Cli.JSON_MAPPING_ADAPTER.validate_python(entry),
                    project,
                    directory=state.directory,
                    group=None,
                )
                for entry in entries
            ]

    @classmethod
    def _resolution_extra_requirements(
        cls,
        state: _ResolutionViewState,
        project: m.Infra.UvResolutionProject,
        optional: t.JsonMapping,
        name: str,
        *,
        root: bool,
    ) -> p.Result[dict[str, t.Pair[str, set[str]]]]:
        """Rewrite the project's extras into view-level target groups.

        Returns:
            Each declared extra mapped to its target name and the canonical
            dependency names it selects.

        """
        resolved: dict[str, t.Pair[str, set[str]]] = {}
        failure = r[dict[str, t.Pair[str, set[str]]]]
        for extra, raw_requirements in optional.items():
            target = (
                extra if root else f"{name}{state.policy.member_group_separator}{extra}"
            )
            normalized = canonicalize_name(target)
            if normalized in state.seen_extras:
                return failure.fail(
                    f"resolution optional-dependency names collide: {target}",
                )
            state.seen_extras.add(normalized)
            selected: list[t.JsonValue] = []
            for requirement in t.Cli.JSON_LIST_ADAPTER.validate_python(
                raw_requirements,
            ):
                if not isinstance(requirement, str):
                    return failure.fail(
                        "optional dependency is not a requirement string",
                    )
                selected.append(cls._resolution_requirement(requirement, project))
            state.extras[target] = selected
            optional_names = {
                dependency
                for requirement in selected
                if isinstance(requirement, str)
                and (
                    dependency := FlextInfraUtilitiesDependencies.dep_name(requirement)
                )
                is not None
            }
            resolved[extra] = (target, optional_names)
        return failure.ok(resolved)

    @classmethod
    def _resolution_context_sources(
        cls,
        state: _ResolutionViewState,
        project: m.Infra.UvResolutionProject,
        project_sources: t.JsonMapping,
        contexts: t.SequenceOf[t.Triple[str, t.StrSequence, str]],
        *,
        qualifier: str,
    ) -> p.Result[bool]:
        """Relocate extra- and group-qualified sources to their view targets.

        Each context carries its view-level target name, the canonical
        dependency names it selects, and the declared qualifier origin. A
        source carrying the opposite qualifier never relocates, and a
        mismatched declared qualifier leaves the entry to its owning context.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        forbidden = "extra" if qualifier == "group" else "group"
        for target, selected_names, origin in contexts:
            for dependency, raw_sources in project_sources.items():
                dependency_name = canonicalize_name(dependency)
                if (
                    dependency_name in state.overridden
                    or dependency_name not in selected_names
                ):
                    continue
                entries = (
                    t.Cli.JSON_LIST_ADAPTER.validate_python(raw_sources)
                    if isinstance(raw_sources, list)
                    else [raw_sources]
                )
                for raw_source in entries:
                    source = t.Cli.JSON_MAPPING_ADAPTER.validate_python(raw_source)
                    declared = source.get(qualifier, origin)
                    if (
                        forbidden in source
                        or not isinstance(declared, str)
                        or canonicalize_name(declared) != canonicalize_name(origin)
                    ):
                        continue
                    relocated = cls._resolution_source(
                        source,
                        project,
                        directory=state.directory,
                        group=target if qualifier == "group" else None,
                    )
                    if qualifier == "extra":
                        relocated["extra"] = target
                    added = cls._resolution_add_source(
                        state.sources, dependency, relocated
                    )
                    if added.failure:
                        return r[bool].from_failure(added)
        return r[bool].ok(value=True)

    @classmethod
    def _resolution_group_entries(
        cls,
        state: _ResolutionViewState,
        project: m.Infra.UvResolutionProject,
        declared_groups: t.JsonDict,
        renamed: t.MappingKV[str, str],
    ) -> None:
        """Rewrite the project's group entries under their target names."""
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
            state.groups[target] = rewritten

    @classmethod
    def _resolution_group_metadata(
        cls,
        state: _ResolutionViewState,
        project_uv: t.JsonMapping,
        renamed: t.MappingKV[str, str],
        name: str,
    ) -> p.Result[bool]:
        """Copy the project's group metadata under its renamed targets.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        for group, metadata_value in t.Cli.JSON_MAPPING_ADAPTER.validate_python(
            project_uv.get("dependency-groups", {}),
        ).items():
            if canonicalize_name(group) not in renamed:
                return r[bool].fail(
                    f"resolution group metadata has no declaration: {name}:{group}",
                )
            state.group_metadata[renamed[canonicalize_name(group)]] = deepcopy(
                metadata_value
            )
        return r[bool].ok(value=True)

    @classmethod
    def _resolution_index_entries(
        cls,
        state: _ResolutionViewState,
        project: m.Infra.UvResolutionProject,
        project_uv: t.JsonMapping,
    ) -> p.Result[bool]:
        """Merge the project's index declarations without conflicts.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        for raw_index in t.Cli.JSON_LIST_ADAPTER.validate_python(
            project_uv.get("index", []),
        ):
            index = t.Cli.JSON_MAPPING_ADAPTER.validate_python(raw_index)
            identity = index.get("name", "")
            if not isinstance(identity, str):
                return r[bool].fail(
                    f"invalid resolution index name: {project.directory}",
                )
            if (
                identity in state.index_entries
                and state.index_entries[identity] != index
            ):
                return r[bool].fail(
                    f"resolution index declarations conflict: {identity}",
                )
            state.index_entries[identity] = deepcopy(dict(index))
        return r[bool].ok(value=True)

    @staticmethod
    def _resolution_group_requirement_names(
        groups: t.JsonMapping,
        group: str,
    ) -> t.StrSequence:
        """Identify native source applicability without flattening output groups.

        Returns:
            The resulting ``t.StrSequence``.

        """
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
        sources: t.MutableJsonMapping,
        dependency: str,
        entry: t.JsonDict,
    ) -> p.Result[bool]:
        """Merge one context-qualified source without hiding source disagreement.

        Returns:
            The resulting ``p.Result[bool]``.

        """
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
        """Detach native metadata without mutating its authenticated document.

        Returns:
            The resulting ``t.JsonDict``.

        Raises:
            ValueError: If the document is not a TOML mapping or the project
                directory is not absolute.

        """
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
        """Rebase relative direct file references while retaining PEP 508 fields.

        Returns:
            The resulting ``str`` requirement.

        """
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
        """Relocate one native group source into its generated group context.

        Returns:
            The resulting ``t.JsonDict``.

        """
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
        local_names = (
            *(
                (workspace.repository.distribution,)
                if workspace.repository.package
                else ()
            ),
            *(member.distribution for member in members),
        )
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
