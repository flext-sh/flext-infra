"""Copyright (c) 2025 FLEXT Team. All rights reserved.

SPDX-License-Identifier: MIT.
"""

from __future__ import annotations

import operator
from collections import defaultdict
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from flext_infra import c, t

_TEMPLATE_ROOT = Path(__file__).resolve().parent.parent / "templates"

_ENV = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_ROOT)),
    trim_blocks=False,
    lstrip_blocks=False,
    keep_trailing_newline=False,
    undefined=StrictUndefined,
    autoescape=select_autoescape(),
)


def _is_local_module(mod: str, root_name: str) -> bool:
    """Check if a module path belongs to the local package."""
    return (
        mod.startswith(".")
        or not root_name
        or mod.split(".", maxsplit=1)[0] == root_name
    )


def _format_import(
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


def _format_module_alias_import(
    indent: str,
    mod: str,
    export_name: str,
) -> str:
    """Format a module import that binds the module object to an alias."""
    if mod.startswith(".") and mod != ".":
        parent_mod, _, child_name = mod.rpartition(".")
        return f"{indent}from {parent_mod or '.'} import {child_name} as {export_name}"
    return f"{indent}import {mod} as {export_name}"


def _group_imports(
    import_map: t.Infra.LazyImportMap,
) -> Mapping[str, MutableSequence[t.Infra.StrPair]]:
    """Group a flat import map into module-keyed pairs."""
    groups: MutableMapping[str, MutableSequence[t.Infra.StrPair]] = defaultdict(list)
    for export_name in sorted(import_map):
        mod, attr = import_map[export_name]
        groups[mod].append((export_name, attr))
    return groups


class FlextInfraCodegenGeneration:
    """Generate Python module files with lazy import infrastructure."""

    @staticmethod
    def _generate_import_lines(
        groups: Mapping[str, t.Infra.StrPairSequence],
        *,
        indent: str = "",
    ) -> t.StrSequence:
        """Generate import lines grouped by module path."""
        if not groups:
            return ()

        lines: MutableSequence[str] = []

        def _emit_module(mod: str) -> None:
            items = groups[mod]
            alias_items = sorted(
                (item for item in items if not item[1]),
                key=operator.itemgetter(0),
            )
            sorted_items = sorted(
                (item for item in items if item[1]),
                key=lambda x: (x[1], x[0] != x[1]),
            )
            for export_name, _ in alias_items:
                lines.append(_format_module_alias_import(indent, mod, export_name))
            if not sorted_items:
                return
            parts: t.StrSequence = [
                export_name
                if export_name == attr_name
                else f"{attr_name} as {export_name}"
                for export_name, attr_name in sorted_items
            ]
            lines.extend(_format_import(indent, mod, parts))

        sorted_mods = sorted(groups, key=str.lower)
        prev_top: str | None = None
        for mod in sorted_mods:
            top = mod.split(".")[0]
            if prev_top is not None and top != prev_top:
                lines.append("")
            _emit_module(mod)
            prev_top = top
        return lines

    @staticmethod
    def generate_type_checking(
        groups: Mapping[str, t.Infra.StrPairSequence],
        *,
        include_flext_types: bool = True,
        child_packages: t.StrSequence | None = None,
        local_package_root: str | None = None,
    ) -> t.StrSequence:
        """Generate TYPE_CHECKING import block with wildcard imports.

        Collapses sub-module imports into parent package wildcards when the
        parent is a known child package (already has its own ``__init__.py``).

        Args:
            groups: Mapping of module paths to lists of (export_name, attr_name) tuples.
            include_flext_types: Whether to import FlextTypes from flext_core.
            child_packages: Child packages whose sub-modules should be collapsed.
            local_package_root: Root package name for local/external classification.

        Returns:
            List of code lines forming the TYPE_CHECKING block.

        """
        if not groups and not include_flext_types:
            return ()
        if not groups and include_flext_types:
            return ("if _TYPE_CHECKING:", "    from flext_core import FlextTypes")

        collapsed = _collapse_to_children(groups, child_packages)
        children = set(child_packages or [])
        root_name = "" if not local_package_root else local_package_root.split(".")[0]

        lines: MutableSequence[str] = ["if _TYPE_CHECKING:"]
        if include_flext_types and not _has_flext_types(collapsed):
            lines.append("    from flext_core import FlextTypes")

        external_imports: t.MutableStrSequenceMapping = defaultdict(list)

        sorted_mods = sorted(collapsed, key=str.lower)
        prev_top: str | None = None
        for mod in sorted_mods:
            top = mod.split(".")[0]
            if prev_top is not None and top != prev_top:
                lines.append("")
            _emit_type_checking_module(
                mod,
                collapsed[mod],
                children,
                root_name,
                lines,
                external_imports,
            )
            prev_top = top

        for mod in sorted(external_imports, key=str.lower):
            parts = sorted(set(external_imports[mod]))
            alias_exports = [
                part.removeprefix("import::")
                for part in parts
                if part.startswith("import::")
            ]
            symbol_parts = tuple(
                part for part in parts if not part.startswith("import::")
            )
            for export_name in alias_exports:
                lines.append(_format_module_alias_import("    ", mod, export_name))
            if symbol_parts:
                lines.extend(_format_import("    ", mod, symbol_parts))

        return () if len(lines) == 1 else lines

    @staticmethod
    def generate_file(
        docstring_source: str,
        exports: t.StrSequence,
        filtered: t.Infra.LazyImportMap,
        inline_constants: t.StrMapping,
        current_pkg: str,
        eager_typevar_names: frozenset[str] = frozenset(),
        eager_imports: t.Infra.LazyImportMap | None = None,
        wildcard_runtime_modules: t.StrSequence | None = None,
        child_packages_for_lazy: t.StrSequence | None = None,
        child_packages_for_tc: t.StrSequence | None = None,
    ) -> str:
        """Generate complete module file with lazy imports and type hints.

        Args:
            docstring_source: Module docstring text (empty string for none).
            exports: List of all exported names.
            filtered: Mapping of export names to (module_path, attr_name) tuples.
            inline_constants: Mapping of constant names to their string values.
            current_pkg: Current package name for import strategy selection.
            eager_typevar_names: Type variable names to import eagerly (not lazily).
            eager_imports: Runtime imports that must exist eagerly in module globals.
            child_packages_for_lazy: Child packages for lazy import collapsing.
            child_packages_for_tc: Child packages for TYPE_CHECKING collapsing.

        Returns:
            Complete Python module file as a single string.

        """
        tpl = c.Infra.Templates
        runtime_imports: t.Infra.LazyImportMap = eager_imports or {}
        lazy_filtered: t.Infra.LazyImportMap = {
            name: val
            for name, val in filtered.items()
            if name not in eager_typevar_names
        }
        children_lazy = tuple(child_packages_for_lazy or ())
        eager_export_names = [
            name for name in sorted(exports) if name not in lazy_filtered
        ]
        is_core_pkg = current_pkg == "flext_core"

        out: MutableSequence[str] = [c.Infra.AUTOGEN_HEADER]
        if docstring_source:
            out.extend([docstring_source, ""])

        preamble: str = _ENV.get_template(tpl.PREAMBLE_STANDARD).render(
            include_merge_helper=bool(children_lazy),
            use_root_helpers=not is_core_pkg,
        )
        out.extend(preamble.splitlines())

        if eager_typevar_names:
            typings_mod = f"{current_pkg}.typings"
            sorted_tvars = sorted(eager_typevar_names)
            out.extend(_format_import("", typings_mod, sorted_tvars))
        out.append("")

        runtime_groups = _group_imports(runtime_imports)
        runtime_import_lines = FlextInfraCodegenGeneration._generate_import_lines(
            runtime_groups,
        )
        runtime_import_block: MutableSequence[str] = [
            f"from {module} import *"
            for module in sorted(set(wildcard_runtime_modules or ()))
        ]
        if runtime_import_block and runtime_import_lines:
            runtime_import_block.append("")
        runtime_import_block.extend(runtime_import_lines)

        tc_groups = _group_imports(lazy_filtered)
        type_checking_lines = FlextInfraCodegenGeneration.generate_type_checking(
            tc_groups,
            include_flext_types=not is_core_pkg,
            child_packages=child_packages_for_tc or [],
            local_package_root=current_pkg,
        )

        lazy_entries = _build_lazy_entries(
            exports,
            lazy_filtered,
            children_lazy,
        )

        body: str = _ENV.get_template(tpl.BODY).render(
            runtime_import_lines="\n".join(runtime_import_block),
            child_module_paths=children_lazy,
            type_checking_lines="\n".join(type_checking_lines),
            inline_constants=sorted(inline_constants.items()),
            eager_export_names=eager_export_names,
            lazy_entries=lazy_entries,
            exports=sorted(exports),
        )
        out.extend(body.splitlines())
        out.append("")

        getattr_rendered: str = _ENV.get_template(tpl.GETATTR_STANDARD).render(
            eager_export_names=eager_export_names,
        )
        out.extend(getattr_rendered.splitlines())

        return "\n".join(out) + "\n"


def _collapse_to_children(
    groups: Mapping[str, t.Infra.StrPairSequence],
    child_packages: t.StrSequence | None,
) -> MutableMapping[str, MutableSequence[t.Infra.StrPair]]:
    """Collapse sub-module imports into parent package when parent is a child package."""
    sorted_children = sorted(set(child_packages or []), key=len, reverse=True)
    collapsed: MutableMapping[str, MutableSequence[t.Infra.StrPair]] = defaultdict(list)
    for mod, items in groups.items():
        target = mod
        for cp in sorted_children:
            if mod.startswith(cp + ".") or mod == cp:
                target = cp
                break
        collapsed[target].extend(items)
    return collapsed


def _has_flext_types(
    collapsed: Mapping[str, Sequence[t.Infra.StrPair]],
) -> bool:
    """Check if FlextTypes is already present in collapsed imports."""
    return any(
        export_name == "FlextTypes"
        for items in collapsed.values()
        for export_name, _ in items
    )


def _emit_type_checking_module(
    mod: str,
    items: Sequence[t.Infra.StrPair],
    children: set[str],
    root_name: str,
    lines: MutableSequence[str],
    external_imports: t.MutableStrSequenceMapping,
) -> None:
    """Emit TYPE_CHECKING lines for a single module using explicit imports only."""
    symbol_items = tuple(
        (export_name, attr_name) for export_name, attr_name in items if attr_name
    )
    has_symbol_aliases = any(
        export_name != attr_name for export_name, attr_name in symbol_items
    )
    alias_exports: MutableSequence[str] = []
    parts: MutableSequence[str] = []
    module_basename = mod.rsplit(".", maxsplit=1)[-1]
    for export_name, attr_name in sorted(
        items,
        key=lambda item: (item[1] or item[0], item[0] != (item[1] or item[0])),
    ):
        if not attr_name:
            if export_name == module_basename:
                alias_exports.append(export_name)
            else:
                parts.append(export_name)
            continue
        parts.append(
            export_name if export_name == attr_name else f"{attr_name} as {export_name}"
        )

    deduped_aliases = tuple(dict.fromkeys(alias_exports))
    deduped_parts = tuple(dict.fromkeys(parts))
    if not deduped_aliases and not deduped_parts:
        return

    if mod in children or (
        _is_local_module(mod, root_name) and ".fixtures." not in mod
    ):
        if not deduped_aliases and deduped_parts and has_symbol_aliases:
            lines.append(f"    from {mod} import *")
            return
        for export_name in deduped_aliases:
            lines.append(_format_module_alias_import("    ", mod, export_name))
        if deduped_parts:
            lines.extend(_format_import("    ", mod, deduped_parts))
        return

    for export_name in deduped_aliases:
        external_imports[mod].append(f"import::{export_name}")
    external_imports[mod].extend(deduped_parts)


def _build_lazy_entries(
    exports: t.StrSequence,
    lazy_filtered: t.Infra.LazyImportMap,
    children_lazy: tuple[str, ...],
) -> Sequence[tuple[str, str, str]]:
    """Build the list of lazy import entries, excluding child-package sub-modules."""
    child_prefixes = tuple(f"{cp}." for cp in children_lazy)
    child_aliases = set(children_lazy)
    entries: MutableSequence[tuple[str, str, str]] = []
    for exp in sorted(exports):
        if exp not in lazy_filtered:
            continue
        mod, attr = lazy_filtered[exp]
        if (mod in child_aliases and not attr) or not mod.startswith(child_prefixes):
            entries.append((exp, mod, attr))
    return entries


__all__ = ["FlextInfraCodegenGeneration"]
