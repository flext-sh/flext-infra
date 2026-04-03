"""TOML rewrite operations for dependency path synchronization.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence
from pathlib import Path

import tomlkit
from tomlkit.items import Table
from tomlkit.toml_document import TOMLDocument

from flext_infra import c, r, t, u


class FlextInfraDependencyPathSyncRewrite:
    """TOML rewrite operations for PEP 621, uv sources/workspace, and Poetry.

    Static helpers (extract_dep_name, _target_path) are resolved via MRO
    from the main FlextInfraDependencyPathSync class.
    """

    @staticmethod
    def _mapping_str_value(
        mapping: Table | t.Infra.ContainerDict,
        key: str,
    ) -> str | None:
        if key not in mapping:
            return None
        value = mapping[key]
        if isinstance(value, str) and value:
            return value
        return None

    @staticmethod
    def _extract_requirement_name(entry: str) -> str | None:
        """Extract requirement name from PEP 621 dependency entry."""
        if " @ " in entry:
            match = c.Infra.PEP621_PATH_DEP_RE.match(entry)
            if match:
                return match.group("name")
        match = c.Infra.PEP621_NAME_RE.match(entry)
        if not match:
            return None
        return match.group("name")

    def _rewrite_pep621(
        self,
        doc: TOMLDocument,
        *,
        internal_names: t.Infra.StrSet,
    ) -> t.Infra.Pair[t.StrSequence, t.Infra.StrSet]:
        project_section = u.Infra.get_table(doc, c.Infra.PROJECT)
        if project_section is None:
            return ([], set())
        deps: t.StrSequence = u.Infra.as_string_list(
            u.Infra.get_item(project_section, c.Infra.DEPENDENCIES)
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
            dep_name = self._extract_requirement_name(requirement_part)
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

    _ensure_table = staticmethod(u.Infra.ensure_table)

    def _rewrite_uv_sources(
        self,
        doc: TOMLDocument,
        *,
        is_root: bool,
        mode: str,
        internal_names: t.Infra.StrSet,
        internal_deps: t.Infra.StrSet,
    ) -> t.StrSequence:
        if not internal_deps:
            return []
        changes: MutableSequence[str] = []
        tool_section = self._ensure_table(doc, c.Infra.TOOL)
        uv_section = self._ensure_table(tool_section, "uv")
        sources = self._ensure_table(uv_section, "sources")
        for source_key in [str(k) for k in sources]:
            if source_key in internal_names and source_key not in internal_deps:
                del sources[source_key]
                changes.append(f"  uv.sources: removed stale source {source_key}")
        from .path_sync import FlextInfraDependencyPathSync  # noqa: PLC0415

        for dep_name in sorted(internal_deps):
            expected: t.Infra.ContainerDict
            if mode == c.Infra.ReportKeys.WORKSPACE:
                expected = {"workspace": True}
            else:
                path_value = FlextInfraDependencyPathSync._target_path(  # noqa: SLF001
                    dep_name,
                    is_root=is_root,
                    mode=mode,
                )
                expected = {"path": path_value, "editable": True}
            current_table = u.Infra.get_table(sources, dep_name)
            empty: t.Infra.ContainerDict = {}
            current_map: t.Infra.ContainerDict = (
                dict(current_table.unwrap()) if current_table is not None else empty
            )
            if current_map == expected:
                continue
            source_table = tomlkit.table()
            for key in sorted(expected):
                source_table[key] = expected[key]
            sources[dep_name] = source_table
            changes.append(f"  uv.sources: synced source for {dep_name}")
        return changes

    def _rewrite_uv_workspace(
        self,
        doc: TOMLDocument,
        *,
        is_root: bool,
        members: t.StrSequence,
    ) -> t.StrSequence:
        if not is_root:
            return []
        changes: MutableSequence[str] = []
        tool_section = self._ensure_table(doc, c.Infra.TOOL)
        uv_section = self._ensure_table(tool_section, "uv")
        workspace_section = self._ensure_table(uv_section, "workspace")
        expected_members = sorted(set(members))
        current_members = u.Infra.as_string_list(
            u.Infra.get_item(workspace_section, "members")
        )
        if current_members != expected_members:
            workspace_section["members"] = u.Infra.array(expected_members)
            changes.append("  uv.workspace: members synchronized")
        return changes

    @staticmethod
    def _rewrite_poetry(
        doc: TOMLDocument,
        *,
        is_root: bool,
        mode: str,
    ) -> t.StrSequence:
        from .path_sync import FlextInfraDependencyPathSync  # noqa: PLC0415

        tool_section = u.Infra.get_table(doc, c.Infra.TOOL)
        if tool_section is None:
            return []
        poetry_section = u.Infra.get_table(tool_section, c.Infra.POETRY)
        if poetry_section is None:
            return []
        deps = u.Infra.get_table(poetry_section, c.Infra.DEPENDENCIES)
        if deps is None:
            return []
        changes: MutableSequence[str] = []
        for dep_key_raw in deps:
            dep_key = dep_key_raw
            value = deps[dep_key_raw]
            if not isinstance(value, Table) or c.Infra.PATH not in value:
                continue
            value_map: Table = value
            raw_path = value_map[c.Infra.PATH]
            if not isinstance(raw_path, str) or not raw_path.strip():
                continue
            dep_name = FlextInfraDependencyPathSync.extract_dep_name(raw_path)
            new_path = FlextInfraDependencyPathSync._target_path(  # noqa: SLF001
                dep_name,
                is_root=is_root,
                mode=mode,
            )
            if raw_path != new_path:
                changes.append(
                    f"  Poetry: {dep_key}.path = {raw_path!r} -> {new_path!r}",
                )
                value_map[c.Infra.PATH] = new_path
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
        doc_result = u.Infra.read_document(pyproject_path)
        if doc_result.is_failure:
            return r[t.StrSequence].fail(
                doc_result.error or "failed to read TOML document",
            )
        doc: TOMLDocument = doc_result.value
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
            write_result = u.Infra.write_document(pyproject_path, doc)
            if write_result.is_failure:
                return r[t.StrSequence].fail(
                    write_result.error or "failed to write TOML",
                )
        return r[t.StrSequence].ok(changes)


__all__ = ["FlextInfraDependencyPathSyncRewrite"]
