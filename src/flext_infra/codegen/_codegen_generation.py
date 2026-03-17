from __future__ import annotations

import operator
from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path

from flext_infra import c
from flext_infra.codegen._codegen_templates import FlextInfraCodegenTemplates


class FlextInfraCodegenGeneration(FlextInfraCodegenTemplates):
    @staticmethod
    def resolve_unmapped(
        exports_set: set[str],
        filtered: dict[str, tuple[str, str]],
        current_pkg: str,
        pkg_dir: Path,
    ) -> None:
        unmapped = exports_set - set(filtered)
        if not unmapped:
            return
        for alias in sorted(unmapped):
            if alias in c.Infra.Codegen.ALIAS_TO_SUFFIX:
                suffix = c.Infra.Codegen.ALIAS_TO_SUFFIX[alias]
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
    def generate_type_checking(
        groups: Mapping[str, list[tuple[str, str]]],
        *,
        include_flext_types: bool = True,
    ) -> list[str]:
        lines: list[str] = ["if TYPE_CHECKING:"]
        if include_flext_types:
            lines.append("    from flext_core.typings import FlextTypes")
        if not groups:
            return lines if len(lines) > 1 else []

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
            line = f"    from {mod} import {joined}"
            if len(line) > c.Infra.Codegen.MAX_LINE_LENGTH:
                lines.append(f"    from {mod} import (")
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
        lazy_filtered: dict[str, tuple[str, str]] = {
            name: val
            for name, val in filtered.items()
            if name not in eager_typevar_names
        }
        groups: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for export_name in sorted(lazy_filtered):
            mod, attr = lazy_filtered[export_name]
            groups[mod].append((export_name, attr))
        out: list[str] = [c.Infra.Codegen.AUTOGEN_HEADER]
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
            lazy_import = "from flext_core._utilities.lazy import cleanup_submodule_namespace, lazy_getattr"
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
            if len(eager_line) > c.Infra.Codegen.MAX_LINE_LENGTH:
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


__all__ = ["FlextInfraCodegenGeneration"]
