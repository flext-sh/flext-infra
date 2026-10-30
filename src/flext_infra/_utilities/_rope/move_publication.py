"""Native publication-token changes participating in a module move.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import importlib.util
from collections.abc import Mapping, Set as AbstractSet

from flext_cli import u

from flext_infra import c, m, p, r
from flext_infra._utilities._rope import (
    FlextInfraUtilitiesRopeRuntimeRefactors,
    FlextInfraUtilitiesRopeRuntimeTypes,
)


class FlextInfraUtilitiesRopeMovePublication:
    """Keep lazy publication providers inside the native source transaction."""

    @staticmethod
    def rewrite_module_move_publications(
        module: p.Infra.RopeSourceModule,
        *,
        package: str,
        moves: Mapping[str, str],
        exports: Mapping[str, AbstractSet[str]] | None = None,
    ) -> p.Result[str]:
        """Retarget proven installer literals without rebuilding their module.

        Rope move owns executable imports. Native binding metadata selects only
        the canonical installer and MappingProxyType wrapper. Literal changes
        preserve keys, attributes, comments and all unrelated source bytes.

        Returns:
            Candidate source or the original typed publication refusal.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeTypes
        edits: dict[tuple[int, int], m.Infra.SourceRewrite] = {}
        index = module.get_source_binding_index()
        for declaration in index.import_layouts():
            if declaration.module_region is None:
                continue
            provider = "." * declaration.level + (declaration.module_name or "")
            if declaration.level > len(package.split(".")):
                return r[str].fail("Module import provider escapes its package")
            absolute = (
                importlib.util.resolve_name(provider, package)
                if declaration.level
                else provider
            )
            relocated = moves.get(absolute)
            if relocated is not None:
                start, end = declaration.module_region
                edits[start, end] = m.Infra.SourceRewrite(
                    start=start, end=end, text=relocated
                )
        for mapping in index.string_mapping_arguments("install_lazy_exports", 2):
            installer = mapping.callee_binding
            if not (
                runtime.imported_name(installer)
                and installer.imported_name == "install_lazy_exports"
                and installer.imported_module.module_name
                == c.Infra.LAZY_BOOTSTRAP_MODULE
                and installer.imported_module.level == 0
            ):
                continue
            if mapping.entries is None:
                return r[str].fail("Lazy publication move requires a literal mapping")
            if len(mapping.wrapper_bindings) != 1:
                return r[str].fail("Lazy publication move requires MappingProxyType")
            wrapper = mapping.wrapper_bindings[0]
            if not (
                runtime.imported_name(wrapper)
                and wrapper.imported_name == "MappingProxyType"
                and wrapper.imported_module.module_name == "types"
                and wrapper.imported_module.level == 0
            ):
                return r[str].fail(
                    "Lazy publication move requires the native MappingProxyType"
                )
            for key, values, regions in mapping.entries:
                if len(values) not in {1, 2}:
                    return r[str].fail(
                        "Lazy publication move requires a provider/attribute pair"
                    )
                provider = values[0]
                if provider.startswith(".") and len(provider) - len(
                    provider.lstrip(".")
                ) > len(package.split(".")):
                    return r[str].fail("Lazy publication provider escapes its package")
                absolute = (
                    importlib.util.resolve_name(provider, package)
                    if provider.startswith(".")
                    else provider
                )
                relocated = moves.get(absolute)
                if relocated is None or (
                    exports and key not in exports.get(relocated, ())
                ):
                    continue
                replacement = (
                    "." + relocated[len(package) + 1 :]
                    if relocated.startswith(f"{package}.")
                    else relocated
                )
                literal = u.Cli.json_dumps(replacement)
                if literal.failure:
                    return r[str].from_failure(literal)
                start, end = regions[0]
                edits[start, end] = m.Infra.SourceRewrite(
                    start=start, end=end, text=literal.value
                )
        if not edits:
            return r[str].ok(module.source_code)
        resource = module.get_resource()
        if resource is None:
            return r[str].fail("Lazy publication move requires a source resource")
        changed = FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
            resource, module.source_code, tuple(edits.values())
        )
        return r[str].ok(changed.new_contents)


__all__: list[str] = ["FlextInfraUtilitiesRopeMovePublication"]
