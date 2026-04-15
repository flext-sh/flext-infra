"""Copyright (c) 2025 FLEXT Team. All rights reserved.

SPDX-License-Identifier: MIT.
"""

from __future__ import annotations

import operator
from collections import defaultdict
from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from flext_infra import (
    c,
    p,
    t,
)


class FlextInfraCodegenGeneration:
    """Generate Python module files with lazy import infrastructure."""

    @staticmethod
    def _is_module_or_package_export(attr_name: str) -> bool:
        return not attr_name

    @staticmethod
    def _is_root_namespace_package(current_pkg: str) -> bool:
        return bool(current_pkg) and "." not in current_pkg

    @staticmethod
    def _is_local_module(mod: str, root_name: str) -> bool:
        return (
            mod.startswith(".")
            or not root_name
            or mod.split(".", maxsplit=1)[0] == root_name
        )

    @staticmethod
    def _compact_lazy_module_path(current_pkg: str, mod: str) -> str:
        if not current_pkg:
            return mod
        if mod.startswith("_"):
            return f".{mod}"
        if mod == current_pkg:
            return "."
        prefix = f"{current_pkg}."
        if mod.startswith(prefix):
            return f".{mod.removeprefix(prefix)}"
        return mod

    @staticmethod
    def _normalize_type_checking_module_path(
        mod: str,
        local_package_root: str | None,
    ) -> str:
        if not local_package_root or not mod.startswith("_"):
            return mod
        return f"{local_package_root.split('.', maxsplit=1)[0]}.{mod}"

    @staticmethod
    def _format_root_package_docstring(current_pkg: str) -> str:
        label = current_pkg.replace("_", " ").replace("-", " ").strip()
        package_name = " ".join(word.capitalize() for word in label.split())
        return f'"""{package_name} package."""'

    @staticmethod
    def _format_import(
        indent: str,
        mod: str,
        parts: t.StrSequence,
    ) -> t.StrSequence:
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
    def _format_module_alias_import(
        indent: str,
        mod: str,
        export_name: str,
    ) -> str:
        if mod.startswith(".") and mod != ".":
            parent_mod, _, child_name = mod.rpartition(".")
            return (
                f"{indent}from {parent_mod or '.'} import {child_name} as {export_name}"
            )
        return f"{indent}import {mod} as {export_name}"

    @staticmethod
    def _format_type_checking_module_alias_import(
        indent: str,
        mod: str,
        export_name: str,
    ) -> t.StrSequence:
        return (
            FlextInfraCodegenGeneration._format_module_alias_import(
                indent,
                mod,
                export_name,
            ),
        )

    @staticmethod
    def _group_imports(
        import_map: t.Infra.LazyImportMap,
    ) -> Mapping[str, MutableSequence[t.Infra.StrPair]]:
        groups: dict[str, list[t.Infra.StrPair]] = defaultdict(list)
        for export_name in sorted(import_map):
            mod, attr = import_map[export_name]
            groups[mod].append((export_name, attr))
        return groups

    @staticmethod
    def _collapse_to_children(
        groups: Mapping[str, t.Infra.StrPairSequence],
        child_packages: t.StrSequence | None,
    ) -> Mapping[str, MutableSequence[t.Infra.StrPair]]:
        sorted_children: list[str] = sorted(
            set(child_packages or []),
            key=len,
            reverse=True,
        )
        collapsed: dict[str, list[t.Infra.StrPair]] = defaultdict(list)
        for mod, items in groups.items():
            target = mod
            for cp in sorted_children:
                if mod.startswith(cp + ".") or mod == cp:
                    target = cp
                    break
            collapsed[target].extend(items)
        return collapsed

    @staticmethod
    def _has_flext_types(
        collapsed: Mapping[str, t.Infra.StrPairSequence],
    ) -> bool:
        return any(
            export_name == "FlextTypes"
            for items in collapsed.values()
            for export_name, _ in items
        )

    @staticmethod
    def _type_checking_sort_key(
        mod: str,
        local_package_root: str | None,
    ) -> t.Infra.StrPair:
        top = mod.split(".", maxsplit=1)[0]
        if local_package_root == "tests":
            test_order = {"flext_tests": "0", "flext_infra": "1", "tests": "2"}
            return (test_order.get(top, "1"), mod.lower())
        return ("0", mod.lower())

    @staticmethod
    def _should_skip_type_checking_module_export(
        mod: str,
        export_name: str,
        attr_name: str,
        root_name: str,
    ) -> bool:
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
    def _emit_type_checking_module(
        mod: str,
        items: t.Infra.StrPairSequence,
        root_name: str,
        lines: MutableSequence[str],
    ) -> None:
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
            if FlextInfraCodegenGeneration._should_skip_type_checking_module_export(
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

        for export_name in deduped_aliases:
            lines.extend(
                FlextInfraCodegenGeneration._format_type_checking_module_alias_import(
                    "    ",
                    mod,
                    export_name,
                ),
            )
        if deduped_parts:
            lines.extend(
                FlextInfraCodegenGeneration._format_import("    ", mod, deduped_parts)
            )

    @staticmethod
    def _build_lazy_entries(
        exports: t.StrSequence,
        lazy_filtered: t.Infra.LazyImportMap,
        current_pkg: str,
        children_lazy: tuple[str, ...],
        *,
        include_module_exports: bool = False,
    ) -> Sequence[tuple[str, str, str]]:
        child_aliases = set(children_lazy)
        entries: MutableSequence[tuple[str, str, str]] = []
        for exp in exports:
            if exp not in lazy_filtered:
                continue
            mod, attr = lazy_filtered[exp]
            if (
                FlextInfraCodegenGeneration._is_module_or_package_export(attr)
                and not include_module_exports
            ):
                continue
            compact_mod = FlextInfraCodegenGeneration._compact_lazy_module_path(
                current_pkg,
                mod,
            )
            # Keep module-level child package exports collapsed via merge_lazy_imports,
            # but publish symbol exports from child submodules explicitly at root.
            if mod in child_aliases and not attr:
                continue
            entries.append((exp, compact_mod, attr))
        return entries

    @staticmethod
    def _group_lazy_entries(
        lazy_entries: Sequence[tuple[str, str, str]],
    ) -> tuple[
        Sequence[tuple[str, t.StrSequence]],
        Sequence[tuple[str, t.Infra.StrPairSequence]],
    ]:
        module_groups: dict[str, list[str]] = defaultdict(list)
        alias_groups: dict[str, list[t.Infra.StrPair]] = defaultdict(list)
        for export_name, mod, attr_name in lazy_entries:
            if not attr_name or attr_name == export_name:
                module_groups[mod].append(export_name)
            else:
                alias_groups[mod].append((export_name, attr_name))
        module_items = tuple(
            (mod, tuple(sorted(names)))
            for mod, names in sorted(
                module_groups.items(), key=lambda item: item[0].lower()
            )
        )
        alias_items = tuple(
            (mod, tuple(sorted(pairs)))
            for mod, pairs in sorted(
                alias_groups.items(), key=lambda item: item[0].lower()
            )
        )
        return module_items, alias_items

    @staticmethod
    def _build_published_exports(
        exports: t.StrSequence,
        lazy_filtered: t.Infra.LazyImportMap,
    ) -> t.StrSequence:
        return tuple(
            export_name
            for export_name in exports
            if export_name not in lazy_filtered
            or not FlextInfraCodegenGeneration._is_module_or_package_export(
                lazy_filtered[export_name][1]
            )
        )

    @staticmethod
    def _collapse_blank_runs(lines: t.StrSequence) -> t.StrSequence:
        normalized: MutableSequence[str] = []
        previous_blank = False
        for line in lines:
            current_blank = not line
            if current_blank and previous_blank:
                continue
            normalized.append(line)
            previous_blank = current_blank
        return tuple(normalized)

    @staticmethod
    def _build_env() -> t.Infra.JinjaEnvironment:
        """Create a Jinja2 environment for codegen templates."""
        template_root = Path(__file__).resolve().parent.parent / "templates"
        return Environment(
            loader=FileSystemLoader(str(template_root)),
            trim_blocks=False,
            lstrip_blocks=False,
            keep_trailing_newline=False,
            undefined=StrictUndefined,
            autoescape=select_autoescape(),
        )

    _env: t.Infra.JinjaEnvironment | None = None

    @classmethod
    def _get_template(cls, name: str) -> p.Infra.RenderableTemplate:
        """Return a template narrowed to the local render protocol."""
        if cls._env is None:
            cls._env = cls._build_env()
        return cls._env.get_template(name)

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
                lines.append(
                    FlextInfraCodegenGeneration._format_module_alias_import(
                        indent, mod, export_name
                    )
                )
            if not sorted_items:
                return
            parts: t.StrSequence = [
                export_name
                if export_name == attr_name
                else f"{attr_name} as {export_name}"
                for export_name, attr_name in sorted_items
            ]
            lines.extend(FlextInfraCodegenGeneration._format_import(indent, mod, parts))

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
            return ("if _t.TYPE_CHECKING:", "    from flext_core import FlextTypes")

        normalized_groups = {
            FlextInfraCodegenGeneration._normalize_type_checking_module_path(
                mod,
                local_package_root,
            ): items
            for mod, items in groups.items()
        }
        collapsed = FlextInfraCodegenGeneration._collapse_to_children(
            normalized_groups, child_packages
        )
        root_name = "" if not local_package_root else local_package_root.split(".")[0]

        lines: MutableSequence[str] = ["if _t.TYPE_CHECKING:"]
        if include_flext_types and not FlextInfraCodegenGeneration._has_flext_types(
            collapsed
        ):
            lines.append("    from flext_core import FlextTypes")

        sorted_mods = sorted(
            collapsed,
            key=lambda mod: FlextInfraCodegenGeneration._type_checking_sort_key(
                mod,
                local_package_root,
            ),
        )
        prev_top: str | None = None
        for mod in sorted_mods:
            top = mod.split(".")[0]
            if (
                local_package_root == "tests"
                and prev_top == "flext_tests"
                and top != prev_top
            ):
                lines.append("")
            FlextInfraCodegenGeneration._emit_type_checking_module(
                mod,
                collapsed[mod],
                root_name,
                lines,
            )
            prev_top = top

        return () if len(lines) == 1 else lines

    @staticmethod
    def generate_file(
        exports: t.StrSequence,
        filtered: t.Infra.LazyImportMap,
        inline_constants: t.StrMapping,
        current_pkg: str,
        eager_imports: t.Infra.LazyImportMap | None = None,
        wildcard_runtime_modules: t.StrSequence | None = None,
        child_packages_for_lazy: t.StrSequence | None = None,
        child_packages_for_tc: t.StrSequence | None = None,
    ) -> str:
        """Generate complete module file with lazy imports and type hints.

        Args:
            exports: List of all exported names.
            filtered: Mapping of export names to (module_path, attr_name) tuples.
            inline_constants: Mapping of constant names to their string values.
            current_pkg: Current package name for import strategy selection.
            eager_imports: Runtime imports that must exist eagerly in module globals.
            child_packages_for_lazy: Child packages for lazy import collapsing.
            child_packages_for_tc: Child packages for TYPE_CHECKING collapsing.

        Returns:
            Complete Python module file as a single string.

        """
        runtime_imports: t.Infra.LazyImportMap = eager_imports or {}
        lazy_filtered: t.Infra.LazyImportMap = dict(filtered)
        wildcard_runtime_module_set = frozenset(wildcard_runtime_modules or ())
        publish_all = FlextInfraCodegenGeneration._is_root_namespace_package(
            current_pkg
        )
        published_exports = (
            FlextInfraCodegenGeneration._build_published_exports(
                exports,
                lazy_filtered,
            )
            if publish_all
            else tuple(sorted(exports))
        )
        type_checking_filtered: t.Infra.LazyImportMap = {
            name: val
            for name, val in lazy_filtered.items()
            if val[0] not in wildcard_runtime_module_set
        }
        children_lazy = tuple(child_packages_for_lazy or ())
        rendered_child_module_paths = tuple(
            FlextInfraCodegenGeneration._compact_lazy_module_path(
                current_pkg,
                child_module_path,
            )
            for child_module_path in children_lazy
        )
        use_merge_lazy_imports = bool(rendered_child_module_paths)
        eager_export_names = [
            name for name in published_exports if name not in lazy_filtered
        ]
        runtime_groups = FlextInfraCodegenGeneration._group_imports(runtime_imports)
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

        lazy_entries = FlextInfraCodegenGeneration._build_lazy_entries(
            published_exports,
            lazy_filtered,
            current_pkg,
            children_lazy,
            include_module_exports=not publish_all,
        )
        lazy_module_groups, lazy_alias_groups = (
            FlextInfraCodegenGeneration._group_lazy_entries(lazy_entries)
        )
        type_checking_lines = (
            FlextInfraCodegenGeneration.generate_type_checking(
                FlextInfraCodegenGeneration._group_imports(type_checking_filtered),
                include_flext_types=False,
                child_packages=(
                    ()
                    if FlextInfraCodegenGeneration._is_root_namespace_package(
                        current_pkg
                    )
                    else child_packages_for_tc or ()
                ),
                local_package_root=current_pkg,
            )
            if publish_all
            else ()
        )

        out: MutableSequence[str] = [c.Infra.AUTOGEN_HEADER]
        docstring_pkg = (
            current_pkg if publish_all else current_pkg.rsplit(".", maxsplit=1)[-1]
        )
        out.extend([
            FlextInfraCodegenGeneration._format_root_package_docstring(docstring_pkg),
            "",
        ])

        preamble_template = FlextInfraCodegenGeneration._get_template(
            c.Infra.TEMPLATE_PREAMBLE_STANDARD
        )
        preamble: str = preamble_template.render(
            type_checking_enabled=bool(type_checking_lines),
            use_merge_lazy_imports=use_merge_lazy_imports,
        )
        out.extend(preamble.splitlines())

        if not runtime_import_block:
            out.append("")

        body_template = FlextInfraCodegenGeneration._get_template(c.Infra.TEMPLATE_BODY)
        body: str = body_template.render(
            runtime_import_lines="\n".join(runtime_import_block),
            child_module_paths=rendered_child_module_paths,
            excluded_lazy_names=sorted(
                c.Infra.INFRA_ONLY_EXPORTS,
            ),
            use_merge_lazy_imports=use_merge_lazy_imports,
            inline_constants=sorted(inline_constants.items()),
            eager_export_names=eager_export_names,
            lazy_module_groups=lazy_module_groups,
            lazy_alias_groups=lazy_alias_groups,
            type_checking_lines="\n".join(type_checking_lines),
            exports=published_exports,
            publish_all=publish_all,
        )
        body_lines = body.splitlines()
        if body_lines and not body_lines[0]:
            body_lines = body_lines[1:]
        out.extend(FlextInfraCodegenGeneration._collapse_blank_runs(body_lines))
        out.append("")

        getattr_template = FlextInfraCodegenGeneration._get_template(
            c.Infra.TEMPLATE_GETATTR_STANDARD
        )
        getattr_rendered: str = getattr_template.render(
            eager_export_names=eager_export_names,
            exports=published_exports,
            publish_all=publish_all,
        )
        out.extend(getattr_rendered.splitlines())

        return "\n".join(out) + "\n"


__all__: list[str] = ["FlextInfraCodegenGeneration"]
