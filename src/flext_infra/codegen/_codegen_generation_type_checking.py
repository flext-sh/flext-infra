"""TYPE_CHECKING render helpers for lazy-init generation.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import MutableMapping
from typing import TYPE_CHECKING

from flext_infra.codegen import FlextInfraCodegenGenerationImportsMixin

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraCodegenGenerationTypeCheckingMixin(
    FlextInfraCodegenGenerationImportsMixin,
):
    """TYPE_CHECKING block generation helper methods."""

    @staticmethod
    def _collapse_to_children(
        groups: t.MappingKV[str, t.StrPairSequence],
        child_packages: t.StrSequence | None,
    ) -> t.MappingKV[str, t.MutableSequenceOf[t.StrPair]]:
        """Collapse child module imports into configured child packages.

        Returns:
            The resulting ``t.MappingKV[str, t.MutableSequenceOf[t.StrPair]]``.

        """
        sorted_children: list[str] = sorted(
            set(child_packages or []),
            key=len,
            reverse=True,
        )
        collapsed: MutableMapping[str, list[t.StrPair]] = defaultdict(list)
        for mod, items in groups.items():
            target = mod
            for child_package in sorted_children:
                if mod.startswith(child_package + ".") or mod == child_package:
                    target = child_package
                    break
            collapsed[target].extend(items)
        return collapsed

    @staticmethod
    def _has_flext_types(collapsed: t.MappingKV[str, t.StrPairSequence]) -> bool:
        """Return whether a collapsed import map already imports FlextTypes.

        Returns:
            Whether a collapsed import map already imports FlextTypes.

        """
        return any(
            export_name == "FlextTypes"
            for items in collapsed.values()
            for export_name, _ in items
        )

    @staticmethod
    def _type_checking_sort_key(mod: str, root_names: frozenset[str]) -> t.StrPair:
        """Rank an import by ruff isort section, then by module path.

        ruff/isort partitions imports into sections — third-party, then
        first-party (this package's own root), then local (relative) — sorted
        alphabetically within each section and separated by a single blank
        line (``section_whitelines``). The legacy rank lumped every absolute
        import into one alphabetical run, so a third-party import (e.g.
        ``flext_tests``) sorted ahead of this package's own first-party import,
        violating I001 in the generated ``tests`` initializers. Sections are
        derived from the emitted module's owner and the package root so the
        generated order mirrors each project's ruff isort config.

        Returns:
            The resulting ``t.StrPair``.

        """
        if mod.startswith("."):
            return ("2", mod.lower())  # local-folder section
        own_top = mod.split(".", maxsplit=1)[0]
        return ("1" if own_top in root_names else "0", mod.lower())

    @staticmethod
    def _merge_root_alias_groups(
        collapsed: t.MappingKV[str, t.MutableSequenceOf[t.StrPair]],
    ) -> MutableMapping[str, t.StrPairSequence]:
        """Group each elected static reexport by its emitted import owner.

        Returns:
            The resulting ``MutableMapping[str, t.StrPairSequence]``.

        """
        merged: MutableMapping[str, t.StrPairSequence] = {}
        for mod, items in collapsed.items():
            for export_name, attr_name in items:
                owner, imported = (
                    (mod.rpartition(".")[0], mod.rsplit(".", maxsplit=1)[-1])
                    if not attr_name and "." in mod
                    else (mod, attr_name)
                )
                merged[owner] = (
                    *merged.get(owner, ()),
                    (export_name, imported),
                )
        return merged

    @staticmethod
    def _emit_type_checking_module(
        mod: str,
        items: t.StrPairSequence,
        lines: t.MutableSequenceOf[str],
        module_exports: frozenset[str],
    ) -> None:
        """Emit one TYPE_CHECKING import from its resolved owner."""
        parts: t.MutableSequenceOf[str] = []
        for export_name, attr_name in sorted(
            items,
            key=FlextInfraCodegenGenerationTypeCheckingMixin._import_item_sort_key,
        ):
            if not attr_name:
                lines.extend(
                    FlextInfraCodegenGenerationTypeCheckingMixin._format_type_checking_module_alias_import(
                        "    ", mod, export_name
                    )
                )
                continue
            parts.append(
                f"{attr_name} as {export_name}"
                if export_name in module_exports
                else FlextInfraCodegenGenerationTypeCheckingMixin._format_import_part(
                    attr_name, export_name
                )
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

    @classmethod
    def generate_type_checking(
        cls,
        groups: t.MappingKV[str, t.StrPairSequence],
        *,
        include_flext_types: bool = True,
        child_packages: t.StrSequence | None = None,
        local_package_root: str | None = None,
        root_names: frozenset[str] | None = None,
    ) -> t.StrSequence:
        """Generate a TYPE_CHECKING import block.

        Returns:
            The resulting ``t.StrSequence``.

        """
        if not groups and not include_flext_types:
            return ()
        if not groups:
            return ("if TYPE_CHECKING:", "    from flext_core import FlextTypes")
        normalized_groups: MutableMapping[str, t.StrPairSequence] = {}
        for mod, items in groups.items():
            resolved = cls.normalize_type_checking_module_path(
                mod,
                local_package_root,
            )
            cls._reject_noncanonical_type_checking_import(
                resolved,
                local_package_root,
                items,
            )
            normalized_groups[resolved] = (*normalized_groups.get(resolved, ()), *items)
        collapsed = cls._collapse_to_children(normalized_groups, child_packages)
        module_exports = frozenset(
            name for items in collapsed.values() for name, attr in items if not attr
        )
        merged_groups = cls._merge_root_alias_groups(collapsed)
        if local_package_root:
            prefix = f"{local_package_root}."
            merged_groups = {
                (
                    f".{mod.removeprefix(prefix)}" if mod.startswith(prefix) else mod
                ): items
                for mod, items in merged_groups.items()
            }
        # With include_flext_types=False the collapsed groups are the only
        # content the block would carry; a package whose references collapsed
        # away (its re-exported children moved elsewhere) must render no
        # TYPE_CHECKING block at all — a bare "if TYPE_CHECKING:" header is
        # invalid Python and breaks every conform that follows.
        if not merged_groups and not include_flext_types:
            return ()
        root_name = "" if not local_package_root else local_package_root.split(".")[0]
        # Derive the set of first-party roots for isort sectioning. When the
        # caller provides an explicit root_names (e.g. test facades need both
        # "tests" and the project package), use it; otherwise fall back to the
        # single root_name so non-test packages are unaffected.
        effective_root_names = (
            root_names if root_names is not None else frozenset({root_name})
        )
        lines: t.MutableSequenceOf[str] = ["if TYPE_CHECKING:"]
        flext_types_emitted = include_flext_types and not cls._has_flext_types(
            collapsed,
        )
        if flext_types_emitted:
            lines.append("    from flext_core import FlextTypes")

        def type_checking_module_key(mod: str) -> t.StrPair:
            return cls._type_checking_sort_key(mod, effective_root_names)

        sorted_mods = sorted(merged_groups, key=type_checking_module_key)
        # ``from flext_core import FlextTypes`` (when emitted above) is the
        # leading absolute import; seed the previous section so the first loop
        # group only separates on a real ruff isort section transition rather
        # than against an empty prior state, and so the local-section blank that
        # follows the absolutes is preserved.
        previous_section: str | None = (
            cls._type_checking_sort_key("flext_core", effective_root_names)[0]
            if flext_types_emitted
            else None
        )
        for mod in sorted_mods:
            current_section = type_checking_module_key(mod)[0]
            if previous_section is not None and current_section != previous_section:
                lines.append("")
            cls._emit_type_checking_module(
                mod,
                merged_groups[mod],
                lines,
                module_exports,
            )
            previous_section = current_section
        return () if len(lines) == 1 else lines


__all__: list[str] = ["FlextInfraCodegenGenerationTypeCheckingMixin"]
