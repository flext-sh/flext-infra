"""Copyright (c) 2025 FLEXT Team. All rights reserved.

SPDX-License-Identifier: MIT.
"""

from __future__ import annotations

import operator
from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path

from flext_infra import c


class FlextInfraCodegenGeneration:
    """Generate Python module files with lazy import infrastructure."""

    @staticmethod
    def resolve_unmapped(
        exports_set: set[str],
        filtered: dict[str, tuple[str, str]],
        current_pkg: str,
        pkg_dir: Path,
    ) -> None:
        """Resolve unmapped exports by matching them to known suffixes or version files.

        Updates the filtered dictionary in-place by resolving unmapped aliases to their
        actual module and attribute paths. Handles special cases like `__version__` and
        `__version_info__`.

        Args:
            exports_set: Set of all exported names.
            filtered: Dictionary mapping export names to (module_path, attr_name) tuples.
            current_pkg: Current package name for resolving version files.
            pkg_dir: Package directory path to check for `__version__.py`.

        """
        unmapped = exports_set - set(filtered)
        if not unmapped:
            return
        for alias in sorted(unmapped):
            if alias in c.Infra.ALIAS_TO_SUFFIX:
                suffix = c.Infra.ALIAS_TO_SUFFIX[alias]
                for name, (mod, _) in filtered.items():
                    if name.endswith(suffix) and len(name) > 1:
                        filtered[alias] = (mod, name)
                        break
            elif alias == "__version__" and current_pkg:
                ver_file = pkg_dir / "__version__.py"
                if ver_file.exists():
                    filtered["__version__"] = (
                        f"{current_pkg}.__version__",
                        "__version__",
                    )
            elif alias == "__version_info__" and current_pkg:
                ver_file = pkg_dir / "__version__.py"
                if ver_file.exists():
                    filtered["__version_info__"] = (
                        f"{current_pkg}.__version__",
                        "__version_info__",
                    )

    @staticmethod
    def _render_type_checking_module(mod: str, current_pkg: str) -> str:
        """Render module path for TYPE_CHECKING imports.

        Converts module paths to relative imports for test packages to enable
        static analysis without requiring an installed top-level ``tests`` package.

        Args:
            mod: Module path to render.
            current_pkg: Current package name to determine relative import strategy.

        Returns:
            Rendered module path (absolute or relative).

        """
        if not current_pkg.startswith("tests"):
            return mod
        pkg_parts = current_pkg.split(".")
        mod_parts = mod.split(".")
        if not mod_parts or mod_parts[0] != "tests":
            return mod
        common = 0
        limit = min(len(pkg_parts), len(mod_parts))
        while common < limit and pkg_parts[common] == mod_parts[common]:
            common += 1
        if common == 0:
            return mod
        up_levels = len(pkg_parts) - common
        prefix = "." * (up_levels + 1)
        remainder = ".".join(mod_parts[common:])
        if not remainder:
            return prefix
        return f"{prefix}{remainder}"

    @staticmethod
    def generate_type_checking(
        groups: Mapping[str, list[tuple[str, str]]],
        *,
        include_flext_types: bool = True,
        current_pkg: str = "",
    ) -> list[str]:
        """Generate TYPE_CHECKING import block for type hints.

        Creates Python code for conditional imports guarded by TYPE_CHECKING,
        organizing imports by module with proper spacing between top-level packages.

        Args:
            groups: Mapping of module paths to lists of (export_name, attr_name) tuples.
            include_flext_types: Whether to import FlextTypes from flext_core.
            current_pkg: Current package name for module path rendering.

        Returns:
            List of code lines forming the TYPE_CHECKING block.

        """
        lines: list[str] = ["if TYPE_CHECKING:"]
        if include_flext_types:
            lines.append("    from flext_core.typings import FlextTypes")
        if not groups:
            return lines if len(lines) > 1 else []

        def _emit_module(mod: str) -> None:
            items = groups[mod]
            rendered_mod = FlextInfraCodegenGeneration._render_type_checking_module(
                mod,
                current_pkg,
            )
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
            parts: list[str] = []
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
        exports: list[str],
        filtered: Mapping[str, tuple[str, str]],
        inline_constants: Mapping[str, str],
        current_pkg: str,
        eager_typevar_names: frozenset[str] = frozenset(),
    ) -> str:
        """Generate complete module file with lazy imports and type hints.

        Assembles all components (docstring, imports, lazy import table, __all__,
        __getattr__, __dir__) into a single module file. Handles special cases
        for core internal packages and L0 typings modules.

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
        lazy_filtered: dict[str, tuple[str, str]] = {
            name: val
            for name, val in filtered.items()
            if name not in eager_typevar_names
        }
        groups: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for export_name in sorted(lazy_filtered):
            mod, attr = lazy_filtered[export_name]
            groups[mod].append((export_name, attr))
        out: list[str] = [c.Infra.AUTOGEN_HEADER]
        if docstring_source:
            out.extend([docstring_source, ""])
        is_core_internal = current_pkg.startswith(
            c.Infra.Packages.CORE_UNDERSCORE + ".",
        )
        is_l0_typings = current_pkg.startswith(
            c.Infra.Packages.CORE_UNDERSCORE + "._typings",
        )
        if is_l0_typings:
            out.extend([
                "# L0-OVERRIDE — inline lazy to avoid circular: _typings -> _utilities.lazy -> typings -> _typings",
                "from __future__ import annotations",
                "",
                "import importlib",
                "import sys",
                "",
                "from typing import TYPE_CHECKING",
            ])
        elif current_pkg == c.Infra.Packages.CORE_UNDERSCORE or is_core_internal:
            lazy_import = (
                "from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr"
            )
            out.extend([
                "from __future__ import annotations",
                "",
                "from typing import TYPE_CHECKING",
                "",
                lazy_import,
            ])
        else:
            lazy_import = (
                "from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr"
            )
            out.extend([
                "from __future__ import annotations",
                "",
                "from typing import TYPE_CHECKING",
                "",
                lazy_import,
            ])
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
        out.extend(
            FlextInfraCodegenGeneration.generate_type_checking(
                groups,
                include_flext_types=not is_l0_typings,
                current_pkg=current_pkg,
            ),
        )
        out.append("")
        for name, value in sorted(inline_constants.items()):
            out.append(f'{name} = "{value}"')
        if inline_constants:
            out.append("")
        out.extend([
            "_LAZY_IMPORTS: dict[str, tuple[str, str]] = {",
        ])
        for exp in sorted(exports):
            if exp in lazy_filtered:
                mod, attr = lazy_filtered[exp]
                out.append(f'    "{exp}": ("{mod}", "{attr}"),')
        out.extend(["}", ""])
        out.append("__all__ = [")
        out.extend(f'    "{exp}",' for exp in sorted(exports))
        out.extend(["]", "", ""])
        if is_l0_typings:
            out.extend(FlextInfraCodegenGeneration._getattr_block_l0())
        else:
            out.extend(FlextInfraCodegenGeneration._getattr_block_standard())
        return "\n".join(out)

    @staticmethod
    def _getattr_block_standard() -> list[str]:
        """Generate standard __getattr__ and __dir__ implementation block.

        Creates PEP 562 module-level __getattr__ for lazy loading with a
        persistent ``_LAZY_CACHE`` for performance, and __dir__ for attribute
        discovery, using the lazy_getattr utility.

        Returns:
            List of code lines implementing lazy attribute access with caching.

        """
        return [
            "_LAZY_CACHE: dict[str, object] = {}",
            "",
            "",
            "def __getattr__(name: str) -> FlextTypes.ModuleExport:",
            '    """Lazy-load module attributes on first access (PEP 562).',
            "",
            "    A local cache ``_LAZY_CACHE`` persists resolved objects across repeated",
            "    accesses during process lifetime.",
            "",
            "    Args:",
            "        name: Attribute name requested by dir()/import.",
            "",
            "    Returns:",
            "        Lazy-loaded module export type.",
            "",
            "    Raises:",
            "        AttributeError: If attribute not registered.",
            '    """',
            "    if name in _LAZY_CACHE:",
            "        return _LAZY_CACHE[name]",
            "",
            "    value = lazy_getattr(name, _LAZY_IMPORTS, globals(), __name__)",
            "    _LAZY_CACHE[name] = value",
            "    return value",
            "",
            "",
            "def __dir__() -> list[str]:",
            '    """Return list of available attributes for dir() and autocomplete.',
            "",
            "    Returns:",
            "        List of public names from module exports.",
            '    """',
            "    return sorted(__all__)",
            "",
            "",
            "cleanup_submodule_namespace(__name__, _LAZY_IMPORTS)",
        ]

    @staticmethod
    def _getattr_block_l0() -> list[str]:
        """Generate L0 typings module __getattr__ and __dir__ implementation block.

        Creates custom __getattr__ for L0 typings modules to avoid circular imports
        while maintaining lazy loading. Cleans up submodule namespace references
        to prevent import confusion.

        Returns:
            List of code lines implementing L0-specific lazy attribute access.

        """
        return [
            "def __getattr__(name: str) -> type:",
            "    if name in _LAZY_IMPORTS:",
            "        module_path, attr_name = _LAZY_IMPORTS[name]",
            "        module = importlib.import_module(module_path)",
            "        value = getattr(module, attr_name)",
            "        globals()[name] = value",
            "        return value",
            '    msg = f"module {__name__!r} has no attribute {name!r}"',
            "    raise AttributeError(msg)",
            "",
            "",
            "def __dir__() -> list[str]:",
            "    return sorted(__all__)",
            "",
            "",
            "_current = sys.modules.get(__name__)",
            "if _current is not None:",
            '    _parts = __name__.split(".")',
            "    for _mod_path, _ in _LAZY_IMPORTS.values():",
            "        if _mod_path:",
            '            _mp = _mod_path.split(".")',
            "            if len(_mp) > len(_parts) and _mp[: len(_parts)] == _parts:",
            "                _sub = getattr(_current, _mp[len(_parts)], None)",
            "                if _sub is not None and isinstance(_sub, type(sys)):",
            "                    delattr(_current, _mp[len(_parts)])",
        ]


__all__ = ["FlextInfraCodegenGeneration"]
