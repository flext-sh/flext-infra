"""Copyright (c) 2025 FLEXT Team. All rights reserved.

SPDX-License-Identifier: MIT.
"""

from __future__ import annotations

import operator
from collections import defaultdict
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path
from typing import Protocol

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


class _Renderable(Protocol):
    def render(self, **kwargs: t.Infra.InfraValue) -> str: ...


def _render(template: _Renderable, **kwargs: t.Infra.InfraValue) -> str:
    """Render a jinja2 template with explicit str return type."""
    return template.render(**kwargs)


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
            return []

        lines: MutableSequence[str] = []

        def _emit_module(mod: str) -> None:
            items = groups[mod]
            rendered_mod = mod
            alias_items = sorted(
                (item for item in items if not item[1]),
                key=operator.itemgetter(0),
            )
            sorted_items = sorted(
                (item for item in items if item[1]),
                key=lambda x: (x[1], x[0] != x[1]),
            )
            for export_name, _ in alias_items:
                if rendered_mod.startswith(".") and rendered_mod != ".":
                    parent_mod, _, child_name = rendered_mod.rpartition(".")
                    alias_line = (
                        f"{indent}from {parent_mod or '.'} import {child_name} "
                        f"as {export_name}"
                    )
                else:
                    alias_line = f"{indent}import {mod} as {export_name}"
                lines.append(alias_line)
            if not sorted_items:
                return
            parts: Sequence[str] = [
                export_name
                if export_name == attr_name
                else f"{attr_name} as {export_name}"
                for export_name, attr_name in sorted_items
            ]
            joined = ", ".join(parts)
            line = f"{indent}from {rendered_mod} import {joined}"
            if len(line) > c.Infra.MAX_LINE_LENGTH:
                lines.append(f"{indent}from {rendered_mod} import (")
                lines.extend(f"{indent}    {part}," for part in parts)
                lines.append(f"{indent})")
            else:
                lines.append(line)

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
    def generate_runtime_imports(
        groups: Mapping[str, t.Infra.StrPairSequence],
    ) -> t.StrSequence:
        """Generate eager runtime import lines."""
        return FlextInfraCodegenGeneration._generate_import_lines(groups)

    @staticmethod
    def generate_type_checking(
        groups: Mapping[str, t.Infra.StrPairSequence],
        *,
        include_flext_types: bool = True,
        child_packages: Sequence[str] | None = None,
        local_package_root: str | None = None,
    ) -> t.StrSequence:
        """Generate TYPE_CHECKING import block with wildcard imports.

        Collapses sub-module imports into parent package wildcards when the
        parent is a known child package (already has its own ``__init__.py``).

        Args:
            groups: Mapping of module paths to lists of (export_name, attr_name) tuples.
            include_flext_types: Whether to import FlextTypes from flext_core.
            child_packages: Child packages whose sub-modules should be collapsed.

        Returns:
            List of code lines forming the TYPE_CHECKING block.

        """
        if not groups:
            return []

        # Collapse: if mod starts with a child_package prefix, replace with the child
        children = set(child_packages or [])
        sorted_children = sorted(children, key=len, reverse=True)
        collapsed: MutableMapping[str, MutableSequence[t.Infra.StrPair]] = defaultdict(
            list,
        )
        for mod, items in groups.items():
            target = mod
            for cp in sorted_children:
                if mod.startswith(cp + ".") or mod == cp:
                    target = cp
                    break
            collapsed[target].extend(items)

        lines: MutableSequence[str] = ["if TYPE_CHECKING:"]
        root_name = "" if not local_package_root else local_package_root.split(".")[0]
        flext_types_in_groups = any(
            export_name == "FlextTypes"
            for items in collapsed.values()
            for export_name, _ in items
        )
        if include_flext_types and not flext_types_in_groups:
            lines.append("    from flext_core import FlextTypes")

        # Collect all mods that will get wildcard imports
        wildcard_mods: set[str] = set()
        for mod in collapsed:
            items = collapsed[mod]
            if mod in children or any(attr for _, attr in items):
                wildcard_mods.add(mod)

        sorted_mods = sorted(collapsed, key=str.lower)
        prev_top: str | None = None
        for mod in sorted_mods:
            top = mod.split(".")[0]
            if prev_top is not None and top != prev_top:
                lines.append("")
            items = collapsed[mod]
            is_collapsed_child = mod in children
            if is_collapsed_child:
                lines.append(f"    from {mod} import *")
            else:
                attr_items = [(exp, attr) for exp, attr in items if attr]
                if attr_items:
                    is_local_module = (
                        mod.startswith(".")
                        or not root_name
                        or mod.split(".")[0] == root_name
                    )
                    if is_local_module:
                        lines.append(f"    from {mod} import *")
            prev_top = top
        return [] if len(lines) == 1 else lines

    @staticmethod
    def generate_file(
        docstring_source: str,
        exports: t.StrSequence,
        filtered: t.Infra.LazyImportMap,
        inline_constants: t.StrMapping,
        current_pkg: str,
        eager_typevar_names: frozenset[str] = frozenset(),
        eager_imports: t.Infra.LazyImportMap | None = None,
        child_packages_for_lazy: Sequence[str] | None = None,
        child_packages_for_tc: Sequence[str] | None = None,
    ) -> str:
        """Generate complete module file with lazy imports and type hints.

        Assembles all components (docstring, imports, lazy import table, __all__,
        __getattr__, __dir__) into a single module file using Jinja2 templates.

        Args:
            docstring_source: Module docstring text (empty string for none).
            exports: List of all exported names.
            filtered: Mapping of export names to (module_path, attr_name) tuples.
            inline_constants: Mapping of constant names to their string values.
            current_pkg: Current package name for import strategy selection.
            eager_typevar_names: Type variable names to import eagerly (not lazily).
            eager_imports: Runtime imports that must exist eagerly in module globals.

        Returns:
            Complete Python module file as a single string.

        """
        tpl = c.Infra.Templates
        runtime_imports: t.Infra.LazyImportMap = (
            {} if eager_imports is None else eager_imports
        )
        lazy_filtered: t.Infra.LazyImportMap = {
            name: val
            for name, val in filtered.items()
            if name not in eager_typevar_names
        }

        # L0 (_typings) no longer needs special templates — flext_core.lazy
        # has zero runtime imports from flext_core, so no circular deps.
        is_l0_typings = False

        # --- header + docstring ---
        out: MutableSequence[str] = [c.Infra.AUTOGEN_HEADER]
        if docstring_source:
            out.extend([docstring_source, ""])

        # --- preamble (from .j2 template) ---
        preamble_name = tpl.PREAMBLE_L0 if is_l0_typings else tpl.PREAMBLE_STANDARD
        preamble_rendered: str = _render(_ENV.get_template(preamble_name))
        out.extend(preamble_rendered.splitlines())

        # --- eager TypeVar imports ---
        if eager_typevar_names:
            typings_mod = f"{current_pkg}.typings"
            sorted_tvars = sorted(eager_typevar_names)
            eager_line = f"from {typings_mod} import " + ", ".join(sorted_tvars)
            if len(eager_line) > c.Infra.MAX_LINE_LENGTH:
                out.append(f"from {typings_mod} import (")
                out.extend(f"    {tv}," for tv in sorted_tvars)
                out.append(")")
            else:
                out.append(eager_line)
        out.append("")

        # --- eager runtime imports ---
        runtime_groups: Mapping[str, MutableSequence[t.Infra.StrPair]] = defaultdict(
            list
        )
        for export_name in sorted(runtime_imports):
            mod, attr = runtime_imports[export_name]
            runtime_groups[mod].append((export_name, attr))
        runtime_import_lines = FlextInfraCodegenGeneration.generate_runtime_imports(
            runtime_groups,
        )
        children_lazy = tuple(child_packages_for_lazy or ())
        child_lazy_specs = [
            (child_pkg, f"_CHILD_LAZY_{index}")
            for index, child_pkg in enumerate(children_lazy)
        ]
        child_lazy_import_lines = [
            f"from {child_pkg} import _LAZY_IMPORTS as {alias_name}"
            for child_pkg, alias_name in child_lazy_specs
        ]

        # --- determine child packages for TYPE_CHECKING collapse ---
        children_tc = child_packages_for_tc or []

        # --- TYPE_CHECKING block ---
        groups: Mapping[str, MutableSequence[t.Infra.StrPair]] = defaultdict(list)
        for export_name in sorted(lazy_filtered):
            mod, attr = lazy_filtered[export_name]
            groups[mod].append((export_name, attr))

        type_checking_lines = FlextInfraCodegenGeneration.generate_type_checking(
            groups,
            include_flext_types=False,
            child_packages=children_tc,
            local_package_root=current_pkg,
        )
        lazy_entries: MutableSequence[tuple[str, str, str]] = []
        child_prefixes = tuple(f"{child_pkg}." for child_pkg in children_lazy)
        child_package_aliases = set(children_lazy)
        for exp in sorted(exports):
            if exp not in lazy_filtered:
                continue
            mod, attr = lazy_filtered[exp]
            if mod in child_package_aliases and not attr:
                lazy_entries.append((exp, mod, attr))
                continue
            if not mod.startswith(child_prefixes):
                lazy_entries.append((exp, mod, attr))

        # --- body (inline constants + _LAZY_IMPORTS) from .j2 ---
        body: str = _render(
            _ENV.get_template(tpl.BODY),
            runtime_import_lines="\n".join(runtime_import_lines),
            child_lazy_import_lines="\n".join(child_lazy_import_lines),
            child_lazy_aliases=[alias_name for _, alias_name in child_lazy_specs],
            type_checking_lines="\n".join(type_checking_lines),
            inline_constants=sorted(inline_constants.items()),
            eager_export_names=[
                export_name
                for export_name in sorted(exports)
                if export_name not in lazy_filtered
            ],
            lazy_entries=lazy_entries,
            exports=sorted(exports),
        )
        out.extend(body.splitlines())
        out.append("")

        # --- getattr block (from .j2 template) ---
        getattr_name = tpl.GETATTR_L0 if is_l0_typings else tpl.GETATTR_STANDARD
        getattr_rendered: str = _render(
            _ENV.get_template(getattr_name),
            eager_export_names=[
                export_name
                for export_name in sorted(exports)
                if export_name not in lazy_filtered
            ],
        )
        out.extend(getattr_rendered.splitlines())

        return "\n".join(out) + "\n"


__all__ = ["FlextInfraCodegenGeneration"]
