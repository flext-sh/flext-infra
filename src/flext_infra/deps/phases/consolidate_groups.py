"""Phase: Consolidate optional-dependencies and Poetry groups into single dev group."""

from __future__ import annotations

from collections.abc import MutableSequence

import tomlkit
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
        project: t.Infra.TomlItem | t.Infra.TomlContainer | None = None
        if c.Infra.PROJECT in doc:
            project = doc[c.Infra.PROJECT]
        if not isinstance(project, Table):
            project = tomlkit.table()
            doc[c.Infra.PROJECT] = project

        optional: t.Infra.TomlItem | t.Infra.TomlContainer | None = None
        if c.Infra.OPTIONAL_DEPENDENCIES in project:
            optional = project[c.Infra.OPTIONAL_DEPENDENCIES]
        if not isinstance(optional, Table):
            optional = tomlkit.table()
            project[c.Infra.OPTIONAL_DEPENDENCIES] = optional
        existing = u.Infra.project_dev_groups(doc)
        merged_dev = u.Infra.dedupe_specs([
            *canonical_dev,
            *existing.get(c.Infra.DEV, []),
            *existing.get(c.Infra.DIR_DOCS, []),
            *existing.get(c.Infra.SECURITY, []),
            *existing.get(c.Infra.TEST, []),
            *existing.get(c.Infra.DIR_TYPINGS, []),
        ])
        current_dev = u.Cli.toml_as_string_list(u.Infra.get(optional, c.Infra.DEV))
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
        tool: t.Infra.TomlItem | t.Infra.TomlContainer | None = None
        if c.Infra.TOOL in doc:
            tool = doc[c.Infra.TOOL]
        if not isinstance(tool, Table):
            tool = tomlkit.table()
            doc[c.Infra.TOOL] = tool
        poetry = u.Cli.toml_ensure_table(tool, c.Infra.POETRY)
        poetry_group_raw: t.Infra.TomlItem | t.Infra.TomlContainer | None = None
        if c.Infra.GROUP in poetry:
            poetry_group_raw = poetry[c.Infra.GROUP]
        poetry_group = poetry_group_raw if isinstance(poetry_group_raw, Table) else None
        poetry_dev_table: t.Infra.TomlTable | None = None
        for old_group in (
            c.Infra.DOCS,
            c.Infra.SECURITY,
            c.Infra.TEST,
            c.Infra.DIR_TYPINGS,
        ):
            if poetry_group is None:
                continue
            old_group_table: t.Infra.TomlItem | t.Infra.TomlContainer | None = None
            if old_group in poetry_group:
                old_group_table = poetry_group[old_group]
            if not isinstance(old_group_table, Table):
                continue
            old_deps: t.Infra.TomlItem | t.Infra.TomlContainer | None = None
            if c.Infra.DEPENDENCIES in old_group_table:
                old_deps = old_group_table[c.Infra.DEPENDENCIES]
            if isinstance(old_deps, Table):
                if poetry_dev_table is None:
                    poetry_dev_table = u.Cli.toml_ensure_table(
                        u.Cli.toml_ensure_table(poetry_group, c.Infra.DEV),
                        c.Infra.DEPENDENCIES,
                    )
                for dep_name_raw in old_deps:
                    dep_name = dep_name_raw
                    dep_value = old_deps[dep_name_raw]
                    if dep_name not in poetry_dev_table:
                        poetry_dev_table[dep_name] = dep_value
            del poetry_group[old_group]
            changes.append(f"tool.poetry.group.{old_group} removed")
        deptry = u.Cli.toml_ensure_table(tool, c.Infra.DEPTRY)
        current_groups = u.Cli.toml_as_string_list(
            u.Infra.get(deptry, "pep621_dev_dependency_groups")
        )
        if current_groups != [c.Infra.DEV]:
            deptry["pep621_dev_dependency_groups"] = u.Cli.toml_array([c.Infra.DEV])
            changes.append("tool.deptry.pep621_dev_dependency_groups set to ['dev']")
        return changes


__all__ = ["FlextInfraConsolidateGroupsPhase"]
