"""Native UV declaration policy without a parallel dependency graph.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping

from flext_cli import u
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from flext_infra import c, m, p, r, t
from flext_infra._utilities import FlextInfraUtilitiesDependencies
from flext_infra._utilities._pyproject import FlextInfraUtilitiesPyprojectRequirements
from flext_infra._utilities.dependency_requirements import (
    FlextInfraUtilitiesDependencyRequirements,
)


class FlextInfraUtilitiesPyprojectUvSources(FlextInfraUtilitiesPyprojectRequirements):
    """Conform generated native UV leaves and preserve authored native policy."""

    @classmethod
    def document_requirement_lines(
        cls,
        document: t.Cli.TomlDocument,
        *,
        development: bool = True,
        extras: t.StrSequence | None = None,
    ) -> p.Result[list[str]]:
        """Read declared requirements without resolving or flattening a graph.

        Returns:
            Runtime, selected optional, and optionally development requirements.

        """
        payload = u.Cli.toml_as_mapping(document)
        if payload is None:
            return r[list[str]].fail("pyproject document is not a TOML mapping")
        requirements: list[str] = []
        project = payload.get(c.Infra.PROJECT)
        if isinstance(project, Mapping):
            requirements.extend(
                FlextInfraUtilitiesDependencies.raw_requirement_values(
                    project.get(c.Infra.DEPENDENCIES),
                ),
            )
            optional = project.get(c.Infra.OPTIONAL_DEPENDENCIES)
            if isinstance(optional, Mapping):
                selected = (
                    None if extras is None else set(map(canonicalize_name, extras))
                )
                for extra, entries in optional.items():
                    if selected is None or canonicalize_name(extra) in selected:
                        requirements.extend(
                            FlextInfraUtilitiesDependencies.raw_requirement_values(
                                entries
                            )
                        )
        groups = payload.get(c.Infra.DEPENDENCY_GROUPS)
        if development and isinstance(groups, Mapping):
            for group in groups.values():
                requirements.extend(
                    FlextInfraUtilitiesDependencies.raw_requirement_values(group),
                )
        return r[list[str]].ok(requirements)

    @classmethod
    def direct_source_names(
        cls, document: t.Cli.TomlDocument
    ) -> p.Result[t.VariadicTuple[str]]:
        """Name every requirement declared by direct source reference.

        Returns:
            The canonical distribution names of direct requirement sources.

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
        """Return the native UV table, creating only missing parents.

        Returns:
            The document's native UV table.

        """
        return u.Cli.toml_ensure_path(document, (c.Infra.TOOL, "uv"))

    @staticmethod
    def _uv_override_wire(
        entries: t.SequenceOf[str | m.Infra.UvScopedOverride],
    ) -> t.JsonValueList:
        """Elect declared global overrides while preserving native scoped policy.

        Returns:
            Native override entries, with later declarations taking precedence.

        """
        parsed = m.Infra.UvOverrideEntries.model_validate(list(entries), strict=True)
        selected: list[str | m.Infra.UvScopedOverride] = []
        seen: set[t.Pair[str, str | None]] = set()
        for entry in reversed(parsed.root):
            if isinstance(entry, str):
                requirement = Requirement(entry)
                identity = (
                    canonicalize_name(requirement.name),
                    str(requirement.marker) if requirement.marker is not None else None,
                )
                if identity in seen:
                    continue
                seen.add(identity)
            selected.append(entry)
        elected = m.Infra.UvOverrideEntries.model_validate(
            list(reversed(selected)), strict=True
        )
        return list(
            u.json_list_adapter().validate_python(
                elected.model_dump(mode="json", exclude_none=True),
            ),
        )

    @staticmethod
    def _sync_uv_candidates(
        uv: t.Cli.TomlTable,
        candidate_sources: t.StrMapping,
        requirements: t.StrSequence,
        resolution: m.Infra.UvResolutionSpec,
    ) -> None:
        """Publish explicit toolchain overrides and authenticated candidate pins."""
        overrides = list(resolution.override_dependencies)
        for name, source in sorted(candidate_sources.items()):
            extras = FlextInfraUtilitiesDependencyRequirements.dependency_extras(
                requirements, name
            )
            overrides.append(f"{name}{extras} @ {source}")
        if overrides:
            u.Cli.toml_sync_value(
                uv,
                "override-dependencies",
                FlextInfraUtilitiesPyprojectUvSources._uv_override_wire(overrides),
            )
        else:
            u.Cli.toml_remove_key_if_present(uv, "override-dependencies")

    @staticmethod
    def _sync_uv_constraints(
        uv: t.Cli.TomlTable, resolution: m.Infra.UvResolutionSpec
    ) -> None:
        """Publish declared constraints and native linking, without cooldown copies."""
        constraints = tuple(
            requirement
            for requirement in resolution.constraint_dependencies
            if FlextInfraUtilitiesDependencies.dep_name(requirement) != "uv"
        )
        if constraints:
            u.Cli.toml_sync_string_list(uv, "constraint-dependencies", constraints)
        else:
            u.Cli.toml_remove_key_if_present(uv, "constraint-dependencies")
        u.Cli.toml_sync_value(uv, "link-mode", resolution.link_mode)
        u.Cli.toml_remove_key_if_present(uv, "exclude-newer")
        u.Cli.toml_remove_key_if_present(uv, "exclude-newer-package")

    @staticmethod
    def _sync_uv_environments(
        uv: t.Cli.TomlTable, resolution: m.Infra.UvResolutionSpec
    ) -> None:
        """Publish the environments declared by the native toolchain policy."""
        if resolution.environments:
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
        """Publish native workspace membership without altering package requirements.

        Sources on the root are inherited by members. Their standalone PEP 508
        declarations remain intact; UV owns source lowering and graph resolution.

        Returns:
            Successful declaration synchronization or a conflicting native source.

        """
        uv = cls._resolved_uv_table(document)
        if workspace.repository.role is c.Infra.MakeProfile.WORKSPACE:
            members = tuple(
                member for member in workspace.subprojects if member.package
            )
            repositories = (
                *((workspace.repository,) if workspace.repository.package else ()),
                *members,
            )
            conflicting = {
                canonicalize_name(item.distribution) for item in repositories
            } & candidate_sources.keys()
            if conflicting:
                return r[bool].fail(
                    "candidate source overrides local members: "
                    + ", ".join(sorted(conflicting)),
                )
            sources = u.Cli.toml_ensure_table(uv, "sources")
            declared_sources = u.json_mapping_adapter().validate_python(
                u.Cli.toml_unwrap_item(sources)
            )
            for repository in repositories:
                name = canonicalize_name(repository.distribution)
                names = tuple(
                    source_name
                    for source_name in declared_sources
                    if canonicalize_name(source_name) == name
                )
                if len(names) > 1:
                    return r[bool].fail(
                        f"workspace member has duplicate native source names: {name}"
                    )
                if names:
                    existing = declared_sources[names[0]]
                    entries = existing if isinstance(existing, list) else [existing]
                    if not entries or not all(
                        isinstance(entry, Mapping) and entry.get("workspace") is True
                        for entry in entries
                    ):
                        return r[bool].fail(
                            "declared workspace member has a conflicting "
                            f"native source: {name}",
                        )
                    continue
                u.Cli.toml_sync_value(sources, name, {"workspace": True})
            native_workspace = u.Cli.toml_ensure_table(uv, "workspace")
            u.Cli.toml_sync_string_list(
                native_workspace,
                "members",
                tuple(member.path.as_posix() for member in members),
            )
        cls._sync_uv_candidates(uv, candidate_sources, local_requirements, resolution)
        cls._sync_uv_constraints(uv, resolution)
        cls._sync_uv_environments(uv, resolution)
        u.Cli.toml_remove_key_if_present(uv, "required-version")
        u.Cli.toml_remove_key_if_present(uv, "exclude-dependencies")
        return r[bool].ok(value=True)


__all__: list[str] = ["FlextInfraUtilitiesPyprojectUvSources"]
