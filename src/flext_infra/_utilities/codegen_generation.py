"""Helper functions for codegen generation type-checking and lazy imports."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence

from flext_infra import c, t


class FlextInfraUtilitiesCodegenGeneration:
    """Utilities for codegen import formatting, grouping, and lazy entries."""

    @staticmethod
    def is_local_module(mod: str, root_name: str) -> bool:
        """Check if a module path belongs to the local package."""
        return (
            mod.startswith(".")
            or not root_name
            or mod.split(".", maxsplit=1)[0] == root_name
        )

    @staticmethod
    def format_import(
        indent: str,
        mod: str,
        parts: t.StrSequence,
    ) -> t.StrSequence:
        """Format an import statement, wrapping to multi-line if too long."""
        joined = ", ".join(parts)
        line = f"{indent}from {mod} import {joined}"
        if len(line) <= c.Infra.MAX_LINE_LENGTH:
            return [line]
        return [
            f"{indent}from {mod} import (",
            *(f"{indent}    {part}," for part in parts),
            f"{indent})",
        ]

    @staticmethod
    def format_module_alias_import(
        indent: str,
        mod: str,
        export_name: str,
    ) -> str:
        """Format a module import that binds the module object to an alias."""
        if mod.startswith(".") and mod != ".":
            parent_mod, _, child_name = mod.rpartition(".")
            return (
                f"{indent}from {parent_mod or '.'}"
                f" import {child_name} as {export_name}"
            )
        return f"{indent}import {mod} as {export_name}"

    @staticmethod
    def format_type_checking_module_alias_import(
        indent: str,
        mod: str,
        export_name: str,
    ) -> t.StrSequence:
        """Format TYPE_CHECKING module imports in a ruff-stable form."""
        module_basename = mod.rsplit(".", maxsplit=1)[-1]
        if "." in mod and export_name == module_basename:
            private_alias = f"_{mod.replace('.', '_')}"
            return (
                f"{indent}import {mod} as {private_alias}",
                f"{indent}{export_name} = {private_alias}",
            )
        return (
            FlextInfraUtilitiesCodegenGeneration.format_module_alias_import(
                indent, mod, export_name,
            ),
        )

    @staticmethod
    def group_imports(
        import_map: t.Infra.LazyImportMap,
    ) -> Mapping[str, MutableSequence[t.Infra.StrPair]]:
        """Group a flat import map into module-keyed pairs."""
        groups: MutableMapping[str, MutableSequence[t.Infra.StrPair]] = defaultdict(
            list,
        )
        for export_name in sorted(import_map):
            mod, attr = import_map[export_name]
            groups[mod].append((export_name, attr))
        return groups

    @staticmethod
    def collapse_to_children(
        groups: Mapping[str, t.Infra.StrPairSequence],
        child_packages: t.StrSequence | None,
    ) -> MutableMapping[str, MutableSequence[t.Infra.StrPair]]:
        """Collapse sub-module imports into parent package."""
        sorted_children: MutableSequence[str] = sorted(
            set(child_packages or []), key=len, reverse=True,
        )
        collapsed: MutableMapping[str, MutableSequence[t.Infra.StrPair]] = defaultdict(
            list,
        )
        for mod, items in groups.items():
            target: str = mod
            for cp in sorted_children:
                if mod.startswith(cp + ".") or mod == cp:
                    target = cp
                    break
            collapsed[target].extend(items)
        return collapsed

    @staticmethod
    def has_flext_types(
        collapsed: Mapping[str, Sequence[t.Infra.StrPair]],
    ) -> bool:
        """Check if FlextTypes is already present in collapsed imports."""
        return any(
            export_name == "FlextTypes"
            for items in collapsed.values()
            for export_name, _ in items
        )

    @staticmethod
    def emit_type_checking_module(
        mod: str,
        items: Sequence[t.Infra.StrPair],
        children: set[str],
        root_name: str,
        lines: MutableSequence[str],
        external_imports: t.MutableStrSequenceMapping,
    ) -> None:
        """Emit TYPE_CHECKING lines for a single module."""
        alias_exports: MutableSequence[str] = []
        parts: MutableSequence[str] = []
        module_basename = mod.rsplit(".", maxsplit=1)[-1]
        for export_name, attr_name in sorted(
            items,
            key=lambda item: (
                item[1] or item[0],
                item[0] != (item[1] or item[0]),
            ),
        ):
            if not attr_name:
                if export_name == module_basename:
                    alias_exports.append(export_name)
                else:
                    parts.append(export_name)
                continue
            parts.append(
                export_name
                if export_name == attr_name
                else f"{attr_name} as {export_name}"
            )

        deduped_aliases = tuple(dict.fromkeys(alias_exports))
        deduped_parts = tuple(dict.fromkeys(parts))

        if not deduped_aliases and not deduped_parts:
            return

        if mod in children or (
            FlextInfraUtilitiesCodegenGeneration.is_local_module(mod, root_name) and ".fixtures." not in mod
        ):
            for export_name in deduped_aliases:
                lines.extend(
                    FlextInfraUtilitiesCodegenGeneration.format_type_checking_module_alias_import(
                        "    ", mod, export_name,
                    ),
                )
            if deduped_parts:
                lines.extend(FlextInfraUtilitiesCodegenGeneration.format_import("    ", mod, deduped_parts))
            return

        for export_name in deduped_aliases:
            external_imports[mod].append(f"import::{export_name}")
        external_imports[mod].extend(deduped_parts)

    @staticmethod
    def build_lazy_entries(
        exports: t.StrSequence,
        lazy_filtered: t.Infra.LazyImportMap,
        children_lazy: tuple[str, ...],
    ) -> Sequence[tuple[str, str, str]]:
        """Build lazy import entries, excluding child-package sub-modules."""
        child_prefixes = tuple(f"{cp}." for cp in children_lazy)
        child_aliases = set(children_lazy)
        entries: MutableSequence[tuple[str, str, str]] = []
        for exp in sorted(exports):
            if exp not in lazy_filtered:
                continue
            mod, attr = lazy_filtered[exp]
            if (
                mod in child_aliases and not attr
            ) or not mod.startswith(child_prefixes):
                entries.append((exp, mod, attr))
        return entries


__all__: t.StrSequence = ["FlextInfraUtilitiesCodegenGeneration"]
