"""TOML rewrite operations for dependency path synchronization.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence
from pathlib import Path

from tomlkit.items import InlineTable, Table as TomlTable

from flext_cli import u
from flext_infra import FlextInfraUtilitiesTomlParse, c, r, t


class FlextInfraDependencyPathSyncRewrite(FlextInfraUtilitiesTomlParse):
    """TOML rewrite operations for PEP 621, uv sources/workspace, and Poetry."""

    def _rewrite_pep621(
        self,
        doc: t.Cli.TomlDocument,
        *,
        internal_names: t.Infra.StrSet,
    ) -> t.Infra.Pair[t.StrSequence, t.Infra.StrSet]:
        project_section = u.Cli.toml_get_table(doc, c.Infra.PROJECT)
        if project_section is None:
            return ([], set())
        deps: t.StrSequence = u.Cli.toml_as_string_list(
            u.Cli.toml_get_item(project_section, c.Infra.DEPENDENCIES)
        )
        if not deps:
            return ([], set())
        changes: MutableSequence[str] = []
        updated_deps: MutableSequence[str] = []
        internal_deps: t.Infra.StrSet = set()
        for item_raw in deps:
            item = item_raw
            marker = ""
            requirement_part = item
            if ";" in item:
                requirement_part, marker_part = item.split(";", 1)
                marker = f" ;{marker_part}"
            dep_name = type(self).dep_name(requirement_part)
            if not dep_name or dep_name not in internal_names:
                updated_deps.append(item)
                continue
            internal_deps.add(dep_name)
            new_entry = f"{dep_name}{marker}" if " @ " in requirement_part else item
            if item != new_entry:
                changes.append(f"  PEP621: {item} -> {new_entry}")
                updated_deps.append(new_entry)
            else:
                updated_deps.append(item)
        if changes:
            project_section[c.Infra.DEPENDENCIES] = updated_deps
        return (changes, internal_deps)

    def _rewrite_uv_sources(
        self,
        doc: t.Cli.TomlDocument,
        *,
        is_root: bool,
        mode: str,
        internal_names: t.Infra.StrSet,
        internal_deps: t.Infra.StrSet,
        workspace_members: t.StrSequence,
    ) -> t.StrSequence:
        expected_names: t.Infra.StrSet = (
            set(workspace_members)
            if is_root and mode == c.Infra.ReportKeys.WORKSPACE
            else set(internal_deps)
        )
        if not expected_names:
            return []
        changes: MutableSequence[str] = []
        tool_section = u.Cli.toml_ensure_table(doc, c.Infra.TOOL)
        uv_section = u.Cli.toml_ensure_table(tool_section, "uv")
        sources = u.Cli.toml_ensure_table(uv_section, "sources")
        for source_key in [str(k) for k in sources]:
            if source_key in internal_names and source_key not in expected_names:
                del sources[source_key]
                changes.append(f"  uv.sources: removed stale source {source_key}")
        for dep_name in sorted(expected_names):
            expected: t.Infra.ContainerDict
            if mode == c.Infra.ReportKeys.WORKSPACE:
                expected = {"workspace": True}
            else:
                expected = {
                    "path": f"{c.Infra.FLEXT_DEPS_DIR}/{dep_name}",
                    "editable": True,
                }
            current_table = u.Cli.toml_get_table(sources, dep_name)
            empty: t.Infra.ContainerDict = {}
            current_map: t.Infra.ContainerDict = (
                dict(current_table.unwrap()) if current_table is not None else empty
            )
            if current_map == expected:
                continue
            source_table = u.Cli.toml_table()
            for key in sorted(expected):
                source_table[key] = expected[key]
            sources[dep_name] = source_table
            changes.append(f"  uv.sources: synced source for {dep_name}")
        return changes

    def _rewrite_uv_workspace(
        self,
        doc: t.Cli.TomlDocument,
        *,
        is_root: bool,
        members: t.StrSequence,
    ) -> t.StrSequence:
        if not is_root:
            return []
        changes: MutableSequence[str] = []
        tool_section = u.Cli.toml_ensure_table(doc, c.Infra.TOOL)
        uv_section = u.Cli.toml_ensure_table(tool_section, "uv")
        workspace_section = u.Cli.toml_ensure_table(uv_section, "workspace")
        expected_members = sorted(set(members))
        current_members = u.Cli.toml_as_string_list(
            u.Cli.toml_get_item(workspace_section, "members")
        )
        if current_members != expected_members:
            workspace_section["members"] = u.Cli.toml_array(expected_members)
            changes.append("  uv.workspace: members synchronized")
        return changes

    @staticmethod
    def _rewrite_poetry(
        doc: t.Cli.TomlDocument,
        *,
        is_root: bool,
        mode: str,
    ) -> t.StrSequence:
        tool_section = u.Cli.toml_get_table(doc, c.Infra.TOOL)
        if tool_section is None:
            return []
        poetry_section = u.Cli.toml_get_table(tool_section, c.Infra.POETRY)
        if poetry_section is None:
            return []
        deps = u.Cli.toml_get_table(poetry_section, c.Infra.DEPENDENCIES)
        if deps is None:
            return []
        changes: MutableSequence[str] = []
        for dep_key_raw in deps:
            dep_key = dep_key_raw
            value = deps[dep_key_raw]
            if not isinstance(value, TomlTable | InlineTable):
                continue
            if c.Infra.PATH not in value:
                continue
            raw_path = value[c.Infra.PATH]
            if not isinstance(raw_path, str) or not raw_path.strip():
                continue
            dep_name = FlextInfraDependencyPathSyncRewrite.dep_name(raw_path)
            new_path = (
                dep_name
                if mode == c.Infra.ReportKeys.WORKSPACE and is_root
                else (
                    f"../{dep_name}"
                    if mode == c.Infra.ReportKeys.WORKSPACE
                    else f"{c.Infra.FLEXT_DEPS_DIR}/{dep_name}"
                )
            )
            if raw_path != new_path:
                changes.append(
                    f"  Poetry: {dep_key}.path = {raw_path!r} -> {new_path!r}",
                )
                value[c.Infra.PATH] = new_path
        return changes

    def rewrite_dep_paths(
        self,
        pyproject_path: Path,
        *,
        mode: str,
        internal_names: t.Infra.StrSet,
        workspace_members: t.StrSequence,
        is_root: bool = False,
        dry_run: bool = False,
    ) -> r[t.StrSequence]:
        """Rewrite PEP 621 and Poetry dependency paths."""
        doc_result = u.Cli.toml_read_document(pyproject_path)
        if doc_result.is_failure:
            return r[t.StrSequence].fail(
                doc_result.error or "failed to read TOML document",
            )
        doc: t.Cli.TomlDocument = doc_result.value
        pep_changes, internal_deps = self._rewrite_pep621(
            doc,
            internal_names=internal_names,
        )
        changes: MutableSequence[str] = list(pep_changes)
        changes += list(
            self._rewrite_uv_sources(
                doc,
                is_root=is_root,
                mode=mode,
                internal_names=internal_names,
                internal_deps=internal_deps,
                workspace_members=workspace_members,
            ),
        )
        changes += list(
            self._rewrite_uv_workspace(
                doc,
                is_root=is_root,
                members=workspace_members,
            ),
        )
        changes += list(self._rewrite_poetry(doc, is_root=is_root, mode=mode))
        if changes and (not dry_run):
            write_result = u.Cli.toml_write_document(pyproject_path, doc)
            if write_result.is_failure:
                return r[t.StrSequence].fail(
                    write_result.error or "failed to write TOML",
                )
        return r[t.StrSequence].ok(changes)


__all__ = ["FlextInfraDependencyPathSyncRewrite"]
