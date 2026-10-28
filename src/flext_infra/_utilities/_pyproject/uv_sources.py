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
from flext_infra._utilities import (
    FlextInfraUtilitiesDependencies,
    FlextInfraUtilitiesDependencyRequirements,
)
from flext_infra._utilities._git.requirement_source import (
    FlextInfraUtilitiesGitRequirementSource,
)
from flext_infra._utilities._pyproject.requirements import (
    FlextInfraUtilitiesPyprojectRequirements,
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
    ) -> p.Result[tuple[str, ...]]:
        """Name every requirement declared by direct source reference.

        Returns:
            The canonical distribution names of direct requirement sources.

        """
        lines = cls.document_requirement_lines(document)
        if lines.failure:
            return r[tuple[str, ...]].from_failure(lines)
        return r[tuple[str, ...]].ok(
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
        seen: set[tuple[str, str | None]] = set()
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
    def _own_distribution(document: t.Cli.TomlDocument) -> str | None:
        """Return this document's canonical distribution name.

        Returns:
            The canonical ``[project].name``, or None when undeclared.

        """
        payload = u.Cli.toml_as_mapping(document)
        project = None if payload is None else payload.get(c.Infra.PROJECT)
        name = project.get("name") if isinstance(project, Mapping) else None
        return canonicalize_name(name) if isinstance(name, str) else None

    @classmethod
    def _declared_internal_overrides(
        cls, document: t.Cli.TomlDocument
    ) -> p.Result[t.StrSequence]:
        """Derive internal overrides from this project's own Git URL requirements.

        Every declared internal requirement carrying a direct Git URL (runtime,
        optional or development) becomes one override at exactly that URL, so a
        transitive request for the same distribution resolves to the line this
        project declares. The project itself never overrides itself.

        Returns:
            The derived overrides by distribution, or the conflicting declaration.

        """
        lines = cls.document_requirement_lines(document)
        if lines.failure:
            return r[t.StrSequence].from_failure(lines)
        own = cls._own_distribution(document)
        urls: t.MutableMappingKV[str, str] = {}
        for line in lines.value:
            name = cls._internal_dependency_name(
                line, declared_sources={}, candidate_sources={}
            )
            if name is None or name == own or not cls._declares_direct_source(line):
                continue
            url = Requirement(line).url
            if url is None or not url.startswith(c.Infra.GIT_URL_SCHEME_PREFIX):
                continue
            if urls.setdefault(name, url) != url:
                return r[t.StrSequence].fail(
                    f"internal requirement {name} declares conflicting Git URLs: "
                    f"{urls[name]} and {url}"
                )
        return r[t.StrSequence].ok(
            tuple(f"{name} @ {url}" for name, url in sorted(urls.items()))
        )

    @classmethod
    def internal_reference_migrations(
        cls,
        document: t.Cli.TomlDocument,
        *,
        target_ref: str,
    ) -> p.Result[tuple[m.Infra.GitSourceReferenceMigration, ...]]:
        """Elect one Git-ref migration per internal requirement off the line.

        Every declared internal requirement whose direct Git source names a
        reference other than ``target_ref`` (the declared integration line)
        yields the existing source-reference migration scoped to its own source
        directory and current reference; the manifest keeps the URL, the lock
        alone pins the exact commit.

        Returns:
            The distinct migrations aligning internal references, or the first
            invalid declared source.

        """
        result_type = r[tuple[m.Infra.GitSourceReferenceMigration, ...]]
        lines = cls.document_requirement_lines(document)
        if lines.failure:
            return result_type.from_failure(lines)
        migrations: t.MutableMappingKV[
            tuple[str, str], m.Infra.GitSourceReferenceMigration
        ] = {}
        for line in lines.value:
            name = cls._internal_dependency_name(
                line, declared_sources={}, candidate_sources={}
            )
            if name is None or not cls._declares_direct_source(line):
                continue
            declared = FlextInfraUtilitiesGitRequirementSource.declared_git_source(line)
            if declared.failure:
                return result_type.from_failure(declared)
            url, reference = declared.value
            if not url or reference == target_ref:
                continue
            prefix = f"{url.rpartition('/')[0]}/"
            migrations.setdefault(
                (prefix, reference),
                m.Infra.GitSourceReferenceMigration(
                    url_prefix=prefix,
                    source_ref=reference,
                    target_ref=target_ref,
                ),
            )
        return result_type.ok(tuple(migrations.values()))

    @classmethod
    def _sync_uv_candidates(
        cls,
        uv: t.Cli.TomlTable,
        document: t.Cli.TomlDocument,
        *,
        candidate_sources: t.StrMapping,
        requirements: t.StrSequence,
        resolution: m.Infra.UvResolutionSpec,
    ) -> None:
        """Publish declared, derived internal and candidate overrides once.

        Each internal override also excludes this project from that
        distribution's requirements: the distribution may require this project
        back by its own Git URL, which native uv cannot reconcile with the local
        project in a standalone lock. The scoped exclusion removes only that
        reciprocal requirement and does nothing where it is absent.
        """
        overrides: list[str | m.Infra.UvScopedOverride] = list(
            resolution.override_dependencies
        )
        for name, source in sorted(candidate_sources.items()):
            extras = FlextInfraUtilitiesDependencyRequirements.dependency_extras(
                requirements, name
            )
            overrides.append(f"{name}{extras} @ {source}")
        wire = cls._uv_override_wire(overrides) if overrides else []
        if wire:
            u.Cli.toml_sync_value(uv, "override-dependencies", wire)
        else:
            u.Cli.toml_remove_key_if_present(uv, "override-dependencies")
        own = cls._own_distribution(document)
        internal = sorted({
            name
            for entry in wire
            if isinstance(entry, str)
            and (
                name := cls._internal_dependency_name(
                    entry, declared_sources={}, candidate_sources={}
                )
            )
            is not None
            and name != own
        })
        exclusions: t.JsonValueList = [
            {"package": {"name": name}, "dependencies": [own]}
            for name in internal
            if own is not None
        ]
        if exclusions:
            u.Cli.toml_sync_value(uv, "exclude-dependencies", exclusions)
        else:
            u.Cli.toml_remove_key_if_present(uv, "exclude-dependencies")

    @staticmethod
    def _sync_uv_constraints(
        uv: t.Cli.TomlTable, resolution: m.Infra.UvResolutionSpec
    ) -> None:
        """Publish declared constraints and native linking, without cooldown copies."""
        constraints = tuple(resolution.constraint_dependencies)
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
        # A workspace root lowers its members through native workspace sources;
        # only a project resolving its internal requirements by URL derives them.
        derived = (
            r[t.StrSequence].ok(())
            if workspace.repository.role is c.Infra.MakeProfile.WORKSPACE
            else cls._declared_internal_overrides(document)
        )
        if derived.failure:
            return r[bool].from_failure(derived)
        cls._sync_uv_candidates(
            uv,
            document,
            candidate_sources=candidate_sources,
            requirements=local_requirements,
            resolution=resolution.model_copy(
                update={
                    "override_dependencies": (
                        *resolution.override_dependencies,
                        *derived.value,
                    ),
                },
            ),
        )
        cls._sync_uv_constraints(uv, resolution)
        cls._sync_uv_environments(uv, resolution)
        u.Cli.toml_remove_key_if_present(uv, "required-version")
        return r[bool].ok(value=True)


__all__: list[str] = ["FlextInfraUtilitiesPyprojectUvSources"]
