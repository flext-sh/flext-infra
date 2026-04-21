"""Phase: Consolidate optional-dependencies and Poetry groups into single dev group."""

from __future__ import annotations

from collections.abc import (
    MutableMapping,
    MutableSequence,
)

from tomlkit.items import Table

from flext_infra import c, t, u


class FlextInfraConsolidateGroupsPhase:
    """Consolidate optional-dependencies and Poetry groups into single dev group."""

    def apply(
        self,
        doc: t.Infra.TomlDocument,
        canonical_dev: t.StrSequence,
    ) -> t.StrSequence:
        """Merge all legacy optional groups into canonical ``project.optional-dependencies.dev``."""
        changes: MutableSequence[str] = []
        project = u.Cli.toml_ensure_table(doc, c.Infra.PROJECT)
        optional = u.Cli.toml_ensure_table(project, c.Infra.OPTIONAL_DEPENDENCIES)
        existing = u.Infra.project_dev_groups(doc)
        merged_dev = u.Infra.dedupe_specs([
            *canonical_dev,
            *existing.get(c.Infra.DEV, []),
            *existing.get(c.Infra.DIR_DOCS, []),
            *existing.get(c.Infra.SECURITY, []),
            *existing.get(c.Infra.TEST, []),
            *existing.get(c.Infra.DIR_TYPINGS, []),
        ])
        current_dev = u.Cli.toml_as_string_list(u.Cli.toml_value(optional, c.Infra.DEV))
        if sorted(current_dev) != sorted(merged_dev):
            optional[c.Infra.DEV] = u.Cli.toml_array(sorted(merged_dev))
            changes.append("project.optional-dependencies.dev consolidated")
        for old_key in (
            c.Infra.DOCS,
            c.Infra.SECURITY,
            c.Infra.TEST,
            c.Infra.DIR_TYPINGS,
        ):
            if old_key in optional:
                del optional[old_key]
                changes.append(f"project.optional-dependencies.{old_key} removed")
        tool = u.Cli.toml_ensure_table(doc, c.Infra.TOOL)
        poetry = u.Cli.toml_ensure_table(tool, c.Infra.POETRY)
        poetry_group = u.Cli.toml_ensure_table(poetry, c.Infra.GROUP)
        poetry_dev_table: t.Infra.TomlTable | None = None
        for old_group in (
            c.Infra.DOCS,
            c.Infra.SECURITY,
            c.Infra.TEST,
            c.Infra.DIR_TYPINGS,
        ):
            if old_group not in poetry_group:
                continue
            old_group_table = poetry_group[old_group]
            if not isinstance(old_group_table, Table):
                continue
            old_deps = old_group_table.get(c.Infra.DEPENDENCIES)
            if isinstance(old_deps, Table):
                if poetry_dev_table is None:
                    poetry_dev_table = u.Cli.toml_ensure_table(
                        u.Cli.toml_ensure_table(poetry_group, c.Infra.DEV),
                        c.Infra.DEPENDENCIES,
                    )
                if not isinstance(poetry_dev_table, Table):
                    continue
                current_dev_table: Table = poetry_dev_table
                for dep_name_raw in old_deps:
                    dep_name = dep_name_raw
                    dep_value = old_deps[dep_name_raw]
                    if dep_name not in current_dev_table:
                        current_dev_table[dep_name] = dep_value
            del poetry_group[old_group]
            changes.append(f"tool.poetry.group.{old_group} removed")
        deptry = u.Cli.toml_ensure_table(tool, c.Infra.DEPTRY)
        current_groups = u.Cli.toml_as_string_list(
            u.Cli.toml_value(deptry, "pep621_dev_dependency_groups")
        )
        if current_groups != [c.Infra.DEV]:
            deptry["pep621_dev_dependency_groups"] = u.Cli.toml_array([c.Infra.DEV])
            changes.append("tool.deptry.pep621_dev_dependency_groups set to ['dev']")
        return changes

    def apply_payload(
        self,
        payload: MutableMapping[str, t.Cli.JsonValue],
        canonical_dev: t.StrSequence,
    ) -> t.StrSequence:
        """Merge legacy groups into one canonical dev group in one plain payload."""
        changes: MutableSequence[str] = []
        project = u.Cli.toml_mapping_ensure_table(payload, c.Infra.PROJECT)
        optional = u.Cli.toml_mapping_ensure_table(
            project,
            c.Infra.OPTIONAL_DEPENDENCIES,
        )
        existing = u.Infra.project_dev_groups_from_payload(payload)
        merged_dev = u.Infra.dedupe_specs([
            *canonical_dev,
            *existing.get(c.Infra.DEV, []),
            *existing.get(c.Infra.DIR_DOCS, []),
            *existing.get(c.Infra.SECURITY, []),
            *existing.get(c.Infra.TEST, []),
            *existing.get(c.Infra.DIR_TYPINGS, []),
        ])
        _ = u.Cli.toml_mapping_sync_string_list(
            optional,
            c.Infra.DEV,
            sorted(merged_dev),
            changes,
            "project.optional-dependencies.dev consolidated",
        )
        for old_key in (
            c.Infra.DOCS,
            c.Infra.SECURITY,
            c.Infra.TEST,
            c.Infra.DIR_TYPINGS,
        ):
            _ = u.Cli.toml_mapping_remove_key_if_present(
                optional,
                old_key,
                changes,
                f"project.optional-dependencies.{old_key} removed",
            )
        poetry_group = u.Cli.toml_mapping_path(
            payload,
            (c.Infra.TOOL, c.Infra.POETRY, c.Infra.GROUP),
        )
        poetry_dev_table: MutableMapping[str, t.Cli.JsonValue] | None = None
        for old_group in (
            c.Infra.DOCS,
            c.Infra.SECURITY,
            c.Infra.TEST,
            c.Infra.DIR_TYPINGS,
        ):
            old_group_table = (
                u.Cli.toml_mapping_child(poetry_group, old_group)
                if poetry_group is not None
                else None
            )
            old_deps = (
                u.Cli.toml_mapping_child(old_group_table, c.Infra.DEPENDENCIES)
                if old_group_table is not None
                else None
            )
            if old_deps is not None:
                if poetry_dev_table is None:
                    poetry_dev_table = u.Cli.toml_mapping_ensure_path(
                        payload,
                        (
                            c.Infra.TOOL,
                            c.Infra.POETRY,
                            c.Infra.GROUP,
                            c.Infra.DEV,
                            c.Infra.DEPENDENCIES,
                        ),
                    )
                for dep_name, dep_value in old_deps.items():
                    if dep_name not in poetry_dev_table:
                        poetry_dev_table[dep_name] = dep_value
            if poetry_group is None:
                continue
            _ = u.Cli.toml_mapping_remove_key_if_present(
                poetry_group,
                old_group,
                changes,
                f"tool.poetry.group.{old_group} removed",
            )
        deptry = u.Cli.toml_mapping_ensure_path(
            payload,
            (c.Infra.TOOL, c.Infra.DEPTRY),
        )
        _ = u.Cli.toml_mapping_sync_string_list(
            deptry,
            "pep621_dev_dependency_groups",
            [c.Infra.DEV],
            changes,
            "tool.deptry.pep621_dev_dependency_groups set to ['dev']",
        )
        return changes


__all__: list[str] = ["FlextInfraConsolidateGroupsPhase"]
