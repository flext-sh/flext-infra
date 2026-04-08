"""Copyright (c) 2025 FLEXT Team. All rights reserved.

SPDX-License-Identifier: MIT.
"""

from __future__ import annotations

import operator
from collections import defaultdict
from collections.abc import Mapping, MutableSequence
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from flext_infra import (
    FlextInfraUtilitiesCodegenGeneration,
    c,
    p,
    t,
)


class FlextInfraCodegenGeneration:
    """Generate Python module files with lazy import infrastructure."""

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
                    FlextInfraUtilitiesCodegenGeneration.format_module_alias_import(
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
            lines.extend(
                FlextInfraUtilitiesCodegenGeneration.format_import(indent, mod, parts)
            )

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

        collapsed = FlextInfraUtilitiesCodegenGeneration.collapse_to_children(
            groups, child_packages
        )
        children = set(child_packages or [])
        root_name = "" if not local_package_root else local_package_root.split(".")[0]

        lines: MutableSequence[str] = ["if _t.TYPE_CHECKING:"]
        if (
            include_flext_types
            and not FlextInfraUtilitiesCodegenGeneration.has_flext_types(collapsed)
        ):
            lines.append("    from flext_core import FlextTypes")

        external_imports: t.MutableStrSequenceMapping = defaultdict(list)

        sorted_mods = sorted(collapsed, key=str.lower)
        prev_top: str | None = None
        for mod in sorted_mods:
            top = mod.split(".")[0]
            if prev_top is not None and top != prev_top:
                lines.append("")
            FlextInfraUtilitiesCodegenGeneration.emit_type_checking_module(
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
                lines.extend(
                    FlextInfraUtilitiesCodegenGeneration.format_type_checking_module_alias_import(
                        "    ",
                        mod,
                        export_name,
                    ),
                )
            if symbol_parts:
                lines.extend(
                    FlextInfraUtilitiesCodegenGeneration.format_import(
                        "    ", mod, symbol_parts
                    )
                )

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
        publish_all = FlextInfraUtilitiesCodegenGeneration.is_root_namespace_package(
            current_pkg
        )
        published_exports = (
            FlextInfraUtilitiesCodegenGeneration.build_published_exports(
                exports,
                lazy_filtered,
            )
        )
        type_checking_filtered: t.Infra.LazyImportMap = {
            name: val
            for name, val in lazy_filtered.items()
            if val[0] not in wildcard_runtime_module_set
        }
        children_lazy = tuple(child_packages_for_lazy or ())
        rendered_child_module_paths = tuple(
            FlextInfraUtilitiesCodegenGeneration.compact_lazy_module_path(
                current_pkg,
                child_module_path,
            )
            for child_module_path in children_lazy
        )
        eager_export_names = [
            name for name in published_exports if name not in lazy_filtered
        ]
        out: MutableSequence[str] = [c.Infra.AUTOGEN_HEADER]
        docstring_pkg = (
            current_pkg if publish_all else current_pkg.rsplit(".", maxsplit=1)[-1]
        )
        out.extend([
            FlextInfraUtilitiesCodegenGeneration.format_root_package_docstring(
                docstring_pkg
            ),
            "",
        ])

        preamble_template = FlextInfraCodegenGeneration._get_template(
            c.Infra.Templates.PREAMBLE_STANDARD
        )
        preamble: str = preamble_template.render(
            include_merge_helper=bool(children_lazy),
        )
        out.extend(preamble.splitlines())

        out.append("")

        runtime_groups = FlextInfraUtilitiesCodegenGeneration.group_imports(
            runtime_imports
        )
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

        lazy_entries = FlextInfraUtilitiesCodegenGeneration.build_lazy_entries(
            published_exports,
            lazy_filtered,
            current_pkg,
            children_lazy,
        )
        type_checking_lines = (
            FlextInfraCodegenGeneration.generate_type_checking(
                FlextInfraUtilitiesCodegenGeneration.group_imports(
                    type_checking_filtered
                ),
                include_flext_types=False,
                child_packages=(
                    ()
                    if FlextInfraUtilitiesCodegenGeneration.is_root_namespace_package(
                        current_pkg
                    )
                    else child_packages_for_tc or ()
                ),
                local_package_root=current_pkg,
            )
            if publish_all
            else ()
        )

        body_template = FlextInfraCodegenGeneration._get_template(
            c.Infra.Templates.BODY
        )
        body: str = body_template.render(
            runtime_import_lines="\n".join(runtime_import_block),
            child_module_paths=rendered_child_module_paths,
            excluded_lazy_names=sorted(
                c.Infra.INFRA_ONLY_EXPORTS,
            ),
            inline_constants=sorted(inline_constants.items()),
            eager_export_names=eager_export_names,
            lazy_entries=lazy_entries,
            type_checking_lines="\n".join(type_checking_lines),
            exports=published_exports,
            publish_all=publish_all,
        )
        out.extend(body.splitlines())
        out.append("")

        getattr_template = FlextInfraCodegenGeneration._get_template(
            c.Infra.Templates.GETATTR_STANDARD
        )
        getattr_rendered: str = getattr_template.render(
            eager_export_names=eager_export_names,
            publish_all=publish_all,
        )
        out.extend(getattr_rendered.splitlines())

        return "\n".join(out) + "\n"


__all__ = ["FlextInfraCodegenGeneration"]
