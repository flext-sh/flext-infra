"""Release registry metadata: pinned requirements and the sdist boundary.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import PurePosixPath

from flext_infra import c, m, p, r, t, u
from flext_infra.release import FlextInfraReleaseReleaseSource


class FlextInfraReleaseReleaseMetadata(FlextInfraReleaseReleaseSource):
    """Render the pyproject a public registry accepts from the committed one.

    ``versions`` maps every internal distribution the build can see to the
    version its own repository declares; internal requirements are pinned to
    those versions, never to this project's version.
    """

    @classmethod
    def _release_requirements(
        cls,
        container: t.Cli.TomlDocument | t.Cli.TomlTable,
        key: str,
        versions: Mapping[str, str],
        *,
        dependency_group: bool = False,
    ) -> p.Result[bool]:
        """Pin every internal requirement of one TOML array; others pass verbatim.

        A dependency this build cannot see is not publishable: a guessed
        range would be a silent contract.

        Returns:
            Whether a rendered requirement retains a direct reference.

        """
        raw = u.Cli.toml_value(container, key)
        if raw is None:
            return r[bool].ok(value=False)
        entries = cls._release_requirement_entries(
            raw,
            dependency_group=dependency_group,
        )
        if entries.failure:
            return r[bool].from_failure(entries)
        rendered: list[str | m.Infra.DependencyGroupInclude] = []
        has_direct_references = False
        for requirement in entries.value:
            if not isinstance(requirement, str):
                rendered.append(requirement)
                continue
            pinned = u.Infra.release_pinned_requirement(requirement, versions)
            if pinned.failure:
                return r[bool].from_failure(pinned)
            text, has_direct_url = pinned.value
            rendered.append(text)
            has_direct_references |= has_direct_url
        u.Cli.toml_sync_value(container, key, u.Infra.dependency_group_wire(rendered))
        return r[bool].ok(has_direct_references)

    @classmethod
    def _release_requirement_entries(
        cls,
        raw: t.JsonValue,
        *,
        dependency_group: bool,
    ) -> p.Result[Sequence[str | m.Infra.DependencyGroupInclude]]:
        """Parse one TOML requirement array into its declared entries.

        Args:
            raw: The unwrapped TOML array value of the requirement field.
            dependency_group: Whether the array follows the PEP 735 schema.

        Returns:
            The declared requirement entries, or the parse failure.

        """
        result_type = r[Sequence[str | m.Infra.DependencyGroupInclude]]
        if dependency_group:
            parsed_group = u.validate_value(
                m.Infra.DependencyGroupEntries,
                u.Cli.toml_unwrap_item(raw),
            )
            if parsed_group.failure:
                return result_type.from_failure(parsed_group)
            return result_type.ok(parsed_group.value.root)
        strings = u.validate_value(
            t.Infra.STR_SEQ_ADAPTER,
            u.Cli.toml_unwrap_item(raw),
            strict=True,
        )
        if strings.failure:
            return result_type.from_failure(strings)
        return result_type.ok(strings.value)

    @classmethod
    def _release_pyproject(
        cls,
        source: str,
        version: str,
        versions: Mapping[str, str],
    ) -> p.Result[str]:
        """Render a pyproject a public registry accepts: pinned, sourceless, bounded.

        Returns:
            The resulting ``p.Result[str]``.

        """
        document = u.Cli.toml_parse_text(source)
        project = (
            u.Cli.toml_table_child(document, c.Infra.PROJECT)
            if document is not None
            else None
        )
        if document is None or project is None:
            return r[str].fail(
                "release pyproject must be valid TOML defining [project]",
            )
        groups = u.Cli.toml_table_child(document, c.Infra.DEPENDENCY_GROUPS)
        pinned_fields = cls._pin_release_groups(
            document, project, groups, version, versions
        )
        if pinned_fields.failure:
            return r[str].from_failure(pinned_fields)
        tool = u.Cli.toml_table_child(document, c.Infra.TOOL)
        hatch = u.Cli.toml_table_child(tool, "hatch") if tool is not None else None
        if tool is None or hatch is None:
            return r[str].fail("release pyproject must define [tool.hatch]")
        released = cls._release_hatch(
            tool, hatch, has_direct_references=pinned_fields.value
        )
        if released.failure:
            return r[str].from_failure(released)
        rendered = u.Cli.toml_dumps(document)
        if u.Cli.toml_parse_text(rendered) is None:
            return r[str].fail("release pyproject rendering produced invalid TOML")
        return r[str].ok(rendered)

    @classmethod
    def _pin_release_groups(
        cls,
        document: t.Cli.TomlDocument,
        project: t.Cli.TomlTable,
        groups: t.Cli.TomlTable | None,
        version: str,
        versions: Mapping[str, str],
    ) -> p.Result[bool]:
        """Validate declared groups and pin every release requirement field.

        Args:
            document: The parsed release pyproject document.
            project: The document's project table receiving the version.
            groups: The document's dependency-groups table, or ``None``.
            version: The release version stamped into the project table.
            versions: Internal distribution versions declared by their repos.

        Returns:
            Whether a rendered requirement retains a direct reference.

        """
        validated_groups = u.validate_value(
            m.Infra.DependencyGroupDeclarations,
            {
                "dependency-groups": (
                    {} if groups is None else u.Cli.toml_unwrap_item(groups)
                ),
            },
        )
        if validated_groups.failure:
            return r[bool].from_failure(validated_groups)
        project[c.Infra.VERSION] = version
        fields = (
            (project, c.Infra.DEPENDENCIES),
            *u.Infra.requirement_group_fields(document, project),
        )
        has_direct_references = False
        for container, key in fields:
            pinned = cls._release_requirements(
                container,
                key,
                versions,
                dependency_group=container is groups,
            )
            if pinned.failure:
                return r[bool].from_failure(pinned)
            has_direct_references |= pinned.value
        return r[bool].ok(has_direct_references)

    @classmethod
    def _release_hatch(
        cls,
        tool: t.Cli.TomlTable,
        hatch: t.Cli.TomlTable,
        *,
        has_direct_references: bool,
    ) -> p.Result[bool]:
        """Bound the sdist targets and sync Hatch metadata for publication.

        Args:
            tool: The release document's tool table.
            hatch: The tool table's hatch table.
            has_direct_references: Whether a rendered requirement retains one.

        Returns:
            Whether the bounded Hatch targets rendered successfully.

        """
        u.Cli.toml_remove_key_if_present(tool, "uv")
        bounded = cls._sdist_boundary(hatch)
        if bounded.failure:
            return r[bool].from_failure(bounded)
        metadata = u.Cli.toml_table_child(hatch, "metadata")
        if metadata is not None:
            # Direct references survive only when a rendered requirement still
            # carries one: the flag is deduced, never configured.
            if has_direct_references:
                metadata["allow-direct-references"] = True
            else:
                u.Cli.toml_remove_key_if_present(metadata, "allow-direct-references")
            if not metadata:
                u.Cli.toml_remove_key_if_present(hatch, "metadata")
        return r[bool].ok(value=True)

    @classmethod
    def _sdist_boundary(cls, hatch: t.Cli.TomlTable) -> p.Result[Sequence[str]]:
        """Verify matching, bounded source selection for both archive targets.

        Returns:
            The resulting ``p.Result[Sequence[str]]``.

        """
        tables = cls._archive_targets(hatch)
        if tables.failure:
            return r[Sequence[str]].from_failure(tables)
        _build, wheel, sdist = tables.value
        includes = cls._matching_includes(wheel, sdist)
        if includes.failure:
            return r[Sequence[str]].from_failure(includes)
        sources = cls._forced_sources(wheel, sdist)
        if sources.failure:
            return r[Sequence[str]].from_failure(sources)
        policy = cls._target_policy_verdicts(
            wheel,
            sdist,
            includes.value,
            sources.value,
        )
        if policy.failure:
            return r[Sequence[str]].from_failure(policy)
        bounded = cls._bounded_sources(includes.value, sources.value)
        if bounded.failure:
            return r[Sequence[str]].from_failure(bounded)
        return r[Sequence[str]].ok(bounded.value)

    @staticmethod
    def _archive_targets(
        hatch: t.Cli.TomlTable,
    ) -> p.Result[tuple[t.Cli.TomlTable | None, t.Cli.TomlTable, t.Cli.TomlTable]]:
        """Navigate to the declared Hatch build targets.

        Returns:
            The resulting ``(build, wheel, sdist)`` archive target tables.

        """
        result_type = r[tuple[t.Cli.TomlTable | None, t.Cli.TomlTable, t.Cli.TomlTable]]
        build = u.Cli.toml_table_child(hatch, "build")
        targets = (
            u.Cli.toml_table_child(build, "targets") if build is not None else None
        )
        wheel = (
            u.Cli.toml_table_child(targets, "wheel") if targets is not None else None
        )
        sdist = (
            u.Cli.toml_table_child(targets, "sdist") if targets is not None else None
        )
        if targets is None or wheel is None or sdist is None:
            return result_type.fail(
                "release pyproject must define Hatch wheel and sdist targets",
            )
        if build is not None and any(
            key in build for key in ("only-include", "packages", "exclude")
        ):
            return result_type.fail(
                "Hatch build must use target source patterns without exclusions",
            )
        return result_type.ok((build, wheel, sdist))

    @staticmethod
    def _matching_includes(
        wheel: t.Cli.TomlTable,
        sdist: t.Cli.TomlTable,
    ) -> p.Result[Sequence[str]]:
        """Validate and match the wheel and sdist source patterns.

        Returns:
            The resulting wheel source patterns.

        """
        wheel_includes: p.Result[Sequence[str]] = u.validate_value(
            t.Infra.STR_SEQ_ADAPTER,
            u.Cli.json_as_sequence(u.Cli.toml_value(wheel, "include")),
            strict=True,
        )
        if wheel_includes.failure:
            return r[Sequence[str]].fail_op(
                "validate Hatch wheel include",
                wheel_includes.error,
            )
        sdist_includes: p.Result[Sequence[str]] = u.validate_value(
            t.Infra.STR_SEQ_ADAPTER,
            u.Cli.json_as_sequence(u.Cli.toml_value(sdist, "include")),
            strict=True,
        )
        if sdist_includes.failure:
            return r[Sequence[str]].fail_op(
                "validate Hatch sdist include",
                sdist_includes.error,
            )
        if not wheel_includes.value or set(wheel_includes.value) != set(
            sdist_includes.value,
        ):
            return r[Sequence[str]].fail(
                "Hatch wheel and sdist source patterns must match",
            )
        return r[Sequence[str]].ok(wheel_includes.value)

    @staticmethod
    def _forced_sources(
        wheel: t.Cli.TomlTable,
        sdist: t.Cli.TomlTable,
    ) -> p.Result[Sequence[str]]:
        """Prove the sdist retains every forced and extra-metadata wheel source.

        A wheel built from the sdist reads both tables' sources from the sdist
        tree, so each one must ride in it under its own path.

        Returns:
            The resulting forced and extra-metadata wheel source keys.

        """
        sdist_forced = u.Cli.toml_table_child(sdist, "force-include")
        sources = tuple(
            str(source)
            for key in ("force-include", "extra-metadata")
            if (table := u.Cli.toml_table_child(wheel, key)) is not None
            for source in table
        )
        retained: Mapping[str, str] = {}
        if sdist_forced is not None:
            parsed: p.Result[Mapping[str, str]] = u.validate_value(
                t.Infra.STR_MAPPING_ADAPTER,
                u.Cli.toml_value(sdist, "force-include"),
                strict=True,
            )
            if parsed.failure:
                return r[Sequence[str]].from_failure(parsed)
            retained = parsed.value
        if retained != {source: source for source in sources}:
            return r[Sequence[str]].fail(
                "Hatch sdist must retain every forced and extra-metadata wheel source",
            )
        return r[Sequence[str]].ok(sources)

    @classmethod
    def _target_policy_verdicts(
        cls,
        wheel: t.Cli.TomlTable,
        sdist: t.Cli.TomlTable,
        wheel_includes: Sequence[str],
        sources: Sequence[str],
    ) -> p.Result[bool]:
        """Enforce the bounded source patterns and exclusion policy of both targets.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        for target in (wheel, sdist):
            if any(key in target for key in ("only-include", "packages")):
                return r[bool].fail(
                    "Hatch targets must use bounded source patterns",
                )
        for pattern in wheel_includes:
            if not pattern.startswith("/") or not pattern.endswith("/**"):
                return r[bool].fail(
                    f"Hatch source pattern is not a directory: {pattern}",
                )
        for source in sources:
            if PurePosixPath(source).is_absolute():
                return r[bool].fail(
                    f"Hatch source path is outside the release boundary: {source}",
                )
        wheel_excludes = u.Cli.json_as_sequence(u.Cli.toml_value(wheel, "exclude"))
        sdist_excludes = u.Cli.json_as_sequence(u.Cli.toml_value(sdist, "exclude"))
        if wheel_excludes != sdist_excludes:
            return r[bool].fail("Hatch wheel and sdist exclusions must match")
        for excluded in wheel_excludes:
            error = cls._excluded_error(excluded, wheel_includes)
            if error:
                return r[bool].fail(error)
        return r[bool].ok(value=True)

    @classmethod
    def _excluded_error(
        cls,
        excluded: t.JsonValue,
        wheel_includes: Sequence[str],
    ) -> str:
        """Return why one exclusion leaves the declared data, or an empty string.

        Returns:
            Why one exclusion leaves the declared data, or an empty string.

        """
        if not isinstance(excluded, str) or not excluded.startswith("/"):
            return f"invalid Hatch exclusion: {excluded}"
        path = PurePosixPath(excluded.removeprefix("/"))
        if (
            ".." in path.parts
            or path.as_posix() != excluded.removeprefix("/")
            or len(path.parts) <= 1
            or path.parts[0] == c.Infra.DEFAULT_SRC_DIR
            or not any(
                excluded.startswith(pattern.removesuffix("**"))
                for pattern in wheel_includes
            )
        ):
            return f"Hatch exclusion is outside declared data: {excluded}"
        return ""

    @classmethod
    def _bounded_sources(
        cls,
        wheel_includes: Sequence[str],
        sources: Sequence[str],
    ) -> p.Result[Sequence[str]]:
        """Prove every declared source stays inside the release boundary.

        Returns:
            The resulting sorted release source roots.

        """
        roots = tuple(
            sorted({
                PurePosixPath(
                    pattern.removeprefix("/").removesuffix("/**"),
                ).parts[0]
                for pattern in wheel_includes
                if pattern.startswith("/") and pattern.endswith("/**")
            }),
        )
        for source in (*wheel_includes, *sources):
            error = cls._bounded_source_error(source, wheel_includes, roots)
            if error:
                return r[Sequence[str]].fail(error)
        return r[Sequence[str]].ok(roots)

    @classmethod
    def _bounded_source_error(
        cls,
        source: str,
        wheel_includes: Sequence[str],
        roots: Sequence[str],
    ) -> str:
        """Return why one source leaves the release boundary, or an empty string.

        Returns:
            Why one source leaves the release boundary, or an empty string.

        """
        relative = (
            source.removeprefix("/").removesuffix("/**")
            if source in wheel_includes
            else source
        )
        path = PurePosixPath(relative)
        safe_path = (
            bool(relative)
            and not path.is_absolute()
            and ".." not in path.parts
            and path.as_posix() == relative
        )
        if not safe_path or (
            cls._path_error(relative, "release source", root_index=0)
            or not cls._sdist_member_allowed(("release-root", *path.parts), roots)
        ):
            return f"Hatch source path is outside the release boundary: {source}"
        return ""


__all__: list[str] = ["FlextInfraReleaseReleaseMetadata"]
