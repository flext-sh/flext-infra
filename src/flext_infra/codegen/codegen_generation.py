"""Copyright (c) 2025 FLEXT Team. All rights reserved.

SPDX-License-Identifier: MIT.
"""

from __future__ import annotations

import operator
from collections import defaultdict
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from flext_infra import (
    c,
    p,
    t,
)

type _LazyEntryContext = tuple[str, frozenset[str], bool]


class FlextInfraCodegenGeneration:
    """Generate Python module files with lazy import infrastructure."""

    @staticmethod
    def _uses_direct_bootstrap(current_pkg: str) -> bool:
        """Return whether a package bootstraps the lazy runtime itself."""
        return current_pkg in {"flext_core._lazy_parts", "flext_core._typings"}

    @staticmethod
    def _uses_static_child_map(current_pkg: str) -> bool:
        """Return whether child exports are already fully enumerated statically."""
        return current_pkg == "flext_core" or current_pkg.startswith("flext_core.")

    @staticmethod
    def _is_module_or_package_export(attr_name: str) -> bool:
        """Is module or package export."""
        return not attr_name

    @staticmethod
    def _is_private_subpackage_source(module_path: str) -> bool:
        """Whether a symbol's canonical source lives in a ``_``-private subpackage.

        Canonical FLEXT owners such as ``_models``, ``_constants``, and
        ``_utilities`` are allowed root sources when their symbols are declared
        explicitly. Non-canonical private implementation packages such as
        ``_internal`` remain outside the frozen public facade.
        """
        return any(
            segment.startswith("_")
            and not segment.startswith("__")
            and segment not in c.Infra.LOCAL_INFERRED_SEGMENTS
            for segment in module_path.split(".")[1:]
        )

    @staticmethod
    def _should_publish_root_export(
        export_name: str,
        lazy_filtered: t.LazyAliasMap,
    ) -> bool:
        """Return whether a root export belongs in the frozen ``__all__`` ABI."""
        if export_name in c.Infra.INFRA_ONLY_EXPORTS | c.Infra.PUBLISHED_ALL_EXCLUDE:
            return False
        target = lazy_filtered.get(export_name)
        if target is None:
            return True
        module_path, attr_name = target
        if FlextInfraCodegenGeneration._is_module_or_package_export(attr_name):
            return False
        if not FlextInfraCodegenGeneration._is_private_subpackage_source(module_path):
            return True
        return (
            export_name in c.Infra.ALIAS_NAMES
            or export_name in c.Infra.TEST_RUNTIME_ALIAS_TARGETS
            or "_fixtures" in module_path.split(".")
        )

    @staticmethod
    def _is_root_namespace_package(current_pkg: str) -> bool:
        """Is root namespace package."""
        return bool(current_pkg) and "." not in current_pkg

    @staticmethod
    def _is_public_api_root_namespace(current_pkg: str) -> bool:
        """Return whether ``current_pkg`` is a generated public package ABI root."""
        return (
            FlextInfraCodegenGeneration._is_root_namespace_package(current_pkg)
            and current_pkg not in c.Infra.NON_PUBLIC_LAZY_ROOTS
        )

    @staticmethod
    def _is_local_module(mod: str, root_name: str) -> bool:
        """Is local module."""
        return (
            mod.startswith(".")
            or not root_name
            or mod.split(".", maxsplit=1)[0] == root_name
        )

    @staticmethod
    def _compact_lazy_module_path(current_pkg: str, mod: str) -> str:
        """Compact lazy module path."""
        if not current_pkg:
            result = mod
        elif mod.startswith("_"):
            result = f".{mod}"
        elif mod == current_pkg:
            result = "."
        elif mod.startswith(f"{current_pkg}."):
            result = f".{mod.removeprefix(f'{current_pkg}.')}"
        else:
            root_pkg = current_pkg.split(".", maxsplit=1)[0]
            first_segment = mod.split(".", maxsplit=1)[0]
            internal_segments = frozenset(current_pkg.split(".")[1:])
            if (
                first_segment == root_pkg
                or internal_segments & c.Infra.LOCAL_INFERRED_SEGMENTS
            ):
                result = mod
            elif first_segment in internal_segments or (
                current_pkg == root_pkg
                and "." in mod
                and first_segment in c.Infra.LOCAL_INFERRED_SEGMENTS
            ):
                result = f".{mod}"
            else:
                result = mod
        return result

    @staticmethod
    def _normalize_type_checking_module_path(
        mod: str,
        local_package_root: str | None,
    ) -> str:
        """Normalize type checking module path."""
        if not local_package_root:
            result = mod
        else:
            root_pkg = local_package_root.split(".", maxsplit=1)[0]
            first_segment = mod.split(".", maxsplit=1)[0]
            internal_segments = frozenset(local_package_root.split(".")[1:])
            if first_segment == root_pkg:
                result = mod
            elif (
                mod.startswith("_")
                or first_segment in internal_segments
                or (
                    local_package_root == root_pkg
                    and "." in mod
                    and first_segment in c.Infra.LOCAL_INFERRED_SEGMENTS
                )
            ):
                result = f"{root_pkg}.{mod}"
            else:
                result = mod
        return result

    @staticmethod
    def _reject_non_absolute_import(
        mod: str,
        local_package_root: str | None,
        items: t.StrPairSequence,
    ) -> None:
        """Abort gen init if a TYPE_CHECKING import is not fully-qualified.

        Relative imports are FORBIDDEN in FLEXT source code. The only
        exception is the generated ``_LAZY_IMPORTS`` dict inside
        ``__init__.py`` (which uses ``.submodule`` relative paths).
        TYPE_CHECKING imports must always be absolute.
        """
        if mod.startswith("."):
            exports = ", ".join(name for name, _ in items)
            msg = (
                f"relative import {mod!r} in TYPE_CHECKING block "
                f"(package {local_package_root!r}, exports: {exports}). "
                "FLEXT forbids relative imports in source — "
                "fix the module to use a fully-qualified path"
            )
            raise ValueError(msg)
        if not local_package_root:
            return
        root_pkg = local_package_root.split(".", maxsplit=1)[0]
        first_segment = mod.split(".", maxsplit=1)[0]
        if first_segment == root_pkg:
            return
        # Check if the first segment is an internal subdirectory of the
        # project (matches a non-root segment of local_package_root) but
        # was not fully-qualified. E.g. ``scripts.audit`` when
        # local_package_root is ``flext_quality.docs.scripts`` — the
        # ``scripts`` segment is internal and needs the full path.
        internal_segments = frozenset(local_package_root.split(".")[1:])
        if first_segment not in internal_segments:
            return
        exports = ", ".join(name for name, _ in items)
        msg = (
            f"non-absolute import {mod!r} in TYPE_CHECKING block "
            f"(package {local_package_root!r}, root {root_pkg!r}, "
            f"exports: {exports}). "
            "FLEXT forbids non-absolute imports — "
            "the source module must export via a fully-qualified path "
            f"(expected: {root_pkg}.{mod!s})"
        )
        raise ValueError(msg)

    @staticmethod
    def _format_root_package_docstring(current_pkg: str) -> str:
        """Format root package docstring."""
        label = current_pkg.replace("_", " ").replace("-", " ").strip()
        package_name = " ".join(word.capitalize() for word in label.split())
        return f'"""{package_name} package."""'

    @staticmethod
    def _format_import(
        indent: str,
        mod: str,
        parts: t.StrSequence,
    ) -> t.StrSequence:
        """Format import."""
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
        """Format module alias import."""
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
        """Format type checking module alias import."""
        return (
            FlextInfraCodegenGeneration._format_module_alias_import(
                indent,
                mod,
                export_name,
            ),
        )

    @staticmethod
    def _group_imports(
        import_map: t.LazyAliasMap,
    ) -> t.MappingKV[str, t.MutableSequenceOf[t.StrPair]]:
        """Group imports."""
        groups: dict[str, list[t.StrPair]] = defaultdict(list)
        for export_name in sorted(import_map):
            mod, attr = import_map[export_name]
            groups[mod].append((export_name, attr))
        return groups

    @staticmethod
    def _collapse_to_children(
        groups: t.MappingKV[str, t.StrPairSequence],
        child_packages: t.StrSequence | None,
    ) -> t.MappingKV[str, t.MutableSequenceOf[t.StrPair]]:
        """Collapse to children."""
        sorted_children: list[str] = sorted(
            set(child_packages or []),
            key=len,
            reverse=True,
        )
        collapsed: dict[str, list[t.StrPair]] = defaultdict(list)
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
        collapsed: t.MappingKV[str, t.StrPairSequence],
    ) -> bool:
        """Has flext types."""
        return any(
            export_name == "FlextTypes"
            for items in collapsed.values()
            for export_name, _ in items
        )

    @staticmethod
    def _type_checking_sort_key(
        mod: str,
        local_package_root: str | None,
    ) -> t.StrPair:
        """Type checking sort key."""
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
        """Should skip type checking module export."""
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
        items: t.StrPairSequence,
        root_name: str,
        lines: t.MutableSequenceOf[str],
    ) -> None:
        """Emit type checking module."""
        alias_exports: t.MutableSequenceOf[str] = []
        parts: t.MutableSequenceOf[str] = []
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
            # Emit the redundant-alias re-export form (PEP 484 `X as X`) so type
            # checkers treat non-alias TYPE_CHECKING imports as intentional
            # re-exports. Without it, sub-facades dropped from __all__ by the
            # privacy rule are flagged reportUnusedImport.
            parts.append(f"{attr_name} as {export_name}")

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
        lazy_filtered: t.LazyAliasMap,
        context: _LazyEntryContext,
    ) -> t.SequenceOf[tuple[str, str, str]]:
        """Build lazy entries."""
        current_pkg, child_aliases, include_module_exports = context
        entries: t.MutableSequenceOf[tuple[str, str, str]] = []
        for exp in exports:
            if exp not in lazy_filtered:
                continue
            mod, attr = lazy_filtered[exp]
            module_or_package_export = (
                FlextInfraCodegenGeneration._is_module_or_package_export(attr)
            )
            if module_or_package_export and not include_module_exports:
                continue
            child_package_module = (
                module_or_package_export
                and mod in child_aliases
                and exp == mod.rsplit(".", maxsplit=1)[-1]
            )
            compact_mod = FlextInfraCodegenGeneration._compact_lazy_module_path(
                current_pkg,
                mod,
            )
            # Keep module-level child package exports collapsed via merge_lazy_imports,
            # but publish symbol exports from child submodules explicitly at root.
            if mod in child_aliases and not attr and not child_package_module:
                continue
            entries.append((exp, compact_mod, attr))
        return entries

    @staticmethod
    def _group_lazy_entries(
        lazy_entries: t.SequenceOf[tuple[str, str, str]],
    ) -> tuple[
        t.SequenceOf[t.StrSequencePair],
        t.SequenceOf[t.StrPairSequencePair],
    ]:
        """Group lazy entries."""
        module_groups: dict[str, list[str]] = defaultdict(list)
        alias_groups: dict[str, list[t.StrPair]] = defaultdict(list)
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
        lazy_filtered: t.LazyAliasMap,
    ) -> t.StrSequence:
        """Build published exports."""
        export_candidates = tuple(dict.fromkeys(exports))
        published = tuple(
            export_name
            for export_name in export_candidates
            if FlextInfraCodegenGeneration._should_publish_root_export(
                export_name,
                lazy_filtered,
            )
        )
        alias_order = c.Infra.PUBLIC_ROOT_ALIAS_ORDER
        return tuple(
            export_name
            for _index, export_name in sorted(
                enumerate(published),
                key=FlextInfraCodegenGeneration._public_export_order_key,
            )
            if export_name not in alias_order
        ) + tuple(name for name in alias_order if name in published)

    @staticmethod
    def _public_export_order_key(item: tuple[int, str]) -> tuple[int, int, str]:
        """Order classes before metadata before root aliases."""
        index, export_name = item
        if export_name in c.Infra.PUBLIC_ROOT_ALIAS_ORDER:
            return (2, index, export_name)
        if export_name.startswith("__") and export_name.endswith("__"):
            return (1, index, export_name)
        return (0, index, export_name)

    @staticmethod
    def _collapse_blank_runs(lines: t.StrSequence) -> t.StrSequence:
        """Collapse blank runs."""
        normalized: t.MutableSequenceOf[str] = []
        previous_blank = False
        for line in lines:
            current_blank = not line
            if current_blank and previous_blank:
                continue
            normalized.append(line)
            previous_blank = current_blank
        return tuple(normalized)

    @staticmethod
    def _generate_direct_bootstrap_file(
        exports: t.StrSequence,
        filtered: t.LazyAliasMap,
        inline_constants: t.StrMapping,
        current_pkg: str,
    ) -> str:
        """Generate a direct-import package initializer for lazy bootstrap code."""
        out: t.MutableSequenceOf[str] = [
            c.Infra.AUTOGEN_HEADER,
            FlextInfraCodegenGeneration._format_root_package_docstring(
                current_pkg.rsplit(".", maxsplit=1)[-1],
            ),
            "",
            "from __future__ import annotations",
            "",
        ]
        runtime_groups = FlextInfraCodegenGeneration._group_imports(filtered)
        out.extend(
            FlextInfraCodegenGeneration._generate_import_lines(runtime_groups),
        )
        if runtime_groups:
            out.append("")
        for name, value in sorted(inline_constants.items()):
            out.append(f'{name} = "{value}"')
        if inline_constants:
            out.append("")
        if exports:
            out.append("__all__: list[str] = [")
            out.extend(f'    "{export}",' for export in exports)
            out.append("]")
        out.append("")
        return "\n".join(out)

    @staticmethod
    def _generate_flext_core_root_file() -> str:
        """Generate the flext-core root from its canonical root export map."""
        lines: t.MutableSequenceOf[str] = [
            c.Infra.AUTOGEN_HEADER,
            '"""Flext Core package."""',
            "",
            "from __future__ import annotations",
            "",
            "from typing import TYPE_CHECKING",
            "",
            "from flext_core.__version__ import (",
            "    __author__,",
            "    __author_email__,",
            "    __description__,",
            "    __license__,",
            "    __title__,",
            "    __url__,",
            "    __version__,",
            "    __version_info__,",
            ")",
            "from flext_core._root_exports import (",
            "    ROOT_ALL,",
            "    ROOT_LAZY_MODULES,",
            "    ROOT_METADATA_NAMES,",
            ")",
            "from flext_core.lazy import build_lazy_import_map, install_lazy_exports",
            "",
            "if TYPE_CHECKING:",
            "    from flext_core.constants import FlextConstants, c",
            "    from flext_core.container import FlextContainer",
            "    from flext_core.context import FlextContext",
            "    from flext_core.decorators import FlextDecorators, d",
            "    from flext_core.dispatcher import FlextDispatcher",
            "    from flext_core.exceptions import FlextExceptions, e",
            "    from flext_core.handlers import FlextHandlers, h",
            "    from flext_core.lazy import FlextLazy",
            "    from flext_core.loggings import FlextLogger",
            "    from flext_core.mixins import FlextMixins, x",
            "    from flext_core.models import FlextModels, m",
            "    from flext_core.protocols import FlextProtocols, p",
            "    from flext_core.registry import FlextRegistry",
            "    from flext_core.result import FlextResult, r",
            "    from flext_core.runtime import FlextRuntime",
            "    from flext_core.service import FlextService, s",
            "    from flext_core.settings import FlextSettings",
            "    from flext_core.typings import FlextTypes, t",
            "    from flext_core.utilities import FlextUtilities, u",
            "",
            "_LAZY_IMPORTS = build_lazy_import_map(ROOT_LAZY_MODULES, sort_keys=False)",
            "_PUBLISHED_NAMES = frozenset({*_LAZY_IMPORTS, *ROOT_METADATA_NAMES})",
            "_PUBLIC_NAMES = frozenset(ROOT_ALL)",
            '_ROOT_EXPORTS_DRIFT_ERROR = "flext_core root exports drift from ROOT_ALL"',
            "if not _PUBLIC_NAMES <= _PUBLISHED_NAMES:",
            "    raise RuntimeError(_ROOT_EXPORTS_DRIFT_ERROR)",
            "",
            "install_lazy_exports(",
            "    __name__,",
            "    globals(),",
            "    _LAZY_IMPORTS,",
            "    public_exports=ROOT_ALL,",
            ")",
            "",
        ]
        return "\n".join(lines)

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
    def get_template(cls, name: str) -> p.Infra.RenderableTemplate:
        """Return a template narrowed to the local render protocol."""
        env = cls._env
        if env is None:
            env = cls._build_env()
            cls._env = env
        return env.get_template(name)

    @staticmethod
    def _generate_import_lines(
        groups: t.MappingKV[str, t.StrPairSequence],
        *,
        indent: str = "",
    ) -> t.StrSequence:
        """Generate import lines grouped by module path."""
        if not groups:
            return ()

        lines: t.MutableSequenceOf[str] = []

        def _emit_module(mod: str) -> None:
            """Emit module."""
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
        groups: t.MappingKV[str, t.StrPairSequence],
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
            return ("if TYPE_CHECKING:", "    from flext_core import FlextTypes")

        normalized_groups: dict[str, t.StrPairSequence] = {}
        for mod, items in groups.items():
            resolved = FlextInfraCodegenGeneration._normalize_type_checking_module_path(
                mod,
                local_package_root,
            )
            FlextInfraCodegenGeneration._reject_non_absolute_import(
                resolved,
                local_package_root,
                items,
            )
            normalized_groups[resolved] = items
        collapsed = FlextInfraCodegenGeneration._collapse_to_children(
            normalized_groups, child_packages
        )
        root_name = "" if not local_package_root else local_package_root.split(".")[0]

        lines: t.MutableSequenceOf[str] = ["if TYPE_CHECKING:"]
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
        filtered: t.LazyAliasMap,
        inline_constants: t.StrMapping,
        current_pkg: str,
        eager_imports: t.LazyAliasMap | None = None,
        type_checking_imports: t.LazyAliasMap | None = None,
        wildcard_runtime_modules: t.StrSequence | None = None,
        child_packages_for_lazy: t.StrSequence | None = None,
        excluded_lazy_names: t.StrSequence | None = None,
    ) -> str:
        """Generate complete module file with lazy imports and type hints.

        Args:
            exports: List of all exported names.
            filtered: Mapping of export names to (module_path, attr_name) tuples.
            inline_constants: Mapping of constant names to their string values.
            current_pkg: Current package name for import strategy selection.
            eager_imports: Runtime imports that must exist eagerly in module globals.
            type_checking_imports: Static-only imports exposed to type checkers.
            child_packages_for_lazy: Child packages for lazy import collapsing.
            excluded_lazy_names: Runtime lazy merge exclusions.

        Returns:
            Complete Python module file as a single string.

        """
        if current_pkg == "flext_core":
            return FlextInfraCodegenGeneration._generate_flext_core_root_file()
        if FlextInfraCodegenGeneration._uses_direct_bootstrap(current_pkg):
            direct_filtered = filtered
            direct_exports = exports
            if current_pkg == "flext_core._typings":
                direct_filtered = {
                    name: target
                    for name, target in filtered.items()
                    if target[0] == "flext_core._typings.lazy"
                }
                direct_exports = tuple(
                    name for name in exports if name in direct_filtered
                )
            return FlextInfraCodegenGeneration._generate_direct_bootstrap_file(
                direct_exports,
                direct_filtered,
                inline_constants,
                current_pkg,
            )
        runtime_imports: t.LazyAliasMap = eager_imports or {}
        lazy_filtered: t.LazyAliasMap = dict(filtered)
        wildcard_runtime_module_set = frozenset(wildcard_runtime_modules or ())
        publish_all = FlextInfraCodegenGeneration._is_public_api_root_namespace(
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
        public_export_set = frozenset(published_exports)
        type_checking_filtered: t.LazyAliasMap = {
            name: val
            for name, val in (
                type_checking_imports
                if type_checking_imports is not None
                else lazy_filtered
            ).items()
            if val[0] not in wildcard_runtime_module_set
            and (not publish_all or name in public_export_set)
        }
        merged_excluded_lazy_names = tuple(
            sorted(c.Infra.INFRA_ONLY_EXPORTS | set(excluded_lazy_names or ()))
        )
        children_lazy = (
            ()
            if FlextInfraCodegenGeneration._uses_static_child_map(current_pkg)
            else tuple(child_packages_for_lazy or ())
        )
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
        runtime_import_block: t.MutableSequenceOf[str] = [
            f"from {module} import *"
            for module in sorted(set(wildcard_runtime_modules or ()))
        ]
        if runtime_import_block and runtime_import_lines:
            runtime_import_block.append("")
        runtime_import_block.extend(runtime_import_lines)

        lazy_entry_names = tuple(sorted(lazy_filtered)) if publish_all else exports
        lazy_entries = FlextInfraCodegenGeneration._build_lazy_entries(
            lazy_entry_names,
            lazy_filtered,
            (current_pkg, frozenset(children_lazy), not publish_all),
        )
        lazy_module_groups, lazy_alias_groups = (
            FlextInfraCodegenGeneration._group_lazy_entries(lazy_entries)
        )
        type_checking_lines = (
            FlextInfraCodegenGeneration.generate_type_checking(
                FlextInfraCodegenGeneration._group_imports(type_checking_filtered),
                include_flext_types=False,
                child_packages=(),
                local_package_root=current_pkg,
            )
            if type_checking_filtered
            else ()
        )

        out: t.MutableSequenceOf[str] = [c.Infra.AUTOGEN_HEADER]
        docstring_pkg = (
            current_pkg if publish_all else current_pkg.rsplit(".", maxsplit=1)[-1]
        )
        out.extend([
            FlextInfraCodegenGeneration._format_root_package_docstring(docstring_pkg),
            "",
        ])

        preamble_template = FlextInfraCodegenGeneration.get_template(
            c.Infra.TEMPLATE_PREAMBLE_STANDARD
        )
        preamble: str = preamble_template.render(
            type_checking_enabled=bool(type_checking_lines),
            use_merge_lazy_imports=use_merge_lazy_imports,
        )
        out.extend(preamble.splitlines())

        if not runtime_import_block:
            out.append("")

        body_template = FlextInfraCodegenGeneration.get_template(c.Infra.TEMPLATE_BODY)
        body: str = body_template.render(
            runtime_import_lines="\n".join(runtime_import_block),
            child_module_paths=rendered_child_module_paths,
            excluded_lazy_names=merged_excluded_lazy_names,
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

        getattr_template = FlextInfraCodegenGeneration.get_template(
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
