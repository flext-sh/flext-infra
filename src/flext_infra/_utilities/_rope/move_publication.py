"""Native publication-token changes participating in a module move.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import importlib.util
from collections.abc import Mapping, Set as AbstractSet

from flext_cli import u

from flext_infra import c, p, r
from flext_infra._models.transformers import FlextInfraModelsTransformers
from flext_infra._utilities._rope import (
    FlextInfraUtilitiesRopeRuntimeRefactors,
    FlextInfraUtilitiesRopeRuntimeTypes,
)


class FlextInfraUtilitiesRopeMovePublication:
    """Keep lazy publication providers inside the native source transaction."""

    @classmethod
    def rewrite_module_move_publications(
        cls,
        module: p.Infra.RopeSourceModule,
        *,
        package: str,
        moves: Mapping[str, str],
        exports: Mapping[str, AbstractSet[str]] | None = None,
    ) -> p.Result[str]:
        """Retarget proven installer literals without rebuilding their module.

        Rope move owns executable imports. Native binding metadata selects only
        the canonical installer and optional native MappingProxyType wrapper.
        Literal changes
        preserve keys, attributes, comments and all unrelated source bytes.

        Returns:
            Candidate source or the original typed publication refusal.

        """
        edits: dict[tuple[int, int], p.Infra.SourceRewrite] = {}
        index = module.get_source_binding_index()
        imported = cls._import_provider_edits(
            index, package=package, moves=moves, edits=edits
        )
        if imported.failure:
            return r[str].from_failure(imported)
        for mapping in index.string_mapping_arguments(
            "install_lazy_exports", c.Infra.LAZY_EXPORT_MAPPING_ARGUMENT_INDEX
        ):
            if not cls._canonical_installer(mapping):
                continue
            literals = cls._mapping_edits(
                mapping, package=package, moves=moves, exports=exports, edits=edits
            )
            if literals.failure:
                return r[str].from_failure(literals)
        if not edits:
            return r[str].ok(module.source_code)
        resource = module.get_resource()
        if resource is None:
            return r[str].fail("Lazy publication move requires a source resource")
        changed = FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
            resource, module.source_code, tuple(edits.values())
        )
        return r[str].ok(changed.new_contents)

    @staticmethod
    def _import_provider_edits(
        index: p.Infra.RopeSourceBindingIndex,
        *,
        package: str,
        moves: Mapping[str, str],
        edits: dict[tuple[int, int], p.Infra.SourceRewrite],
    ) -> p.Result[bool]:
        """Record executable import providers relocated by the module move.

        Returns:
            Successful admission or the package-escape refusal.

        """
        for declaration in index.import_layouts():
            if declaration.module_region is None:
                continue
            provider = "." * declaration.level + (declaration.module_name or "")
            if declaration.level > len(package.split(".")):
                return r[bool].fail("Module import provider escapes its package")
            absolute = (
                importlib.util.resolve_name(provider, package)
                if declaration.level
                else provider
            )
            relocated = moves.get(absolute)
            if relocated is not None:
                start, end = declaration.module_region
                edits[start, end] = FlextInfraModelsTransformers.SourceRewrite(
                    start=start, end=end, text=relocated
                )
        return r[bool].ok(value=True)

    @staticmethod
    def _canonical_installer(mapping: p.Infra.RopeSourceStringMapping) -> bool:
        """Return whether the mapping feeds the canonical lazy-export installer.

        Returns:
            True only for the bootstrap module's absolute installer binding.

        """
        installer = mapping.callee_binding
        return (
            FlextInfraUtilitiesRopeRuntimeTypes.imported_name(installer)
            and installer.imported_name == "install_lazy_exports"
            and installer.imported_module.module_name == c.Infra.LAZY_BOOTSTRAP_MODULE
            and installer.imported_module.level == 0
        )

    @staticmethod
    def _mapping_entries(
        mapping: p.Infra.RopeSourceStringMapping,
    ) -> p.Result[tuple[tuple[str, tuple[str, ...], tuple[tuple[int, int], ...]], ...]]:
        """Read literals, optionally enclosed by the native MappingProxyType.

        Returns:
            The literal mapping entries, or the typed admission refusal.

        """
        result_type = r[
            tuple[tuple[str, tuple[str, ...], tuple[tuple[int, int], ...]], ...]
        ]
        entries = mapping.entries
        if entries is None:
            return result_type.fail("Lazy publication move requires a literal mapping")
        wrappers = mapping.wrapper_bindings
        if not wrappers:
            return result_type.ok(entries)
        if len(wrappers) != 1:
            return result_type.fail("Lazy publication move requires one native wrapper")
        wrapper = wrappers[0]
        if not (
            FlextInfraUtilitiesRopeRuntimeTypes.imported_name(wrapper)
            and wrapper.imported_name == "MappingProxyType"
            and wrapper.imported_module.module_name == "types"
            and wrapper.imported_module.level == 0
        ):
            return result_type.fail(
                "Lazy publication move requires the native MappingProxyType"
            )
        return result_type.ok(entries)

    @classmethod
    def _mapping_edits(
        cls,
        mapping: p.Infra.RopeSourceStringMapping,
        *,
        package: str,
        moves: Mapping[str, str],
        exports: Mapping[str, AbstractSet[str]] | None,
        edits: dict[tuple[int, int], p.Infra.SourceRewrite],
    ) -> p.Result[bool]:
        """Record relocated provider literals of one admitted installer mapping.

        Returns:
            Successful admission or the original typed publication refusal.

        """
        entries = cls._mapping_entries(mapping)
        if entries.failure:
            return r[bool].from_failure(entries)
        for key, values, regions in entries.value:
            if len(values) not in {1, 2}:
                return r[bool].fail(
                    "Lazy publication move requires a provider/attribute pair"
                )
            provider = values[0]
            if provider.startswith(".") and len(provider) - len(
                provider.lstrip(".")
            ) > len(package.split(".")):
                return r[bool].fail("Lazy publication provider escapes its package")
            absolute = (
                importlib.util.resolve_name(provider, package)
                if provider.startswith(".")
                else provider
            )
            relocated = moves.get(absolute)
            if relocated is None or (exports and key not in exports.get(relocated, ())):
                continue
            replacement = (
                "." + relocated[len(package) + 1 :]
                if relocated.startswith(f"{package}.")
                else relocated
            )
            literal = u.Cli.json_dumps(replacement)
            if literal.failure:
                return r[bool].from_failure(literal)
            start, end = regions[0]
            edits[start, end] = FlextInfraModelsTransformers.SourceRewrite(
                start=start, end=end, text=literal.value
            )
        return r[bool].ok(value=True)


__all__: list[str] = ["FlextInfraUtilitiesRopeMovePublication"]
