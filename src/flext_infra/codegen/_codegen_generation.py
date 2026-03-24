"""Copyright (c) 2025 FLEXT Team. All rights reserved.

SPDX-License-Identifier: MIT.
"""

from __future__ import annotations

import operator
from collections import defaultdict
from collections.abc import Mapping, MutableSequence, Sequence
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
    def render(self, **kwargs: object) -> str: ...


def _render(template: _Renderable, **kwargs: object) -> str:
    """Render a jinja2 template with explicit str return type."""
    return template.render(**kwargs)


class FlextInfraCodegenGeneration:
    """Generate Python module files with lazy import infrastructure."""

    @staticmethod
    def normalized_value_key_cases(mod: str, _current_pkg: str) -> str:
        """Render module path for TYPE_CHECKING imports.

        Returns absolute module paths for all packages (src, tests, examples,
        scripts) to maintain consistency across the codebase.

        Args:
            mod: Module path to render.
            _current_pkg: Current package name (unused, kept for API compat).

        Returns:
            Absolute module path.

        """
        return mod

    @staticmethod
    def generate_type_checking(
        groups: Mapping[str, Sequence[tuple[str, str]]],
        *,
        include_flext_types: bool = True,
    ) -> t.StrSequence:
        """Generate TYPE_CHECKING import block for type hints.

        Creates Python code for conditional imports guarded by TYPE_CHECKING,
        organizing imports by module with proper spacing between top-level packages.

        Args:
            groups: Mapping of module paths to lists of (export_name, attr_name) tuples.
            include_flext_types: Whether to import FlextTypes from flext_core.

        Returns:
            List of code lines forming the TYPE_CHECKING block.

        """
        lines: MutableSequence[str] = ["if TYPE_CHECKING:"]
        # Only emit the standalone FlextTypes import when it does NOT already
        # appear in the groups (avoids F811 redefinition in flext_core's own
        # __init__.py where FlextTypes is re-exported from flext_core.typings).
        flext_types_in_groups = any(
            export_name == "FlextTypes"
            for items in groups.values()
            for export_name, _ in items
        )
        if include_flext_types and not flext_types_in_groups:
            lines.append("    from flext_core import FlextTypes")

        if not groups:
            return lines if len(lines) > 1 else []

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
                        f"    from {parent_mod or '.'} import {child_name} "
                        f"as {export_name}"
                    )
                else:
                    alias_line = f"    import {mod} as {export_name}"
                lines.append(alias_line)
            if not sorted_items:
                return
            parts: MutableSequence[str] = []
            for export_name, attr_name in sorted_items:
                if export_name == attr_name:
                    parts.append(export_name)
                else:
                    parts.append(f"{attr_name} as {export_name}")
            joined = ", ".join(parts)
            line = f"    from {rendered_mod} import {joined}"
            if len(line) > c.Infra.MAX_LINE_LENGTH:
                lines.append(f"    from {rendered_mod} import (")
                lines.extend(f"        {part}," for part in parts)
                lines.append("    )")
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
    def generate_file(
        docstring_source: str,
        exports: t.StrSequence,
        filtered: Mapping[str, tuple[str, str]],
        inline_constants: t.StrMapping,
        current_pkg: str,
        eager_typevar_names: frozenset[str] = frozenset(),
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

        Returns:
            Complete Python module file as a single string.

        """
        tpl = c.Infra.Templates
        lazy_filtered: Mapping[str, tuple[str, str]] = {
            name: val
            for name, val in filtered.items()
            if name not in eager_typevar_names
        }

        # --- determine L0 vs standard ---
        is_l0_typings = current_pkg.startswith(
            c.Infra.Packages.CORE_UNDERSCORE + "._typings",
        )

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

        # --- TYPE_CHECKING block ---
        groups: Mapping[str, MutableSequence[tuple[str, str]]] = defaultdict(list)
        for export_name in sorted(lazy_filtered):
            mod, attr = lazy_filtered[export_name]
            groups[mod].append((export_name, attr))

        type_checking_lines = FlextInfraCodegenGeneration.generate_type_checking(
            groups,
            include_flext_types=not is_l0_typings,
        )

        # --- body (inline constants + _LAZY_IMPORTS + __all__) from .j2 ---
        lazy_entries = [
            (exp, lazy_filtered[exp][0], lazy_filtered[exp][1])
            for exp in sorted(exports)
            if exp in lazy_filtered
        ]
        body: str = _render(
            _ENV.get_template(tpl.BODY),
            type_checking_lines="\n".join(type_checking_lines),
            inline_constants=sorted(inline_constants.items()),
            lazy_entries=lazy_entries,
            exports=sorted(exports),
        )
        out.extend(body.splitlines())
        out.extend(["", ""])

        # --- getattr block (from .j2 template) ---
        getattr_name = tpl.GETATTR_L0 if is_l0_typings else tpl.GETATTR_STANDARD
        getattr_rendered: str = _render(_ENV.get_template(getattr_name))
        out.extend(getattr_rendered.splitlines())

        return "\n".join(out)


__all__ = ["FlextInfraCodegenGeneration"]
