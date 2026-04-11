"""Helper functions for codegen generation type-checking and lazy imports."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence

from flext_infra import c, t


class FlextInfraUtilitiesCodegenGeneration:
    """Utilities for codegen import formatting, grouping, and lazy entries."""

    @staticmethod
    def is_module_or_package_export(attr_name: str) -> bool:
        """Return True for compatibility exports that point at a module object."""
        return not attr_name

    @staticmethod
    def is_root_namespace_package(current_pkg: str) -> bool:
        """Return True only for top-level root namespace packages."""
        return bool(current_pkg) and "." not in current_pkg

    @staticmethod
    def is_local_module(mod: str, root_name: str) -> bool:
        """Check if a module path belongs to the local package."""
        return (
            mod.startswith(".")
            or not root_name
            or mod.split(".", maxsplit=1)[0] == root_name
        )

    @staticmethod
    def compact_lazy_module_path(current_pkg: str, mod: str) -> str:
        """Compact same-package lazy targets to relative module paths."""
        if not current_pkg:
            return mod
        if mod == current_pkg:
            return "."
        prefix = f"{current_pkg}."
        if mod.startswith(prefix):
            return f".{mod.removeprefix(prefix)}"
        return mod

    @staticmethod
    def format_root_package_docstring(current_pkg: str) -> str:
        """Build a compact root-package docstring for generated __init__.py files."""
        label = current_pkg.replace("_", " ").replace("-", " ").strip()
        package_name = " ".join(word.capitalize() for word in label.split())
        return f'"""{package_name} package."""'

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
                f"{indent}from {parent_mod or '.'} import {child_name} as {export_name}"
            )
        return f"{indent}import {mod} as {export_name}"

    @staticmethod
    def format_type_checking_module_alias_import(
        indent: str,
        mod: str,
        export_name: str,
    ) -> t.StrSequence:
        """Format TYPE_CHECKING module imports without compatibility rebinds."""
        return (
            FlextInfraUtilitiesCodegenGeneration.format_module_alias_import(
                indent,
                mod,
                export_name,
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
            set(child_packages or []),
            key=len,
            reverse=True,
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
    def should_skip_type_checking_module_export(
        mod: str,
        export_name: str,
        attr_name: str,
        root_name: str,
    ) -> bool:
        """Skip root re-exported module/package names in TYPE_CHECKING."""
        if export_name in c.Infra.ALIAS_NAMES:
            return False
        if not export_name or export_name in {"cli", "main", "infra"}:
            return False
        module_style_name = export_name == export_name.lower()
        if not module_style_name:
            return False
        if not attr_name:
            return export_name == mod.rsplit(".", maxsplit=1)[-1]
        return mod == root_name and attr_name == export_name

    @staticmethod
    def emit_type_checking_module(
        mod: str,
        items: Sequence[t.Infra.StrPair],
        children: t.Infra.StrSet,
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
            if FlextInfraUtilitiesCodegenGeneration.should_skip_type_checking_module_export(
                mod,
                export_name,
                attr_name,
                root_name,
            ):
                continue
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
            FlextInfraUtilitiesCodegenGeneration.is_local_module(mod, root_name)
            and ".fixtures." not in mod
        ):
            for export_name in deduped_aliases:
                lines.extend(
                    FlextInfraUtilitiesCodegenGeneration.format_type_checking_module_alias_import(
                        "    ",
                        mod,
                        export_name,
                    ),
                )
            if deduped_parts:
                lines.extend(
                    FlextInfraUtilitiesCodegenGeneration.format_import(
                        "    ", mod, deduped_parts
                    )
                )
            return

        for export_name in deduped_aliases:
            external_imports[mod].append(f"import::{export_name}")
        external_imports[mod].extend(deduped_parts)

    @staticmethod
    def build_lazy_entries(
        exports: t.StrSequence,
        lazy_filtered: t.Infra.LazyImportMap,
        current_pkg: str,
        children_lazy: tuple[str, ...],
        *,
        include_module_exports: bool = False,
    ) -> Sequence[tuple[str, str, str]]:
        """Build lazy import entries, excluding child-package sub-modules."""
        child_prefixes = tuple(f"{cp}." for cp in children_lazy)
        child_aliases = set(children_lazy)
        entries: MutableSequence[tuple[str, str, str]] = []
        for exp in exports:
            if exp not in lazy_filtered:
                continue
            mod, attr = lazy_filtered[exp]
            if (
                FlextInfraUtilitiesCodegenGeneration.is_module_or_package_export(attr)
                and not include_module_exports
            ):
                continue
            compact_mod = FlextInfraUtilitiesCodegenGeneration.compact_lazy_module_path(
                current_pkg,
                mod,
            )
            if (mod in child_aliases and not attr) or not mod.startswith(
                child_prefixes
            ):
                entries.append((exp, compact_mod, attr))
        return entries

    @staticmethod
    def group_lazy_entries(
        lazy_entries: Sequence[tuple[str, str, str]],
    ) -> tuple[
        Sequence[tuple[str, t.StrSequence]],
        Sequence[tuple[str, t.Infra.StrPairSequence]],
    ]:
        """Group lazy entries into compact module- and alias-based buckets.

        Returns:
            - module_groups: (module_path, (export_name, ...)) entries where
              ``export_name == attr_name`` (same-name imports).
            - alias_groups: (module_path, ((export_name, attr_name), ...)) entries
              where ``export_name != attr_name``.

        """
        module_groups: MutableMapping[str, MutableSequence[str]] = defaultdict(list)
        alias_groups: MutableMapping[str, MutableSequence[t.Infra.StrPair]] = (
            defaultdict(
                list,
            )
        )

        for export_name, mod, attr_name in lazy_entries:
            if not attr_name or attr_name == export_name:
                module_groups[mod].append(export_name)
            else:
                alias_groups[mod].append((export_name, attr_name))

        module_items: Sequence[tuple[str, t.StrSequence]] = tuple(
            (mod, tuple(sorted(names)))
            for mod, names in sorted(
                module_groups.items(), key=lambda item: item[0].lower()
            )
        )
        alias_items: Sequence[tuple[str, t.Infra.StrPairSequence]] = tuple(
            (mod, tuple(sorted(pairs)))
            for mod, pairs in sorted(
                alias_groups.items(), key=lambda item: item[0].lower()
            )
        )
        return module_items, alias_items

    @staticmethod
    def build_published_exports(
        exports: t.StrSequence,
        lazy_filtered: t.Infra.LazyImportMap,
    ) -> t.StrSequence:
        """Drop compatibility module/package names from published exports."""
        return tuple(
            export_name
            for export_name in sorted(exports)
            if export_name not in lazy_filtered
            or not FlextInfraUtilitiesCodegenGeneration.is_module_or_package_export(
                lazy_filtered[export_name][1]
            )
        )


__all__: t.StrSequence = ["FlextInfraUtilitiesCodegenGeneration"]
