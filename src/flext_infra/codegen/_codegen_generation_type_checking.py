"""TYPE_CHECKING render helpers for lazy-init generation."""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from flext_infra.codegen._codegen_generation_imports import (
    FlextInfraCodegenGenerationImportsMixin,
)
from flext_infra.constants import c

if TYPE_CHECKING:
    from flext_infra.typings import t


class FlextInfraCodegenGenerationTypeCheckingMixin(
    FlextInfraCodegenGenerationImportsMixin,
):
    """TYPE_CHECKING block generation helper methods."""

    @staticmethod
    def _collapse_to_children(
        groups: t.MappingKV[str, t.StrPairSequence],
        child_packages: t.StrSequence | None,
    ) -> t.MappingKV[str, t.MutableSequenceOf[t.StrPair]]:
        """Collapse child module imports into configured child packages."""
        sorted_children: list[str] = sorted(
            set(child_packages or []),
            key=len,
            reverse=True,
        )
        collapsed: dict[str, list[t.StrPair]] = defaultdict(list)
        for mod, items in groups.items():
            target = mod
            for child_package in sorted_children:
                if mod.startswith(child_package + ".") or mod == child_package:
                    target = child_package
                    break
            collapsed[target].extend(items)
        return collapsed

    @staticmethod
    def _has_flext_types(
        collapsed: t.MappingKV[str, t.StrPairSequence],
    ) -> bool:
        """Return whether a collapsed import map already imports FlextTypes."""
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
        """Return a stable TYPE_CHECKING import sort key."""
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
        """Return whether a module-style export is redundant in TYPE_CHECKING."""
        if export_name in c.Infra.ALIAS_NAMES or not export_name:
            return False
        if export_name in {"cli", "main", "infra"}:
            return False
        if export_name != export_name.lower():
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
        """Emit one TYPE_CHECKING module import group."""
        alias_exports: t.MutableSequenceOf[str] = []
        parts: t.MutableSequenceOf[str] = []
        module_basename = mod.rsplit(".", maxsplit=1)[-1]
        for export_name, attr_name in sorted(
            items,
            key=lambda item: (item[1] or item[0], item[0] != (item[1] or item[0])),
        ):
            if FlextInfraCodegenGenerationTypeCheckingMixin._should_skip_type_checking_module_export(
                mod,
                export_name,
                attr_name,
                root_name,
            ):
                continue
            if not attr_name:
                target = alias_exports if export_name == module_basename else parts
                target.append(export_name)
                continue
            parts.append(f"{attr_name} as {export_name}")
        for export_name in tuple(dict.fromkeys(alias_exports)):
            lines.extend(
                FlextInfraCodegenGenerationTypeCheckingMixin._format_type_checking_module_alias_import(
                    "    ",
                    mod,
                    export_name,
                ),
            )
        deduped_parts = tuple(dict.fromkeys(parts))
        if deduped_parts:
            lines.extend(
                FlextInfraCodegenGenerationTypeCheckingMixin._format_import(
                    "    ",
                    mod,
                    deduped_parts,
                ),
            )

    @staticmethod
    def generate_type_checking(
        groups: t.MappingKV[str, t.StrPairSequence],
        *,
        include_flext_types: bool = True,
        child_packages: t.StrSequence | None = None,
        local_package_root: str | None = None,
    ) -> t.StrSequence:
        """Generate a TYPE_CHECKING import block."""
        if not groups and not include_flext_types:
            return ()
        if not groups:
            return ("if TYPE_CHECKING:", "    from flext_core import FlextTypes")
        normalized_groups: dict[str, t.StrPairSequence] = {}
        for mod, items in groups.items():
            resolved = FlextInfraCodegenGenerationTypeCheckingMixin._normalize_type_checking_module_path(
                mod,
                local_package_root,
            )
            FlextInfraCodegenGenerationTypeCheckingMixin._reject_non_absolute_import(
                resolved,
                local_package_root,
                items,
            )
            normalized_groups[resolved] = items
        collapsed = FlextInfraCodegenGenerationTypeCheckingMixin._collapse_to_children(
            normalized_groups,
            child_packages,
        )
        root_name = "" if not local_package_root else local_package_root.split(".")[0]
        lines: t.MutableSequenceOf[str] = ["if TYPE_CHECKING:"]
        if include_flext_types and (
            not FlextInfraCodegenGenerationTypeCheckingMixin._has_flext_types(collapsed)
        ):
            lines.append("    from flext_core import FlextTypes")
        sorted_mods = sorted(
            collapsed,
            key=lambda mod: (
                FlextInfraCodegenGenerationTypeCheckingMixin._type_checking_sort_key(
                    mod,
                    local_package_root,
                )
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
            FlextInfraCodegenGenerationTypeCheckingMixin._emit_type_checking_module(
                mod,
                collapsed[mod],
                root_name,
                lines,
            )
            prev_top = top
        return () if len(lines) == 1 else lines


__all__: list[str] = ["FlextInfraCodegenGenerationTypeCheckingMixin"]
