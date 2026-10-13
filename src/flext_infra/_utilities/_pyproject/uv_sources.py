"""Conform-owned ``[tool.uv]`` rendering for one pyproject document.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping

from flext_cli import u

from flext_infra import c, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesDependencies,
    FlextInfraUtilitiesDependencyRequirements,
)
from flext_infra._utilities._pyproject import (
    FlextInfraUtilitiesPyprojectRequirements,
    FlextInfraUtilitiesPyprojectSession,
)


class FlextInfraUtilitiesPyprojectUvSources(
    FlextInfraUtilitiesPyprojectRequirements,
    FlextInfraUtilitiesPyprojectSession,
):
    """Render the conform-owned ``[tool.uv]`` keys of one pyproject document."""

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

        Declared candidate policy and workspace topology own overrides: uv
        already unifies a repository's own distribution to its editable root
        (the committed pre-override lock carried one ``flext-infra =
        editable "."`` entry with the full dev group), while a rendered
        self-override forces the workspace-source shape that hard-fails
        standalone ``uv lock`` without a sources entry and drops the dev
        group with one. Standalone repositories must lock exactly like
        fleet members.
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
            if workspace.repository.role == c.Infra.MakeProfile.WORKSPACE
            else ()
        )
        root_names = (
            (workspace.repository.distribution,) if workspace.repository.package else ()
        )
        local_names = (
            *root_names,
            *(member.distribution for member in members),
        )
        conflicting = set(local_names) & candidate_sources.keys()
        if conflicting:
            return r[bool].fail(
                "candidate source overrides local members: "
                + ", ".join(sorted(conflicting)),
            )
        # Source replacement must not discard declared version/marker bounds.
        constraints = tuple(
            sorted({
                *resolution.constraint_dependencies,
                *(
                    FlextInfraUtilitiesDependencies.dependency_constraint(
                        line,
                        replace_source=True,
                    )
                    for line in local_requirements
                    if FlextInfraUtilitiesDependencies.dep_name(line) in local_names
                ),
            }),
        )
        # Erase transitive direct Git origins so the topology's local sources win.
        # Never override the root itself: that drops its native development group.
        cls._sync_uv_candidates(
            uv,
            candidate_sources,
            local_requirements,
            resolution.model_copy(
                update={
                    "override_dependencies": tuple(
                        dict.fromkeys((
                            *resolution.override_dependencies,
                            *(member.distribution for member in members),
                        ))
                    ),
                },
            ),
        )
        u.Cli.toml_remove_key_if_present(uv, "required-version")
        cls._sync_uv_constraints(
            uv,
            resolution.model_copy(update={"constraint_dependencies": constraints}),
        )
        cls._sync_uv_environments(uv, resolution)
        u.Cli.toml_remove_key_if_present(uv, "exclude-dependencies")
        cls._sync_member_sources(uv, members)
        return r[bool].ok(value=True)

    @staticmethod
    def _sync_member_sources(
        uv: t.Cli.TomlTable,
        members: t.SequenceOf[p.Infra.RepositoryRef],
    ) -> None:
        """Render declared member paths without changing their editable policy.

        The native TOML mapping validator propagates malformed source-table input.
        """
        u.Cli.toml_remove_key_if_present(uv, "workspace")
        sources = u.Cli.toml_table_child(uv, "sources")
        if sources is None:
            sources = u.Cli.toml_ensure_table(uv, "sources")
        wanted = {member.distribution for member in members}
        source_names = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
            u.Cli.toml_unwrap_item(sources),
        )
        for source_name in source_names:
            entry = u.Cli.toml_table_child(sources, source_name)
            if source_name not in wanted and (
                entry is not None
                and any(
                    u.Cli.toml_value(entry, key) is not None
                    for key in ("workspace", "path")
                )
            ):
                u.Cli.toml_remove_key_if_present(sources, source_name)
        for member in members:
            u.Cli.toml_sync_value(
                sources,
                member.distribution,
                {"path": member.path.as_posix(), "editable": member.editable},
            )
        if not sources:
            u.Cli.toml_remove_key_if_present(uv, "sources")


__all__: list[str] = ["FlextInfraUtilitiesPyprojectUvSources"]
