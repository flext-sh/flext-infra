"""Lazy import entry helpers for generated ``__init__`` files."""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from flext_infra import c
from flext_infra.codegen._codegen_generation_type_checking import (
    FlextInfraCodegenGenerationTypeCheckingMixin,
)

if TYPE_CHECKING:
    from flext_infra import t

type _LazyEntryContext = tuple[str, frozenset[str], bool]


class FlextInfraCodegenGenerationLazyEntriesMixin(
    FlextInfraCodegenGenerationTypeCheckingMixin
):
    """Lazy-entry grouping and publication helper methods."""

    @staticmethod
    def _build_lazy_entries(
        exports: t.StrSequence,
        lazy_filtered: t.LazyAliasMap,
        context: _LazyEntryContext,
    ) -> t.SequenceOf[tuple[str, str, str]]:
        """Build normalized lazy entries for template rendering."""
        current_pkg, child_aliases, include_module_exports = context
        entries: t.MutableSequenceOf[tuple[str, str, str]] = []
        for exp in exports:
            if exp not in lazy_filtered:
                continue
            mod, attr = lazy_filtered[exp]
            module_or_package_export = FlextInfraCodegenGenerationLazyEntriesMixin._is_module_or_package_export(
                attr
            )
            if module_or_package_export and not include_module_exports:
                continue
            child_package_module = (
                module_or_package_export
                and mod in child_aliases
                and exp == mod.rsplit(".", maxsplit=1)[-1]
            )
            compact_mod = (
                FlextInfraCodegenGenerationLazyEntriesMixin._compact_lazy_module_path(
                    current_pkg, mod
                )
            )
            if mod in child_aliases and not attr and not child_package_module:
                continue
            entries.append((exp, compact_mod, attr))
        return entries

    @staticmethod
    def _group_lazy_entries(
        lazy_entries: t.SequenceOf[tuple[str, str, str]],
    ) -> tuple[t.SequenceOf[t.StrSequencePair], t.SequenceOf[t.StrPairSequencePair]]:
        """Group lazy entries by module and alias group."""
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
        exports: t.StrSequence, lazy_filtered: t.LazyAliasMap
    ) -> t.StrSequence:
        """Build root public exports preserving canonical alias order."""
        # mro-wkii.17.26 (codex): the planner is the sole ABI filter; rendering
        # only orders its validated contract and must not reinterpret target paths.
        _ = lazy_filtered
        export_candidates = tuple(dict.fromkeys(exports))
        alias_order = c.Infra.PUBLIC_ROOT_ALIAS_ORDER
        return tuple(
            export_name
            for _index, export_name in sorted(
                enumerate(export_candidates),
                key=FlextInfraCodegenGenerationLazyEntriesMixin._public_export_order_key,
            )
            if export_name not in alias_order
        ) + tuple(name for name in alias_order if name in export_candidates)

    @staticmethod
    def _public_export_order_key(item: tuple[int, str]) -> tuple[int, int, str]:
        """Order classes before metadata before root aliases."""
        index, export_name = item
        if export_name in c.Infra.PUBLIC_ROOT_ALIAS_ORDER:
            return (2, index, export_name)
        if export_name.startswith("__") and export_name.endswith("__"):
            return (1, index, export_name)
        return (0, index, export_name)


__all__: list[str] = ["FlextInfraCodegenGenerationLazyEntriesMixin"]
