"""Preserve live CUSTOM project keys and unmanaged tool tables over renders.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_cli import u

from flext_infra import c, m, p, r, t
from flext_infra._utilities._pyproject.requirements import (
    FlextInfraUtilitiesPyprojectRequirements,
)
from flext_infra._utilities.dependencies import FlextInfraUtilitiesDependencies
from flext_infra._utilities.managed_conflicts import FlextInfraUtilitiesManagedConflicts


class FlextInfraUtilitiesPyprojectOverlay:
    """Merge one rendered pyproject with its live CUSTOM surface."""

    @staticmethod
    def _validated_requirement_lists(
        project: t.JsonMapping,
        live_project: t.JsonMapping,
        key: str,
    ) -> p.Result[t.Pair[t.StrSequence, t.StrSequence]]:
        """Validate generated and CUSTOM runtime dependency lists once.

        Returns:
            The resulting ``(required, custom)`` requirement lists.

        """
        validated_required: p.Result[t.StrSequence] = u.validate_value(
            t.Infra.STR_SEQ_ADAPTER,
            project.get(key, []),
            strict=True,
        )
        if validated_required.failure:
            return r[t.Pair[t.StrSequence, t.StrSequence]].fail_op(
                "validate runtime dependencies",
                validated_required.error,
            )
        validated_custom: p.Result[t.StrSequence] = u.validate_value(
            t.Infra.STR_SEQ_ADAPTER,
            live_project.get(key, []),
            strict=True,
        )
        if validated_custom.failure:
            return r[t.Pair[t.StrSequence, t.StrSequence]].fail_op(
                "validate runtime dependencies",
                validated_custom.error,
            )
        return r[t.Pair[t.StrSequence, t.StrSequence]].ok(
            (validated_required.value, validated_custom.value),
        )

    @staticmethod
    def _merged_requirements(
        required: t.StrSequence,
        custom: t.StrSequence,
    ) -> list[t.JsonValue]:
        """Merge CUSTOM runtime requirements under the generated ownership order.

        Profiles own same-name requirements. CUSTOM requirements retain full
        specs, including distinct markers for one name. Conformance uses this
        same order: overlay must not move generated requirements ahead of
        preserved custom ones.

        Returns:
            The resulting ``list[t.JsonValue]``.

        """
        owned_names = {
            FlextInfraUtilitiesDependencies.dep_name(item) for item in required
        }
        # The list display widens the sorted ``str`` items to the JSON value
        # list the caller stores, in the single pass that materializes them.
        return [
            *sorted(
                dict.fromkeys((
                    *required,
                    *(
                        item
                        for item in custom
                        if FlextInfraUtilitiesDependencies.dep_name(item)
                        not in owned_names
                    ),
                )),
                key=FlextInfraUtilitiesPyprojectRequirements.dependency_order_key,
            ),
        ]

    @classmethod
    def _overlay_project_surface(
        cls,
        merged: t.MutableJsonMapping,
        live_payload: t.JsonMapping | None,
        project_keys: t.StrSequence,
    ) -> p.Result[t.JsonDict]:
        """Overlay every declared CUSTOM project key onto the merged document.

        Existing metadata owns omitted CUSTOM keys as well as provided values;
        only a new project receives those scaffold defaults.

        Returns:
            The resulting ``p.Result[t.JsonDict]``.

        """
        rendered_project = u.Cli.toml_mapping_child(merged, c.Infra.PROJECT) or {}
        live_project = (
            u.Cli.toml_mapping_child(live_payload, c.Infra.PROJECT)
            if live_payload is not None
            else None
        )
        if live_project is None:
            return r[t.JsonDict].ok(dict(rendered_project))
        project = dict(live_project)
        project.update(
            (key, value)
            for key, value in rendered_project.items()
            if key not in project_keys
        )
        if c.Infra.DEPENDENCIES in project_keys:
            validated = cls._validated_requirement_lists(
                rendered_project,
                live_project,
                c.Infra.DEPENDENCIES,
            )
            if validated.failure:
                return r[t.JsonDict].from_failure(validated)
            required, custom = validated.value
            project[c.Infra.DEPENDENCIES] = cls._merged_requirements(required, custom)
        return r[t.JsonDict].ok(project)

    @staticmethod
    def sync_member_dev_provenance(
        document: t.Cli.TomlDocument,
        *,
        custom: t.SequenceOf[str | m.Infra.DependencyGroupInclude],
        group: str = str(c.Infra.DEV),
    ) -> None:
        """Tag generated additions in the existing dev group, not another registry."""
        groups = u.Cli.toml_ensure_table(document, c.Infra.DEPENDENCY_GROUPS)
        group = FlextInfraUtilitiesPyprojectRequirements.dependency_group_name(
            groups,
            group,
        )
        values = FlextInfraUtilitiesPyprojectRequirements.read_dependency_group(
            groups,
            group,
        )
        if not values:
            return
        custom_values = frozenset(custom)
        generated = u.Cli.toml_array(()).multiline(multiline=False)
        for value in values:
            generated.add_line(
                (
                    value
                    if isinstance(value, str)
                    else value.model_dump(mode="json", by_alias=True)
                ),
                comment=(
                    None
                    if not isinstance(value, str) or value in custom_values
                    else c.Infra.MEMBER_DEV_PROVENANCE
                ),
            )
        generated.add_line(indent="")
        groups[group] = generated

    @staticmethod
    def _overlay_dev_group(
        merged: t.MutableJsonMapping,
        live_payload: t.JsonMapping,
        live: str | None,
    ) -> p.Result[bool]:
        """Preserve CUSTOM environment additions before conformance floors.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        rendered_groups = dict(
            u.Cli.toml_mapping_child(merged, c.Infra.DEPENDENCY_GROUPS) or {},
        )
        live_groups = (
            u.Cli.toml_mapping_child(live_payload, c.Infra.DEPENDENCY_GROUPS) or {}
        )
        groups = dict(rendered_groups)
        for name, entries in live_groups.items():
            authored_name = (
                FlextInfraUtilitiesPyprojectRequirements.dependency_group_name(
                    tuple(live_groups),
                    name,
                )
            )
            previous = FlextInfraUtilitiesPyprojectRequirements.dependency_group_name(
                tuple(groups),
                authored_name,
            )
            if previous != authored_name:
                groups.pop(previous, None)
            groups[authored_name] = entries
        for group in (str(c.Infra.DEV), c.Infra.DependencyGroup.CODEGEN):
            selected = FlextInfraUtilitiesPyprojectRequirements.dependency_group_name(
                tuple(groups),
                str(group),
            )
            custom = FlextInfraUtilitiesPyprojectRequirements.custom_dev_additions(
                live_payload,
                live,
                group=group,
            )
            if custom.failure:
                return r[bool].from_failure(custom)
            if group == c.Infra.DependencyGroup.CODEGEN:
                required = u.validate_value(
                    m.Infra.DependencyGroupEntries,
                    rendered_groups.get(
                        FlextInfraUtilitiesPyprojectRequirements.dependency_group_name(
                            tuple(rendered_groups),
                            str(group),
                        ),
                        (),
                    ),
                    strict=True,
                )
                if required.failure:
                    return r[bool].from_failure(required)
                requirements = FlextInfraUtilitiesPyprojectRequirements
                merged_entries = requirements.merge_dependency_group_entries(
                    required.value.root,
                    custom.value,
                )
                groups[selected] = (
                    FlextInfraUtilitiesPyprojectRequirements.dependency_group_wire(
                        merged_entries,
                    )
                )
            else:
                groups[selected] = (
                    FlextInfraUtilitiesPyprojectRequirements.dependency_group_wire(
                        custom.value,
                    )
                )
        validated = u.validate_value(
            m.Infra.DependencyGroupDeclarations,
            {"dependency-groups": groups},
        )
        if validated.failure:
            return r[bool].from_failure(validated)
        merged[c.Infra.DEPENDENCY_GROUPS] = groups
        return r[bool].ok(value=True)

    @classmethod
    def _overlay_tool_subtree(
        cls,
        rendered: t.JsonMapping,
        live: t.JsonMapping,
        prefix: t.VariadicTuple[str],
        managed: t.SequenceOf[t.VariadicTuple[str]],
    ) -> t.JsonDict:
        """Merge CUSTOM siblings of one tool subtree over its rendered form.

        An ancestor of an owned table exists only when the render declares it
        or a CUSTOM descendant survives; an empty ancestor would pin a table
        position the generator does not own and break the fixed point.

        Returns:
            The merged subtree.

        """
        merged: t.JsonDict = dict(rendered)
        for key, value in live.items():
            path = (*prefix, key)
            if any(path[: len(owned)] == owned for owned in managed):
                continue
            if not any(owned[: len(path)] == path for owned in managed):
                merged[key] = value
                continue
            rendered_child = u.Cli.toml_mapping_child(rendered, key)
            child = cls._overlay_tool_subtree(
                rendered_child or {},
                u.Cli.toml_mapping_child(live, key) or {},
                path,
                managed,
            )
            if child or rendered_child is not None:
                merged[key] = child
        return merged

    @classmethod
    def _overlay_tool_tables(
        cls,
        merged: t.MutableJsonMapping,
        live_payload: t.JsonMapping,
        tool_tables: t.StrSequence,
    ) -> None:
        """Preserve CUSTOM siblings without merging into an owned table subtree."""
        rendered_tool = u.Cli.toml_mapping_child(merged, c.Infra.TOOL)
        tool = cls._overlay_tool_subtree(
            rendered_tool or {},
            u.Cli.toml_mapping_child(live_payload, c.Infra.TOOL) or {},
            (),
            tuple(tuple(table.split(".")) for table in tool_tables),
        )
        if tool or rendered_tool is not None:
            merged[c.Infra.TOOL] = tool

    @classmethod
    def overlay_preserved(
        cls,
        rendered: str,
        live: str | None,
        *,
        preserve_project_keys: t.StrSequence | None = None,
        managed_tool_tables: t.StrSequence | None = None,
    ) -> p.Result[str]:
        """Keep live CUSTOM project keys and unmanaged tool tables.

        Returns:
            The resulting ``p.Result[str]``.

        """
        spec = FlextInfraUtilitiesManagedConflicts.pyproject_managed_file()
        if spec.failure:
            return r[str].from_failure(spec)
        project_keys = (
            spec.value.preserve_project_keys
            if preserve_project_keys is None
            else preserve_project_keys
        )
        tool_tables = (
            spec.value.managed_tool_tables
            if managed_tool_tables is None
            else managed_tool_tables
        )
        rendered_payload = u.Cli.toml_mapping_from_text_result(rendered)
        # An absent live file takes the same canonicalization path as a present
        # one: the projection is the parse-merge-dump form, so first publication
        # and every later conform produce byte-identical output (fixed point).
        empty_payload: t.JsonMapping = {}
        live_payload = (
            u.Cli.toml_mapping_from_text_result(live)
            if live is not None
            else r[t.JsonMapping].ok(empty_payload)
        )
        if rendered_payload.failure:
            return r[str].fail(
                f"rendered pyproject is not valid TOML: {rendered_payload.error}",
                error_code=rendered_payload.error_code,
                error_data=rendered_payload.error_data,
                exception=rendered_payload.exception,
            )
        if live_payload.failure:
            return r[str].fail(
                f"live pyproject is not valid TOML: {live_payload.error}",
                error_code=live_payload.error_code,
                error_data=live_payload.error_data,
                exception=live_payload.exception,
            )
        merged = dict(rendered_payload.value)
        project = cls._overlay_project_surface(
            merged,
            live_payload.value if live is not None else None,
            project_keys,
        )
        if project.failure:
            return r[str].from_failure(project)
        merged[c.Infra.PROJECT] = project.value
        dev = cls._overlay_dev_group(merged, live_payload.value, live)
        if dev.failure:
            return r[str].from_failure(dev)
        cls._overlay_tool_tables(merged, live_payload.value, tool_tables)
        return r[str].ok(u.Cli.toml_dumps(u.Cli.toml_document_from_mapping(merged)))


__all__: list[str] = ["FlextInfraUtilitiesPyprojectOverlay"]
